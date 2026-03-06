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


def fetch_incidents(neris_id: str, **kwargs) -> list[dict]:
    """Fetch all incidents for a department, handling pagination."""
    client = get_client()
    incidents = []
    cursor = None

    while True:
        result = client.list_incidents(neris_id_entity=neris_id, cursor=cursor, **kwargs)
        if not result:
            break

        batch = result.get("data", [])
        incidents.extend(batch)

        cursor = result.get("next_cursor")
        if not cursor:
            break

    return incidents


def fetch_entity(neris_id: str) -> dict:
    client = get_client()
    return client.get_entity(neris_id)
