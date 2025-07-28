# IBKR-Web-MCP Application Context

## Overview

IBKR-Web-MCP is a comprehensive trading and portfolio management application that provides AI-powered tools for interacting with Interactive Brokers (IB) Client Portal Web API. The application serves as a bridge between AI assistants and IB's trading platform through the Model Context Protocol (MCP), enabling intelligent portfolio management, market analysis, and automated trading operations.

## Core Architecture

### MCP Server (`server.py`)
- **FastMCP-based server** running on port 8000 that exposes IB trading functionality as AI tools
- **RESTful API endpoints** for tool discovery (`/tools/list`) and execution (`/tools/call`)
- **Comprehensive tool categorization** across 6 main functional areas
- **Error handling and validation** for all trading operations

### IB Client Library (`ib_client/`)
A modular Python client library providing:
- **Portfolio Management**: Account summaries, positions, P&L tracking, ledger operations
- **Market Data**: Real-time snapshots, historical OHLCV data, order book depth
- **Trading Operations**: Order placement, cancellation, what-if analysis, live order monitoring
- **Market Scanning**: Top gainers/losers, most active stocks, custom scanner codes
- **Core Infrastructure**: Contract resolution, authentication, API communication

### Tool Discovery (`mcp_tools.py`)
- **Diagnostic utility** for exploring available MCP tools
- **Categorized tool listing** with descriptions and usage examples
- **Development aid** for understanding API capabilities

## Tool Categories

### 📊 Reference & Contract Tools
- Contract resolution and symbol lookup
- Exchange information and trading parameters

### 💼 Portfolio & Account Tools  
- Multi-account support and account selection
- Real-time portfolio summaries and net liquidation values
- Position tracking and performance monitoring
- Cash and FX balance management

### 📈 Market Data Tools
- Real-time market snapshots with bid/ask/last pricing
- Historical data retrieval with customizable timeframes
- Level 2 order book data for market depth analysis

### 📋 Trading Tools
- Pre-trade risk analysis with what-if scenarios
- Order placement with multiple order types (Market, Limit, Stop)
- Live order monitoring and management
- Order cancellation and modification

### 🔍 Scanner Tools
- Market screening for top gainers, losers, and most active stocks
- Custom scanner code execution
- Configurable result limits and geographic filters

### 📊 Analysis Tools
- Comprehensive portfolio health assessments
- Individual stock analysis with risk metrics
- Portfolio allocation and cash management insights

## Key Features

### AI-First Design
- **Tool-based architecture** enabling AI assistants to perform complex trading operations
- **Natural language interfaces** for portfolio management and market analysis
- **Contextual responses** with relevant financial data and risk assessments

### Risk Management
- **What-if analysis** before order execution
- **Portfolio health monitoring** with real-time metrics
- **Position sizing calculations** relative to available funds

### Real-Time Integration
- **Live market data** streaming from IB Client Portal
- **Real-time P&L tracking** across asset classes
- **Dynamic order book** and market depth information

### Multi-Account Support
- **Account discovery** and automatic primary account selection
- **Cross-account** order and position management
- **Account-specific** risk and performance analytics

## Technical Requirements

- **Interactive Brokers Client Portal Gateway** (port 8765) for market connectivity
- **Python 3.8+** with async/await support
- **FastMCP framework** for tool server implementation
- **Authenticated IB account** with API trading permissions

## Use Cases

- **Algorithmic Trading**: AI-driven order placement and portfolio rebalancing
- **Risk Management**: Automated portfolio health monitoring and alerts
- **Market Research**: AI-powered stock screening and analysis
- **Portfolio Optimization**: Intelligent asset allocation and position sizing
- **Trading Education**: Interactive exploration of market data and trading concepts

┌── START (cron trigger @14:00) ───────────────────────────────┐
│ 1. Market & Alt-Data Ingest                                  │
│ 2. Signal Computation  ─┐                                    │
│ 3. Portfolio Snapshot   │──► 4. Target Vector Optimisation ──┤
│                         └──► 5. News & Sentiment Overlay     │
│ 6. Risk & Compliance Gate                                    │
│ 7. What-If Simulation                                        │
│ 8. Order List Generation & (optional) Auto-Submit            │
│ 9. Decision Journal Append                                   │
└───────────────────────────────────────────────────────────────┘


Hey Gabi! Below is a pragmatic “operating manual” for running your IBKR-Web-MCP agent every day, end-to-end—from cron-kickoff to audit-grade logging. Steal whatever chunks fit your workflow.

⸻

0 · Clock & Environment

Location	Local clock	Typical U.S. cash-session (NYSE / NASDAQ)	Comment
Bucharest	UTC +3	16:30 → 23:00 EEST	You’ll pre-compute signals during your afternoon coffee and still have a few hours of sunlight.

All times below are Bucharest (EEST). Adjust to target exchanges as needed.

⸻

1 · Daily Scheduler

Option A — pure cron

Put the one-liner agent call in /etc/cron.d/alpha_agent:

