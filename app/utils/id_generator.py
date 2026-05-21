import random
import string
from datetime import datetime


def generate_object_id() -> str:
    """Generates OBJ-XXXX format ID."""
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"OBJ-{suffix}"


def generate_inspection_id() -> str:
    """Generates INSP-YYYYMMDD-XXXX format ID."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"INSP-{date_str}-{suffix}"


def generate_report_filename(inspection_id: str, fmt: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    ext = "pdf" if fmt.upper() == "PDF" else "xlsx"
    return f"report_{inspection_id}_{ts}.{ext}"
