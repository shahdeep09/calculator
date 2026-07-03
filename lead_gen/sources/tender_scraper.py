"""
tender_scraper.py — GeM (Government e-Marketplace) tender monitoring.

GeM requires login to access search results programmatically, so this module:
  1. Constructs ready-to-open GeM search URLs for each keyword.
  2. Provides a formatter to turn a tender dict into a WhatsApp / email alert.

To use:
    from lead_gen.sources.tender_scraper import search_gem_tenders, format_tender_alert
    tenders = search_gem_tenders(get_tender_keywords())
    for t in tenders:
        print(format_tender_alert(t))
"""

import urllib.parse
from datetime import datetime
from lead_gen.config import TENDER_KEYWORDS

# GeM portal search URL pattern
GEM_SEARCH_BASE = "https://bidplus.gem.gov.in/all-bids"
GEM_KEYWORD_URL = "https://bidplus.gem.gov.in/search/bids?searchedBid={query}"

# CPPP (Central Public Procurement Portal) — public, no login needed for search
CPPP_SEARCH_URL = "https://etenders.gov.in/eprocure/app?page=FrontEndTendersByCategory&service=page&query={query}"

# Tender Tiger (aggregator, free browsing)
TENDER_TIGER_URL = "https://www.tendertiger.com/tenders/electrical-{slug}-tenders.html"


def get_tender_keywords() -> list:
    """Return the configured list of tender search keywords."""
    return list(TENDER_KEYWORDS)


def search_gem_tenders(keywords: list) -> list:
    """
    Build GeM and CPPP search URLs for the given keywords.

    GeM requires login for API access, so this function returns a list of
    tender search result dicts — each containing the keyword and ready-to-open
    URLs for manual review or browser automation.

    Parameters
    ----------
    keywords : list[str]
        Keywords to search for, e.g. ["armoured cable", "MCB"].

    Returns
    -------
    list[dict]
        Each dict has: keyword, gem_url, cppp_url, tiger_url, generated_at
    """
    results = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for kw in keywords:
        encoded = urllib.parse.quote_plus(kw)
        slug = kw.lower().replace(" ", "-")
        results.append(
            {
                "keyword": kw,
                "gem_url": GEM_KEYWORD_URL.format(query=encoded),
                "cppp_url": CPPP_SEARCH_URL.format(query=encoded),
                "tiger_url": TENDER_TIGER_URL.format(slug=slug),
                "generated_at": now,
                "source": "url_list",
                "status": "pending_review",
            }
        )
    return results


def format_tender_alert(tender: dict) -> str:
    """
    Format a tender dict into a human-readable WhatsApp / email alert.

    Parameters
    ----------
    tender : dict
        A dict as returned by search_gem_tenders(), or a richer dict
        with keys: title, organization, deadline, value, location, gem_url.

    Returns
    -------
    str
        Formatted alert string ready to copy-paste into WhatsApp or email.
    """
    lines = ["*TENDER ALERT*", ""]

    if tender.get("title"):
        lines.append(f"Tender : {tender['title']}")
    if tender.get("keyword"):
        lines.append(f"Keyword: {tender['keyword']}")
    if tender.get("organization"):
        lines.append(f"Org    : {tender['organization']}")
    if tender.get("location"):
        lines.append(f"Location: {tender['location']}")
    if tender.get("deadline"):
        lines.append(f"Deadline: {tender['deadline']}")
    if tender.get("value"):
        lines.append(f"Est. Value: {tender['value']}")

    lines.append("")
    lines.append("Links to check:")
    if tender.get("gem_url"):
        lines.append(f"  GeM  : {tender['gem_url']}")
    if tender.get("cppp_url"):
        lines.append(f"  CPPP : {tender['cppp_url']}")
    if tender.get("tiger_url"):
        lines.append(f"  Tiger: {tender['tiger_url']}")

    lines.append("")
    lines.append(f"Generated: {tender.get('generated_at', datetime.now().strftime('%Y-%m-%d'))}")
    return "\n".join(lines)


def print_all_tender_links(keywords: list = None) -> None:
    """
    Convenience function: print all tender search URLs to stdout.
    Useful for a quick Monday morning check.
    """
    kws = keywords or get_tender_keywords()
    tenders = search_gem_tenders(kws)
    print("=" * 60)
    print("WEEKLY TENDER URL CHECKLIST")
    print("=" * 60)
    for t in tenders:
        print(f"\nKeyword: {t['keyword']}")
        print(f"  GeM  : {t['gem_url']}")
        print(f"  CPPP : {t['cppp_url']}")
        print(f"  Tiger: {t['tiger_url']}")
    print("\nOpen these links and note any new tenders.")
