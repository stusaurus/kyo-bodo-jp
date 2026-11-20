"""Offline contract tests: never require Google credentials or external requests."""
import datetime as dt
import importlib.util
import os
from pathlib import Path
from unittest import TestCase, mock

MODULE = Path(__file__).with_name("read_only_report.py")
spec = importlib.util.spec_from_file_location("free_google_report", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(dimensions, values):
    return {"dimensionValues": [{"value": v} for v in dimensions],
            "metricValues": [{"value": str(x)} for x in values]}


class FreeOfficialMeasurementTests(TestCase):
    def test_exact_properties_are_not_other_sites(self):
        self.assertEqual(m.GA4_PROPERTY, "556462193")
        self.assertEqual(m.SITE, "https://stusaurus.github.io/kyo-bodo-jp/")
        self.assertEqual(m.CAMPAIGN, "gift_guide_20261119")

    def test_recent_publication_not_in_completed_ga4_days(self):
        dates = m.report_dates(dt.date(2026, 11, 20))
        self.assertIsNone(dates["ga4"])
        self.assertEqual(dates["gsc"][1], dt.date(2026, 11, 17))
        dates = m.report_dates(dt.date(2026, 11, 23))
        self.assertEqual(dates["ga4"], (dt.date(2026, 11, 20),
                                        dt.date(2026, 11, 21)))

    def test_unconfigured_is_neither_traffic_zero_nor_successful_auth(self):
        with mock.patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": ""}):
            report = m.run(today=dt.date(2026, 11, 20))
        self.assertEqual(report["status"], "NOT_CONFIGURED")
        self.assertEqual(report["ga4"]["status"], "NOT_CONFIGURED")
        self.assertEqual(report["gsc"]["status"], "NOT_CONFIGURED")
        self.assertIsNone(report["gsc"]["metrics"])
        self.assertFalse(report["ga4"]["missing_is_zero"])
        md = m.to_markdown(report)
        self.assertIn("未取得・未観測", md)

    def test_gsc_missing_page_row_is_unknown(self):
        site = {"rows": [{"clicks": 2, "impressions": 31, "ctr": 2/31,
                          "position": 17.5}]}
        pages = {"rows": [{"keys": [m.SITE + "scenes/two-player/"],
                            "clicks": 1, "impressions": 10,
                            "ctr": 0.1, "position": 16.5},
                           {"keys": ["https://other.example/path/"],
                            "clicks": 777, "impressions": 888,
                            "ctr": 0.8, "position": 1.0}]}
        r = m.parse_gsc(site, pages, (dt.date(2026, 11, 1),
                                      dt.date(2026, 11, 18)))
        self.assertEqual(r["site_metrics"]["clicks"], 2)
        self.assertEqual(r["pages"]["scenes/two-player/"]["impressions"], 10)
        self.assertIsNone(r["pages"]["guides/gift-board-games/"])
        self.assertNotIn("https://other.example/path/", r["pages"])

    def test_gsc_empty_rows_are_unknown(self):
        r = m.parse_gsc({}, {}, (dt.date(2026, 10, 20), dt.date(2026, 11, 16)))
        self.assertEqual(r["status"], "NO_OBSERVED_ROWS")
        self.assertIsNone(r["site_metrics"])
        self.assertTrue(all(p is None for p in r["pages"].values()))

    def test_gsc_bad_metrics_rejected(self):
        self.assertIsNone(m.metrics({"clicks": -1, "impressions": 2,
                                     "ctr": 0.0, "position": 1.5}))
        self.assertIsNone(m.metrics({"clicks": "x", "impressions": 2,
                                     "ctr": 0.0, "position": 1.5}))

    def test_ga4_registered_operator_dimension_is_provisional(self):
        dims0 = ["20261120", "note_campaign_landing", m.CAMPAIGN,
                 "note / referral", "/kyo-bodo-jp/guides/gift-board-games/", "0"]
        dims1 = ["20261120", "note_campaign_landing", m.CAMPAIGN,
                 "note / referral", "/kyo-bodo-jp/guides/gift-board-games/", "1"]
        event_rows = {"rowCount": 2, "rows": [row(dims0, [2]),
                                                row(dims1, [1])]}
        session_rows = {"rowCount": 1,
                        "rows": [row([m.CAMPAIGN, "note / referral"], [2, 2])]}
        r = m.parse_ga4(event_rows, session_rows, True,
                        (dt.date(2026, 11, 20), dt.date(2026, 11, 21)))
        self.assertEqual(r["status"], "OBSERVED_ROWS")
        metric = r["event_counts"]["note_campaign_landing"]
        self.assertEqual(metric["raw_event_count"], 3)
        self.assertEqual(metric["known_operator_tests"], 1)
        self.assertEqual(metric["possibly_non_test_events"], 2)
        self.assertIsNone(r["event_counts"]["affiliate_click"]["raw_event_count"])
        self.assertEqual(r["visits"]["sessions_including_tests"], 2)

    def test_ga4_missing_custom_dimension_cannot_establish_non_tests(self):
        sample = row(["20261120", "affiliate_click", m.CAMPAIGN,
                      "note / referral", "/kyo-bodo-jp/games/dobble/"], [2])
        r = m.parse_ga4({"rows": [sample]}, {"rows": []}, False,
                        (dt.date(2026, 11, 20), dt.date(2026, 11, 21)))
        values = r["event_counts"]["affiliate_click"]
        self.assertEqual(values["raw_event_count"], 2)
        self.assertIsNone(values["possibly_non_test_events"])
        self.assertFalse(r["operator_dimension_registered"])

    def test_ga4_cross_site_or_campaign_is_rejected(self):
        bad = row(["20261120", "affiliate_click", "other_campaign",
                   "note / referral", "/daily-cost-jp/"], [250])
        r = m.parse_ga4({"rows": [bad]}, {"rows": []}, False,
                        (dt.date(2026, 11, 20), dt.date(2026, 11, 21)))
        self.assertEqual(r["status"], "QUALITY_RESTRICTED")
        self.assertIsNone(r["metrics"])

    def test_ga4_thresholding_and_truncation_are_not_zero(self):
        for raw in ({"metadata": {"subjectToThresholding": True}},
                    {"rowCount": 2, "rows": [row([], [1])]},
                    {"metadata": {"dataLossFromOtherRow": True}}):
            r = m.parse_ga4(raw, {}, False,
                            (dt.date(2026, 11, 20), dt.date(2026, 11, 21)))
            self.assertEqual(r["status"], "QUALITY_RESTRICTED")
            self.assertIsNone(r["metrics"])

    def test_no_ga4_rows_are_unknown(self):
        r = m.parse_ga4({}, {}, True,
                        (dt.date(2026, 11, 20), dt.date(2026, 11, 21)))
        self.assertEqual(r["status"], "NO_OBSERVED_ROWS")
        self.assertIsNone(r["visits"])
        self.assertTrue(all(x["raw_event_count"] is None for x in
                            r["event_counts"].values()))

    def test_gsc_requires_exact_own_property_not_parent(self):
        class Fake:
            status_code = 200
            def json(self):
                return {"siteEntry": [
                    {"siteUrl": "https://stusaurus.github.io/",
                     "permissionLevel": "siteOwner"}]}
        class Session:
            def get(self, *args, **kwargs):
                return Fake()
            def post(self, *args, **kwargs):
                raise AssertionError("Queries must not run on parent property")
        r = m.fetch_gsc(Session(), dt.date(2026, 11, 20))
        self.assertEqual(r["status"], "NOT_AUTHORIZED")
        self.assertEqual(r["reason"], "EXACT_SITE_PERMISSION_MISSING")


if __name__ == "__main__":
    import unittest
    unittest.main()