# ┌ minute (0-59)
# │ ┌ hour (0-23, EEST)
# │ │  ┌ dom
# │ │  │  ┌ month
# │ │  │  │  ┌ dow (0-Sun)
# │ │  │  │  │
  00  14  *  *  1-5  gabi   /opt/alpha/bin/run_agent.sh >> /var/log/alpha_agent.log 2>&1

Runs 14:00 daily (≈ 08:00 NY).

Option B — Airflow / Prefect / Dagster

Use an orchestrator if you want retries, backfills, alerting, and parameterized back-tests. Treat each bold heading in §2 as a task.

⸻

2 · Pipeline Stages (high-level DAG)

┌── START (cron trigger @14:00) ───────────────────────────────┐
│ 1. Market & Alt-Data Ingest                                  │
│ 2. Signal Computation  ─┐                                    │
│ 3. Portfolio Snapshot   │──► 4. Target Vector Optimisation ──┤
│                         └──► 5. News & Sentiment Overlay     │
│ 6. Risk & Compliance Gate                                    │
│ 7. What-If Simulation                                        │
│ 8. Order List Generation & (optional) Auto-Submit            │
│ 9. Decision Journal Append                                   │
└───────────────────────────────────────────────────────────────┘

Below is the how for each node.

⸻

1. Market & Alt-Data Ingest  (14:00-14:05)

Feed	Tool / API	Granularity	Latency OK?
IBKR snapshots	MarketData.bulk_quote()	live	seconds
Historical bars	MarketData.history()	1 m-1 d	seconds
Fundamentals	EOD fundamental dump (e.g. Financial Modeling Prep)	1× day	minutes
News sentiment	GDELT, RavenPack, or open-source FinBERT run on RSS	minute	minutes

Write all raw payloads to /data/staging/YYYY-MM-DD/… then emit a parquet “feature matrix” (one row per symbol) into /data/features/.

⸻

2. Signal Computation  (14:05-14:15)
	•	Technical block:
	•	moving averages crossover, ATR breakout, RSI extremes, etc.—vectorised in numpy/pandas or TA-Lib bindings.
	•	Fundamental block:
	•	Piotroski F-Score, forward P/E deviation vs sector, YoY revenue delta > 15 %, etc.
	•	Sentiment block:
	•	z-score of headline polarity past 24 h, Reddit r/wallstreetbets post spike, Twitter volume anomaly.

Normalize each block to -1 … +1, blend with learned weights, output alpha_score.

⸻

3. Portfolio Snapshot  (14:05-14:06, parallel)

from ib_client import Portfolio
current_pos = Portfolio.snapshot()   # JSON: {symbol: {qty, market_value, …}}

Persist to /data/positions/YYYY-MM-DD.json.

⸻

4. Target Vector Optimisation  (14:15-14:18)

from optimiser import mean_variance_cvar
targets = mean_variance_cvar(
    universe      = feature_df.symbol,
    alpha_scores  = feature_df.alpha_score,
    risk_model    = 'shrunk_cov',
    max_gross     = 1.2,
    max_single    = 0.12,
    cash_buffer   = 0.05)

Returns {symbol: target_weight} plus risk metrics.

⸻

5. News & Sentiment Overlay  (14:18-14:20)

Hard overrides—examples:

if sentiment["NVDA"] < -2.5:  targets.pop("NVDA", None)
if breaking_news_contains("FDA ban") and "PM" in targets: targets["PM"] = 0


⸻

6. Risk & Compliance Gate  (14:20-14:22)
	•	Run risk.check_constraints(current_pos, targets):
	•	Δ Gross Exposure, VAR < threshold
	•	Concentration < 12 %
	•	Liquidity: shares ≤ 10 % avg-daily-vol
	•	If fail → export “recommendation only” report; abort execution path.

⸻

7. What-If Simulation  (14:22-14:25)

For each candidate order produced by portfolio.diff_to_orders(targets):

sim = TradingTools.what_if(order)
if sim.maintenance_margin_exceeded:
    flag, remove, or size-down by 20 %


⸻

8. Order List Generation & (optionally) Auto-Submit  (14:25)

orders = portfolio.diff_to_orders(targets, force_even_lots=True)
if AUTO_MODE:
    TradingTools.place_orders(orders)
else:
    save_json("/reports/order_ticket_2025-06-09.json", orders)
    send_slack("Orders ready for review: ...")


⸻

9. Decision Journal Append  (14:25-14:26)

Append a row to /data/decision_log/ (parquet + sha256 file links):

journal.log(
    timestamp        = now_utc,
    hash_targets     = sha256(targets),
    hash_orders      = sha256(orders),
    top_drivers      = feature_df.nlargest(5, 'alpha_score')[['symbol','alpha_score']],
    expected_return  = optimiser.ex_ante_return,
    expected_vol     = optimiser.ex_ante_vol,
    constraints_ok   = True)


⸻

3 · Monitoring & Alerting
	•	Prometheus + Grafana ➜ CPU, latency, failed tasks.
	•	Slack / Email ➜
	•	14:30 ping: “Orders queued / executed.”
	•	Exception notifier: risk-gate fail, IBKR reject, cron exit≠0.

