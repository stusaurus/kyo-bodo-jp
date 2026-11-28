"""Guard the existing Google read-only workflow's scheduled execution boundary."""
import unittest
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[1] / ".github/workflows/free-google-measurement.yml").read_text(encoding="utf-8")


class GoogleScheduleContractTests(unittest.TestCase):
    def test_daily_and_manual_triggers_share_main_only_authenticated_job(self):
        triggers, jobs = WORKFLOW.split("\njobs:\n", 1)
        self.assertIn("\n  workflow_dispatch:\n", triggers)
        self.assertIn("\n  schedule:\n", triggers)
        self.assertIn("- cron: '37 1 * * *'", triggers)
        offline, official = jobs.split("\n  official-read-only-report:\n", 1)
        self.assertIn("if: github.event_name == 'pull_request'", offline)
        self.assertNotIn("id-token: write", offline)
        self.assertNotIn("google-github-actions/auth@", offline)
        self.assertIn("if: github.ref == 'refs/heads/main' && (github.event_name == 'workflow_dispatch' || github.event_name == 'schedule')", official)

    def test_auth_and_evidence_require_existing_read_only_configuration(self):
        _, official = WORKFLOW.split("\n  official-read-only-report:\n", 1)
        self.assertIn("contents: read", official)
        self.assertIn("id-token: write", official)
        self.assertIn("persist-credentials: false", official)
        self.assertIn("vars.KYO_GCP_WIF_PROVIDER != '' && vars.KYO_GCP_SERVICE_ACCOUNT != ''", official)
        self.assertIn("python analytics/read_only_report.py", official)
        self.assertIn('allowed = {"OBSERVED_ROWS", "NO_OBSERVED_ROWS"}', official)
        self.assertIn("raise SystemExit(1)", official)
        self.assertIn("retention-days: 14", official)
        self.assertIn("cancel-in-progress: false", official)
        self.assertNotIn("pages: write", official)
        self.assertNotIn("contents: write", official)


if __name__ == "__main__":
    unittest.main()
