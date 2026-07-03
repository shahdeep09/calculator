"""
lead_tracker.py — CSV-based lead tracker (no external database needed).

Stores all leads in leads.csv with a simple, human-readable format.
Works with spreadsheet apps (Excel, Google Sheets) as well as Python.

CSV columns:
  id, date_found, company, location, signal_type, score, status,
  products_needed, contact_info, notes, last_updated

Status values: new | contacted | meeting | quoted | won | lost

To use:
    from lead_gen.lead_tracker import LeadTracker
    tracker = LeadTracker()
    tracker.add_lead({...})
    print(tracker.export_weekly_digest())
"""

import csv
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from lead_gen.config import LEADS_CSV_PATH, FOLLOWUP_DAYS

# All columns in order
CSV_COLUMNS = [
    "id",
    "date_found",
    "company",
    "location",
    "signal_type",
    "score",
    "status",
    "products_needed",
    "contact_info",
    "notes",
    "last_updated",
]

VALID_STATUSES = {"new", "contacted", "meeting", "quoted", "won", "lost"}


class LeadTracker:
    """
    Simple CSV-based lead tracker.

    Parameters
    ----------
    csv_path : str, optional
        Path to the leads CSV file. Defaults to LEADS_CSV_PATH from config.
    """

    def __init__(self, csv_path: str = None):
        self.csv_path = Path(csv_path or LEADS_CSV_PATH)
        self._ensure_file()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_lead(self, lead: dict) -> str:
        """
        Add a new lead to the CSV file.

        Parameters
        ----------
        lead : dict
            Lead data. Expected keys match CSV_COLUMNS.
            'id', 'date_found', 'last_updated', 'status' are auto-filled if missing.

        Returns
        -------
        str
            The assigned lead ID.
        """
        now = datetime.now().strftime("%Y-%m-%d")
        row = {col: "" for col in CSV_COLUMNS}
        row.update(lead)
        row["id"] = row.get("id") or self._generate_id()
        row["date_found"] = row.get("date_found") or now
        row["last_updated"] = now
        row["status"] = row.get("status") or "new"
        if isinstance(row.get("products_needed"), list):
            row["products_needed"] = "|".join(row["products_needed"])

        # Check for duplicate company + location combination
        existing = self._load_all()
        for ex in existing:
            if (
                ex.get("company", "").strip().lower() == str(row.get("company", "")).strip().lower()
                and ex.get("location", "").strip().lower() == str(row.get("location", "")).strip().lower()
                and ex.get("status") not in ("won", "lost")
            ):
                print(
                    f"[lead_tracker] Lead for '{row['company']}' in '{row['location']}' already exists "
                    f"(id={ex['id']}). Skipping duplicate."
                )
                return ex["id"]

        self._append_row(row)
        print(f"[lead_tracker] Added lead {row['id']} — {row.get('company', 'Unknown')} ({row.get('location', '?')})")
        return row["id"]

    def update_status(self, lead_id: str, status: str, notes: str = "") -> bool:
        """
        Update the status (and optionally notes) for a lead.

        Parameters
        ----------
        lead_id : str
            The lead's id field.
        status : str
            New status value — must be one of VALID_STATUSES.
        notes : str, optional
            Append notes to the existing notes field.

        Returns
        -------
        bool
            True if the lead was found and updated, False otherwise.
        """
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid: {VALID_STATUSES}")

        rows = self._load_all()
        updated = False
        for row in rows:
            if row["id"] == lead_id:
                row["status"] = status
                row["last_updated"] = datetime.now().strftime("%Y-%m-%d")
                if notes:
                    existing_notes = row.get("notes", "")
                    row["notes"] = (existing_notes + f" | {notes}").lstrip(" | ")
                updated = True
                break

        if updated:
            self._write_all(rows)
            print(f"[lead_tracker] Updated lead {lead_id} → status='{status}'")
        else:
            print(f"[lead_tracker] WARNING: Lead {lead_id} not found.")
        return updated

    def get_followup_due(self) -> list:
        """
        Return leads where status is 'contacted' and last_updated was >FOLLOWUP_DAYS ago.

        Returns
        -------
        list[dict]
            Leads needing follow-up, sorted by last_updated (oldest first).
        """
        cutoff = (datetime.now() - timedelta(days=FOLLOWUP_DAYS)).strftime("%Y-%m-%d")
        rows = self._load_all()
        due = [
            r for r in rows
            if r.get("status") == "contacted" and r.get("last_updated", "9999") <= cutoff
        ]
        due.sort(key=lambda r: r.get("last_updated", ""))
        return due

    def get_all_leads(self) -> list:
        """Return all leads as a list of dicts."""
        return self._load_all()

    def get_leads_by_status(self, status: str) -> list:
        """Return all leads with the given status."""
        return [r for r in self._load_all() if r.get("status") == status]

    def export_weekly_digest(self) -> str:
        """
        Generate a formatted text summary of this week's leads and pipeline.

        Returns
        -------
        str
            Multi-line summary suitable for printing or sending via email/WhatsApp.
        """
        rows = self._load_all()
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

        new_this_week = [r for r in rows if r.get("date_found", "") >= week_start]
        followup_due = self.get_followup_due()

        status_counts: dict = {}
        for r in rows:
            s = r.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        lines = [
            "=" * 60,
            f"WEEKLY LEAD DIGEST — {now.strftime('%d %b %Y')}",
            "=" * 60,
            "",
            f"Total leads in pipeline : {len(rows)}",
        ]
        for status, count in sorted(status_counts.items()):
            lines.append(f"  {status:<15}: {count}")

        lines += [
            "",
            f"NEW THIS WEEK ({len(new_this_week)})",
            "-" * 40,
        ]
        for r in new_this_week:
            score_str = f"[Score: {r.get('score', '?')}]"
            lines.append(
                f"  {r.get('company', 'Unknown'):<30} {r.get('location', '?'):<15} "
                f"{r.get('signal_type', '?'):<20} {score_str}"
            )

        lines += [
            "",
            f"FOLLOW-UP OVERDUE ({len(followup_due)})",
            "-" * 40,
        ]
        for r in followup_due:
            days_ago = (now - datetime.strptime(r.get("last_updated", now.strftime("%Y-%m-%d")), "%Y-%m-%d")).days
            lines.append(
                f"  {r.get('company', 'Unknown'):<30} last contacted {days_ago} days ago"
                f"  [{r.get('contact_info', 'no contact')}]"
            )

        lines += ["", "=" * 60]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        """Create the CSV file with headers if it does not exist."""
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()

    def _load_all(self) -> list:
        """Load all rows from the CSV file."""
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _append_row(self, row: dict) -> None:
        """Append a single row to the CSV file."""
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})

    def _write_all(self, rows: list) -> None:
        """Overwrite the CSV file with all rows."""
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})

    @staticmethod
    def _generate_id() -> str:
        """Generate a short unique ID for a lead."""
        return "LD-" + uuid.uuid4().hex[:8].upper()
