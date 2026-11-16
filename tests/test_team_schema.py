"""Regression tests for teammate extractor -> dashboard interface."""
import tempfile
from pathlib import Path
import unittest

from autopay_core import (
    add_email, initialize_database, list_subscriptions,
    normalize_date, normalize_subscription, save_subscription,
)


class TeamSchemaTests(unittest.TestCase):
    def test_teammate_ai_shape(self):
        teammate_output = {
            "name": "Sample Service",
            "price": "$12.50",
            "billing_cycle": "monthly",
            "renewal_date": "December 12, 2026",
            "cancellation_policy": "Cancel 48 hours before renewal.",
            "cancellation_notice_amount": 48,
            "cancellation_notic_unit": "hours",  # exactly as teammate's prompt spells it
        }
        item = normalize_subscription(teammate_output)
        self.assertEqual(item["service_name"], "Sample Service")
        self.assertEqual(item["amount_cents"], 1250)
        self.assertEqual(item["frequency"], "Monthly")
        self.assertEqual(item["renewal_date"], "2026-12-12")
        self.assertEqual(item["cancellation_instructions"], "Cancel 48 hours before renewal.")
        self.assertIn("48 hours", item["notes"])
        self.assertIsNone(item["cancellation_deadline"])

    def test_end_to_end_team_result_into_database(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "test.db"
            initialize_database(database)
            mail_id, is_new = add_email(
                "example.eml",
                b"From: demo@example.invalid\nSubject: Renewal\nContent-Type: text/plain; charset=utf-8\n\nThis is fake test data.",
                database,
            )
            self.assertTrue(is_new)
            result = normalize_subscription({
                "name": "Fake Sub", "price": "4.99", "billing_cycle": "yearly",
                "renewal_date": "November 20, 2026", "cancellation_policy": None,
            })
            save_subscription(result, email_id=mail_id, source="ai", path=database)
            records = list_subscriptions(database)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["service_name"], "Fake Sub")
            self.assertEqual(records[0]["frequency"], "Yearly")
            self.assertEqual(records[0]["renewal_date"], "2026-11-20")
            self.assertEqual(records[0]["email_id"], mail_id)
            self.assertIsNone(records[0]["cancellation_deadline"])

    def test_unambiguous_date_only(self):
        self.assertEqual(normalize_date("Nov 20, 2026"), "2026-11-20")
        self.assertEqual(normalize_date("2026-11-20"), "2026-11-20")
        with self.assertRaises(ValueError):
            normalize_date("11/12/2026")

    def test_missing_fields_stay_unknown(self):
        row = normalize_subscription({"name": "Missing"})
        self.assertIsNone(row["amount_cents"])
        self.assertIsNone(row["renewal_date"])
        self.assertIsNone(row["cancellation_deadline"])
        self.assertEqual(row["frequency"], "Unknown")


if __name__ == "__main__":
    unittest.main()
