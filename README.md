# 🌐 Forward Ledger: International Soccer Predictive Model

An automated, forward-testing accountability ledger and predictive model for international soccer fixtures (FIFA World Cup, UEFA Nations League, Copa America, AFCON, AFC Asian Cup, International Friendlies).

Maintains strict probabilistic calibration, Closing Line Value (CLV), Brier Scores, and profit/loss accountability.

---

## 🔑 Required API Keys & Service Links

To run the automated forward ledger pipeline (locally or deployed to Vercel), sign up for and configure these services:

| Service | Purpose | Free Tier Limit | Direct Signup Link |
|:---|:---|:---|:---|
| **API-Football** | Fixture IDs, match schedules, live & final scores (`FT`) | **100 requests / day** | **[RapidAPI - API-Football](https://rapidapi.com/api-sports/api/api-football)** or **[API-Sports Dashboard](https://dashboard.api-football.com/)** |
| **The Odds API** | Captures bookmaker closing odds 10 min pre-kickoff | **500 requests / month** | **[The Odds API Get Access](https://the-odds-api.com/#get-access)** |
| **ntfy.sh** | Instant mobile/desktop push notifications for alerts and crons | **100% Free Pub/Sub** (No account strictly needed for public topics) | **[ntfy.sh](https://ntfy.sh/)** (or web app: **[ntfy.sh/app](https://ntfy.sh/app)**) |
| **GitHub** | Version control & remote git host for immutable `LEDGER.md` | Free | **[GitHub New Repo](https://github.com/new)** & **[GitHub Personal Access Tokens](https://github.com/settings/tokens)** |
| **Vercel** | Serverless hosting & automated Cron scheduling (`*/10 * * * *` and `0 */2 * * *`) | Free Tier | **[Vercel Dashboard](https://vercel.com/)** & **[Vercel Cron Docs](https://vercel.com/docs/cron-jobs)** |

---

## 🚀 Quick Setup & Verification

### 1. Configure Your `.env`
Open the `.env` file in the project root:
```ini
# 1. API-Football (Get from RapidAPI or dashboard.api-football.com)
API_FOOTBALL_KEY=your_key_here
API_FOOTBALL_PROVIDER=rapidapi

# 2. The Odds API (Pre-populated if already using the odds api)
ODDS_API_KEY=b13b5a5d59a4906ee1178421d0c7aa72

# 3. ntfy.sh Topic (Subscribe to this topic in https://ntfy.sh or the ntfy app)
NTFY_TOPIC=forward-ledger-soccer-alerts-9x2k

# 4. GitHub Credentials (For Vercel Crons to auto-commit LEDGER.md updates)
GITHUB_TOKEN=your_pat_here
GITHUB_REPO_OWNER=your-username
GITHUB_REPO_NAME=forward-ledger
```

### 2. Verify Your API Keys & Connections
Run the diagnostic script to test your keys and network reachability without leaking secrets:
```powershell
uv run python src/verify_apis.py
```

### 3. Check Ledger Calibration Statistics
To test the calibration math engine and verify historical metrics against `LEDGER.md`:
```powershell
uv run python -c "from src.calibration import evaluate_summary_metrics; print('Calibration engine ready!')"
```

---

## ⏱️ Vercel Automated Cron Architecture

The repository is pre-configured with two automated Vercel Cron jobs defined in `vercel.json`:

1. **Pre-Kickoff Active Selections (`/api/cron/pre-kickoff`)**
   - **Schedule:** `*/10 * * * *` (Every 10 minutes)
   - **Action:** Queries `API-Football` for matches scheduled within 24 hours. When matches are ~10 minutes from kickoff, queries `The Odds API` to lock the closing bookmaker odds, computes the model edge ($EV = (P_{model} \times Odds) - 1$), and queues them in the `PENDING ⏳` table in `LEDGER.md`.
   - **Alerts:** Dispatches `ntfy.sh` push notifications if odds lock fails or rate limits approach.

2. **Historical Grading Log (`/api/cron/grade-matches`)**
   - **Schedule:** `0 */2 * * *` (Every 2 hours)
   - **Action:** Queries `API-Football` for `FT` (Full Time) scores on all pending fixtures. Evaluates binary betting conditions (`HIT 🎯`, `MISS ❌`, `PUSH 🔄`), moves rows into Section 3 of `LEDGER.md`, and updates the calibration dashboard matrix.

---

## 📐 Mathematical Formulas

* **Expected Hits:**
  $$E = \sum_{i=1}^{n} p_i$$
  *(Sum of model predicted probabilities across all graded fixtures).*

* **Brier Score:**
  $$BS = \frac{1}{N} \sum_{t=1}^{N} (f_t - o_t)^2$$
  *(Forecast probability $f_t$ vs binary outcome $o_t$. A score $< 0.2000$ indicates elite probabilistic calibration).*

* **Expected Value (EV):**
  $$EV = (P_{model} \times Odds_{decimal}) - 1$$
