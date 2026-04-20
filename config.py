from pathlib import Path

ROOT        = Path(__file__).parent
MODELS_DIR  = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
CHARTS_DIR  = ROOT / "charts"
LOGS_DIR    = ROOT / "logs"

for d in [MODELS_DIR, REPORTS_DIR, CHARTS_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)

SYMBOL          = "GC=F"
MACRO_TICKERS   = {"dxy":"DX-Y.NYB","oil":"CL=F","spx":"^GSPC","tnx":"^TNX","vix":"^VIX"}
FORWARD_BARS    = 24
MIN_RR          = 2.0
MIN_CONFIDENCE  = 70.0
MIN_CONFLUENCE  = 4
ACCOUNT_SIZE    = 10000.0
RISK_PCT        = 1.0
POLL_SECONDS    = 900
WEB_PORT        = 5000
