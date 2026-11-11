"""Safe API Key & Connection Verifier for Forward Ledger.

Tests connections without exposing secret tokens.
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminal
if sys.stdout and getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Load .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def mask_key(k: str) -> str:
    if not k:
        return "(NOT SET)"
    if len(k) <= 8:
        return k[:2] + "..." + k[-2:]
    return k[:4] + "..." + k[-4:]


def check_odds_api() -> bool:
    print("\n[1/3] Testing The Odds API (api.the-odds-api.com)...")
    key = os.getenv("ODDS_API_KEY", "").strip()
    print(f"      Key: {mask_key(key)}")

    if not key or key == "your_the_odds_api_key_here":
        print("      ❌ ODDS_API_KEY is missing or using placeholder.")
        print("      👉 Get a free API key at: https://the-odds-api.com/#get-access")
        return False

    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        res = requests.get(url, timeout=10)
        remaining = res.headers.get("x-requests-remaining", "unknown")
        used = res.headers.get("x-requests-used", "unknown")

        if res.status_code == 200:
            print(f"      ✅ Success! Connected to The Odds API.")
            print(f"      📊 Requests remaining: {remaining} | Requests used: {used}")
            return True
        elif res.status_code == 401:
            print(f"      ❌ Unauthorized (401). Invalid ODDS_API_KEY.")
            return False
        else:
            print(f"      ⚠️ Status {res.status_code}: {res.text[:120]}")
            return False
    except Exception as e:
        print(f"      ❌ Network error connecting to The Odds API: {e}")
        return False


def check_api_football() -> bool:
    print("\n[2/3] Testing API-Football...")
    key = os.getenv("API_FOOTBALL_KEY", "").strip()
    provider = os.getenv("API_FOOTBALL_PROVIDER", "rapidapi").lower().strip()
    print(f"      Key: {mask_key(key)}")
    print(f"      Provider: {provider}")

    if not key or key == "your_api_football_key_here":
        print("      ⚠️ API_FOOTBALL_KEY is not configured yet.")
        print("      👉 RapidAPI: https://rapidapi.com/api-sports/api/api-football")
        print("      👉 API-Sports Direct: https://dashboard.api-football.com/")
        return False

    if provider == "direct":
        url = "https://v3.football.api-sports.io/status"
        headers = {"x-apisports-key": key}
    else:
        url = "https://api-football-v1.p.rapidapi.com/v3/status"
        headers = {
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            account = data.get("response", {}).get("account", {})
            requests_info = data.get("response", {}).get("requests", {})
            print(f"      ✅ Success! Connected to API-Football.")
            if account:
                print(f"      👤 Account: {account.get('firstname', '')} {account.get('lastname', '')} ({account.get('email', '')})")
            if requests_info:
                print(f"      📊 Current day requests: {requests_info.get('current', 0)} / {requests_info.get('limit_day', 100)}")
            return True
        elif res.status_code in (401, 403):
            print(f"      ❌ Unauthorized ({res.status_code}). Invalid API_FOOTBALL_KEY.")
            return False
        else:
            print(f"      ⚠️ Status {res.status_code}: {res.text[:120]}")
            return False
    except Exception as e:
        print(f"      ❌ Network error connecting to API-Football: {e}")
        return False


def check_ntfy() -> bool:
    print("\n[3/3] Testing ntfy.sh alert channel...")
    topic = os.getenv("NTFY_TOPIC", "forward-ledger-alerts").strip()
    print(f"      Topic: https://ntfy.sh/{topic}")

    url = f"https://ntfy.sh/{topic}"
    try:
        res = requests.post(
            url,
            data="Forward Ledger API Verification Test: OK".encode("utf-8"),
            headers={"Title": "Forward Ledger Initialized", "Priority": "low", "Tags": "white_check_mark,soccer"},
            timeout=10
        )
        if res.status_code == 200:
            print("      ✅ Success! Published test heartbeat notification to ntfy.sh.")
            return True
        else:
            print(f"      ⚠️ Status {res.status_code}: {res.text[:120]}")
            return False
    except Exception as e:
        print(f"      ❌ Network error publishing to ntfy: {e}")
        return False


def main():
    print("=" * 60)
    print(" 🌐 FORWARD LEDGER API KEY & CONNECTION VERIFICATION")
    print("=" * 60)

    odds_ok = check_odds_api()
    foot_ok = check_api_football()
    ntfy_ok = check_ntfy()

    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(f" The Odds API:  {'✅ READY' if odds_ok else '❌ ACTION REQUIRED'}")
    print(f" API-Football:  {'✅ READY' if foot_ok else '⚠️ ACTION REQUIRED (Paste key into .env)'}")
    print(f" ntfy.sh:       {'✅ READY' if ntfy_ok else '❌ FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
