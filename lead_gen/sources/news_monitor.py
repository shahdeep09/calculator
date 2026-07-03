"""
news_monitor.py — Monitor Google News RSS for new plant / expansion signals.

Uses Google News RSS (no API key required):
  https://news.google.com/rss/search?q=<query>&hl=en-IN&gl=IN&ceid=IN:en

To use:
    from lead_gen.sources.news_monitor import search_expansion_news
    articles = search_expansion_news(["Vapi", "Silvassa"])
    for a in articles:
        print(a['title'], a['link'])
"""

import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import requests

from lead_gen.config import EXPANSION_KEYWORDS, GOOGLE_NEWS_RSS_BASE, ALL_REGIONS

# Industries present in the Vapi-Silvassa-Daman belt — used to sharpen queries
BELT_INDUSTRIES = [
    "chemical plant",
    "pharmaceutical",
    "textile",
    "plastic",
    "packaging",
    "manufacturing",
    "factory",
    "industrial estate",
    "GIDC",
    "SEZ",
]

REQUEST_TIMEOUT = 15  # seconds


def _build_query(region: str) -> str:
    """Build a Google News search query for expansion signals in a region."""
    return f'"{region}" (new plant OR expansion OR greenfield OR investment OR factory) industrial'


def search_expansion_news(regions: list) -> list:
    """
    Search Google News RSS for industrial expansion / new plant news
    across the specified regions.

    Parameters
    ----------
    regions : list[str]
        Regions to monitor, e.g. ["Vapi", "Silvassa", "Daman"].

    Returns
    -------
    list[dict]
        Deduplicated articles with keys: title, link, published, snippet, region,
        is_relevant. Sorted newest-first.
    """
    seen_links: set = set()
    articles: list = []

    for region in regions:
        query = _build_query(region)
        rss_url = GOOGLE_NEWS_RSS_BASE.format(query=urllib.parse.quote_plus(query))
        fetched = parse_news_feed(rss_url)
        for article in fetched:
            if article["link"] not in seen_links:
                seen_links.add(article["link"])
                article["region"] = region
                article["is_relevant"] = is_relevant_signal(article)
                articles.append(article)

    # Sort newest first (published may be RFC-822 string or empty)
    articles.sort(key=lambda a: a.get("published", ""), reverse=True)
    return articles


def parse_news_feed(rss_url: str) -> list:
    """
    Fetch and parse a Google News RSS feed URL.

    Parameters
    ----------
    rss_url : str
        Full RSS URL to fetch.

    Returns
    -------
    list[dict]
        List of articles: {title, link, published, snippet}
        Returns empty list on any error (network, parse, etc.).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LeadGenBot/1.0; +https://github.com)"
        )
    }
    try:
        response = requests.get(rss_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return _parse_rss_xml(response.text)
    except requests.RequestException as exc:
        print(f"[news_monitor] WARNING: Could not fetch feed {rss_url}: {exc}")
        return []
    except ET.ParseError as exc:
        print(f"[news_monitor] WARNING: Could not parse RSS XML: {exc}")
        return []


def _parse_rss_xml(xml_text: str) -> list:
    """Parse RSS XML string and return list of article dicts."""
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item"):
        title = _tag_text(item, "title") or ""
        link = _tag_text(item, "link") or ""
        published = _tag_text(item, "pubDate") or ""
        description = _tag_text(item, "description") or ""

        # Strip HTML tags from description (Google News wraps snippet in <a>)
        snippet = _strip_html(description)

        articles.append(
            {
                "title": title.strip(),
                "link": link.strip(),
                "published": published.strip(),
                "snippet": snippet.strip(),
            }
        )
    return articles


def is_relevant_signal(article: dict) -> bool:
    """
    Determine whether a news article is a relevant expansion / new plant signal.

    Checks title + snippet against known expansion keywords and industry terms.

    Parameters
    ----------
    article : dict
        Article dict with at least 'title' and 'snippet' keys.

    Returns
    -------
    bool
        True if the article likely signals a new facility or major expansion.
    """
    text = " ".join(
        [
            article.get("title", ""),
            article.get("snippet", ""),
        ]
    ).lower()

    expansion_hit = any(kw.lower() in text for kw in EXPANSION_KEYWORDS)
    industry_hit = any(kw.lower() in text for kw in BELT_INDUSTRIES)

    return expansion_hit and industry_hit


def get_relevant_articles(regions: list = None) -> list:
    """
    Convenience wrapper: return only the relevant articles.

    Parameters
    ----------
    regions : list[str], optional
        Defaults to ALL_REGIONS from config.

    Returns
    -------
    list[dict]
        Only articles where is_relevant is True.
    """
    rgns = regions if regions is not None else ALL_REGIONS
    all_articles = search_expansion_news(rgns)
    return [a for a in all_articles if a.get("is_relevant")]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tag_text(element, tag: str) -> Optional[str]:
    """Return text of first child with given tag, or None."""
    child = element.find(tag)
    return child.text if child is not None else None


def _strip_html(html: str) -> str:
    """Very lightweight HTML tag stripper (no external deps)."""
    import re
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()
