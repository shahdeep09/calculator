"""
weekly_scout.py — Main orchestration script. Run every Monday morning.

What this script does:
  1. Searches Google News RSS for new plant / expansion signals in all regions
  2. Prints tender search URLs to review manually (GeM / CPPP)
  3. Prints job posting search URLs (Naukri / Indeed) for expansion signals
  4. Scores each news-derived lead using LeadScorer
  5. Appends new leads to leads.csv via LeadTracker
  6. Prints a full weekly digest including follow-up reminders

Usage:
    # From the repo root:
    python -m lead_gen.weekly_scout

    # Or with email scanning (requires Yahoo IMAP credentials):
    python -m lead_gen.weekly_scout --scan-email --email you@yahoo.co.in --app-password YOUR_APP_PASSWORD

    # Dry run (don't write to CSV):
    python -m lead_gen.weekly_scout --dry-run
"""

import argparse
import sys
from datetime import datetime

from lead_gen.config import RING_1, RING_2, ALL_REGIONS, TENDER_KEYWORDS
from lead_gen.scorer import LeadScorer
from lead_gen.lead_tracker import LeadTracker
from lead_gen.sources.news_monitor import search_expansion_news, get_relevant_articles
from lead_gen.sources.tender_scraper import search_gem_tenders, get_tender_keywords, format_tender_alert
from lead_gen.sources.job_monitor import build_job_search_urls, PRIMARY_ROLES


