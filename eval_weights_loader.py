import json
from pathlib import Path

_DEFAULT = {
    "technical_competency": 0.35,
    "communication": 0.20,
    "problem_solving": 0.25,
    "cultural_fit": 0.10,
    "role_alignment": 0.10
}

_WEIGHTS_FILE = Path(__file__).parent / "eval_weights.json"


def load() -> dict:
    try:
        return json.loads(_WEIGHTS_FILE.read_text())
    except Exception:
        return _DEFAULT
