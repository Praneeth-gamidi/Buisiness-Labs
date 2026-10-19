import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CHROMA_PATH = os.getenv("CHROMA_PATH", str(ROOT / ".chroma"))
SQLITE_PATH = os.getenv("SQLITE_PATH", str(DATA_DIR / "knowledge.db"))
SITEMAP_URL = "https://support.brilliantdirectories.com/support/sitemap.xml"
DELAY = float(os.getenv("REQUEST_DELAY_SECONDS", "1.0"))
