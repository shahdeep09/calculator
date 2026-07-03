"""
email_parser.py — Yahoo email IMAP client for dormant-lead revival.

Connects to your Yahoo business email via IMAP, fetches old enquiry emails,
extracts lead information, and builds a revival list.

Prerequisites:
  - Enable IMAP access in Yahoo Mail settings (Settings > Security > Allow apps)
  - Generate an App Password (if 2FA is enabled) from your Yahoo account security page

To use:
    from lead_gen.sources.email_parser import connect_yahoo_imap, fetch_old_enquiries, build_revival_list

    conn = connect_yahoo_imap("you@yahoo.com", "your_app_password")
    emails = fetch_old_enquiries(conn, since_date="01-Jan-2023")
    revival = build_revival_list(emails)
    conn.logout()
"""

import email
import imaplib
import re
from datetime import datetime, timedelta
from email.header import decode_header

from lead_gen.config import ENQUIRY_EMAIL_KEYWORDS, IMAP_HOST, IMAP_PORT, PRODUCTS


def connect_yahoo_imap(email_address: str, app_password: str) -> imaplib.IMAP4_SSL:
    """
    Connect to Yahoo Mail via IMAP SSL.

    Parameters
    ----------
    email_address : str
        Your Yahoo email address, e.g. "yourbusiness@yahoo.co.in".
    app_password : str
        Yahoo App Password (generate from Yahoo Account Security page).

    Returns
    -------
    imaplib.IMAP4_SSL
        Authenticated IMAP connection. Call .logout() when done.

    Raises
    ------
    imaplib.IMAP4.error
        If authentication fails.
    """
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(email_address, app_password)
    return conn


def fetch_old_enquiries(
    imap_conn: imaplib.IMAP4_SSL,
    since_date: str = None,
    subject_keywords: list = None,
    mailbox: str = "INBOX",
) -> list:
    """
    Fetch emails containing enquiry / requirement keywords from a date onwards.

    Parameters
    ----------
    imap_conn : imaplib.IMAP4_SSL
        Authenticated IMAP connection from connect_yahoo_imap().
    since_date : str, optional
        IMAP date string e.g. "01-Jan-2023". Defaults to 1 year ago.
    subject_keywords : list[str], optional
        Keywords to filter by. Defaults to ENQUIRY_EMAIL_KEYWORDS from config.
    mailbox : str, optional
        IMAP mailbox/folder name. Default "INBOX".

    Returns
    -------
    list[dict]
        List of email dicts: {message_id, from_addr, from_domain, subject,
                              date, body_text, raw_keywords_found}
    """
    if since_date is None:
        one_year_ago = datetime.now() - timedelta(days=365)
        since_date = one_year_ago.strftime("%d-%b-%Y")

    keywords = subject_keywords or ENQUIRY_EMAIL_KEYWORDS

    imap_conn.select(mailbox)

    # Build IMAP search: emails since date
    status, msg_ids_raw = imap_conn.search(None, f'SINCE "{since_date}"')
    if status != "OK" or not msg_ids_raw[0]:
        return []

    msg_ids = msg_ids_raw[0].split()
    results = []

    for msg_id in msg_ids:
        try:
            status, data = imap_conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not data or not data[0]:
                continue

            raw_bytes = data[0][1] if isinstance(data[0], tuple) else None
            if raw_bytes is None:
                continue

            msg = email.message_from_bytes(raw_bytes)
            subject = _decode_header_field(msg.get("Subject", ""))
            from_addr = _decode_header_field(msg.get("From", ""))
            date_str = msg.get("Date", "")
            body = _extract_body(msg)

            combined_text = (subject + " " + body).lower()
            matched_kws = [kw for kw in keywords if kw.lower() in combined_text]

            if matched_kws:
                domain = _extract_domain(from_addr)
                results.append(
                    {
                        "message_id": msg_id.decode(),
                        "from_addr": from_addr,
                        "from_domain": domain,
                        "subject": subject,
                        "date": date_str,
                        "body_text": body[:2000],  # truncate large bodies
                        "raw_keywords_found": matched_kws,
                    }
                )
        except Exception as exc:
            print(f"[email_parser] WARNING: Skipping message {msg_id}: {exc}")
            continue

    return results


