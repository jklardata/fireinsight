import anthropic
import json
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def generate_trend_summary(dept_name: str, stats: dict, period: str) -> str:
    """
    Use case 1: Plain-English incident trend summary for a fire chief.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a fire service analyst helping a fire chief understand their department's performance data.

Department: {dept_name}
Period: {period}
Incident Data Summary:
{json.dumps(stats, indent=2)}

Write a clear, plain-English trend summary a fire chief can read in under 2 minutes. Structure it as:

1. **Overview** — Total call volume and what it means
2. **Call Type Breakdown** — What types of incidents dominated and any notable patterns
3. **Response Times** — How the department is performing and what's driving the numbers
4. **Busiest Periods** — When demand peaks (time of day, day of week)
5. **Key Takeaways** — 2-3 actionable observations the chief should pay attention to

Use plain language. Avoid jargon. Be specific with numbers. Do not pad with filler sentences."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
