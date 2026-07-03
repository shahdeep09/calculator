"""
outreach_templates.py — Ready-to-use outreach messages for every lead scenario.

All templates are plain-text so they work in email clients, WhatsApp Web,
and basic SMS. Call each function and copy-paste the output.

To use:
    from lead_gen.outreach_templates import new_plant_email, whatsapp_intro
    print(new_plant_email("ABC Polymers", "Vapi", "Mr. Patel"))
    print(whatsapp_intro("ABC Polymers", "Vapi", "new plant construction"))
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

def new_plant_email(company: str, location: str, contact_name: str = "") -> str:
    """
    Introduction email for a company building a new plant / expanding.

    Parameters
    ----------
    company : str
        Company name, e.g. "ABC Polymers Pvt. Ltd."
    location : str
        Location of the new plant, e.g. "Vapi GIDC".
    contact_name : str, optional
        Recipient's name. If empty, uses a generic salutation.

    Returns
    -------
    str
        Formatted email (Subject + Body).
    """
    salutation = f"Dear {contact_name}," if contact_name else "Dear Sir/Madam,"
    date_str = datetime.now().strftime("%B %Y")

    subject = f"Electrical Materials Supply for Your New {location} Facility — RR Kabel, Legrand & More"

    body = f"""\
Subject: {subject}

{salutation}

Congratulations on the upcoming expansion at {location}! We came across news of {company}'s \
new facility and wanted to introduce ourselves.

We are a specialised industrial electrical materials distributor serving the Vapi-Silvassa-Daman \
belt for over a decade. We supply:

  • Power & Control Cables  — RR Kabel (LT, armoured XLPE, multicore control cables)
  • Switchgear & Panels     — Legrand (MCBs, RCCBs, distribution boards, LT panels, wiring accessories)
  • Industrial Lighting      — Bajaj, Panasonic & Havells (LED highbay, well glass, floodlights)

Why work with us?
  ✓ Same-day delivery within the Vapi-Silvassa-Daman belt
  ✓ Project-quantity pricing with credit terms for established businesses
  ✓  Complete BOM (Bill of Materials) assistance for new plant electrical installations
  ✓  After-sales technical support on Legrand panel wiring

We would be happy to visit your site, understand your electrical requirements, and submit a \
competitive quotation. We are available 7 days a week.

Could we schedule a brief call or site visit at your convenience?

Warm regards,
[Your Name]
[Your Designation]
[Company Name]
Mobile: [Your Number]
Email: [Your Email]

P.S. We also assist with GeM/tender documentation for government-linked procurement if required.
"""
    return body.strip()


def tender_email(tender_name: str, organization: str) -> str:
    """
    Introduction email for responding to a tender / RFQ.

    Parameters
    ----------
    tender_name : str
        Tender title or reference number, e.g. "Supply of Armoured Cables — Ref. GEM/2024/XXX".
    organization : str
        Procuring organization name, e.g. "ONGC, Hazira".

    Returns
    -------
    str
        Formatted email (Subject + Body).
    """
    subject = f"Expression of Interest — {tender_name} | {organization}"

    body = f"""\
Subject: {subject}

Dear Sir/Madam,

We write with reference to the above tender / requirement floated by {organization} and wish to \
submit our Expression of Interest.

About Us:
We are an established distributor of industrial electrical materials in the Vapi-Silvassa-Daman \
region. Our product portfolio directly relevant to this requirement includes:

  • Cables       : RR Kabel — LT power cables, armoured XLPE cables, multicore control cables
  • Switchgear   : Legrand — MCBs, RCCBs, distribution boards, LT switchgear panels
  • Lighting     : Bajaj / Panasonic / Havells — LED highbay, floodlights, industrial luminaires

We are registered on GeM (Government e-Marketplace) and can supply with:
  — GST-compliant invoicing
  — Manufacturer quality certificates & test reports
  — Delivery within 7 working days for in-stock items

We would be pleased to submit a detailed technical and commercial bid. Please share the full \
tender specification or BOQ at your earliest convenience so we can prepare a competitive offer.

Thanking you,
[Your Name]
[Your Designation]
[Company Name] | GST: [GSTIN] | GeM Seller ID: [ID]
Mobile: [Your Number]
Email: [Your Email]
"""
    return body.strip()


def revival_email(company: str, last_product: str, months_ago: int) -> str:
    """
    Dormant-lead revival email for companies that enquired in the past.

    Parameters
    ----------
    company : str
        Company name.
    last_product : str
        Product they previously enquired about, e.g. "armoured cables".
    months_ago : int
        Approximate months since the last enquiry.

    Returns
    -------
    str
        Formatted email (Subject + Body).
    """
    subject = f"Following Up on Your Earlier {last_product.title()} Enquiry — Updated Pricing Available"

    body = f"""\