def extract_lead_info(email_text: str) -> dict:
    """
    Extract structured lead info from raw email body text using regex.

    Attempts to find:
    - Company name (looks for patterns like "from XYZ Ltd", "Company: XYZ")
    - Products mentioned (matches against our PRODUCTS config)
    - Quantity if present (e.g. "500 metres", "100 nos")
    - Phone number
    - Email address

    Parameters
    ----------
    email_text : str
        Raw email body text.

    Returns
    -------
    dict
        {company, products, quantity, phone, email}
    """
    text = email_text

    company = _extract_company(text)
    products_found = _extract_products(text)
    quantity = _extract_quantity(text)
    phone = _extract_phone(text)
    email_addr = _extract_email(text)

    return {
        "company": company,
        "products": products_found,
        "quantity": quantity,
        "phone": phone,
        "email": email_addr,
    }


def build_revival_list(emails: list) -> list:
    """
    Deduplicate emails by sender domain and build a prioritised revival list.

    Parameters
    ----------
    emails : list[dict]
        Email dicts as returned by fetch_old_enquiries().

    Returns
    -------
    list[dict]
        Deduplicated leads sorted by date (newest first), with extracted info.
        Each dict: {from_domain, from_addr, subject, date, lead_info, keywords}
    """
    # Keep most recent email per domain
    domain_map: dict = {}
    for em in emails:
        domain = em.get("from_domain", em.get("from_addr", "unknown"))
        existing = domain_map.get(domain)
        if existing is None:
            domain_map[domain] = em
        else:
            # Keep newer email (compare date strings — fallback to keeping first)
            if em.get("date", "") > existing.get("date", ""):
                domain_map[domain] = em

    revival = []
    for domain, em in domain_map.items():
        lead_info = extract_lead_info(em.get("body_text", "") + " " + em.get("subject", ""))
        revival.append(
            {
                "from_domain": domain,
                "from_addr": em["from_addr"],
                "subject": em["subject"],
                "date": em["date"],
                "lead_info": lead_info,
                "keywords": em.get("raw_keywords_found", []),
            }
        )

    # Sort newest first (string comparison works for RFC 2822 dates approximately)
    revival.sort(key=lambda x: x.get("date", ""), reverse=True)
    return revival


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _decode_header_field(value: str) -> str:
    """Decode RFC 2047 encoded email headers."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return " ".join(parts)


def _extract_body(msg: email.message.Message) -> str:
    """Extract plain text body from an email message."""
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                try:
                    body_parts.append(part.get_payload(decode=True).decode(charset, errors="replace"))
                except Exception:
                    body_parts.append("")
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            body_parts.append(msg.get_payload(decode=True).decode(charset, errors="replace"))
        except Exception:
            body_parts.append("")
    return "\n".join(body_parts)


def _extract_domain(from_addr: str) -> str:
    """Extract domain from an email address string."""
    match = re.search(r"[\w.+-]+@([\w.-]+\.\w+)", from_addr)
    return match.group(1).lower() if match else from_addr.lower()


def _extract_email(text: str) -> str:
    """Extract first email address found in text."""
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    """Extract first Indian phone number found in text."""
    # Matches +91-XXXXX-XXXXX, 9XXXXXXXXX, 0XXXXXXXXXX etc.
    match = re.search(r"(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}", text)
    return match.group(0).strip() if match else ""


def _extract_company(text: str) -> str:
    """Attempt to extract company name from email body."""
    patterns = [
        r"(?:from|company|organisation|organization|firm)\s*[:\-]?\s*([A-Z][A-Za-z\s&.,()\-]{2,40}(?:Ltd|Pvt|Inc|Corp|Industries|Enterprises|Manufacturing|Works|Co\.?)?)",
        r"([A-Z][A-Za-z\s&.]{2,30}(?:Ltd|Pvt\.?\s*Ltd|Industries|Enterprises|Manufacturing|Works)\.?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_products(text: str) -> list:
    """Return list of product categories mentioned in text."""
    text_lower = text.lower()
    found = []
    for category, keywords in PRODUCTS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            found.append(category)
    return found


def _extract_quantity(text: str) -> str:
    """Extract quantity string from text (e.g. '500 metres', '100 nos')."""
    pattern = r"\b(\d[\d,]*)\s*(metres?|mtrs?|nos?\.?|units?|pcs?|pieces?|rolls?|coils?|sets?|kgs?)\b"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return ""
