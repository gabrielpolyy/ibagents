1 Moderate “Core + Satellite” — now with real stocks

Sleeve	% NAV	Examples	Why it earns a seat
Diversified ETF core	70 %	VWRA, VHYG, JEPI, IBTM, VUCP, ITPS, SGLD	Cheap beta, income, duration hedge
Quality-Dividend Stock sleeve	15 %	JNJ (3.2 % yld)  ￼, PG (2.5 %)  ￼, ES (4.6 %)  ￼, FDS (1 %)  ￼, CVX (4.8 %)  ￼	Raises cash-flow, keeps beta ≈ 0.6
“High-octane” micro-sleeve	5 %	IQQH (quality-growth ETF) or two conviction growth stocks you screen weekly	Adds upside; capped at 5 % so blow-ups can’t sink the ship
Dry-powder / cash	10 %	ECSH or IBKR’s EUR MMF	Fee buffer + rebalance ammo

Headline mix: Equity 70 % | Bonds 20 % | Diversifiers & cash 10 %.
Historic vol ≈ 10 %, max draw-down ~-19 % — still moderate, just not timid.

⸻

2 Why single stocks instead of more ETFs?

ETF-only	With a 15 % stock sleeve
Pros: ultra-diversified, fire-and-forget.	Pros: control tax lot harvesting, tilt sectors (e.g., utilities vs tech), pick higher-yielders, practise stock analysis.
Cons: no idiosyncratic alpha; all beta, all fees baked-in.	Cons: monitoring overhead, higher single-name risk — so we ring-fence it at 15 % and impose rules.


⸻

3 Rules the agent enforces on that 15 %
	1.	Screen weekly
S&P 500 member + ≥ 25 y dividend growth + payout < 70 % + β < 1 + Altman-Z > 3 + yield > 2 %.
	2.	Equal-weight at 3 % NAV each; never let one stock exceed 3.5 %.
	3.	Hard stop-loss –30 % from cost; if triggered it rolls into cash until next screen runs.
	4.	Trailing profit lock – when any holding is +50 % from cost, sell half and redistribute.
	5.	Liquidity guard – trade ≤ 10 % of 20-day ADV.

Because these are deterministic rules, your MCP agent can run them automatically and push out an order list with explanations.

⸻

4 “More spice, still safe” assets you could add later

Asset	How to size	What it buys you
Single corporate bond (e.g. BMW 3 ⅛ % 2028 EUR)	2 % slice inside the bond bucket	Lifts coupon without junk-bond volatility.
Covered-call on an index (e.g. SX5E call, Δ 0.25, 30 d)	Sell 1 contract per €30 k NAV	Extra income when markets drift sideways.
Structured note (capital-protected with equity kicker)	≤ 3 % NAV	Defined-outcome payoff; useful if core already equity-heavy.
Crypto ETP (BTCE)	1–2 % NAV max	Diversification—price path uncorrelated to stocks most of the time.

Each one just gets another sleeve entry in the agent’s allocation dict plus its own guard-rails (liquidity, issuer risk, stop-levels).

⸻

5 Putting it in code (snippet)

alloc = {
    # Core ETFs
    "VWRA": 0.35, "VHYG": 0.10, "JEPI": 0.05,
    "IBTM": 0.15, "VUCP": 0.05,
    "ITPS": 0.05, "SGLD": 0.05,

    # Stock sleeve (equal-weight)
    "JNJ": 0.03, "PG": 0.03, "ES": 0.03, "FDS": 0.03, "CVX": 0.03,

    # Optional high-octane ETF or stock pair
    "IQQH": 0.05
}

targets = target_shares(nav_eur, live_prices, alloc)
orders  = portfolio.diff_to_orders(targets)

Guard-rail checks (beta, stop-losses, sleeve caps) slot right before place_orders.

⸻

Bottom line
	•	Yes – keep the ETF core for cheap diversification and carve out a well-ruled 15 % stock sleeve (plus 5 % “spicy” sleeve if you want).
	•	Your risk stays moderate because position-size, stop-loss, and liquidity rules prevent any single idea from torpedoing the boat.
	•	The agent just needs two extra screening tasks and a few if-clauses in the risk gate—everything else is the same pipeline we drew up earlier.
