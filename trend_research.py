"""Fail-closed validation for researched TrendScope story dossiers.

This validates editorial evidence; it does not discover trends or certify source truth.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from urllib.parse import urlparse


def _date(value: str, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def validate_dossier(dossier: dict, *, today: date | None = None,
                     max_age_days: int = 14) -> dict:
    """Validate source-backed claims and freshness; return a compact QA report."""
    today = today or datetime.now(timezone.utc).date()
    if not isinstance(dossier, dict):
        raise ValueError("dossier must be an object")
    for field in ("topic", "editorial_angle", "discovery_timestamp", "sources", "claims"):
        if not dossier.get(field):
            raise ValueError(f"missing required field: {field}")
    try:
        discovered = datetime.fromisoformat(
            dossier["discovery_timestamp"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("discovery_timestamp must be an ISO-8601 timestamp") from exc
    if discovered.tzinfo is None:
        raise ValueError("discovery_timestamp must include a timezone")
    if discovered.date() > today:
        raise ValueError("discovery_timestamp cannot be in the future")

    sources = dossier["sources"]
    claims = dossier["claims"]
    if not isinstance(sources, list) or len(sources) < 2:
        raise ValueError("at least two sources are required")
    if not isinstance(claims, list) or not claims:
        raise ValueError("at least one sourced claim is required")

    by_id = {}
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("each source must be an object")
        sid = source.get("id")
        if not sid or sid in by_id:
            raise ValueError("source IDs must be present and unique")
        url = source.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError(f"source {sid}: URL must use HTTPS")
        if not source.get("publisher") or not source.get("source_type"):
            raise ValueError(f"source {sid}: publisher and source_type are required")
        published = _date(source.get("published_at"), f"source {sid} published_at")
        age = (today - published).days
        if age < 0:
            raise ValueError(f"source {sid}: publication date is in the future")
        if age > max_age_days:
            raise ValueError(f"source {sid}: stale source ({age} days old)")
        by_id[sid] = {**source, "domain": parsed.hostname.lower()}

    claim_count = 0
    for claim in claims:
        if not isinstance(claim, dict) or not claim.get("text"):
            raise ValueError("each claim must include text")
        refs = claim.get("source_ids")
        if not isinstance(refs, list) or len(set(refs)) < 2:
            raise ValueError("each material claim needs at least two source IDs")
        if any(ref not in by_id for ref in refs):
            raise ValueError("claim references an unknown source ID")
        domains = {by_id[ref]["domain"] for ref in refs}
        if len(domains) < 2:
            raise ValueError("each material claim needs two independent source domains")
        if not claim.get("status") or claim["status"] not in (
                "verified", "developing", "disputed", "analysis"):
            raise ValueError("claim status must be verified, developing, disputed, or analysis")
        claim_count += 1

    return {"valid": True, "source_count": len(by_id),
            "claim_count": claim_count, "discovered_at": discovered.isoformat()}
