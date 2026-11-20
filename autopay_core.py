"""Storage, email reading, and the JSON handoff for the AutoPay Watcher UI.

This module intentionally performs NO AI inference, cancellation-date calculation,
or calendar scheduling. Those belong to the other project components.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import os
import sqlite3
from typing import Any, Iterator

MAX_EMAIL_BYTES = 2 * 1024 * 1024
MAX_TEXT_LENGTH = 100_000
FREQUENCIES = ("Unknown", "Weekly", "Monthly", "Quarterly", "Yearly")
RECORD_TYPES = ("subscription", "trial")


def database_path() -> Path:
    configured = os.getenv("AUTOPAY_DB_PATH")
    if configured:
        candidate = Path(configured)
        return candidate if candidate.is_absolute() else Path(__file__).parent / candidate
    return Path(__file__).parent / "data" / "autopay.db"


@contextmanager
def db_connection(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    dest = Path(path) if path is not None else database_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(dest, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(path: str | Path | None = None) -> None:
    with db_connection(path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_sha256 TEXT NOT NULL UNIQUE,
            subject TEXT NOT NULL DEFAULT '',
            sender TEXT NOT NULL DEFAULT '',
            message_date TEXT NOT NULL DEFAULT '',
            body_text TEXT NOT NULL,
            original_bytes BLOB NOT NULL,
            uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            record_type TEXT NOT NULL CHECK (record_type IN ('trial','subscription')),
            amount_cents INTEGER CHECK (amount_cents >= 0),
            currency TEXT NOT NULL DEFAULT 'USD',
            frequency TEXT NOT NULL DEFAULT 'Unknown',
            renewal_date TEXT,
            trial_end_date TEXT,
            cancellation_deadline TEXT,
            cancellation_instructions TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            email_id INTEGER REFERENCES emails(id) ON DELETE SET NULL,
            source TEXT NOT NULL DEFAULT 'manual',
            is_archived INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sub_type_dates ON subscriptions(record_type, trial_end_date, renewal_date);
        """)


class _PlainHTML(HTMLParser):
    """Extract visible text only from HTML emails without rendering markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "head"}:
            self.skip_depth += 1
        elif tag.lower() in {"p", "br", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "head"} and self.skip_depth > 0:
            self.skip_depth -= 1
        elif tag.lower() in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def _decode_part(part: Any) -> str:
    try:
        content = part.get_content()
        if isinstance(content, str):
            return content
    except (LookupError, UnicodeError, ValueError, AttributeError):
        pass
    raw = part.get_payload(decode=True)
    if not isinstance(raw, bytes):
        return ""
    return raw.decode(part.get_content_charset() or "utf-8", errors="replace") if (part.get_content_charset() or "utf-8").lower() in {"utf-8", "us-ascii", "latin-1", "iso-8859-1", "windows-1252"} else raw.decode("utf-8", errors="replace")


def read_email(filename: str, content: bytes) -> dict[str, str]:
    """Read only user-uploaded .eml or .txt; ignore attachments and active HTML."""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".eml", ".txt"}:
        raise ValueError("Only .eml and .txt files are supported.")
    if not content:
        raise ValueError("This email file is empty.")
    if len(content) > MAX_EMAIL_BYTES:
        raise ValueError("Email exceeds the 2 MB per-file limit.")
    if suffix == ".txt":
        return {"subject": Path(filename).stem, "sender": "", "message_date": "", "body_text": content.decode("utf-8-sig", errors="replace")[:MAX_TEXT_LENGTH]}

    msg = BytesParser(policy=policy.default).parsebytes(content)
    plain_parts: list[str] = []
    html_parts: list[str] = []
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.is_multipart() or part.get_content_disposition() == "attachment":
            continue
        if part.get_content_type() == "text/plain":
            plain_parts.append(_decode_part(part))
        elif part.get_content_type() == "text/html":
            parser = _PlainHTML()
            parser.feed(_decode_part(part))
            html_parts.append(parser.text())
    body = "\n\n".join(plain_parts).strip() or "\n".join(html_parts).strip()
    return {
        "subject": str(msg.get("Subject", ""))[:500],
        "sender": str(msg.get("From", ""))[:500],
        "message_date": str(msg.get("Date", ""))[:200],
        "body_text": body[:MAX_TEXT_LENGTH],
    }


def add_email(filename: str, content: bytes, path: str | Path | None = None) -> tuple[int, bool]:
    parsed = read_email(filename, content)
    checksum = hashlib.sha256(content).hexdigest()
    with db_connection(path) as conn:
        existing = conn.execute("SELECT id FROM emails WHERE file_sha256 = ?", (checksum,)).fetchone()
        if existing:
            return int(existing["id"]), False
        cursor = conn.execute(
            "INSERT INTO emails (filename, file_sha256, subject, sender, message_date, body_text, original_bytes) VALUES (?,?,?,?,?,?,?)",
            (Path(filename).name, checksum, parsed["subject"], parsed["sender"], parsed["message_date"], parsed["body_text"], content),
        )
        return int(cursor.lastrowid), True


def list_emails(path: str | Path | None = None) -> list[dict[str, Any]]:
    with db_connection(path) as conn:
        return [dict(row) for row in conn.execute("SELECT id, filename, subject, sender, message_date, uploaded_at FROM emails ORDER BY id DESC")]


def get_email(email_id: int, path: str | Path | None = None) -> dict[str, Any] | None:
    with db_connection(path) as conn:
        row = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
        return dict(row) if row else None


def email_for_ai(email_id: int, path: str | Path | None = None) -> dict[str, str | int]:
    """Integration contract: pass this to teammate's AI extraction function."""
    mail = get_email(email_id, path)
    if mail is None:
        raise ValueError("Email was not found.")
    return {"email_id": mail["id"], "subject": mail["subject"], "sender": mail["sender"], "body": mail["body_text"]}


