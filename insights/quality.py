import anthropic
import json
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def generate_quality_narrative(dept_name: str, report: dict) -> str:
    """
    Use Claude to produce a plain-English data quality debrief for a fire chief
    or data officer, with specific, actionable remediation steps.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build a focused summary to keep the prompt tight
    top_issues = [
        f for f in report["field_completion"]
        if f["completion_pct"] < 90
    ][:6]

    flags = report.get("validity_flags", {})

    summary = {
        "department": dept_name,
        "total_incidents": report["total"],
        "overall_score": report["overall_score"],
        "grade": report["grade"],
        "grade_label": report["grade_label"],
        "score_distribution": report["score_distribution"],
        "top_missing_fields": [
            {
                "field": f["label"],
                "tier": f["tier"],
                "completion_pct": f["completion_pct"],
                "missing_count": f["missing_count"],
            }
            for f in top_issues
        ],
        "validity_issues": flags,
    }

    prompt = f"""You are a fire service data quality specialist reviewing a department's NERIS incident data.

Quality Report:
{json.dumps(summary, indent=2)}

Write a plain-English data quality debrief a fire chief or records officer can act on immediately. Structure it as:

## Overall Assessment
One paragraph — what the score means in practical terms. Be direct, not diplomatic. If the data is poor, say so and explain the downstream consequences (grant applications weakened, ISO rating evidence undermined, trend analysis unreliable).

## Top Issues to Fix
For each of the top missing fields, explain:
- Why that field matters operationally and for reporting
- The most likely reason it's being missed (workflow, RMS config, training gap)
- The single most actionable fix (specific to fire service operations)

## Validity Problems
If there are timestamp or logic errors, explain what causes them and how to catch them at the point of entry.

## Quick Wins
List 2-3 changes the department can make this week that will have the biggest impact on score.

Use plain language. Be specific with numbers from the report. Do not pad with filler."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
