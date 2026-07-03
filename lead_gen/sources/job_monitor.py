"""
job_monitor.py — Job posting monitor for expansion signals.

Job postings for roles like "commissioning engineer", "project engineer greenfield"
are a strong early signal that a company is building a new facility.

This module builds ready-to-open search URLs for Naukri and Indeed — no API keys
needed. The user can open them manually, or these URLs can be driven by browser
automation (Selenium / Playwright) later.

To use:
    from lead_gen.sources.job_monitor import build_job_search_urls, check_expansion_keywords
    urls = build_job_search_urls(["Vapi", "Silvassa"])
    for region, links in urls.items():
        print(region, links)
"""

import urllib.parse
from lead_gen.config import EXPANSION_JOB_KEYWORDS, RING_1, RING_2

# Job roles that strongly signal a new plant / greenfield project
PRIMARY_ROLES = [
    "electrical engineer new plant",
    "project engineer greenfield",
    "commissioning engineer",
    "electrical project engineer",
    "plant electrical engineer",
    "EPC electrical engineer",
]

# Secondary roles — broader signal
SECONDARY_ROLES = [
    "site engineer electrical",
    "electrical supervisor",
    "maintenance engineer electrical",
]

# Naukri search URL pattern
NAUKRI_URL = (
    "https://www.naukri.com/{role_slug}-jobs-in-{location_slug}"
)
NAUKRI_KEYWORD_URL = (
    "https://www.naukri.com/jobs-in-{location_slug}?k={role_encoded}&l={location_encoded}"
)

# Indeed India search URL pattern
INDEED_URL = (
    "https://in.indeed.com/jobs?q={role_encoded}&l={location_encoded}"
)

# LinkedIn Jobs search URL pattern
LINKEDIN_URL = (
    "https://www.linkedin.com/jobs/search/?keywords={role_encoded}&location={location_encoded}&f_TP=1%2C2"
)


def build_job_search_urls(regions: list) -> dict:
    """
    Build job search URLs for expansion-signal roles across the given regions.

    Parameters
    ----------
    regions : list[str]
        Regions to monitor, e.g. ["Vapi", "Silvassa", "Daman"].

    Returns
    -------
    dict
        {region: {"naukri": [...], "indeed": [...], "linkedin": [...]}}
        Each inner list contains URLs for the primary job roles.
    """
    result = {}
    for region in regions:
        region_slug = region.lower().replace(" ", "-")
        region_encoded = urllib.parse.quote_plus(region)
        naukri_urls = []
        indeed_urls = []
        linkedin_urls = []

        for role in PRIMARY_ROLES:
            role_slug = role.lower().replace(" ", "-")
            role_encoded = urllib.parse.quote_plus(role)

            naukri_urls.append(
                NAUKRI_KEYWORD_URL.format(
                    location_slug=region_slug,
                    role_encoded=role_encoded,
                    location_encoded=region_encoded,
                )
            )
            indeed_urls.append(
                INDEED_URL.format(
                    role_encoded=role_encoded,
                    location_encoded=region_encoded,
                )
            )
            linkedin_urls.append(
                LINKEDIN_URL.format(
                    role_encoded=role_encoded,
                    location_encoded=region_encoded,
                )
            )

        result[region] = {
            "naukri": naukri_urls,
            "indeed": indeed_urls,
            "linkedin": linkedin_urls,
        }

    return result


def check_expansion_keywords(job_title: str, job_desc: str = "") -> bool:
    """
    Check whether a job title / description signals a new facility.

    Parameters
    ----------
    job_title : str
        The job title to inspect.
    job_desc : str, optional
        Job description text for deeper analysis.

    Returns
    -------
    bool
        True if the job indicates a greenfield or expansion project.
    """
    text = (job_title + " " + job_desc).lower()

    # Direct expansion keywords
    direct_signals = [
        "greenfield",
        "new plant",
        "new facility",
        "new factory",
        "commissioning",
        "pre-commissioning",
        "startup",
        "start-up",
        "EPC",
        "project engineer",
        "upcoming project",
    ]
    # Must also mention electrical / power context
    electrical_context = [
        "electrical",
        "power",
        "wiring",
        "HT",
        "LT",
        "substation",
        "cable",
        "panel",
        "switchgear",
    ]

    has_signal = any(kw.lower() in text for kw in direct_signals)
    has_electrical = any(kw.lower() in text for kw in electrical_context)

    return has_signal and has_electrical


def format_job_alert(region: str, urls: dict) -> str:
    """
    Format job search URLs for a region into a human-readable checklist.

    Parameters
    ----------
    region : str
        Region name.
    urls : dict
        URLs dict as returned by build_job_search_urls() for one region.

    Returns
    -------
    str
        Formatted text block.
    """
    lines = [f"JOB SIGNAL CHECK — {region}", "-" * 40]
    for role, url in zip(PRIMARY_ROLES, urls.get("naukri", [])):
        lines.append(f"Role: {role}")
        lines.append(f"  Naukri  : {url}")
    lines.append("")
    lines.append("Check these links for new postings — each one could mean a new plant.")
    return "\n".join(lines)


def print_all_job_links(regions: list = None) -> None:
    """
    Convenience function: print all job search URLs to stdout.

    Parameters
    ----------
    regions : list[str], optional
        Defaults to RING_1 + RING_2.
    """
    rgns = regions if regions is not None else (RING_1 + RING_2)
    all_urls = build_job_search_urls(rgns)
    print("=" * 60)
    print("WEEKLY JOB POSTING CHECK (Expansion Signals)")
    print("=" * 60)
    for region, portals in all_urls.items():
        print(f"\n--- {region} ---")
        for i, role in enumerate(PRIMARY_ROLES):
            print(f"\n  [{role}]")
            if i < len(portals["naukri"]):
                print(f"    Naukri  : {portals['naukri'][i]}")
            if i < len(portals["indeed"]):
                print(f"    Indeed  : {portals['indeed'][i]}")
            if i < len(portals["linkedin"]):
                print(f"    LinkedIn: {portals['linkedin'][i]}")
