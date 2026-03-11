import os
from dotenv import load_dotenv

load_dotenv()

CLERK_PUBLISHABLE_KEY = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY") or os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")

NERIS_BASE_URL = os.getenv("NERIS_BASE_URL", "https://api-test.neris.fsri.org/v1")
NERIS_CLIENT_ID = os.getenv("NERIS_CLIENT_ID")
NERIS_CLIENT_SECRET = os.getenv("NERIS_CLIENT_SECRET")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-opus-4-6"

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
DEMO_EMAIL_TO = os.getenv("DEMO_EMAIL_TO", "justinleu@gmail.com")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