def _section(title: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def run_weekly_scout(
    scan_email: bool = False,
    email_address: str = "",
    app_password: str = "",
    dry_run: bool = False,
) -> None:
    """
    Main entry point for the weekly lead scouting run.

    Parameters
    ----------
    scan_email : bool
        Whether to also scan Yahoo IMAP for dormant leads.
    email_address : str
        Yahoo email address (only used if scan_email=True).
    app_password : str
        Yahoo App Password (only used if scan_email=True).
    dry_run : bool
        If True, do not write anything to leads.csv.
    """
    scorer = LeadScorer()
    tracker = LeadTracker()

    print("=" * 60)
    print(f"  WEEKLY LEAD SCOUT — {datetime.now().strftime('%A, %d %B %Y')}")
    print(f"  Territory: Vapi · Silvassa · Daman belt")
    print(f"  Dry-run mode: {'YES (no CSV writes)' if dry_run else 'NO (will write to leads.csv)'}")
    print("=" * 60)

    # ------------------------------------------------------------------ #
    # 1. NEWS MONITOR — expansion / new plant signals
    # ------------------------------------------------------------------ #
    _section("1. EXPANSION NEWS (Google News RSS)")
    print("Scanning Google News for new plant / expansion signals...\n")

    news_leads = []
    try:
        articles = get_relevant_articles(ALL_REGIONS)
        if articles:
            print(f"Found {len(articles)} relevant articles:\n")
            for art in articles:
                print(f"  [{art.get('region', '?')}] {art['title']}")
                print(f"    {art['link']}")
                print(f"    Published: {art.get('published', 'unknown')}")
                print()

                # Build a lead dict from the article
                lead = {
                    "company": art["title"][:60],   # use headline as placeholder
                    "location": art.get("region", ""),
                    "signal_type": "new_plant",
                    "products": ["cables", "switchgear", "lighting"],   # assume full fit for new plant
                    "timing": "6_12months",
                    "source": "google_news",
                    "notes": art["link"],
                    "contact_info": "",
                }
                lead["score"] = scorer.score(lead)
                news_leads.append(lead)
        else:
            print("  No relevant expansion news found this week.")
    except Exception as exc:
        print(f"  WARNING: News monitor error — {exc}")

    # ------------------------------------------------------------------ #
    # 2. TENDER URLS
    # ------------------------------------------------------------------ #
    _section("2. TENDER SEARCH LINKS (review manually)")
    print("Copy-paste these URLs into your browser to check for new tenders:\n")

    try:
        tenders = search_gem_tenders(get_tender_keywords())
        for t in tenders:
            print(f"  [{t['keyword']}]")
            print(f"    GeM  : {t['gem_url']}")
            print(f"    CPPP : {t['cppp_url']}")
            print(f"    Tiger: {t['tiger_url']}")
            print()
    except Exception as exc:
        print(f"  WARNING: Tender URL generation error — {exc}")

    # ------------------------------------------------------------------ #
    # 3. JOB POSTING URLS — Ring 1 only (highest priority)
    # ------------------------------------------------------------------ #
    _section("3. JOB POSTING SIGNALS (Ring 1 regions)")
    print("Check these job portals for expansion-signal postings:\n")

    try:
        job_urls = build_job_search_urls(RING_1)
        for region, portals in job_urls.items():
            print(f"  --- {region} ---")
            for i, role in enumerate(PRIMARY_ROLES[:3]):   # show top 3 roles
                if i < len(portals["naukri"]):
                    print(f"    [{role}]")
                    print(f"      Naukri  : {portals['naukri'][i]}")
                    print(f"      Indeed  : {portals['indeed'][i]}")
            print()
    except Exception as exc:
        print(f"  WARNING: Job URL generation error — {exc}")

    # ------------------------------------------------------------------ #
    # 4. EMAIL SCAN (optional)
    # ------------------------------------------------------------------ #
    email_leads = []
    if scan_email and email_address and app_password:
        _section("4. EMAIL SCAN — Dormant Lead Revival")
        print("Connecting to Yahoo IMAP...\n")
        try:
            from lead_gen.sources.email_parser import (
                connect_yahoo_imap,
                fetch_old_enquiries,
                build_revival_list,
            )
            conn = connect_yahoo_imap(email_address, app_password)
            emails = fetch_old_enquiries(conn, since_date="01-Jan-2023")
            conn.logout()
            revival = build_revival_list(emails)

            if revival:
                print(f"  Found {len(revival)} dormant leads to revive:\n")
                for rev in revival:
                    info = rev.get("lead_info", {})
                    lead = {
                        "company": info.get("company") or rev["from_domain"],
                        "location": "",
                        "signal_type": "directory",
                        "products": info.get("products", []),
                        "timing": "3_6months",
                        "contact_info": rev["from_addr"],
                        "notes": f"Old enquiry — {rev['subject'][:80]}",
                        "source": "email_revival",
                    }
                    lead["score"] = scorer.score(lead)
                    email_leads.append(lead)
                    print(f"    {lead['company']:<35} score={lead['score']:>3}  [{rev['from_addr']}]")
            else:
                print("  No old enquiries found matching keywords.")
        except Exception as exc:
            print(f"  WARNING: Email scan error — {exc}")
    else:
        _section("4. EMAIL SCAN")
        print("  Skipped. Pass --scan-email --email <addr> --app-password <pwd> to enable.")

    # ------------------------------------------------------------------ #
    # 5. SCORE & SAVE NEW LEADS
    # ------------------------------------------------------------------ #
    all_new_leads = news_leads + email_leads

    _section("5. NEW LEADS THIS WEEK")
    if all_new_leads:
        # Sort highest score first
        all_new_leads.sort(key=lambda x: x.get("score", 0), reverse=True)
        print(f"{'Company':<35} {'Location':<15} {'Signal':<20} {'Score':>5}")
        print("-" * 78)
        for lead in all_new_leads:
            print(
                f"  {lead.get('company', '?')[:33]:<35} "
                f"{lead.get('location', '?'):<15} "
                f"{lead.get('signal_type', '?'):<20} "
                f"{lead.get('score', 0):>5}"
            )

        if not dry_run:
            print(f"\nSaving {len(all_new_leads)} leads to leads.csv...")
            for lead in all_new_leads:
                lead_to_save = {
                    "company": lead.get("company", ""),
                    "location": lead.get("location", ""),
                    "signal_type": lead.get("signal_type", ""),
                    "score": lead.get("score", 0),
                    "products_needed": lead.get("products", []),
                    "contact_info": lead.get("contact_info", ""),
                    "notes": lead.get("notes", ""),
                    "status": "new",
                }
                tracker.add_lead(lead_to_save)
    else:
        print("  No new leads identified this week.")

    # ------------------------------------------------------------------ #
    # 6. FOLLOW-UP REMINDERS
    # ------------------------------------------------------------------ #
    _section("6. FOLLOW-UP REMINDERS")
    try:
        due = tracker.get_followup_due()
        if due:
            now = datetime.now()
            print(f"  {len(due)} lead(s) need follow-up:\n")
            for r in due:
                from datetime import datetime as dt_
                try:
                    last = dt_.strptime(r.get("last_updated", "2000-01-01"), "%Y-%m-%d")
                    days_ago = (now - last).days
                except ValueError:
                    days_ago = "?"
                print(
                    f"  {r.get('company', '?'):<30} contacted {days_ago} day(s) ago"
                    f"   [{r.get('contact_info', 'no contact')}]"
                )
        else:
            print("  No follow-ups overdue.")
    except Exception as exc:
        print(f"  WARNING: Follow-up check error — {exc}")

    # ------------------------------------------------------------------ #
    # 7. WEEKLY DIGEST SUMMARY
    # ------------------------------------------------------------------ #
    _section("7. PIPELINE DIGEST")
    try:
        print(tracker.export_weekly_digest())
    except Exception as exc:
        print(f"  WARNING: Could not generate digest — {exc}")

    print("\nDone! Have a productive week. 💪")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Weekly B2B lead scouting script for the Vapi-Silvassa-Daman belt."
    )
    parser.add_argument(
        "--scan-email",
        action="store_true",
        help="Also scan Yahoo IMAP for dormant lead revival.",
    )
    parser.add_argument(
        "--email",
        default="",
        help="Yahoo email address (required with --scan-email).",
    )
    parser.add_argument(
        "--app-password",
        default="",
        help="Yahoo App Password (required with --scan-email).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print results but do not write to leads.csv.",
    )

    args = parser.parse_args()

    if args.scan_email and not (args.email and args.app_password):
        print("ERROR: --scan-email requires both --email and --app-password.")
        sys.exit(1)

    run_weekly_scout(
        scan_email=args.scan_email,
        email_address=args.email,
        app_password=args.app_password,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
