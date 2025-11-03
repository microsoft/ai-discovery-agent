from dotenv import load_dotenv

# Load env values from file before importing other modules
load_dotenv(".azure.env", override=False)
load_dotenv(".env", override=False)

from aida.__main__ import app  # noqa: E402

__all__ = ["app"]
