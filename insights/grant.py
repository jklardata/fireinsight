import anthropic
import json
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


GRANT_TYPES = {
    "AFG": "FEMA Assistance to Firefighters Grant (AFG)",
    "SAFER": "FEMA Staffing for Adequate Fire and Emergency Response (SAFER)",
}


def generate_grant_narrative(
    dept_name: str,
    stats: dict,
    grant_type: str,
    request_description: str,
    period: str,
) -> str:
    """
    Use case 2: Data-backed grant narrative for AFG or SAFER applications.

    Args:
        dept_name: Name of the fire department
        stats: Aggregated incident stats from analytics.summarize_incidents()
        grant_type: "AFG" or "SAFER"
        request_description: What the department is requesting (e.g., "2 thermal imaging cameras")
        period: Time period covered by the data (e.g., "January 2024 - December 2024")
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    grant_label = GRANT_TYPES.get(grant_type.upper(), grant_type)

    prompt = f"""You are an expert grant writer specializing in fire service funding. You write clear, compelling, data-driven narratives for FEMA grant applications.

Department: {dept_name}
Grant Program: {grant_label}
Funding Request: {request_description}
Data Period: {period}

Incident Data:
{json.dumps(stats, indent=2)}

Write a grant project narrative that:
1. Opens with a compelling statement of need grounded in the data
2. Describes the department's call volume, incident types, and service demand using specific numbers
3. Explains how the requested equipment/staffing directly addresses documented needs
4. Highlights response time data to underscore urgency or current gaps
5. Closes with a clear statement of community impact

Guidelines:
- Write in formal but clear prose (no bullet points in the narrative itself)
- Cite specific numbers from the data throughout
- Keep it under 500 words — grant reviewers read quickly
- Do not fabricate statistics; only use what's in the data provided
- Tailor language to {grant_label} review criteria"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
