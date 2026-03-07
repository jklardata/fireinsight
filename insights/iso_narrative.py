"""
ISO PPC Evidence Pack Generator

Analyzes incident data against ISO Public Protection Classification benchmarks
and produces a formatted evidence narrative ready for submission or board review.
"""
from __future__ import annotations

import json
import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

# ISO PPC response time components (seconds)
ISO_DISPATCH_TARGET  = 60    # 1 min dispatch
ISO_TURNOUT_TARGET   = 60    # 1 min turnout (career); 2 min volunteer
ISO_TRAVEL_TARGET    = 240   # 4 min travel to first engine (80th percentile)
ISO_TOTAL_TARGET     = 360   # 6 min total first-unit (dispatch + turnout + travel)
NFPA_1710_TARGET     = 480   # 8 min total (NFPA 1710 first-unit)


def _fmt_secs(s: float) -> str:
    m, sec = int(s) // 60, int(s) % 60
    return f"{m}m {sec:02d}s"


def compute_iso_metrics(incidents: list[dict]) -> dict:
    """Compute ISO-relevant response time statistics from incidents."""
    from datetime import datetime

    def _parse(v):
        try:
            return datetime.fromisoformat(str(v)) if v else None
        except Exception:
            return None

    rt_list: list[float] = []
    under_8min = 0
    under_6min = 0

    for inc in incidents:
        alarm   = _parse(inc.get("call_create"))
        arrival = _parse(inc.get("arrival_time"))
        if alarm and arrival:
            d = (arrival - alarm).total_seconds()
            if 30 < d < 7200:
                rt_list.append(d)
                if d <= 480:
                    under_8min += 1
                if d <= 360:
                    under_6min += 1

    if not rt_list:
        return {}

    rt_sorted = sorted(rt_list)
    n = len(rt_sorted)
    p80_idx = min(int(n * 0.8), n - 1)
    p90_idx = min(int(n * 0.9), n - 1)

    avg_rt = round(sum(rt_list) / n)
    p80_rt = round(rt_sorted[p80_idx])
    p90_rt = round(rt_sorted[p90_idx])

    return {
        "sample_size":       n,
        "avg_rt":            avg_rt,
        "avg_rt_fmt":        _fmt_secs(avg_rt),
        "p80_rt":            p80_rt,
        "p80_rt_fmt":        _fmt_secs(p80_rt),
        "p90_rt":            p90_rt,
        "p90_rt_fmt":        _fmt_secs(p90_rt),
        "pct_under_8min":    round(under_8min / n * 100, 1),
        "pct_under_6min":    round(under_6min / n * 100, 1),
        "nfpa_1710_target":  "8m 00s",
        "iso_travel_target": "4m 00s",
        "iso_total_target":  "6m 00s",
        "meets_nfpa_1710":   avg_rt <= NFPA_1710_TARGET,
        "meets_iso_total":   avg_rt <= ISO_TOTAL_TARGET,
        "p80_meets_iso":     p80_rt <= ISO_TOTAL_TARGET,
    }


def generate_iso_narrative(dept_name: str, stats: dict, iso_metrics: dict, period: str) -> str:
    """Generate an ISO PPC evidence narrative via Claude."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    summary = {
        "department":       dept_name,
        "period":           period,
        "total_incidents":  stats.get("total_incidents", 0),
        "call_types":       dict(list(stats.get("call_types", {}).items())[:8]),
        "iso_metrics":      iso_metrics,
    }

    prompt = f"""You are a fire service consultant preparing an ISO PPC (Public Protection Classification) evidence document for a fire department's rating review.

Department Data:
{json.dumps(summary, indent=2)}

ISO PPC Key Benchmarks:
- Dispatch: 1-minute target
- Turnout: 1–2 minutes
- Travel to first unit: 4 minutes (ISO measures at 80th percentile)
- Total first-unit response: 6 minutes
- NFPA 1710 benchmark: 8 minutes

Write a formal evidence narrative for the fire department's ISO PPC submission. Structure it as:

## ISO PPC Evidence Narrative — {dept_name}

### Department Overview
One paragraph summarizing the department's incident volume and service profile. Reference the period covered and total calls handled.

### Response Time Performance
Detailed analysis of response time data against ISO benchmarks. Include:
- Average and 80th-percentile response times with explicit comparison to the 4-minute travel and 6-minute total targets
- The percentage of incidents meeting NFPA 1710 (8-minute) and ISO 6-minute standards
- An honest assessment of whether the data supports a favorable PPC rating and why

### Incident Type Profile
How the call mix (structure fires, EMS, hazmat, etc.) relates to ISO credit categories. Note any fire suppression call volume that contributes to ISO points.

### Data Reliability Statement
A brief attestation paragraph noting the data source (NERIS), incident count, and time period — suitable for inclusion in a formal submission package.

### Recommendations for Rating Improvement
2–3 specific, actionable items the department can document or improve to strengthen their PPC submission.

Write in formal, professional language suitable for an insurance rating submission. Use specific numbers throughout. Do not hedge excessively — give a clear assessment."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1400,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
