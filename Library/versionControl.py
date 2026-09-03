import re
import sys
from pathlib import Path


def get_version():
    try:
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        elif getattr(sys, "frozen", False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent
        version_file = base / "VERSION.txt"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return "v1.1.0"

def _parse_version(v):
    v = (v or "").strip().lstrip("vV")
    v = re.split(r"[-+]", v, maxsplit=1)[0]  # drop pre-release/build metadata
    parts = []
    for piece in v.split("."):
        m = re.match(r"\d+", piece)
        parts.append(int(m.group()) if m else 0)
    return tuple(parts) or (0,)


def _is_newer(latest, current):
    """True only if `latest` is strictly greater than `current` (real numeric
    comparison, not a naive string inequality)."""
    a, b = _parse_version(latest), _parse_version(current)
    length = max(len(a), len(b))
    a = a + (0,) * (length - len(a))
    b = b + (0,) * (length - len(b))
    return a > b
