// Extract token from URL path: /interview/<token>
const token = window.location.pathname.split('/').pop();
let ws = null;
let cameraStream = null;
let screenStream = null;
let timerInterval = null;
let totalSeconds = 600;
let remainingSeconds = totalSeconds;
let waitingForAnswer = false;

// ─── Voice mode state ─────────────────────────────────────────────────────────
let voiceMode = false;
let recognition = null;
let isRecording = false;
let finalTranscript = '';
let synth = window.speechSynthesis;
let currentUtterance = null;
let voiceReady = false; // true after first user gesture (voices loaded)

// ─── Permission setup ────────────────────────────────────────────────────────
async function requestPermissions() {
  const btn = document.getElementById('grant-btn');
  btn.disabled = true;
  btn.textContent = 'Requesting permissions…';

  let camOk = false, micOk = false, screenOk = false;

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    document.getElementById('camera-preview').srcObject = cameraStream;
    setPermStatus('camera', true);
    setPermStatus('mic', true);
    camOk = true; micOk = true;
  } catch (e) {
    setPermStatus('camera', false, 'Denied');
    setPermStatus('mic', false, 'Denied');
  }

  try {
    screenStream = await navigator.mediaDevices.getDisplayMedia({
      video: { cursor: 'always' }, audio: false
    });
    setPermStatus('screen', true);
    screenOk = true;
    screenStream.getTracks().forEach(t => {
      t.addEventListener('ended', () => setPermStatus('screen', false, 'Stopped'));
    });
  } catch (e) {
    setPermStatus('screen', false, 'Denied');
  }

  if (camOk && micOk && screenOk) {
    btn.style.display = 'none';
    document.getElementById('ready-section').style.display = 'block';
  } else {
    btn.disabled = false;
    btn.textContent = 'Try Again';
  }
}

function setPermStatus(perm, ok, text) {
  const el = document.getElementById('status-' + perm);
  el.textContent = ok ? '✓ Enabled' : (text || 'Error');
  el.className = 'perm-status' + (ok ? ' ok' : '');
}

// ─── Voice toggle ─────────────────────────────────────────────────────────────
function onVoiceToggle() {
  voiceMode = !voiceMode;
  const card = document.getElementById('voice-toggle-card');
  const pill = document.getElementById('voice-toggle-pill');
  const dot  = document.getElementById('voice-toggle-dot');
  if (voiceMode) {
    if (card) card.style.borderColor = 'rgba(91,124,250,0.5)';
    if (card) card.style.background  = 'rgba(91,124,250,0.08)';
    if (pill) pill.style.background  = '#5b7cfa';
    if (dot)  { dot.style.left = 'calc(100% - 21px)'; dot.style.background = '#fff'; }
  } else {
    if (card) card.style.borderColor = 'rgba(148,163,184,0.15)';
    if (card) card.style.background  = '#0d1426';
    if (pill) pill.style.background  = '#1b2540';
    if (dot)  { dot.style.left = '3px'; dot.style.background = '#8899b4'; }
  }
}

// ─── Start interview ─────────────────────────────────────────────────────────
function startInterview() {
  document.getElementById('setup-screen').style.display = 'none';
  document.getElementById('interview-screen').style.display = 'flex';

  const ivCam = document.getElementById('interview-camera');
  if (cameraStream) ivCam.srcObject = cameraStream;

  if (voiceMode) initRecognition();
  connectWS();
}

