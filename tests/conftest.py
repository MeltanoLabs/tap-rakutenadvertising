"""Shared pytest configuration — loads .env before tests run."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root so TAP_RAKUTENADVERTISING_* vars are available.
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
