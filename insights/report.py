import anthropic
import json
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def generate_chiefs_report(dept_name: str, stats: dict, period: str) -> str:
    """
    Use case 3: One-page monthly chief's report for city councils or boards.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are helping a fire chief communicate their department's monthly activity to a city council or board of directors — non-technical stakeholders who care about community safety and budget.

Department: {dept_name}
Report Period: {period}
Incident Data:
{json.dumps(stats, indent=2)}

Write a one-page Chief's Monthly Report with these sections:

**{dept_name} — Monthly Activity Report**
**{period}**

**At a Glance**
(3-4 bullet points with the most important headline numbers)

**Incident Activity**
(Short paragraph: total calls, top call types, any notable trends vs. prior context if available)

**Response Performance**
(Short paragraph: average response time, what it means, any performance highlights)

**Demand Patterns**
(1-2 sentences on when the department is busiest)

**Looking Ahead**
(1-2 sentences: anything the data suggests the department should monitor or prepare for)

Keep the language simple and professional. Avoid internal fire service jargon. A city council member with no fire background should understand every sentence."""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
