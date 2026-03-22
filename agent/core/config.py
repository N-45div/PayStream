"""Configuration for the PayStream Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# LLM (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# WDK
WDK_SEED = os.getenv("WDK_SEED", "")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

# RPC (passed to WDK server via env)
POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon.llamarpc.com")
ETH_RPC = os.getenv("ETH_RPC", "https://eth.llamarpc.com")
ARB_RPC = os.getenv("ARB_RPC", "https://arbitrum.llamarpc.com")

# API
PORT = int(os.getenv("PORT", "8000"))

# WDK MCP server path (relative to agent dir)
WDK_SERVER_DIR = Path(__file__).parent.parent.parent / "wdk-server"
WDK_SERVER_CMD = "node"
WDK_SERVER_ARGS = [str(WDK_SERVER_DIR / "index.js")]

# Contributor roles & hourly rates (USDT)
ROLES = {
    "lead":      {"label": "Lead",      "hourly_rate": 75.0},
    "developer": {"label": "Developer", "hourly_rate": 50.0},
    "reviewer":  {"label": "Reviewer",  "hourly_rate": 30.0},
    "designer":  {"label": "Designer",  "hourly_rate": 40.0},
    "intern":    {"label": "Intern",    "hourly_rate": 15.0},
}

# Treasury policy defaults
DEFAULT_POLICY = {
    "max_daily_spend": 500.0,       # USDT per day
    "max_single_payment": 100.0,    # USDT per tx
    "min_balance": 10.0,            # USDT reserve
    "tick_interval_s": 120,         # agent loop interval (2 min)
    "auto_pause_low_balance": True,
    "require_ai_approval": True,
    "ai_approval_threshold": 25.0,  # AI reviews payments > this
}
