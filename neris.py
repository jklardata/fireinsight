from datetime import datetime
from neris_api_client import NerisApiClient
from neris_api_client.config import Config, GrantType
from config import NERIS_BASE_URL, NERIS_CLIENT_ID, NERIS_CLIENT_SECRET


def get_client() -> NerisApiClient:
    return NerisApiClient(Config(
        base_url=NERIS_BASE_URL,
        grant_type=GrantType.CLIENT_CREDENTIALS,
        client_id=NERIS_CLIENT_ID,
        client_secret=NERIS_CLIENT_SECRET,
    ))


def fetch_incidents(
    neris_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    max_incidents: int = 5000,
    **kwargs,
) -> list[dict]:
    """Fetch incidents for a department, handling pagination up to max_incidents."""
    client = get_client()
    incidents = []
    cursor = None

    while True:
        result = client.list_incidents(
            neris_id_entity=neris_id,
            cursor=cursor,
            call_create_start=start,
            call_create_end=end,
            page_size=200,
            **kwargs,
        )
        # The SDK returns a requests.Response on HTTP errors (falsy when status >= 400)
        import requests as _requests
        if isinstance(result, _requests.Response):
            raise RuntimeError(
                f"NERIS API error {result.status_code} for entity '{neris_id}'. "
                f"Check that the NERIS ID is correct and your credentials have access to this department."
            )

        if not result:
            break

        # Surface API-level errors (e.g. error key in JSON body)
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(f"NERIS API error: {result.get('error')} — {result.get('message', '')}")

        batch = result.get("data", [])
        incidents.extend(batch)

        if len(incidents) >= max_incidents:
            break

        cursor = result.get("next_cursor")
        if not cursor:
            break

    return incidents[:max_incidents]


def fetch_entity(neris_id: str) -> dict:
    client = get_client()
    return client.get_entity(neris_id)
