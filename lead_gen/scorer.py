"""
scorer.py — Lead scoring engine for the industrial B2B lead generation system.

Scores a lead dict on four dimensions:
  - Geography   (which ring the company is in)
  - Signal type (active tender, new plant, etc.)
  - Product fit (how many of our product lines match)
  - Timing      (urgency of the buying opportunity)

Returns a normalised integer score 0-100.

Expected lead dict keys (all optional — missing keys default to 0):
  location      : str  e.g. "Vapi" or "Silvassa"
  signal_type   : str  one of: "active_tender", "new_plant", "energy_upgrade",
                              "job_posting", "directory"
  products      : list[str]  product categories needed e.g. ["cables", "switchgear"]
  timing        : str  one of: "immediate", "3_6months", "6_12months", "longterm"
"""

from lead_gen.config import RING_1, RING_2, SCORING, MAX_RAW_SCORE


class LeadScorer:
    """Score a lead and return a 0-100 integer."""

    def score(self, lead: dict) -> int:
        """
        Parameters
        ----------
        lead : dict
            Lead data dictionary. See module docstring for expected keys.

        Returns
        -------
        int
            Score between 0 and 100 (higher = hotter lead).
        """
        raw = 0
        raw += self._score_geography(lead.get("location", ""))
        raw += self._score_signal(lead.get("signal_type", ""))
        raw += self._score_product_fit(lead.get("products", []))
        raw += self._score_timing(lead.get("timing", ""))

        # Normalise to 0-100
        if MAX_RAW_SCORE <= 0:
            return 0
        normalised = int(min(100, round((raw / MAX_RAW_SCORE) * 100)))
        return normalised

    # ------------------------------------------------------------------
    # Private scoring helpers
    # ------------------------------------------------------------------

    def _score_geography(self, location: str) -> int:
        """Award points based on which geography ring the company is in."""
        if not location:
            return SCORING["ring_other"]
        loc = location.strip().title()
        if any(loc == r.title() for r in RING_1):
            return SCORING["ring_1"]
        if any(loc == r.title() for r in RING_2):
            return SCORING["ring_2"]
        return SCORING["ring_other"]

    def _score_signal(self, signal_type: str) -> int:
        """Award points for the type of buying signal detected."""
        mapping = {
            "active_tender": SCORING["signal_active_tender"],
            "new_plant": SCORING["signal_new_plant"],
            "energy_upgrade": SCORING["signal_energy_upgrade"],
            "job_posting": SCORING["signal_job_posting"],
            "directory": SCORING["signal_directory"],
        }
        return mapping.get(signal_type.lower().strip() if signal_type else "", 0)

    def _score_product_fit(self, products: list) -> int:
        """Award points based on how many product lines the lead needs."""
        if not products:
            return 0
        count = len(set(p.lower().strip() for p in products))
        if count >= 3:
            return SCORING["product_fit_heavy"]
        if count == 2:
            return SCORING["product_fit_medium"]
        return SCORING["product_fit_light"]

    def _score_timing(self, timing: str) -> int:
        """Award points based on urgency / buying timeline."""
        mapping = {
            "immediate": SCORING["timing_immediate"],
            "3_6months": SCORING["timing_3_6months"],
            "6_12months": SCORING["timing_6_12months"],
            "longterm": SCORING["timing_longterm"],
        }
        return mapping.get(timing.lower().strip() if timing else "", 0)

    # ------------------------------------------------------------------
    # Convenience: score + explain
    # ------------------------------------------------------------------

    def score_with_breakdown(self, lead: dict) -> dict:
        """
        Same as score() but also returns a breakdown dict.

        Returns
        -------
        dict with keys: score, geography, signal, product_fit, timing
        """
        geo = self._score_geography(lead.get("location", ""))
        sig = self._score_signal(lead.get("signal_type", ""))
        pft = self._score_product_fit(lead.get("products", []))
        tim = self._score_timing(lead.get("timing", ""))
        raw = geo + sig + pft + tim
        normalised = int(min(100, round((raw / MAX_RAW_SCORE) * 100))) if MAX_RAW_SCORE > 0 else 0
        return {
            "score": normalised,
            "geography": geo,
            "signal": sig,
            "product_fit": pft,
            "timing": tim,
        }
