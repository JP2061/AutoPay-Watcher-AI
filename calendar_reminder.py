"""
AutoPay Watcher AI (Calendar Reminders feature)

Generates downloadable .ics (iCalendar) files so the user can import a
cancellation/renewal reminder into Google Calendar, Outlook, or Apple Calendar.

Each reminder is an all-day calendar event on the recommended cancellation date,
with a built-in alarm (VALARM) that pops up a chosen number of days beforehand.

Uses only the Python standard library -- nothing to add to requirements.txt.
"""

from __future__ import annotations

import datetime as _dt
import uuid as _uuid
from typing import Iterable, Optional, Union

DateLike = Union[_dt.date, _dt.datetime, str]


def _to_date(value: DateLike) -> _dt.date:
    """Accept a date, datetime, or 'YYYY-MM-DD' string and return a date."""
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        return _dt.date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported date value: {value!r}")


def _escape(text: str) -> str:
    """Escape text per RFC 5545 (commas, semicolons, backslashes, newlines)."""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold lines longer than 75 octets, as the iCalendar spec requires."""
    if len(line) <= 75:
        return line
    out = [line[:75]]
    rest = line[75:]
    while rest:
        out.append(" " + rest[:74])  # continuation lines start with a space
        rest = rest[74:]
    return "\r\n".join(out)

def build_event(
    service_name: str,
    cancel_by_date: DateLike,
    amount: Optional[str] = None,
    renewal_date: Optional[DateLike] = None,
    cancellation_url: Optional[str] = None,
    notes: Optional[str] = None,
    reminder_days_before: int = 1,
) -> list[str]:
    """Return the lines of one VEVENT block for the given subscription."""
    day = _to_date(cancel_by_date)
    day_str = day.strftime("%Y%m%d")
    # All-day events end on the following day in iCalendar.
    end_str = (day + _dt.timedelta(days=1)).strftime("%Y%m%d")
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    summary = f"Cancel {service_name} before you're charged"

    # Build a readable description from whatever details we were given.
    desc_parts = [f"Recommended cancellation date for {service_name}."]
    if amount:
        desc_parts.append(f"Expected charge: {amount}.")
    if renewal_date:
        desc_parts.append(f"Renews on: {_to_date(renewal_date).isoformat()}.")
    if cancellation_url:
        desc_parts.append(f"Cancellation instructions: {cancellation_url}")
    if notes:
        desc_parts.append(str(notes))
    desc_parts.append("Created by AutoPay Watcher AI.")
    description = " ".join(desc_parts)

    lines = [
        "BEGIN:VEVENT",
        f"UID:{_uuid.uuid4()}@autopay-watcher-ai",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{day_str}",
        f"DTEND;VALUE=DATE:{end_str}",
        f"SUMMARY:{_escape(summary)}",
        f"DESCRIPTION:{_escape(description)}",
        "STATUS:CONFIRMED",
        "TRANSP:TRANSPARENT",
        # --- the reminder alarm ---
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_escape('Reminder: cancel ' + service_name)}",
        f"TRIGGER:-P{max(0, int(reminder_days_before))}D",
        "END:VALARM",
        "END:VEVENT",
    ]
    return [_fold(line) for line in lines]

def build_calendar(events: Iterable[list[str]]) -> str:
    """Wrap VEVENT blocks in a VCALENDAR and return the full .ics text."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AutoPay Watcher AI//Calendar Reminders//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for event_lines in events:
        lines.extend(event_lines)
    lines.append("END:VCALENDAR")
    # iCalendar requires CRLF line endings.
    return "\r\n".join(lines) + "\r\n"


def make_reminder_ics(
    service_name: str,
    cancel_by_date: DateLike,
    amount: Optional[str] = None,
    renewal_date: Optional[DateLike] = None,
    cancellation_url: Optional[str] = None,
    notes: Optional[str] = None,
    reminder_days_before: int = 1,
) -> bytes:
    """
    Build a one-event .ics file for a single subscription and return it as bytes
    (bytes is what Streamlit's st.download_button wants).
    """
    event = build_event(
        service_name=service_name,
        cancel_by_date=cancel_by_date,
        amount=amount,
        renewal_date=renewal_date,
        cancellation_url=cancellation_url,
        notes=notes,
        reminder_days_before=reminder_days_before,
    )
    return build_calendar([event]).encode("utf-8")


def make_reminders_ics(
    subscriptions: Iterable[dict],
    reminder_days_before: int = 1,
) -> bytes:
    """
    Build ONE .ics file containing a reminder for every subscription in the list.

    Each subscription is a dict. Expected keys (adapt these names to match
    autopay_core.py's records):
        service_name           (required)
        recommended_cancel_date OR cancel_by_date  (required, the event date)
        amount                 (optional)
        renewal_date           (optional)
        cancellation_url       (optional)
        notes                  (optional)
    """
    events = []
    for sub in subscriptions:
        cancel_date = sub.get("recommended_cancel_date") or sub.get("cancel_by_date")
        if not sub.get("service_name") or not cancel_date:
            continue  # skip entries missing the essentials
        events.append(
            build_event(
                service_name=sub["service_name"],
                cancel_by_date=cancel_date,
                amount=sub.get("amount"),
                renewal_date=sub.get("renewal_date"),
                cancellation_url=sub.get("cancellation_url"),
                notes=sub.get("notes"),
                reminder_days_before=reminder_days_before,
            )
        )
    return build_calendar(events).encode("utf-8")


#demo
if __name__ == "__main__":
    ics = make_reminder_ics(
        service_name="Netflix",
        cancel_by_date="2026-12-13",
        amount="$15.49",
        renewal_date="2026-12-15",
        cancellation_url="https://www.netflix.com/cancelplan",
        reminder_days_before=2,
    )
    with open("sample_reminder.ics", "wb") as f:
        f.write(ics)
    print(ics.decode("utf-8"))
    print("Wrote sample_reminder.ics")