// ─── WebSocket ───────────────────────────────────────────────────────────────
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/interview/${token}`);

  ws.onopen = () => addSystemMsg('Connected to interview server…');

  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    handleServerMsg(msg);
  };

  ws.onclose = () => {
    if (document.getElementById('interview-screen').style.display !== 'none') {
      addSystemMsg('Connection closed.');
    }
  };

  ws.onerror = () => addSystemMsg('Connection error. Please refresh.');
}

function handleServerMsg(msg) {
  switch (msg.type) {
    case 'welcome':
      totalSeconds = msg.duration_seconds || 600;
      remainingSeconds = totalSeconds;
      startTimer();
      updateProgress(0, msg.total_questions);
      if (voiceMode) {
        speakText(msg.message); // welcome spoken, no mic shown yet
      } else {
        addAIMsg(msg.message);
      }
      break;

    case 'question':
      remainingSeconds = msg.remaining_seconds || remainingSeconds;
      updateProgress(msg.question_num, msg.total);
      waitingForAnswer = true;
      addAIMsg(msg.text, `Question ${msg.question_num} of ${msg.total} · ${msg.category}`);
      if (voiceMode) {
        showVoiceArea(true);   // mic button visible right away
        setMicEnabled(true);   // mic immediately usable — don't block on TTS
        speakText(msg.text);   // TTS plays in background (no callback needed)
      } else {
        showInputArea(true);
        document.getElementById('answer-input').focus();
      }
      break;

    case 'ack':
      waitingForAnswer = false;
      if (voiceMode) {
        showVoiceArea(false);
        speakText(msg.message);
      } else {
        showInputArea(false);
        addSystemMsg(msg.message);
      }
      break;

    case 'timeout':
      waitingForAnswer = false;
      stopRecording();
      if (voiceMode) {
        showVoiceArea(false);
        speakText(msg.message);
      } else {
        showInputArea(false);
        addSystemMsg(msg.message);
      }
      break;

    case 'time_warning':
      remainingSeconds = msg.remaining_seconds || remainingSeconds;
      break;

    case 'time_up':
    case 'interview_end':
      waitingForAnswer = false;
      stopRecording();
      clearInterval(timerInterval);
      if (voiceMode) {
        showVoiceArea(false);
        speakText(msg.message, () => setTimeout(showDoneScreen, 2000));
      } else {
        showInputArea(false);
        addAIMsg(msg.message);
        setTimeout(showDoneScreen, 3000);
      }
      break;

    case 'error':
      addSystemMsg('⚠️ ' + msg.message);
      break;
  }
}

// ─── Voice: TTS (AI speaks) ──────────────────────────────────────────────────
function speakText(text, onDone) {
  if (!voiceMode || !synth) { onDone?.(); return; }

  synth.cancel();

  // Chrome Mac bug: tab focus changes (e.g. screen share dialog) pause synthesis
  try { synth.resume(); } catch(_) {}

  showAISpeaking(true);

  const utter = new SpeechSynthesisUtterance(text);
  currentUtterance = utter;

  const voices = synth.getVoices();
  const preferred = voices.find(v =>
    v.lang.startsWith('en') && (v.name.includes('Neural') || v.name.includes('Natural') || v.name.includes('Google'))
  ) || voices.find(v => v.lang.startsWith('en')) || voices[0];
  if (preferred) utter.voice = preferred;

  utter.rate   = 0.95;
  utter.pitch  = 1.0;
  utter.volume = 1.0;

  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    clearTimeout(fallbackTimer);
    showAISpeaking(false);
    onDone?.();
  };

  utter.onend   = finish;
  utter.onerror = finish;

  // Fallback: if onend never fires (Chrome bug), unblock after estimated duration
  const estimatedMs = Math.max(3000, text.length * 65);
  const fallbackTimer = setTimeout(finish, estimatedMs);

  const doSpeak = () => {
    try { synth.resume(); } catch(_) {}
    synth.speak(utter);
  };

  if (voices.length === 0) {
    synth.onvoiceschanged = () => { synth.onvoiceschanged = null; doSpeak(); };
  } else {
    doSpeak();
  }
}

function showAISpeaking(show) {
  const el = document.getElementById('ai-speaking');
  if (el) el.style.display = show ? 'flex' : 'none';
}

function setMicEnabled(enabled) {
  showAISpeaking(!enabled);
  const btn   = document.getElementById('mic-btn');
  const label = document.getElementById('mic-status-label');
  if (!btn) return;
  if (enabled) {
    btn.disabled = false;
    btn.style.opacity = '1';
    if (label) label.textContent = 'Tap to answer';
  } else {
    btn.disabled = true;
    btn.style.opacity = '0.4';
    if (label) label.textContent = 'AI is speaking…';
  }
}

// ─── Voice: STT (candidate speaks) ───────────────────────────────────────────
function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    let interim = '';
    finalTranscript = '';
    for (let i = 0; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + ' ';
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    document.getElementById('transcript-text').textContent = finalTranscript;
    document.getElementById('interim-text').textContent    = interim;
    const tBox = document.getElementById('voice-transcript');
    if (finalTranscript || interim) tBox.style.display = 'block';
    // Show send button once we have something to send
    const sendBtn = document.getElementById('voice-send-btn');
    sendBtn.style.display = finalTranscript.trim() ? 'block' : 'none';
  };

  recognition.onerror = (e) => {
    if (e.error !== 'no-speech') addSystemMsg('Speech error: ' + e.error);
    isRecording = false;
    updateMicUI(false);
  };

  recognition.onend = () => {
    if (isRecording) {
      // Auto-restart so continuous recognition keeps going
      try { recognition.start(); } catch(_) {}
    } else {
      updateMicUI(false);
    }
  };
}

function toggleRecording() {
  if (!waitingForAnswer) return;
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

function startRecording() {
  if (!recognition || isRecording) return;
  // Cancel AI speech so candidate can speak cleanly
  try { synth?.cancel(); } catch(_) {}
  showAISpeaking(false);
  finalTranscript = '';
  document.getElementById('transcript-text').textContent = '';
  document.getElementById('interim-text').textContent    = '';
  document.getElementById('voice-transcript').style.display = 'none';
  document.getElementById('voice-send-btn').style.display   = 'none';
  isRecording = true;
  updateMicUI(true);
  try { recognition.start(); } catch(_) {}
}

function stopRecording() {
  if (!recognition || !isRecording) return;
  isRecording = false;
  try { recognition.stop(); } catch(_) {}
  updateMicUI(false);
}

function updateMicUI(recording) {
  const btn   = document.getElementById('mic-btn');
  const label = document.getElementById('mic-status-label');
  const ring1 = document.getElementById('mic-ring-1');
  const ring2 = document.getElementById('mic-ring-2');
  if (!btn) return;
  if (recording) {
    btn.classList.add('recording');
    if (ring1) ring1.classList.add('active');
    if (ring2) ring2.classList.add('active');
    if (label) label.textContent = 'Listening… tap to stop';
  } else {
    btn.classList.remove('recording');
    if (ring1) ring1.classList.remove('active');
    if (ring2) ring2.classList.remove('active');
    if (label) label.textContent = finalTranscript.trim() ? 'Done — send or re-record' : 'Tap to answer';
  }
}

function sendVoiceAnswer() {
  if (!waitingForAnswer) return;
  const text = finalTranscript.trim();
  if (!text) return;
  stopRecording();
  ws.send(JSON.stringify({ type: 'answer', text }));
  addUserMsg(text);
  finalTranscript = '';
  document.getElementById('transcript-text').textContent = '';
  document.getElementById('interim-text').textContent    = '';
  document.getElementById('voice-transcript').style.display = 'none';
  document.getElementById('voice-send-btn').style.display   = 'none';
}

// ─── Show / hide input areas ─────────────────────────────────────────────────
function showInputArea(show) {
  document.getElementById('input-area').style.display = show ? 'flex' : 'none';
  if (show) document.getElementById('answer-input').value = '';
}

function showVoiceArea(show) {
  const area = document.getElementById('voice-area');
  if (!area) return;
  area.style.display = show ? 'flex' : 'none';
  if (show) {
    finalTranscript = '';
    document.getElementById('transcript-text').textContent    = '';
    document.getElementById('interim-text').textContent       = '';
    document.getElementById('voice-transcript').style.display = 'none';
    document.getElementById('voice-send-btn').style.display   = 'none';
    showAISpeaking(false);
    updateMicUI(false);
  } else {
    stopRecording();
    showAISpeaking(false);
  }
}

// ─── Chat UI ─────────────────────────────────────────────────────────────────
function addAIMsg(text, badge) {
  const box = document.getElementById('chat-box');
  const div = document.createElement('div');
  div.className = 'chat-msg ai';
  div.innerHTML = `
    ${badge ? `<div class="question-badge">${esc(badge)}</div>` : ''}
    <div class="msg-bubble">${esc(text)}</div>
    <div class="msg-meta">AI Interviewer · ${now()}</div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function addUserMsg(text) {
  const box = document.getElementById('chat-box');
  const div = document.createElement('div');
  div.className = 'chat-msg user';
  div.innerHTML = `
    <div class="msg-bubble">${esc(text)}</div>
    <div class="msg-meta">You · ${now()}</div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function addSystemMsg(text) {
  const box = document.getElementById('chat-box');
  const div = document.createElement('div');
  div.style.cssText = 'text-align:center;font-size:0.78rem;color:#475569;padding:4px 0';
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// ─── Text answer ─────────────────────────────────────────────────────────────
function sendAnswer() {
  if (!waitingForAnswer) return;
  const input = document.getElementById('answer-input');
  const text = input.value.trim();
  if (!text) return;
  ws.send(JSON.stringify({ type: 'answer', text }));
  addUserMsg(text);
  input.value = '';
  document.getElementById('send-btn').disabled = true;
  setTimeout(() => document.getElementById('send-btn').disabled = false, 500);
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendAnswer();
  }
}

// ─── Timer ────────────────────────────────────────────────────────────────────
function startTimer() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    remainingSeconds = Math.max(0, remainingSeconds - 1);
    updateTimer(remainingSeconds);
    if (remainingSeconds <= 0) clearInterval(timerInterval);
  }, 1000);
}

function updateTimer(secs) {
  const el = document.getElementById('timer-display');
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  el.textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  el.className = 'timer-value';
  if (secs <= 60) el.classList.add('critical');
  else if (secs <= 120) el.classList.add('warning');
}

function updateProgress(current, total) {
  document.getElementById('progress-text').textContent = `Question ${current} of ${total}`;
  document.getElementById('progress-fill').style.width = total ? `${(current / total) * 100}%` : '0%';
}

// ─── Done screen ──────────────────────────────────────────────────────────────
function showDoneScreen() {
  document.getElementById('interview-screen').style.display = 'none';
  document.getElementById('done-screen').style.display = 'flex';
  synth?.cancel();
  stopRecording();
  [cameraStream, screenStream].forEach(s => s?.getTracks().forEach(t => t.stop()));
}

function esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
