"""End-to-end-ish tests for the UI owner's database and email ingestion boundary."""

from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopay_core import (
    add_email, archive_subscription, cents_from_amount, db_connection,
    delete_email, demo_records, email_for_ai, get_email, initialize_database,
    list_emails, list_subscriptions, monthly_equivalent_cents,
    normalize_date, normalize_subscription, read_email, save_subscription,
    sort_by_upcoming,
)


class AutoPayCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "db" / "autopay.db"
        initialize_database(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_eml_multipart_ignores_attachments_and_decodes_subject(self):
        from email.message import EmailMessage
        mail = EmailMessage()
        mail["From"] = "billing@example.invalid"
        mail["To"] = "student@example.invalid"
        mail["Subject"] = "Your café renewal"
        mail.set_content("Your next charge is $12.00.\n")
        mail.add_alternative("<html><body><h2>HTML email</h2><p>$99.99</p></body></html>", subtype="html")
        mail.add_attachment(b"sensitive hidden attachment", maintype="application", subtype="octet-stream", filename="secret.bin")
        parsed = read_email("sample.eml", mail.as_bytes())
        self.assertIn("Your next charge", parsed["body_text"])
        self.assertNotIn("sensitive hidden attachment", parsed["body_text"])
        self.assertNotIn("$99.99", parsed["body_text"])
        self.assertEqual(parsed["subject"], "Your café renewal")

    def test_html_only_email(self):
        data = b"Subject: HTML-only\nMIME-Version: 1.0\nContent-Type: text/html; charset=utf-8\n\n<html><head><style>secret-css</style></head><body><script>dont_run()</script><p>Cancel by Friday</p></body></html>"
        parsed = read_email("s.eml", data)
        self.assertIn("Cancel by Friday", parsed["body_text"])
        self.assertNotIn("secret-css", parsed["body_text"])
        self.assertNotIn("dont_run", parsed["body_text"])

    def test_reject_oversize_empty_invalid_extension(self):
        for name, payload in [("a.eml", b""), ("a.pdf", b"ok"), ("a.eml", b"a" * (2 * 1024 * 1024 + 1))]:
            with self.subTest(name=name, size=len(payload)), self.assertRaises(ValueError):
                read_email(name, payload)

    def test_duplicate_email_and_text_handoff(self):
        payload = b"Subject: Reminder\nFrom: examples@fake.invalid\n\nYour trial ends soon."
        one, created = add_email("email.eml", payload, self.path)
        two, created_again = add_email("different_name.eml", payload, self.path)
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(one, two)
        self.assertEqual(len(list_emails(self.path)), 1)
        self.assertEqual(email_for_ai(one, self.path)["body"], "Your trial ends soon.")
        self.assertEqual(get_email(one, self.path)["original_bytes"], payload)

    def test_json_handoff_persists_and_manual_edit(self):
        eid, _ = add_email("receipt.txt", b"Renew in April", self.path)
        rec_id = save_subscription({"service_name": "Cloud Service", "amount": "19.99", "frequency": "Monthly", "renewal_date": "2027-04-05"}, email_id=eid, source="ai", path=self.path)
        row = list_subscriptions(self.path)[0]
        self.assertEqual(row["amount_cents"], 1999)
        self.assertEqual(row["email_id"], eid)
        self.assertEqual(row["source"], "ai")
        save_subscription({"service_name": "Cloud Service", "amount": "21.50", "frequency": "Yearly", "renewal_date": "2027-04-05"}, email_id=eid, source="ai", subscription_id=rec_id, path=self.path)
        self.assertEqual(list_subscriptions(self.path)[0]["amount_cents"], 2150)
        archive_subscription(rec_id, path=self.path)
        self.assertEqual(len(list_subscriptions(self.path)), 0)
        archive_subscription(rec_id, archived=False, path=self.path)
        self.assertEqual(len(list_subscriptions(self.path)), 1)

    def test_delete_email_detaches_subscription(self):
        eid, _ = add_email("email.txt", b"Subscription receipt", self.path)
        save_subscription({"service_name": "Service"}, email_id=eid, path=self.path)
        delete_email(eid, self.path)
        self.assertIsNone(list_subscriptions(self.path)[0]["email_id"])

    def test_dates_prices_unknown_and_currency(self):
        self.assertIsNone(normalize_date(None))
        self.assertIsNone(normalize_date("unknown"))
        self.assertIsNone(cents_from_amount(None))
        self.assertEqual(cents_from_amount("$1,234.567"), 123457)
        self.assertEqual(normalize_date("2027-02-28"), "2027-02-28")
        for bad_date in ["2027-02-30", "tomorrow"]:
            with self.assertRaises(ValueError): normalize_date(bad_date)
        for bad_amount in ["abc", "-10", "NaN"]:
            with self.assertRaises(ValueError): cents_from_amount(bad_amount)
        with self.assertRaises(ValueError): normalize_subscription({"service_name": "X", "currency": "EUR"})
        missing = normalize_subscription({"service_name": "X", "record_type": "trial"})
        self.assertIsNone(missing["cancellation_deadline"])
        self.assertIsNone(missing["trial_end_date"])
        self.assertIsNone(missing["amount_cents"])

    def test_aliases_and_sort_missing_last(self):
        alias = normalize_subscription({"subscription_name": "Free Course", "is_free_trial": True, "trial_expiration_date": "2027-01-01", "price": "$0", "billing_frequency": "monthly"})
        self.assertEqual(alias["record_type"], "trial")
        self.assertEqual(alias["frequency"], "Monthly")
        self.assertEqual(alias["trial_end_date"], "2027-01-01")
        objects = [{"service_name": "Z", "renewal_date": None}, {"service_name": "A", "renewal_date": "2027-02-02"}, {"service_name": "C", "renewal_date": "2027-01-20"}]
        self.assertEqual([r["service_name"] for r in sort_by_upcoming(objects, "renewal_date")], ["C", "A", "Z"])

    def test_total_excludes_unknowns_and_trials(self):
        s1 = {"record_type": "subscription", "amount_cents": 1200, "frequency": "Monthly"}
        s2 = {"record_type": "subscription", "amount_cents": 5200, "frequency": "Yearly"}
        s3 = {"record_type": "trial", "amount_cents": 1000, "frequency": "Monthly"}
        s4 = {"record_type": "subscription", "amount_cents": 1000, "frequency": "Unknown"}
        self.assertEqual(round(monthly_equivalent_cents(s1) + monthly_equivalent_cents(s2), 2), Decimal("1633.33"))
        self.assertIsNone(monthly_equivalent_cents(s3))
        self.assertIsNone(monthly_equivalent_cents(s4))

    def test_sample_email_through_json_to_dashboard_database(self):
        sample_dir = Path(__file__).resolve().parent.parent / "samples"
        payload = (sample_dir / "renewal_sample.eml").read_bytes()
        eid, created = add_email("renewal_sample.eml", payload, self.path)
        self.assertTrue(created)
        self.assertIn("CloudBox", email_for_ai(eid, self.path)["subject"])
        extracted_fixture = json.loads((sample_dir / "example_extraction.json").read_text())
        record = extracted_fixture[1]
        sid = save_subscription(record, email_id=eid, source="import", path=self.path)
        displayed = list_subscriptions(self.path)
        self.assertEqual(len(displayed), 1)
        self.assertEqual(displayed[0]["id"], sid)
        self.assertEqual(displayed[0]["service_name"], "CloudBox Basic")
        self.assertEqual(displayed[0]["renewal_date"], "2026-12-12")
        self.assertEqual(displayed[0]["amount_cents"], 800)
        self.assertEqual(displayed[0]["email_filename"], "renewal_sample.eml")

    def test_demo_is_repeat_safe_and_dates_dynamic(self):
        self.assertEqual(demo_records(self.path), 5)
        self.assertEqual(demo_records(self.path), 0)
        records = list_subscriptions(self.path)
        self.assertEqual(len(records), 5)
        self.assertEqual(len([r for r in records if r["record_type"] == "trial"]), 2)
        first = next(r for r in records if r["service_name"] == "DesignLab")
        self.assertEqual(first["trial_end_date"], (date.today() + timedelta(days=3)).isoformat())


if __name__ == "__main__":
    unittest.main()