Subject: {subject}

Dear Sir/Madam,

Hope this message finds you well!

We had the pleasure of connecting with {company} approximately {months_ago} month(s) ago \
regarding your requirement for {last_product}. We wanted to follow up and check whether \
the requirement is still active — or if a fresh need has come up.

We are pleased to share:
  • Revised pricing on {last_product} (updated {datetime.now().strftime('%B %Y')})
  • Improved delivery timelines (same-day/next-day within Vapi-Silvassa-Daman belt)
  • Expanded range: RR Kabel cables, Legrand switchgear, and Bajaj/Havells industrial lighting

If the requirement has been fulfilled, we completely understand. However, if there are any \
upcoming projects or regular procurement needs, we would love to be on your approved vendor list.

May we send you our current rate card? A quick reply or call would be most helpful.

Best regards,
[Your Name]
[Company Name]
Mobile: [Your Number]
Email: [Your Email]
"""
    return body.strip()


# ---------------------------------------------------------------------------
# WhatsApp template (under 200 chars for the opening line)
# ---------------------------------------------------------------------------

def whatsapp_intro(company: str, location: str, trigger: str) -> str:
    """
    Short WhatsApp introduction message (opening line under 200 chars).

    Parameters
    ----------
    company : str
        Company name.
    location : str
        Company location.
    trigger : str
        What triggered this outreach, e.g. "new plant construction", "tender on GeM".

    Returns
    -------
    str
        WhatsApp message text.
    """
    # Opening line kept under 200 chars
    opening = (
        f"Hello! We saw {company} ({location}) is working on {trigger}. "
        f"We supply RR Kabel cables, Legrand switchgear & industrial lighting for the Vapi-Silvassa belt. "
        f"Can we share a quote? 🙏"
    )
    # Trim if needed
    if len(opening) > 300:
        opening = opening[:297] + "..."
    return opening


def whatsapp_followup(company: str, days_since_contact: int) -> str:
    """
    Short WhatsApp follow-up nudge for a lead already in the pipeline.

    Parameters
    ----------
    company : str
        Company name.
    days_since_contact : int
        Days since last contact.

    Returns
    -------
    str
        WhatsApp follow-up message.
    """
    return (
        f"Hello {company} team! Just checking in — it has been {days_since_contact} days since we last spoke. "
        f"Did you get a chance to review our quotation? Happy to adjust quantities or revisit pricing. "
        f"Please let us know!"
    )


# ---------------------------------------------------------------------------
# Cold call script
# ---------------------------------------------------------------------------

def cold_call_script(company: str, trigger: str) -> str:
    """
    30-second cold call opener script.

    Parameters
    ----------
    company : str
        Company name.
    trigger : str
        What triggered this call, e.g. "new plant at Vapi GIDC", "tender for LED highbay".

    Returns
    -------
    str
        Formatted call script with timing guidance.
    """
    script = f"""\
COLD CALL SCRIPT — {company}
Trigger: {trigger}
Estimated duration: 30–45 seconds (opening)
─────────────────────────────────────────────

[AFTER CONNECTED]

"Good [morning/afternoon], could I please speak with the Purchase Manager or
 the person handling electrical material procurement?"

[WHEN CONNECTED TO RIGHT PERSON]

"Good [morning/afternoon], my name is [Your Name] from [Your Company].
 We are the go-to electrical materials distributor in the Vapi-Silvassa-Daman
 belt — we supply RR Kabel cables, Legrand switchgear, and Bajaj/Havells
 industrial lighting.

 The reason for my call is — we noticed that {company} is working on
 {trigger}, and we wanted to introduce ourselves as a potential supplier.

 We offer same-day delivery in this area and competitive pricing with credit
 terms.

 Would it be okay if I sent across our catalogue and rate card on WhatsApp or
 email? Or better yet — could we schedule a quick 10-minute meeting at your
 site this week?"

[IF ASKED FOR PRICE]
"I'd love to give you a specific price — could you share the items and quantities
 you need? I'll have a quote ready within the hour."

[IF GATEKEEPER / CALL BACK LATER]
"Of course, no problem. Could I have the name of the right person and a good
 time to call? I'll make sure to reach out then."

─────────────────────────────────────────────
NOTE: Log call outcome in leads.csv immediately after.
"""
    return script.strip()
