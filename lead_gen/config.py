# config.py — Central configuration for the lead generation system

# Geography rings (Ring 1 = priority markets, Ring 2 = secondary)
RING_1 = ["Vapi", "Sarigam", "Silvassa", "Daman", "Umbergaon"]
RING_2 = ["Valsad", "Bhilad", "Boisar", "Tarapur", "Dadra"]

# All monitored regions combined
ALL_REGIONS = RING_1 + RING_2

# Products we distribute
PRODUCTS = {
    "cables": [
        "RR Kabel",
        "armoured cable",
        "LT cable",
        "control cable",
        "XLPE cable",
        "multicore cable",
    ],
    "switchgear": [
        "Legrand",
        "MCB",
        "RCCB",
        "distribution board",
        "LT panel",
        "wiring accessories",
    ],
    "lighting": [
        "Bajaj industrial",
        "Panasonic industrial",
        "Havells industrial",
        "LED highbay",
        "floodlight",
        "well glass",
        "industrial luminaire",
    ],
}

# Keywords used to search tender portals
TENDER_KEYWORDS = [
    "electrical cables",
    "armoured cable",
    "LED highbay",
    "industrial lighting",
    "MCB",
    "distribution board",
    "switchgear",
    "LT panel",
    "wiring accessories",
]

# Signal keywords that indicate a new plant / greenfield / expansion
EXPANSION_KEYWORDS = [
    "new plant",
    "greenfield",
    "expansion",
    "capacity expansion",
    "new facility",
    "new factory",
    "new unit",
    "commissioning",
    "upcoming project",
    "invest",
    "investment",
    "MoU",
    "memorandum of understanding",
    "land acquisition",
    "groundbreaking",
]

# Job title keywords that signal expansion
EXPANSION_JOB_KEYWORDS = [
    "electrical engineer",
    "project engineer",
    "commissioning engineer",
    "site engineer",
    "electrical head",
    "plant engineer",
    "EPC",
    "greenfield",
    "new plant",
]

# Email subject / body keywords for dormant lead revival
ENQUIRY_EMAIL_KEYWORDS = [
    "enquiry",
    "inquiry",
    "requirement",
    "quotation",
    "quote",
    "purchase order",
    "PO",
    "rate",
    "price list",
    "material",
    "cable",
    "switchgear",
    "lighting",
    "electrical",
]

# Lead scoring weights (max theoretical score ~135; normalised to 0-100 in scorer)
SCORING = {
    # Geography
    "ring_1": 30,
    "ring_2": 20,
    "ring_other": 5,
    # Signal type
    "signal_active_tender": 40,
    "signal_new_plant": 35,
    "signal_energy_upgrade": 30,
    "signal_job_posting": 20,
    "signal_directory": 10,
    # Product fit
    "product_fit_heavy": 20,   # matches 3+ product lines
    "product_fit_medium": 15,  # matches 2 product lines
    "product_fit_light": 5,    # matches 1 product line
    # Timing / urgency
    "timing_immediate": 10,
    "timing_3_6months": 7,
    "timing_6_12months": 5,
    "timing_longterm": 2,
}

# Maximum raw score (sum of best values in each category) — used for normalisation
MAX_RAW_SCORE = (
    SCORING["ring_1"]
    + SCORING["signal_active_tender"]
    + SCORING["product_fit_heavy"]
    + SCORING["timing_immediate"]
)  # = 100

# CSV output path (relative to project root when running scripts)
LEADS_CSV_PATH = "lead_gen/leads.csv"

# Follow-up reminder threshold in days
FOLLOWUP_DAYS = 5

# Yahoo IMAP settings
IMAP_HOST = "imap.mail.yahoo.com"
IMAP_PORT = 993

# Google News RSS base URL (no API key required)
GOOGLE_NEWS_RSS_BASE = (
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)
