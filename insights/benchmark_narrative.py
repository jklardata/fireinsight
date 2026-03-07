import anthropic
import json
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def generate_benchmark_narrative(result: dict) -> str:
    """
    Generate a board-ready executive summary of benchmark results.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build a concise summary for the prompt
    dept = result["dept_name"]
    state = result["state"]
    dept_type = result["dept_type"]
    pop = result["population"]
    peers = result["peer_counts"]

    metric_summary = []
    for key, m in result["metrics"].items():
        nat = m.get("national")
        if not nat:
            continue
        metric_summary.append({
            "metric":     m["label"],
            "our_value":  m["our_display"],
            "peer_avg":   nat.get("peer_avg_fmt") or str(nat["peer_avg"]),
            "national_percentile": nat["percentile"],
            "above_average": nat["above_avg"],
        })

    summary = {
        "department": dept,
        "state": state,
        "dept_type": dept_type,
        "population_served": pop,
        "peer_groups": {
            "state_peers":    peers["state"],
            "regional_peers": peers["regional"],
            "national_peers": peers["national"],
        },
        "metrics": metric_summary,
    }

    prompt = f"""You are a fire service performance analyst preparing an executive briefing.

Benchmark Data:
{json.dumps(summary, indent=2)}

Write a concise board-ready executive summary (3-4 paragraphs) that a fire chief could present to a city council or board of directors. Structure it as:

**Paragraph 1 — Opening**: State the department's overall competitive position in plain terms. Lead with the most impressive result. Reference the number of peer departments in the comparison.

**Paragraph 2 — Strengths**: Highlight 2-3 specific metrics where the department outperforms peers. Use exact percentile rankings and actual values.

**Paragraph 3 — Opportunities**: Identify 1-2 areas where improvement would have the most impact. Be specific but constructive — frame as an opportunity, not a failure.

**Paragraph 4 — Closing**: One sentence connecting performance to community trust, public safety investment, or operational readiness.

Rules: Use specific numbers from the data. No filler language. No bullet points — prose only. Do not use the word "benchmarking" — say "peer comparison" instead."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=900,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
