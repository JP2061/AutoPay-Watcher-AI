"""AutoPay Watcher AI — Joshua's mail upload + dashboard UI.

Run: python -m streamlit run "AutoPay Watcher AI.py"
The AI extraction, cancellation-date computation, and .ics reminders are intentionally
integration points, not mocked as if implemented by this module.
"""

from __future__ import annotations

from datetime import date
import os
from decimal import Decimal
import html
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from autopay_core import (
    FREQUENCIES,
    add_email,
    archive_subscription,
    database_path,
    delete_email,
    demo_records,
    email_for_ai,
    get_email,
    initialize_database,
    list_emails,
    list_subscriptions,
    monthly_equivalent_cents,
    normalize_subscription,
    read_email,
    save_subscription,
    sort_by_upcoming,
)

# The team entry point calls st.set_page_config() before importing this module.
# No API request occurs unless the user explicitly clicks Analyze email.
load_dotenv()

st.markdown("""
<style>
  :root { --teal: #70e3ca; --gold: #eac78d; }
  .block-container { padding-top: 2.1rem; padding-bottom: 3rem; max-width: 1420px; }
  [data-testid="stSidebar"] { border-right: 1px solid rgba(150,170,185,.15); }
  .hero { padding: 26px 30px; border: 1px solid rgba(111,216,194,.28);
    border-radius: 22px; background: linear-gradient(108deg,rgba(24,65,72,.75),rgba(38,53,81,.58));
    margin-bottom: 22px; }
  .hero .eyebrow { color: #a0e8d7; letter-spacing: 0.15em; font-size: 0.76rem; font-weight: 700; }
  .hero h1 { font-size: clamp(1.9rem,3.2vw,3rem); margin: 8px 0; line-height: 1.15; color: #f2f7fa; }
  .hero p { color: #c5d5dc; font-size: 1.0rem; margin: 0; }
  .section-label { font-size:.76rem; text-transform:uppercase; letter-spacing:.13em; font-weight:750; color:#73cdbd; margin:24px 0 6px; }
  .hint { font-size:.89rem; opacity:.81; }
  .tag { padding: 4px 10px; border-radius: 9px; font-size: .76rem; font-weight:700; display:inline-block; }
  .tag-trial { background:rgba(232,179,101,.17); color:#f5cf93; }
  .tag-active { background:rgba(102,207,184,.16); color:#8debd7; }
  .tag-review { background:rgba(228,151,129,.16); color:#f1b39e; }
  .soft-note { padding:13px 16px; border:1px solid rgba(137,177,195,.25); border-radius:14px;
    background:rgba(83,111,137,.08); margin: 7px 0 13px; }
  [data-testid="stMetric"] { padding: 17px 18px; border-radius: 15px;
    border: 1px solid rgba(139,180,195,.17); background:rgba(90,123,151,.065); }
  [data-testid="stMetricLabel"] { font-weight:600; }
  div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:17px; }
  [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 14px; }
  footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)


def money(cents: int | None) -> str:
    return "Unknown" if cents is None else f"${cents / 100:,.2f}"


def readable_date(value: str | None) -> str:
    if not value:
        return "Unknown · needs review"
    return date.fromisoformat(value).strftime("%b %d, %Y")


def urgency(value: str | None, *, today: date | None = None) -> str:
    if not value:
        return "Date not provided"
    remaining = (date.fromisoformat(value) - (today or date.today())).days
    if remaining < 0:
        return f"{abs(remaining)} days past — verify status"
    if remaining == 0:
        return "Today"
    if remaining == 1:
        return "Tomorrow"
    return f"In {remaining} days"


def upcoming_deadline(record: dict) -> str | None:
    return record.get("cancellation_deadline") or (
        record.get("trial_end_date") if record.get("record_type") == "trial" else record.get("renewal_date")
    )


def render_hero(page: str) -> None:
    subtitles = {
        "Overview": "One calm place to see what's renewing, what's expiring, and what needs a second look.",
        "Email inbox": "Bring your subscription receipts here. Your uploads remain in this local prototype.",
        "Manage records": "Keep the details accurate. Add, correct, or archive entries whenever you need.",
        "Team integration": "A small, predictable JSON interface for connecting the group's AI extraction module.",
    }
    st.markdown(
        f'<div class="hero"><div class="eyebrow">AUTOPAY WATCHER / STUDENT PROTOTYPE</div>'
        f'<h1>{html.escape(page)}</h1><p>{html.escape(subtitles[page])}</p></div>',
        unsafe_allow_html=True,
    )


def render_email_source(record: dict) -> None:
    email_id = record.get("email_id")
    if email_id is None:
        st.caption("Source email: not linked. Add or edit this record in Manage records.")
        return
    with st.expander(f"✉️ Supporting email · {record.get('email_subject') or record.get('email_filename') or 'Original upload'}"):
        email = get_email(email_id)
        if email is None:
            st.warning("The linked email was removed.")
            return
        st.caption(f"From: {email['sender'] or 'Unknown'} | File: {email['filename']}")
        st.code(email["body_text"][:3000] or "(No readable text found)", language=None)
        st.download_button(
            "Download original email", data=email["original_bytes"], file_name=email["filename"],
            mime="message/rfc822" if email["filename"].lower().endswith(".eml") else "text/plain",
            key=f"email_dl_{record['id']}",
        )


def render_subscription_card(record: dict) -> None:
    is_trial = record["record_type"] == "trial"
    event = record["trial_end_date"] if is_trial else record["renewal_date"]
    needs_review = not event or (record["amount_cents"] is None and not is_trial)
    tag_class = "tag-review" if needs_review else "tag-trial" if is_trial else "tag-active"
    badge = "NEEDS REVIEW" if needs_review else "FREE TRIAL" if is_trial else "ACTIVE"

    with st.container(border=True):
        info, amount, timing = st.columns([3.2, 1.35, 2.1], vertical_alignment="center")
        with info:
            st.markdown(f"<span class='tag {tag_class}'>{badge}</span>", unsafe_allow_html=True)
            st.subheader(record["service_name"], divider=False)
            st.caption(f"{record['frequency']} billing · {record['source'].capitalize()} entry")
        with amount:
            st.caption("Expected charge")
            st.markdown(f"### {money(record['amount_cents'])}")
        with timing:
            st.caption("Trial ends" if is_trial else "Renews")
            st.markdown(f"**{readable_date(event)}**")
            st.caption(urgency(event))
        footer_a, footer_b = st.columns([1, 1])
        with footer_a:
            st.caption(f"Cancellation deadline: {readable_date(record['cancellation_deadline'])}")
        with footer_b:
            if record["cancellation_instructions"]:
                st.caption("Cancellation instructions available ↓")
            else:
                st.caption("Cancellation instructions: unknown")
        if record["cancellation_instructions"] or record["notes"]:
            with st.expander("Cancellation details / notes"):
                if record["cancellation_instructions"]:
                    st.write(record["cancellation_instructions"])
                if record["notes"]:
                    st.caption(f"Notes: {record['notes']}")
        render_email_source(record)


def render_dashboard() -> None:
    render_hero("Overview")
    rows = list_subscriptions()
    subs = [r for r in rows if r["record_type"] == "subscription"]
    trials = [r for r in rows if r["record_type"] == "trial"]
    monthly = sum((monthly_equivalent_cents(r) or Decimal(0)) for r in subs)
    unresolved = sum(1 for r in rows if not (r["trial_end_date"] if r["record_type"] == "trial" else r["renewal_date"]))
    expiring = sum(1 for r in trials if r["trial_end_date"] and 0 <= (date.fromisoformat(r["trial_end_date"]) - date.today()).days <= 7)

    cols = st.columns(4, gap="medium")
    for col, label, value in zip(
        cols,
        ["Monthly equivalent", "Yearly equivalent", "Active subscriptions", "Trials ending in 7 days"],
        [money(int(monthly)), money(int(monthly * 12)), str(len(subs)), str(expiring)],
    ):
        with col:
            st.metric(label, value)
    st.caption("USD estimates include only subscriptions with known amounts and billing frequency; they exclude free trials. Weekly billing is approximated as 52 weeks per year.")

    if not rows:
        st.markdown('<div class="section-label">GET STARTED</div>', unsafe_allow_html=True)
        st.info("No subscriptions yet. Open **Email inbox** to upload emails, or **Manage records** to add an entry. You can also load synthetic demo data from the sidebar.")
        return

    if unresolved:
        st.warning(f"{unresolved} record(s) have no upcoming renewal or expiration date. Check the **Needs review** tab before relying on reminders.")

    tab_trial, tab_sub, tab_review = st.tabs([f"Free trials  ·  {len(trials)}", f"Active subscriptions  ·  {len(subs)}", f"Needs review  ·  {unresolved}"])
    with tab_trial:
        st.markdown('<div class="section-label">ENDING SOONEST FIRST</div>', unsafe_allow_html=True)
        if not trials:
            st.info("No free trials have been added.")
        for record in sort_by_upcoming(trials, "trial_end_date"):
            render_subscription_card(record)
    with tab_sub:
        st.markdown('<div class="section-label">NEXT RENEWAL FIRST</div>', unsafe_allow_html=True)
        if not subs:
            st.info("No active subscriptions have been added.")
        for record in sort_by_upcoming(subs, "renewal_date"):
            render_subscription_card(record)
    with tab_review:
        missing = [r for r in rows if not (r["trial_end_date"] if r["record_type"] == "trial" else r["renewal_date"])]
        if not missing:
            st.success("Every active entry has its next renewal or trial-end date.")
        for record in missing:
            render_subscription_card(record)

    if subs:
        st.markdown('<div class="section-label">COST BREAKDOWN</div>', unsafe_allow_html=True)
        with st.container(border=True):
            costed = [(r["service_name"], monthly_equivalent_cents(r)) for r in subs]
            costed = sorted([(name, cost) for name, cost in costed if cost is not None], key=lambda x: x[1], reverse=True)
            if not costed or monthly == 0:
                st.caption("Add recurring prices and billing frequencies to see a monthly breakdown.")
            for name, cost in costed:
                a, b = st.columns([4, 1])
                a.write(name)
                b.write(money(int(cost)))
                st.progress(float(cost / monthly) if monthly else 0.0)


def render_mail_upload(ai_extractor=None) -> None:
    render_hero("Email inbox")
    st.markdown('<div class="section-label">UPLOAD EMAILS</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Select subscription confirmation, renewal, or trial emails", type=["eml", "txt"], accept_multiple_files=True)
    st.caption("Accepts .eml and .txt; max 2 MB per file. The app reads plaintext / HTML text and skips attachments. Only upload emails you have permission to use.")
    if uploaded:
        st.write(f"**{len(uploaded)} selected file(s)**")
        for file in uploaded[:3]:
            try:
                parsed = read_email(file.name, file.getvalue())
                st.caption(f"{file.name} · {parsed['subject'] or 'No subject'}")
            except ValueError as exc:
                st.error(f"{file.name}: {exc}")
        if len(uploaded) > 3:
            st.caption(f"...and {len(uploaded) - 3} more")
        if st.button("Import selected emails", type="primary", use_container_width=True):
            new_count = duplicate_count = failed = 0
            for file in uploaded:
                try:
                    _, created = add_email(file.name, file.getvalue())
                    new_count += int(created)
                    duplicate_count += int(not created)
                except ValueError as exc:
                    st.error(f"{file.name}: {exc}")
                    failed += 1
            if new_count:
                st.success(f"Imported {new_count} new email(s).")
            if duplicate_count:
                st.info(f"Skipped {duplicate_count} duplicate email(s).")
            if failed:
                st.warning(f"Rejected {failed} file(s).")

    st.markdown('<div class="section-label">SAVED EMAILS</div>', unsafe_allow_html=True)
    emails = list_emails()
    if not emails:
        st.info("Your inbox is empty. Upload a sample .eml file to begin.")
        return
    selected_id = st.selectbox(
        "Choose an email to inspect", options=[r["id"] for r in emails],
        format_func=lambda eid: next(f"#{e['id']}  {e['subject'] or e['filename']}" for e in emails if e["id"] == eid),
    )
    email = get_email(selected_id)
    if not email:
        return
    with st.container(border=True):
        st.subheader(email["subject"] or email["filename"])
        st.caption(f"From: {email['sender'] or 'Unknown'} · Sent: {email['message_date'] or 'Unknown'} · Uploaded: {email['uploaded_at']}")
        st.text_area("Parsed email text (read-only)", value=email["body_text"] or "No readable text found", height=210, disabled=True)
        a, b = st.columns(2)
        with a:
            st.download_button("Download original", data=email["original_bytes"], file_name=email["filename"], key=f"maildl_{email['id']}", use_container_width=True)
        with b:
            with st.popover("Remove this email", use_container_width=True):
                st.warning("This deletes the stored email. Any linked subscription remains, but loses its email reference.")
                if st.button("Confirm deletion", key=f"delete_mail_{email['id']}"):
                    delete_email(email["id"])
                    st.rerun()
    with st.expander("Developer: payload ready for teammate's AI parser"):
        st.caption("This is the actual normalized text handoff, not an AI result. It can contain personal information.")
        st.code(json.dumps(email_for_ai(selected_id), indent=2), language="json")

    # Optional handoff to the teammate's existing extraction function.
    # Nothing is sent to the API without a button click.
    if ai_extractor is not None:
        st.markdown('<div class="section-label">OPTIONAL AI EXTRACTION</div>', unsafe_allow_html=True)
        st.caption("The Analyze button sends this email's text to the configured OpenAI API and may incur a charge. Only use synthetic/anonymized emails during testing.")
        if st.button("Analyze selected email with team AI", key=f"analyze_{selected_id}"):
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_api_key_here":
                st.warning("No usable OPENAI_API_KEY in your local .env. You can still upload and manually add records without AI.")
            elif not email["body_text"].strip():
                st.warning("This email has no text to analyze.")
            else:
                try:
                    with st.spinner("Asking the team's extraction function..."):
                        result = ai_extractor(email["body_text"], OpenAI(api_key=api_key))
                    if not isinstance(result, dict):
                        raise ValueError("The AI result must be one JSON object.")
                    normalized = normalize_subscription(result)
                except Exception as exc:
                    st.error(f"AI extraction failed: {exc}")
                    st.caption("Check your API key, model access, the teammate's prompt, and the returned JSON. Your upload remains saved.")
                else:
                    st.session_state["pending_ai_result"] = {
                        "email_id": selected_id,
                        "raw": result,
                        "normalized": normalized,
                    }
        pending = st.session_state.get("pending_ai_result")
        if pending and pending.get("email_id") == selected_id:
            st.warning("Review every extracted field against the original email before saving. Cancellation deadlines are not calculated or verified here.")
            st.code(json.dumps(pending["raw"], indent=2), language="json")
            st.caption("Normalized dashboard preview (read-only). To correct mistakes, use Manage records after saving.")
            st.json(pending["normalized"])
            if st.button("Save reviewed AI result to dashboard", type="primary", key=f"ai_save_{selected_id}"):
                try:
                    save_subscription(pending["normalized"], email_id=selected_id, source="ai")
                except ValueError as exc:
                    st.error(f"Could not save AI result: {exc}")
                else:
                    st.session_state.pop("pending_ai_result", None)
                    st.success("Saved to your dashboard. Review and correct the record under Manage records.")


def email_selector(label: str, *, selected: int | None = None, key: str | None = None) -> int | None:
    emails = list_emails()
    opts = [None] + [e["id"] for e in emails]
    labels = {e["id"]: f"#{e['id']} — {e['subject'] or e['filename']}" for e in emails}
    return st.selectbox(label, opts, index=opts.index(selected) if selected in opts else 0, format_func=lambda eid: "No email linked" if eid is None else labels[eid], key=key)


def subscription_form(prefix: str, *, existing: dict | None = None) -> None:
    default = existing or {}
    st.caption("Use ISO dates (YYYY-MM-DD). Leave any unknown detail blank—never guess renewal or cancellation dates.")
    with st.form(f"form_{prefix}"):
        service = st.text_input("Service name *", value=default.get("service_name", ""), key=f"{prefix}_name")
        a, b, c = st.columns(3)
        with a:
            type_options = ["subscription", "trial"]
            record_type = st.selectbox("Record type", type_options, index=type_options.index(default.get("record_type", "subscription")), key=f"{prefix}_kind", format_func=lambda s: "Active subscription" if s == "subscription" else "Free trial")
        with b:
            amount = st.text_input("Expected charge (USD)", value=(str(Decimal(default["amount_cents"]) / 100) if default.get("amount_cents") is not None else ""), placeholder="e.g. 9.99", key=f"{prefix}_amount")
        with c:
            freq = st.selectbox("Billing frequency", FREQUENCIES, index=FREQUENCIES.index(default.get("frequency", "Unknown")) if default.get("frequency", "Unknown") in FREQUENCIES else 0, key=f"{prefix}_freq")
        d, e, f = st.columns(3)
        with d:
            renewal = st.text_input("Next renewal date", value=default.get("renewal_date") or "", placeholder="YYYY-MM-DD", key=f"{prefix}_renew")
        with e:
            trial_end = st.text_input("Trial expiration date", value=default.get("trial_end_date") or "", placeholder="YYYY-MM-DD", key=f"{prefix}_trial")
        with f:
            cancel = st.text_input("Cancellation deadline", value=default.get("cancellation_deadline") or "", placeholder="YYYY-MM-DD", key=f"{prefix}_cancel")
        instructions = st.text_area("Cancellation instructions", value=default.get("cancellation_instructions", ""), key=f"{prefix}_instructions", height=84)
        notes = st.text_area("Notes", value=default.get("notes", ""), key=f"{prefix}_notes", height=60)
        linked = email_selector("Supporting email", selected=default.get("email_id"), key=f"{prefix}_email")
        submitted = st.form_submit_button("Save subscription" if existing else "Add subscription", type="primary", use_container_width=True)
    if submitted:
        try:
            record = {
                "service_name": service, "record_type": record_type, "amount": amount, "frequency": freq,
                "renewal_date": renewal, "trial_end_date": trial_end, "cancellation_deadline": cancel,
                "cancellation_instructions": instructions, "notes": notes,
            }
            save_subscription(record, email_id=linked, subscription_id=existing["id"] if existing else None, source=existing["source"] if existing else "manual")
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("Saved. Your dashboard is updated.")
            # Streamlit refreshes cards on the next navigation/rerun.


def render_manage() -> None:
    render_hero("Manage records")
    new_tab, edit_tab, archived_tab = st.tabs(["Add a subscription", "Edit / archive", "Archived records"])
    with new_tab:
        subscription_form("new")
    with edit_tab:
        items = list_subscriptions()
        if not items:
            st.info("Add a subscription or load the synthetic demo data to enable editing.")
        else:
            chosen = st.selectbox("Select a record", items, format_func=lambda r: f"#{r['id']} · {r['service_name']} ({'Trial' if r['record_type'] == 'trial' else 'Subscription'})", key="edit_select")
            subscription_form(f"edit_{chosen['id']}", existing=chosen)
            st.divider()
            with st.popover("Archive this record"):
                st.caption("Archiving hides it from the active dashboard; you can restore it later.")
                if st.button("Confirm archive", key=f"archive_{chosen['id']}"):
                    archive_subscription(chosen["id"])
                    st.rerun()
    with archived_tab:
        archived = [r for r in list_subscriptions(include_archived=True) if r["is_archived"]]
        if not archived:
            st.info("Nothing archived.")
        for rec in archived:
            c1, c2 = st.columns([4, 1], vertical_alignment="center")
            c1.write(f"**{rec['service_name']}** — archived")
            if c2.button("Restore", key=f"restore_{rec['id']}"):
                archive_subscription(rec["id"], archived=False)
                st.rerun()


EXAMPLE_JSON = {
    "service_name": "Example Premium",
    "record_type": "subscription",
    "amount": 9.99,
    "currency": "USD",
    "frequency": "Monthly",
    "renewal_date": "2026-12-05",
    "trial_end_date": None,
    "cancellation_deadline": None,
    "cancellation_instructions": "Open account settings and select Cancel.",
    "notes": "Sample JSON only — not a verified extraction.",
}


def render_integration() -> None:
    render_hero("Team integration")
    st.info("The team AI extractor is optionally available from Email inbox when a valid API key is configured. Date validation/cancellation calculations and calendar reminders still need your teammates' modules.")
    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Import extracted JSON")
        st.caption("Use one subscription object or a JSON array of objects. Every record is checked before anything is saved.")
        json_file = st.file_uploader("Optional JSON file", type=["json"], key="json_upload")
        raw = st.text_area("Or paste JSON", height=225, placeholder=json.dumps(EXAMPLE_JSON, indent=2))
        linked = email_selector("Link imported result to an uploaded email", key="ai_email_link")
        if st.button("Validate & import JSON", type="primary", use_container_width=True):
            try:
                source = json_file.getvalue().decode("utf-8-sig") if json_file else raw
                if not source.strip():
                    raise ValueError("Please paste JSON or select a JSON file.")
                decoded = json.loads(source)
                payloads = decoded if isinstance(decoded, list) else [decoded]
                if not payloads:
                    raise ValueError("The JSON array is empty.")
                if len(payloads) > 100:
                    raise ValueError("Import a maximum of 100 items at a time.")
                validated = [normalize_subscription(item) for item in payloads]
                for rec in validated:
                    save_subscription(rec, email_id=linked, source="import")
                st.success(f"Imported {len(validated)} subscription record(s). View them on Overview.")
            except (ValueError, json.JSONDecodeError, UnicodeError) as exc:
                st.error(f"Import failed: {exc}")
    with right:
        st.subheader("Expected JSON schema")
        st.code(json.dumps(EXAMPLE_JSON, indent=2), language="json")
        st.caption("Accepted teammate keys: `name`, `price`, `billing_cycle`, `renewal_date` (Month DD, YYYY), `cancellation_policy`, `cancellation_notice_amount`, `cancellation_notic_unit`. Unknown values must be null, not invented.")
    st.divider()
    st.subheader("How the team's modules connect")
    st.code('''# 1. Upload (this module)
email_id, _ = add_email("receipt.eml", email_bytes)

# 2. AI extraction (teammate's module)
email_payload = email_for_ai(email_id)
# extraction = teammate_extract(email_payload)  # returns dict

# 3. Validation / cancellation dates (teammate's module)
# checked = teammate_validate(extraction)

# 4. Save to dashboard (this module)
# save_subscription(checked, email_id=email_id, source="ai")

# 5. Calendar reminder (.ics): teammate's module
''', language="python")


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("### 📅 AutoPay Watcher")
        st.caption("SUBSCRIPTION CONTROL CENTER")
        st.divider()
        page = st.radio("Navigation", ["Overview", "Email inbox", "Manage records", "Team integration"], label_visibility="collapsed")
        st.divider()
        st.caption("DEMO MODE")
        if st.button("✨ Load sample subscriptions", use_container_width=True):
            added = demo_records()
            if added:
                st.toast(f"Added {added} synthetic demo records", icon="✅")
            else:
                st.toast("Demo records are already present", icon="ℹ️")
            st.rerun()
        st.caption("Synthetic examples only. No real charges, notifications, or account access.")
        st.divider()
        st.caption("LOCAL STORAGE")
        st.code(str(database_path()), language=None)
        st.caption("Uploaded emails are stored locally in SQLite. Do not commit your database or secrets.")
    return page


def render_app(ai_extractor=None) -> None:
    initialize_database()
    page = render_sidebar()
    if page == "Overview":
        render_dashboard()
    elif page == "Email inbox":
        render_mail_upload(ai_extractor=ai_extractor)
    elif page == "Manage records":
        render_manage()
    else:
        render_integration()

