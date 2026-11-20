#!/usr/bin/env python3
"""Free, read-only, site-scoped official GA4 + GSC measurement.

No private identifiers, no service account keys, no analytics events sent.
Missing credentials, unavailable dimensions and absent rows are NEVER zeroes.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

SITE = "https://stusaurus.github.io/kyo-bodo-jp/"
GA4_PROPERTY = "556462193"
CAMPAIGN = "gift_guide_20261119"
CAMPAIGN_LAUNCH = dt.date(2026, 11, 20)
EVENTS = ("note_campaign_landing", "game_detail_click",
          "affiliate_click", "rakuten_search_click")
PAGES = ("", "scenes/two-player/", "scenes/couple/",
         "scenes/children/", "guides/gift-board-games/")
SCOPES = ("https://www.googleapis.com/auth/analytics.readonly",
          "https://www.googleapis.com/auth/webmasters.readonly")
AUDIT_DIR = Path("audit-results/free-google")
GSC_API = "https://www.googleapis.com/webmasters/v3"
GA_API = "https://analyticsdata.googleapis.com/v1beta"


def report_dates(today):
    """Use only completed and lagged days; the publication day is never guessed."""
    gsc_end = today - dt.timedelta(days=3)
    gsc_start = gsc_end - dt.timedelta(days=27)
    ga_end = today - dt.timedelta(days=2)
    ga_start = max(CAMPAIGN_LAUNCH, ga_end - dt.timedelta(days=6))
    return {"gsc": (gsc_start, gsc_end),
            "ga4": (ga_start, ga_end) if ga_start <= ga_end else None}


def unavailable(source, reason, status="UNAVAILABLE"):
    return {"source": source, "status": status, "reason": reason,
            "metrics": None, "missing_is_zero": False}


def metrics(row):
    if not isinstance(row, dict):
        return None
    try:
        clicks = int(row["clicks"])
        impressions = int(row["impressions"])
        ctr = float(row["ctr"])
        position = float(row["position"])
        if clicks < 0 or impressions < 0 or not 0 <= ctr <= 1 or position < 0:
            return None
        return {"clicks": clicks, "impressions": impressions,
                "ctr": round(ctr, 5), "average_position": round(position, 2)}
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def parse_gsc(site_payload, page_payload, window):
    """No row is unknown, never an implied zero; top rows can be incomplete."""
    site_rows = site_payload.get("rows", [])
    page_rows = page_payload.get("rows", [])
    if not isinstance(site_rows, list) or not isinstance(page_rows, list):
        return unavailable("GSC", "MALFORMED_RESPONSE")
    if len(site_rows) > 1:
        return unavailable("GSC", "UNEXPECTED_AGGREGATION")
    top_pages = {}
    for row in page_rows:
        keys = row.get("keys", [])
        if isinstance(keys, list) and len(keys) == 1:
            url = keys[0]
            if isinstance(url, str) and url.startswith(SITE):
                top_pages[url] = metrics(row)
    return {"source": "GSC Search Analytics API", "status": (
                "OBSERVED_ROWS" if site_rows else "NO_OBSERVED_ROWS"),
            "site_property": SITE, "window": [d.isoformat() for d in window],
            "site_metrics": metrics(site_rows[0]) if site_rows else None,
            "pages": {p: top_pages.get(SITE + p) for p in PAGES},
            "page_rows_returned": len(page_rows),
            "page_coverage": ("TOP_ROWS_POSSIBLY_TRUNCATED"
                              if len(page_rows) >= 25000 else "TOP_ROWS_NONEXHAUSTIVE"),
            "notes": ["Missing page rows are unknown, not zero.",
                      "GSC reports Google Search, not note referrals or Rakuten sales.",
                      "Three-day final-data lag; newly published pages may not be covered."]}


def ga4_quality(response):
    meta = response.get("metadata") or {}
    if meta.get("subjectToThresholding") or meta.get("dataLossFromOtherRow"):
        return "THRESHOLDED_OR_OTHER_ROW"
    rows = response.get("rows", [])
    if not isinstance(rows, list):
        return "MALFORMED_ROWS"
    if int(response.get("rowCount", len(rows))) > len(rows):
        return "TRUNCATED_ROWS"
    return None


def parse_ga4(events_response, visits_response, operator_registered, window):
    for response in (events_response, visits_response):
        reason = ga4_quality(response)
        if reason:
            return unavailable("GA4 Data API", reason, "QUALITY_RESTRICTED")
    names = ["date", "eventName", "sessionManualCampaignName",
             "sessionManualSourceMedium", "pagePath"]
    if operator_registered:
        names.append("customEvent:operator_test")
    summary = {}
    for name in EVENTS:
        summary[name] = {"raw_event_count": None, "known_operator_tests": None,
                         "possibly_non_test_events": None, "unknown_operator_events": None}
    for row in events_response.get("rows", []):
        try:
            vals = [v["value"] for v in row["dimensionValues"]]
            raw = dict(zip(names, vals))
            count = int(row["metricValues"][0]["value"])
            if (len(vals) != len(names) or count < 0 or
                raw["eventName"] not in EVENTS or
                raw["sessionManualCampaignName"] != CAMPAIGN or
                raw["sessionManualSourceMedium"].strip().lower() != "note / referral" or
                not raw["pagePath"].startswith("/kyo-bodo-jp/")):
                return unavailable("GA4 Data API", "UNEXPECTED_EVENT_SCOPE", "QUALITY_RESTRICTED")
        except (KeyError, TypeError, ValueError, IndexError):
            return unavailable("GA4 Data API", "MALFORMED_EVENT_ROW", "QUALITY_RESTRICTED")
        item = summary[raw["eventName"]]
        item["raw_event_count"] = (item["raw_event_count"] or 0) + count
        if operator_registered:
            flag = raw["customEvent:operator_test"]
            key = {"1": "known_operator_tests", "0": "possibly_non_test_events"}.get(
                flag, "unknown_operator_events")
            item[key] = (item[key] or 0) + count
    visits = None
    if visits_response.get("rows"):
        if len(visits_response["rows"]) != 1:
            return unavailable("GA4 Data API", "MULTIPLE_SESSION_ROWS", "QUALITY_RESTRICTED")
        try:
            row = visits_response["rows"][0]
            dims = [x["value"] for x in row["dimensionValues"]]
            nums = [int(x["value"]) for x in row["metricValues"]]
            if (dims != [CAMPAIGN, "note / referral"] or len(nums) != 2
                    or min(nums) < 0):
                raise ValueError("Invalid aggregate")
            visits = {"sessions_including_tests": nums[0],
                      "active_users_including_tests": nums[1]}
        except (KeyError, TypeError, ValueError, IndexError):
            return unavailable("GA4 Data API", "MALFORMED_SESSION_ROW", "QUALITY_RESTRICTED")
    return {"source": "GA4 Data API", "status": (
                "OBSERVED_ROWS" if events_response.get("rows") or visits
                else "NO_OBSERVED_ROWS"),
            "property_id": GA4_PROPERTY, "campaign": CAMPAIGN,
            "window": [d.isoformat() for d in window],
            "operator_dimension_registered": operator_registered,
            "event_counts": summary, "visits": visits,
            "notes": ["Event count is not user count or confirmed purchase.",
                      "operator_test=0 can include unmarked owner tests.",
                      "No row means unknown; no fabricated zero.",
                      "If customEvent:operator_test is absent, non-test events are unknowable."]}


def safe_json(response, source):
    if response.status_code != 200:
        raise RuntimeError(source + "_HTTP_" + str(response.status_code))
    return response.json()


def fetch_gsc(session, today):
    windows = report_dates(today)
    access = safe_json(session.get(GSC_API + "/sites", timeout=30), "GSC_ACCESS")
    authorized = access.get("siteEntry", [])
    if not any(x.get("siteUrl") == SITE and x.get("permissionLevel") in
               ("siteOwner", "siteFullUser", "siteRestrictedUser") for x in authorized):
        return unavailable("GSC", "EXACT_SITE_PERMISSION_MISSING", "NOT_AUTHORIZED")
    start, end = windows["gsc"]
    base = {"startDate": start.isoformat(), "endDate": end.isoformat(),
            "type": "web", "dataState": "final"}
    endpoint = GSC_API + "/sites/" + quote(SITE, safe="") + "/searchAnalytics/query"
    def query(payload):
        return safe_json(session.post(endpoint, json=payload, timeout=45), "GSC_QUERY")
    site = query(base)
    pages = query({**base, "dimensions": ["page"], "rowLimit": 25000})
    return parse_gsc(site, pages, (start, end))


def fetch_ga4(session, today):
    window = report_dates(today)["ga4"]
    if window is None:
        return unavailable("GA4", "PUBLICATION_NOT_IN_COMPLETED_DATA", "NOT_YET_REPORTABLE")
    property_resource = "properties/" + GA4_PROPERTY
    metadata = safe_json(session.get(GA_API + "/" + property_resource + "/metadata",
                                     timeout=30), "GA4_METADATA")
    available = {x.get("apiName") for x in metadata.get("dimensions", [])}
    required = {"date", "eventName", "sessionManualCampaignName",
                "sessionManualSourceMedium", "pagePath"}
    if not required.issubset(available):
        return unavailable("GA4", "REQUIRED_DIMENSIONS_UNAVAILABLE", "DATA_LIMITED")
    has_operator = "customEvent:operator_test" in available
    date_range = [{"startDate": window[0].isoformat(),
                   "endDate": window[1].isoformat()}]
    def exact(field, value):
        return {"filter": {"fieldName": field, "stringFilter": {
            "matchType": "EXACT", "value": value}}}
    def scoped_filters():
        return {"andGroup": {"expressions": [
            exact("sessionManualCampaignName", CAMPAIGN),
            exact("sessionManualSourceMedium", "note / referral"),
            exact("hostName", "stusaurus.github.io")]}}
    def query(body):
        return safe_json(session.post(GA_API + "/" + property_resource +
                                      ":runReport", json=body, timeout=45), "GA4_QUERY")
    dimensions = ["date", "eventName", "sessionManualCampaignName",
                  "sessionManualSourceMedium", "pagePath"]
    if has_operator:
        dimensions.append("customEvent:operator_test")
    raw = query({"dateRanges": date_range,
                 "dimensions": [{"name": name} for name in dimensions],
                 "metrics": [{"name": "eventCount"}],
                 "dimensionFilter": scoped_filters(), "limit": 10000})
    visits = query({"dateRanges": date_range,
                    "dimensions": [{"name": "sessionManualCampaignName"},
                                   {"name": "sessionManualSourceMedium"}],
                    "metrics": [{"name": "sessions"}, {"name": "activeUsers"}],
                    "dimensionFilter": scoped_filters(), "limit": 1000})
    return parse_ga4(raw, visits, has_operator, window)


def to_markdown(report):
    a, b = report["ga4"], report["gsc"]
    lines = ["## きょうボド｜Google公式API 無料・読み取り専用計測", "",
             "- GA4：**" + a["status"] + "**（" + a.get("reason", "計測結果は下記") + "）",
             "- GSC：**" + b["status"] + "**（" + b.get("reason", "計測結果は下記") + "）",
             "- 対象：GA4 property " + GA4_PROPERTY + " ／ GSC " + SITE,
             "- Google検索クリック ≠ note流入 ≠ 楽天確定報酬。",
             "- 未取得・未観測は **0ではなく不明** として記録します。", ""]
    if "site_metrics" in b:
        lines += ["### GSC（確定データだけ）", "- 期間：" + " ～ ".join(b["window"]),
                  "- 全体：" + str(b["site_metrics"] or "不明"), ""]
        for p, m in b["pages"].items():
            lines.append("- " + (p or "トップ") + "：" + (str(m) if m else "不明"))
    if "event_counts" in a:
        lines += ["", "### GA4（noteギフトキャンペーン）",
                  "- 期間：" + " ～ ".join(a["window"]),
                  "- 実顧客数・購入確定：未検証", ""]
        for name, counts in a["event_counts"].items():
            lines.append("- " + name + "：" + str(counts))
        lines += ["- セッション・ユーザー（運営者テスト含む）：" +
                  str(a["visits"] if a["visits"] else "不明")]
    return "\n".join(lines) + "\n"


def run(today=None, session=None):
    today = today or dt.datetime.now(ZoneInfo("Asia/Tokyo")).date()
    if session is None:
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            return {"status": "NOT_CONFIGURED",
                    "ga4": unavailable("GA4", "MISSING_WORKLOAD_IDENTITY", "NOT_CONFIGURED"),
                    "gsc": unavailable("GSC", "MISSING_WORKLOAD_IDENTITY", "NOT_CONFIGURED"),
                    "tested_at": today.isoformat()}
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        credentials, _ = google.auth.default(scopes=list(SCOPES))
        session = AuthorizedSession(credentials)
    def read(fn, source):
        try:
            return fn(session, today)
        except Exception as exc:
            # Never publish sensitive API response details or credential contents.
            reason = str(exc) if str(exc).startswith(("GA4_", "GSC_")) else "READ_FAILED"
            return unavailable(source, reason)
    result = {"status": "READ_ONLY",
              "ga4": read(fetch_ga4, "GA4"),
              "gsc": read(fetch_gsc, "GSC"),
              "tested_at": today.isoformat(),
              "revenue": "NOT_QUERIED",
              "contains_personal_information": False}
    return result


def main():
    report = run()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "report.json").write_text(json.dumps(
        report, ensure_ascii=False, indent=2), encoding="utf-8")
    text = to_markdown(report)
    (AUDIT_DIR / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