⸻

4 · Back-Testing & Continuous Calibration
	1.	Schedule a weekly Airflow DAG to replay the entire pipeline on the last 6 months of data.
	2.	Write Sharpe, max-drawdown, turnover into /metrics/rolling_backtest.csv.
	3.	Automatically bump signal weights if the multi-objective optimiser says so (optional but spicy).

⸻

5 · Security & Ops Checklist
	•	Store IBKR gateway key in HashiCorp Vault or AWS Secrets Manager.
	•	Rotate API tokens monthly; pipeline should read them at runtime.
	•	Use a dedicated IBKR paper account for staging → promote configs to live after X green days.
	•	Version-control everything (infra code, signal notebooks, configs) in Git; tag Y-m-d releases.

⸻

TL;DR
	1.	Kick off at 14:00 EEST with cron (or orchestrator).
	2.	Ingest → score → optimise → risk-gate in ~25 min.
	3.	Produce target-vector + atomic order list, optionally auto-submit via IBKR MCP.
	4.	Log every artefact (raw data, orders, reasons) for traceability.
	5.	Alert on success/failure; rerun intraday if you crave higher frequency.

Stick to that skeleton and you’ll have a daily machine that thinks, acts, and—crucially—remembers why.

Ping me any time you want to zoom in on a specific stage, add an NLP headline classifier, or wire up federated back-testing. Have fun building, maestro! 🛠️


Sure thing, Gabi—let’s zoom in on that “Market & Alt-Data Ingest” block and translate it from engineer-speak to plain English:

Feed	What you’re really grabbing	Why you need it	How fresh it is
IBKR snapshots	The latest bid/ask price, last trade, volume, etc. for every symbol you care about.	Tells you “what’s happening this very second” so you can size orders, set good limit prices, and spot sudden jumps.	Arrives in seconds.
Historical bars	Candlestick data (open, high, low, close, volume) over the last day, week, month—whatever timeframe you ask for.	Fuels technical indicators like moving averages, RSI, breakouts, etc. You need a history to judge whether today’s move is unusual.	Also seconds (it’s just downloading the past).
Fundamentals	End-of-day snapshots of balance-sheet stuff: P/E, revenue growth, EPS surprises, debt ratios, …	Lets you know if the company is cheap, growing, over-leveraged, etc. Good for fundamental alpha models and risk checks.	Updated once per day after markets close—minutes of delay is fine because fundamentals don’t change intraday.
News sentiment	Headlines + social chatter run through an NLP model that scores each symbol from very negative (-) to very positive (+).	Catches narrative shifts—e.g., “FDA rejection” or “earnings beat”—that price data alone hasn’t digested yet.	A few minutes behind real time (RSS / API poll + model run).


⸻

So… what does “ingest” actually look like?
	1.	Decide on your watch-list.
	•	Might be the entire S&P 500, a curated factor universe, or simply “whatever I hold + today’s top movers.”
	2.	Pull the four feeds above in parallel.

prices_live   = MarketData.bulk_quote(watchlist)      # IBKR snapshots
prices_hist   = MarketData.history(watchlist, "1d")   # historical bars
fundamentals  = fmp_api.get_fundamentals(watchlist)   # or similar
sentiment     = news_pipe.score_sentiment(watchlist)  # FinBERT, GDELT, etc.


	3.	Stick all of it into one table (one row per symbol, many columns of features).
That’s the feature matrix your signal engine works on.

⸻

Macro vs. Micro vs. Top Movers—how to sequence?
	1.	Macro sweep (index + rates + commodities).
	•	Pull 10-year Treasury yield, EUR/USD, crude oil, VIX, SPY, QQQ.
	•	Build global signals like “risk-on vs risk-off,” “yield-curve steepening,” etc.
	•	These become environment features—e.g., risk-off penalty or sector tilts.
	2.	Micro fundamentals & sentiment (per-symbol).
	•	Stick to your universe; evaluate each stock’s value/growth quality + today’s news tone.
	3.	Top-mover scan (optional fast-lane).
	•	Use IBKR Scanner Tools: “TOP%GAIN” / “TOP%LOSER” / “HOT_BY_VOLUME.”
	•	Any symbol that moves, say, > 5 % on heavy volume but isn’t already in your watch-list gets temporarily added for today’s run.
	•	This stops you missing sudden opportunities in off-radar names.

⸻

A 3-minute mental picture

14:00 — Pull macro gauges (10-year, VIX, index futures)
14:01 — Pull live quotes + 30-day candles for ~700 symbols
14:02 — Pull yesterday’s fundamentals dump (CSV / API)
14:03 — Pull news headlines last 24 h → run sentiment model
14:04 — Merge → big DataFrame → onward to “Signal Computation”

That’s really it: four data buckets, one merge, done. The rest of the pipeline (technicals, fundamentals, sentiment scoring, optimisation) works off that unified snapshot.

Does that clear up what you’re ingesting and why? Let me know if you want code snippets for a specific feed or deeper talk on, say, the sentiment NLP set-up.

