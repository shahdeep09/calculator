# Lead Generation System — Vapi-Silvassa-Daman Belt

AI-assisted B2B lead generation for industrial electrical materials distribution
(RR Kabel cables · Legrand switchgear · Bajaj / Panasonic / Havells industrial lighting).

---

## Quick Start

```bash
# Install dependencies (Python 3.8+)
pip install -r lead_gen/requirements.txt

# Run the weekly scout (from repo root)
python -m lead_gen.weekly_scout

# With Yahoo email scanning for dormant leads
python -m lead_gen.weekly_scout --scan-email --email you@yahoo.co.in --app-password YOUR_APP_PASSWORD

# Dry-run (preview without writing to CSV)
python -m lead_gen.weekly_scout --dry-run
```

---

## File Reference

| File | What it does |
|------|-------------|
| `config.py` | All tunable settings: geography rings, products, scoring weights, keywords |
| `scorer.py` | `LeadScorer` class — scores any lead dict 0-100 across geography, signal, product fit, timing |
| `lead_tracker.py` | `LeadTracker` class — adds/updates leads in `leads.csv`, generates weekly digest |
| `outreach_templates.py` | Ready-to-paste email, WhatsApp, and cold-call scripts for every lead type |
| `weekly_scout.py` | **Main orchestration script** — tie everything together, run every Monday |
| `sources/news_monitor.py` | Scans Google News RSS for new plant / expansion signals (no API key needed) |
| `sources/tender_scraper.py` | Generates GeM / CPPP / TenderTiger search URLs for electrical tender keywords |
| `sources/job_monitor.py` | Builds Naukri / Indeed / LinkedIn search URLs for expansion-signal job roles |
| `sources/email_parser.py` | Connects to Yahoo IMAP and extracts dormant leads from old enquiry emails |
| `requirements.txt` | Python dependencies (`requests`, `beautifulsoup4`, `lxml`) |

---

## How the Scoring Works

Each lead is scored 0-100 on four dimensions:

```
Geography   (max 30)  — Ring 1 cities score highest
Signal type (max 40)  — Active tender > new plant > energy upgrade > job posting > directory
Product fit (max 20)  — More matching product lines = higher score
Timing      (max 10)  — Immediate need scores highest
```

Leads scoring **80+** are hot and should be called the same day.
Leads scoring **50-79** should be contacted within the week.
Leads scoring **below 50** are nurture / long-term.

---

## Lead CSV Structure (`leads.csv`)

| Column | Description |
|--------|-------------|
| `id` | Auto-generated ID (e.g. LD-A3F2B1C0) |
| `date_found` | Date the lead was identified |
| `company` | Company name |
| `location` | City / area |
| `signal_type` | What triggered the lead (new_plant, active_tender, etc.) |
| `score` | 0-100 score |
| `status` | `new` → `contacted` → `meeting` → `quoted` → `won` / `lost` |
| `products_needed` | Pipe-separated product categories e.g. `cables|switchgear` |
| `contact_info` | Name, phone, email of contact person |
| `notes` | Free-text notes, URLs, call logs |
| `last_updated` | Date of last status change |

---

## Manual Weekly Checklist

Even without running the script, follow this 15-minute Monday routine:

1. Open the GeM tender links from `sources/tender_scraper.py` and check for new bids
2. Run a Google News search for `"Vapi" OR "Silvassa" OR "Daman" new plant`
3. Check Naukri for "commissioning engineer" or "project engineer" postings in these cities
4. Review Yahoo inbox for new enquiry emails
5. Call any overdue follow-ups from `leads.csv` where status = `contacted` and age > 5 days

---

## Outreach Templates

```python
from lead_gen.outreach_templates import (
    new_plant_email,
    tender_email,
    revival_email,
    whatsapp_intro,
    cold_call_script,
)

# New plant lead
print(new_plant_email("ABC Polymers Pvt. Ltd.", "Vapi GIDC", "Mr. Patel"))

# Tender response
print(tender_email("Supply of Armoured Cables — GEM/2024/B/XXX", "ONGC Hazira"))

# Revival of dormant enquiry
print(revival_email("XYZ Industries", "armoured cables", months_ago=8))

# WhatsApp opener
print(whatsapp_intro("ABC Polymers", "Vapi", "new plant construction"))

# Cold call script
print(cold_call_script("ABC Polymers", "new plant at Vapi GIDC"))
```

---

## Yahoo IMAP Setup

1. Log in to Yahoo Mail → Settings → Security → **Allow apps that use less secure sign in** (or generate an App Password if you use 2FA)
2. Note your App Password
3. Run: `python -m lead_gen.weekly_scout --scan-email --email you@yahoo.co.in --app-password <APP_PWD>`

---

## Extending the System

- **Add a new region**: Add to `RING_1` or `RING_2` in `config.py` — all scripts pick it up automatically.
- **Add a product line**: Add to the `PRODUCTS` dict in `config.py`.
- **Add a tender keyword**: Append to `TENDER_KEYWORDS` in `config.py`.
- **Change scoring**: Adjust `SCORING` weights in `config.py` — no other file needs changing.
- **Automate weekly run**: Add a cron job: `0 9 * * 1 cd /path/to/repo && python -m lead_gen.weekly_scout >> lead_gen/scout_log.txt 2>&1`
