import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, COMPANY_NAME, BASE_URL


# ─── Email wrapper ────────────────────────────────────────────────────────────

def _build_message(to_email: str, subject: str, html_body: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{COMPANY_NAME} <{EMAIL_FROM}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))
    return msg


def _send(to_email: str, subject: str, html_body: str) -> None:
    msg = _build_message(to_email, subject, html_body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, [to_email], msg.as_string())


# ─── Shared layout helpers ────────────────────────────────────────────────────

def _email_wrapper(header_html: str, body_html: str, footer_extra: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#eef0f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;-webkit-text-size-adjust:100%">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eef0f5">
  <tr>
    <td align="center" style="padding:48px 16px">

      <!-- Outer card -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">

        <!-- Header -->
        {header_html}

        <!-- Body card -->
        <tr>
          <td style="background:#ffffff;padding:40px 48px;border-left:1px solid #e2e5ea;border-right:1px solid #e2e5ea">
            {body_html}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f8f9fb;border:1px solid #e2e5ea;border-top:0;border-radius:0 0 16px 16px;padding:24px 48px;text-align:center">
            <p style="margin:0 0 6px;font-size:13px;color:#9ca3af">This email was sent by <strong style="color:#6b7280">{COMPANY_NAME}</strong></p>
            <p style="margin:0;font-size:12px;color:#c0c4cc">{footer_extra}If you did not expect this email, you can safely ignore it.</p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

</body>
</html>"""


def _divider() -> str:
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:28px 0"><tr><td style="border-top:1px solid #f0f2f6"></td></tr></table>'


def _checklist_item(icon: str, text: str) -> str:
    return f"""
    <tr>
      <td style="padding:7px 0;vertical-align:top">
        <table role="presentation" cellpadding="0" cellspacing="0">
          <tr>
            <td style="width:28px;vertical-align:top;padding-top:1px">
              <span style="display:inline-block;width:20px;height:20px;border-radius:50%;background:#eef2ff;text-align:center;line-height:20px;font-size:11px">{icon}</span>
            </td>
            <td style="font-size:14px;color:#374151;line-height:1.6">{text}</td>
          </tr>
        </table>
      </td>
    </tr>"""


def _step_item(number: str, title: str, desc: str) -> str:
    return f"""
    <tr>
      <td style="padding:10px 0;vertical-align:top">
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
          <tr>
            <td style="width:36px;vertical-align:top;padding-top:2px">
              <span style="display:inline-block;width:26px;height:26px;border-radius:50%;background:#4f46e5;color:#fff;text-align:center;line-height:26px;font-size:12px;font-weight:700">{number}</span>
            </td>
            <td>
              <p style="margin:0 0 2px;font-size:14px;font-weight:600;color:#111827">{title}</p>
              <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.5">{desc}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


# ─── Interview Invitation ─────────────────────────────────────────────────────

def send_interview_invitation(candidate_name: str, to_email: str, meeting_token: str) -> None:
    link = f"{BASE_URL}/interview/{meeting_token}"
    subject = f"Your Interview Invitation — {COMPANY_NAME}"

    first_name = candidate_name.split()[0] if candidate_name else candidate_name

    header = f"""
    <tr>
      <td style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#4338ca 100%);border-radius:16px 16px 0 0;padding:36px 48px 32px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <p style="margin:0 0 20px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:2px;color:rgba(199,210,254,0.8)">Interview Invitation</p>
              <p style="margin:0 0 4px;font-size:28px;font-weight:700;color:#ffffff;line-height:1.2">You've been<br>shortlisted! &#127881;</p>
            </td>
            <td align="right" style="vertical-align:top">
              <span style="display:inline-block;width:52px;height:52px;background:rgba(255,255,255,0.1);border-radius:14px;text-align:center;line-height:52px;font-size:24px">&#128203;</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""

    body = f"""
    <p style="margin:0 0 8px;font-size:16px;color:#111827;font-weight:600">Dear {first_name},</p>
    <p style="margin:0 0 20px;font-size:15px;color:#374151;line-height:1.7">
      Congratulations — after carefully reviewing your application, we are pleased to invite you to the
      next stage of our hiring process at <strong>{COMPANY_NAME}</strong>. We were impressed with your
      background and believe you could be a great fit.
    </p>

    <!-- CTA Button -->
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0">
      <tr>
        <td style="border-radius:10px;background:#4f46e5">
          <a href="{link}" target="_blank"
             style="display:inline-block;padding:15px 36px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;letter-spacing:0.3px;border-radius:10px">
            Begin Your Interview &rarr;
          </a>
        </td>
      </tr>
    </table>

    <p style="margin:0 0 6px;font-size:12px;color:#9ca3af;text-align:center">
      Or copy this link: <span style="color:#6366f1;word-break:break-all">{link}</span>
    </p>

    {_divider()}

    <!-- Info box -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8f7ff;border:1px solid #e0e7ff;border-radius:10px;margin-bottom:24px">
      <tr>
        <td style="padding:20px 24px">
          <p style="margin:0 0 12px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#6366f1">Interview Details</p>
          <table role="presentation" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:4px 16px 4px 0;font-size:13px;color:#6b7280;white-space:nowrap">&#8987; Duration</td>
              <td style="padding:4px 0;font-size:13px;color:#111827;font-weight:600">Up to 10 minutes</td>
            </tr>
            <tr>
              <td style="padding:4px 16px 4px 0;font-size:13px;color:#6b7280;white-space:nowrap">&#128187; Format</td>
              <td style="padding:4px 0;font-size:13px;color:#111827;font-weight:600">AI-conducted text interview</td>
            </tr>
            <tr>
              <td style="padding:4px 16px 4px 0;font-size:13px;color:#6b7280;white-space:nowrap">&#127760; Where</td>
              <td style="padding:4px 0;font-size:13px;color:#111827;font-weight:600">In your browser — no download needed</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <!-- Checklist -->
    <p style="margin:0 0 12px;font-size:14px;font-weight:700;color:#111827">Before you start, make sure you have:</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      {_checklist_item("&#128247;", "<strong>Camera &amp; microphone</strong> access enabled in your browser")}
      {_checklist_item("&#128396;", "<strong>Screen sharing</strong> enabled — required for interview integrity")}
      {_checklist_item("&#127968;", "A <strong>quiet, well-lit environment</strong> free from distractions")}
      {_checklist_item("&#127760;", "A <strong>stable internet connection</strong>")}
      {_checklist_item("&#128274;", "Use this link <strong>only once</strong> and do not share it with others")}
    </table>

    {_divider()}

    <p style="margin:0 0 4px;font-size:14px;color:#374151;line-height:1.7">
      We look forward to learning more about you. If you have any questions before the interview,
      don't hesitate to reach out.
    </p>
    <p style="margin:16px 0 0;font-size:14px;color:#374151">
      Best of luck,<br>
      <strong style="color:#111827">The {COMPANY_NAME} Team</strong>
    </p>"""

    html = _email_wrapper(header, body, "This link is unique to you and should not be shared. &nbsp;|&nbsp; ")
    _send(to_email, subject, html)


# ─── Selection Email ──────────────────────────────────────────────────────────

def send_selection_email(candidate_name: str, to_email: str, role_title: str) -> None:
    subject = f"Congratulations — You've been selected! &#127881; | {COMPANY_NAME}"
    first_name = candidate_name.split()[0] if candidate_name else candidate_name

    header = f"""
    <tr>
      <td style="background:linear-gradient(135deg,#064e3b 0%,#065f46 50%,#047857 100%);border-radius:16px 16px 0 0;padding:36px 48px 32px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <p style="margin:0 0 20px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:2px;color:rgba(167,243,208,0.8)">Offer Update</p>
              <p style="margin:0 0 4px;font-size:28px;font-weight:700;color:#ffffff;line-height:1.2">Congratulations,<br>{first_name}! &#127881;</p>
            </td>
            <td align="right" style="vertical-align:top">
              <span style="display:inline-block;width:52px;height:52px;background:rgba(255,255,255,0.15);border-radius:14px;text-align:center;line-height:52px;font-size:26px">&#9989;</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""

    body = f"""
    <p style="margin:0 0 8px;font-size:16px;color:#111827;font-weight:600">Dear {first_name},</p>
    <p style="margin:0 0 20px;font-size:15px;color:#374151;line-height:1.7">
      We are absolutely delighted to inform you that after a thorough review of your performance
      and qualifications, you have been <strong style="color:#059669">selected</strong> for the
      <strong>{role_title}</strong> position at <strong>{COMPANY_NAME}</strong>.
    </p>
    <p style="margin:0 0 24px;font-size:15px;color:#374151;line-height:1.7">
      Your skills, experience, and the way you approached the interview set you apart from a
      highly competitive pool of candidates. We are excited to have you join the team.
    </p>

    <!-- Highlight box -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;margin-bottom:28px">
      <tr>
        <td style="padding:20px 24px">
          <p style="margin:0 0 6px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#059669">Position Confirmed</p>
          <p style="margin:0;font-size:22px;font-weight:700;color:#064e3b">{role_title}</p>
          <p style="margin:4px 0 0;font-size:13px;color:#047857">{COMPANY_NAME}</p>
        </td>
      </tr>
    </table>

    <p style="margin:0 0 14px;font-size:14px;font-weight:700;color:#111827">What happens next:</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      {_step_item("1", "Offer Letter", "You will receive a formal offer letter via email within 1–2 business days.")}
      {_step_item("2", "Onboarding Details", "Our HR team will contact you with onboarding documents and your start date.")}
      {_step_item("3", "Welcome to the Team", "Prepare to hit the ground running — we can't wait to work with you!")}
    </table>

    {_divider()}

    <p style="margin:0 0 16px;font-size:14px;color:#374151;line-height:1.7">
      If you have any questions or need to discuss the offer, please don't hesitate to get in touch
      with our team. We are here to make your transition as smooth as possible.
    </p>
    <p style="margin:0;font-size:14px;color:#374151">
      Once again, congratulations — welcome aboard!<br><br>
      Warm regards,<br>
      <strong style="color:#111827">The {COMPANY_NAME} Team</strong>
    </p>"""

    html = _email_wrapper(header, body)
    _send(to_email, subject, html)


# ─── Rejection Email ──────────────────────────────────────────────────────────

def send_rejection_email(candidate_name: str, to_email: str, role_title: str) -> None:
    subject = f"Your Application at {COMPANY_NAME} — Update"
    first_name = candidate_name.split()[0] if candidate_name else candidate_name

    header = f"""
    <tr>
      <td style="background:linear-gradient(135deg,#1e293b 0%,#334155 100%);border-radius:16px 16px 0 0;padding:36px 48px 32px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <p style="margin:0 0 20px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:2px;color:rgba(148,163,184,0.8)">Application Update</p>
              <p style="margin:0;font-size:28px;font-weight:700;color:#ffffff;line-height:1.3">A note regarding<br>your application</p>
            </td>
            <td align="right" style="vertical-align:top">
              <span style="display:inline-block;width:52px;height:52px;background:rgba(255,255,255,0.08);border-radius:14px;text-align:center;line-height:52px;font-size:24px">&#128084;</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""

    body = f"""
    <p style="margin:0 0 8px;font-size:16px;color:#111827;font-weight:600">Dear {first_name},</p>
    <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.7">
      Thank you sincerely for your interest in the <strong>{role_title}</strong> role at
      <strong>{COMPANY_NAME}</strong> and for the time and effort you invested in our interview process.
    </p>
    <p style="margin:0 0 20px;font-size:15px;color:#374151;line-height:1.7">
      After a thorough and careful review of all applications, we have decided to move forward with
      a candidate whose experience more closely aligns with our specific requirements at this time.
      This was not an easy decision — the overall quality of candidates was very high.
    </p>

    <!-- Note box -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-left:4px solid #6366f1;border-radius:0 8px 8px 0;margin-bottom:24px">
      <tr>
        <td style="padding:16px 20px">
          <p style="margin:0;font-size:14px;color:#475569;line-height:1.7;font-style:italic">
            "This decision reflects our current needs and hiring direction, not a measure of your
            talent or potential. We encourage you to keep growing — you are clearly capable."
          </p>
        </td>
      </tr>
    </table>

    <p style="margin:0 0 20px;font-size:15px;color:#374151;line-height:1.7">
      We genuinely encourage you to <strong>apply for future openings</strong> at {COMPANY_NAME}
      that match your profile. We retain your information and may reach out when a suitable
      opportunity arises.
    </p>

    {_divider()}

    <p style="margin:0 0 16px;font-size:14px;color:#374151;line-height:1.7">
      We wish you every success in your career journey and are confident the right opportunity is
      just ahead for you.
    </p>
    <p style="margin:0;font-size:14px;color:#374151">
      With appreciation,<br>
      <strong style="color:#111827">The {COMPANY_NAME} Team</strong>
    </p>"""

    html = _email_wrapper(header, body)
    _send(to_email, subject, html)
