import os
from dotenv import load_dotenv

load_dotenv()

NERIS_BASE_URL = os.getenv("NERIS_BASE_URL", "https://api-test.neris.fsri.org/v1")
NERIS_CLIENT_ID = os.getenv("NERIS_CLIENT_ID")
NERIS_CLIENT_SECRET = os.getenv("NERIS_CLIENT_SECRET")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-opus-4-6"