def delete_email(email_id: int, path: str | Path | None = None) -> None:
    with db_connection(path) as conn:
        conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))


def normalize_date(value: Any) -> str | None:
    if value in (None, "", "unknown", "Unknown", "N/A"):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value).strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        pass
    # Teammate's extraction prompt explicitly requests "Month DD, YYYY".
    # Parse only these unambiguous formats; never silently guess numeric dates.
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD or Month DD, YYYY, or leave blank.")


def cents_from_amount(value: Any) -> int | None:
    if value in (None, "", "unknown", "Unknown", "N/A"):
        return None
    try:
        amt = Decimal(str(value).strip().replace("$", "").replace(",", ""))
        if not amt.is_finite() or amt < 0 or amt > 1_000_000:
            raise ValueError("Amount must be between $0 and $1,000,000.")
        return int((amt * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Invalid amount '{value}'.") from error


def normalize_subscription(data: dict[str, Any]) -> dict[str, Any]:
    """Schema boundary between teammate AI JSON and UI database. Never infer missing data."""
    if not isinstance(data, dict):
        raise ValueError("Each subscription must be a JSON object.")
    service = data.get("service_name") or data.get("subscription_name") or data.get("name") or ""
    service = str(service).strip()
    if not service or len(service) > 160:
        raise ValueError("service_name is required (maximum 160 characters).")
    rtype = str(data.get("record_type") or ("trial" if data.get("is_free_trial") is True else "subscription")).strip().lower()
    if rtype in {"free_trial", "free trial"}:
        rtype = "trial"
    if rtype not in RECORD_TYPES:
        raise ValueError("record_type must be 'trial' or 'subscription'.")
    raw_frequency = data.get("frequency") or data.get("billing_frequency") or data.get("billing_cycle") or "Unknown"
    freq_text = str(raw_frequency).strip().lower()
    frequency_aliases = {
        "weekly": "Weekly", "week": "Weekly", "every week": "Weekly",
        "monthly": "Monthly", "month": "Monthly", "every month": "Monthly",
        "quarterly": "Quarterly", "quarter": "Quarterly", "every 3 months": "Quarterly",
        "yearly": "Yearly", "annual": "Yearly", "annually": "Yearly", "year": "Yearly", "every year": "Yearly",
    }
    frequency = frequency_aliases.get(freq_text, "Unknown")
    currency = str(data.get("currency") or "USD").upper().strip()
    if currency != "USD":
        raise ValueError("This prototype supports USD only; please review other currencies manually.")
    amount_raw = data.get("amount") if "amount" in data else data.get("price")
    if "amount_cents" in data and amount_raw is None:
        try:
            amount_cents = int(data["amount_cents"]) if data["amount_cents"] is not None else None
        except (ValueError, TypeError) as error:
            raise ValueError("amount_cents must be an integer.") from error
        if amount_cents is not None and not (0 <= amount_cents <= 100_000_000):
            raise ValueError("amount_cents is outside supported range.")
    else:
        amount_cents = cents_from_amount(amount_raw)
    policy_text = data.get("cancellation_instructions") or data.get("cancellation_policy") or ""
    notice_amount = data.get("cancellation_notice_amount")
    notice_unit = data.get("cancellation_notice_unit") or data.get("cancellation_notic_unit")
    extra_notice = ""
    if notice_amount is not None and notice_unit:
        extra_notice = f"AI-reported notice: {notice_amount} {notice_unit} before renewal. Not a verified deadline."
    notes = str(data.get("notes") or "")
    if extra_notice:
        notes = f"{notes}\n{extra_notice}".strip()
    return {
        "service_name": service,
        "record_type": rtype,
        "amount_cents": amount_cents,
        "currency": currency,
        "frequency": frequency,
        "renewal_date": normalize_date(data.get("renewal_date") or data.get("next_renewal_date")),
        "trial_end_date": normalize_date(data.get("trial_end_date") or data.get("trial_expiration_date")),
        "cancellation_deadline": normalize_date(data.get("cancellation_deadline")),
        "cancellation_instructions": str(policy_text)[:4000],
        "notes": notes[:4000],
    }


def save_subscription(
    data: dict[str, Any],
    *,
    email_id: int | None = None,
    source: str = "manual",
    subscription_id: int | None = None,
    path: str | Path | None = None,
) -> int:
    normalized = normalize_subscription(data)
    if source not in {"manual", "ai", "demo", "import"}:
        raise ValueError("Unknown source")
    with db_connection(path) as conn:
        if email_id is not None and not conn.execute("SELECT 1 FROM emails WHERE id=?", (email_id,)).fetchone():
            raise ValueError("Linked email no longer exists.")
        fields = list(normalized) + ["email_id", "source"]
        values = list(normalized.values()) + [email_id, source]
        if subscription_id is None:
            cursor = conn.execute(
                f"INSERT INTO subscriptions ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",
                values,
            )
            return int(cursor.lastrowid)
        existing = conn.execute("SELECT id FROM subscriptions WHERE id=?", (subscription_id,)).fetchone()
        if existing is None:
            raise ValueError("Subscription no longer exists.")
        conn.execute(
            f"UPDATE subscriptions SET {','.join(field + '=?' for field in fields)}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values + [subscription_id],
        )
        return subscription_id


def list_subscriptions(path: str | Path | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
    with db_connection(path) as conn:
        query = "SELECT s.*, e.subject AS email_subject, e.filename AS email_filename FROM subscriptions s LEFT JOIN emails e ON e.id = s.email_id"
        if not include_archived:
            query += " WHERE s.is_archived = 0"
        query += " ORDER BY s.id DESC"
        return [dict(row) for row in conn.execute(query)]


def archive_subscription(subscription_id: int, archived: bool = True, path: str | Path | None = None) -> None:
    with db_connection(path) as conn:
        conn.execute("UPDATE subscriptions SET is_archived=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (int(archived), subscription_id))


def sort_by_upcoming(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return sorted(records, key=lambda r: (not bool(r.get(field)), str(r.get(field) or "9999-12-31"), r["service_name"].casefold()))


def monthly_equivalent_cents(rec: dict[str, Any]) -> Decimal | None:
    """Approximate recurring monthly cost. Unknown billing periods stay out of totals."""
    cents = rec.get("amount_cents")
    if cents is None or rec.get("record_type") != "subscription":
        return None
    periods = {"Weekly": Decimal(52) / Decimal(12), "Monthly": Decimal(1), "Quarterly": Decimal(1) / Decimal(3), "Yearly": Decimal(1) / Decimal(12)}
    multiplier = periods.get(rec.get("frequency"))
    return Decimal(cents) * multiplier if multiplier is not None else None


def demo_records(path: str | Path | None = None) -> int:
    """Opt-in synthetic demo, repeat-safe; dates relative to today for live presentations."""
    today = date.today()
    examples = [
        ("StreamFlix", "subscription", "15.49", "Monthly", today + timedelta(days=4), None, today + timedelta(days=2), "Cancel in account settings before renewal."),
        ("CloudBox", "subscription", "8.00", "Monthly", today + timedelta(days=18), None, None, "Visit Billing > Manage subscription."),
        ("StudyPro", "subscription", "49.99", "Yearly", today + timedelta(days=45), None, today + timedelta(days=40), "Review renewal terms in the receipt."),
        ("DesignLab", "trial", "12.00", "Monthly", None, today + timedelta(days=3), today + timedelta(days=1), "Cancel before the trial expires."),
        ("MusicMix", "trial", "10.99", "Monthly", None, today + timedelta(days=10), None, "Instructions were not included in the email."),
    ]
    count = 0
    for name, kind, cost, freq, renewal, trial_end, cancel, instructions in examples:
        body = f"This is SYNTHETIC demo email for {name}. Amount ${cost}.\nNo real account is associated with this message."
        email_bytes = f"From: demo@example.invalid\nTo: student@example.invalid\nSubject: {name} subscription sample\nContent-Type: text/plain; charset=utf-8\n\n{body}".encode()
        email_id, _ = add_email(f"demo_{name.lower()}.eml", email_bytes, path)
        existing = [r for r in list_subscriptions(path, include_archived=True) if r["email_id"] == email_id and r["source"] == "demo"]
        if existing:
            continue
        save_subscription({
            "service_name": name, "record_type": kind, "amount": cost, "frequency": freq,
            "renewal_date": renewal, "trial_end_date": trial_end, "cancellation_deadline": cancel,
            "cancellation_instructions": instructions,
        }, email_id=email_id, source="demo", path=path)
        count += 1
    return count
