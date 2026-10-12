"""Save a TopDeck API key locally for Delver's Python backend.

Run this once from the project folder. It writes a gitignored .env file with
owner-only permissions when the operating system supports them.
"""

from getpass import getpass
from pathlib import Path


root = Path(__file__).parent
key = getpass("Paste your TopDeck API key: ").strip()
if not key:
    raise SystemExit("No key entered; nothing was saved.")

env_file = root / ".env"
env_file.write_text(f"TOPDECK_API_KEY={key}\n")
try:
    env_file.chmod(0o600)
except OSError:
    pass

print("Saved .env locally. Start the app with: python3 server.py")
