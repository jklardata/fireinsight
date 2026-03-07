"""
Staffing Justification Narrative Generator

Uses Claude to produce a board-presentation-ready staffing justification
report based on concurrent incident analysis and demand data.
"""
from __future__ import annotations

import json
import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def generate_staffing_narrative(dept_name: str, report: dict) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    summary = {
        "department":          dept_name,
        "total_incidents":     report.get("total_incidents"),
        "incidents_per_day":   report.get("incidents_per_day"),
        "max_concurrent":      report.get("max_concurrent"),
        "avg_concurrent":      report.get("avg_concurrent"),
        "understaffing_count": report.get("understaffing_count"),
        "understaffing_pct":   report.get("understaffing_pct"),
        "avg_rt_normal_fmt":   report.get("avg_rt_normal_fmt"),
        "avg_rt_busy_fmt":     report.get("avg_rt_busy_fmt"),
        "rt_degradation_pct":  report.get("rt_degradation_pct"),
        "peak_hours":          report.get("peak_hours", [])[:3],
        "peak_days":           report.get("peak_days", [])[:3],
        "worst_events":        report.get("worst_events", [])[:3],
    }

    prompt = f"""You are a fire service analyst preparing a staffing justification report for a fire department board meeting.

Incident Analysis Data:
{json.dumps(summary, indent=2)}

Context:
- "Understaffing events" = incidents where 2 or more OTHER calls were active at the same time (simultaneous demand exceeding typical crew deployment)
- Response time degradation = the difference in average response time between normal periods (0-1 concurrent calls) vs. busy periods (2+ concurrent)
- NFPA 1710 benchmark: 8-minute response time standard for career departments

Write a board-presentation-ready staffing justification report. Structure it exactly as:

## Staffing Analysis Report — {dept_name}

### Executive Summary
One tight paragraph a board member can read in 30 seconds. State the core problem — simultaneous incidents are degrading response times — with two or three hard numbers. Make the case for why this is a public safety issue, not just an operational inconvenience.

### Demand Analysis
Detail the call volume, concurrency data, and peak demand periods. Explain what "understaffing events" mean operationally — who is covering what when multiple calls drop simultaneously. Be specific about days and hours of peak demand.

### Response Time Impact
Quantify the response time degradation during concurrent incidents. Compare to NFPA 1710 (8 minutes) and explain what the additional seconds mean in a structure fire or cardiac arrest context. Make the time cost of understaffing viscerally clear.

### Risk Exposure
Translate the data into public safety and liability terms. What is the department's exposure if a concurrent incident results in a delayed response to a life-threatening call? Reference realistic scenarios the board can understand.

### Staffing Recommendation
State clearly what additional staffing (or mutual aid agreements) the data supports. Be specific about shift coverage gaps. Give the board a concrete ask, not vague language.

Use plain, direct language. Every claim must reference a specific number from the data. This is a persuasion document — write it to win the budget argument."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1400,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
