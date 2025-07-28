
decide on watchlist
- scanner by rules ...


Build feature matrix

each S-, C-

prices_live   = MarketData.bulk_quote(watchlist)      # IBKR snapshots
prices_hist   = MarketData.history(watchlist, "1d")   # historical bars
fundamentals  = fmp_api.get_fundamentals(watchlist)   # or similar
sentiment     = news_pipe.score_sentiment(watchlist)  # FinBERT, GDELT, etc.

Stick all of it into one table (one row per symbol, many columns of features).
That’s the feature matrix your signal engine works on.


Hey Gabi! 🙂
When the cash lands in your brand-new IBKR account the first objective is to grab the big, liquid building blocks that give you “instant diversification” while you’re still wiring the rest of the machine together. A sensible, low-friction sequence looks like this:

Step	Ticker (exchange)	Size vs. NAV	Why first?	Practical tip
0	ECSH (IBKR EUR MMF)	whatever isn’t deployed yet	Cash earns ~€STR minus 50 bp and is sweep-eligible; no trade needed – it auto-parks overnight.  ￼	Make sure “Sweep to MMF” is ON in Settings → Cash Management.
1	VWRA or its EUR-traded share class (VWRP)	35 %	One trade gives you ≈ 3,900 stocks in 50 countries – true one-click global beta.  ￼	Deal during the London continuous session (10:00–17:30 RO) and use a limit a few ticks inside the spread.
2	IBTM (iShares Core Global Agg Bond)	15 %	Locks in the duration hedge early and settles in EUR so no FX legs.  ￼	Again, use LSE or Xetra listing in EUR to avoid a USD conversion.
3	VHYG	10 %	Fills out the bond sleeve with higher coupons; still UCITS so it settles T+2 like any equity ETF.	
4	ITPS + SGLD	5 % + 5 %	The diversifiers (inflation linkers + physical gold) round off the core so equity draw-downs won’t wreck total NAV.	
5	JEPI (NYSE)	5 %	U.S. session fill; the covered-call overlay juicing monthly income starts working right away.	
6	IQQH or your two growth names	5 %	Now that the “sensible” ballast is set, you can let the micro-sleeve off the leash.	
7	Stock sleeve – JNJ, PG, ES, FDS, CVX	3 % each (15 % total)	Only after your first weekly screen has confirmed they still meet the β, Altman-Z, payout tests. Place bracket orders with the –30 % stop at the same time.	

Why this order?
	1.	Diversification ASAP – VWRA + IBTM alone already gives you a 50 %-of-NAV, two-asset portfolio with ~9 % vol and global reach, so any gap between trades does minimal harm.
	2.	Liquidity & spreads – The ETFs above all show penny-wide spreads on LSE/Xetra. Stocks you’ll equal-weight later have micro impact thanks to the ≤ 3 % position cap.
	3.	Settlement simplicity – Everything in steps 1-5 settles in EUR. JEPI (USD) is next so your first automatic FX conversion happens on a single line item you can verify.
	4.	Guard-rail integrity – By the time you touch the stock sleeve the stop-loss logic, ADV throttle and β filter have already fired in paper trading at least once.

Execution checklist for the first trading day
	1.	Fire up TWS/Gateway in paper mode and replay the order stack to be sure nothing breaches the liquidity rule (≤ 10 % ADV).
	2.	Switch to the live account, start with odd-lot sizing (e.g. 25 % of target quantities) to watch slippage in the real book, then scale to full weights over two or three sessions.
	3.	All orders limit-or-better, GTC for anything overnight. For the ETFs the limits can sit ±0.10 % of iNAV; they’ll fill fast.
	4.	Confirm the cash sweep the next morning: you should see an ECSH position and interest accrual in the Activity → Interest tab.
	5.	Run the weekly screen (β, Altman-Z, 25-year dividend growth, etc.) before you buy the five stocks; if any fail, replace them so the sleeve launches clean.

⸻

TL;DR

Buy the core ETF ballast first (VWRA, IBTM, etc.) so you’re diversified from minute one, then layer in income toys (JEPI), your growth kicker (IQQH) and only then the individual dividend-aristocrat stocks once the screen blesses them. That sequence keeps risk, FX, and operational complexity to an absolute minimum while the portfolio is still “getting on its feet.”

Ping me if you’d like a ready-to-run Python snippet that spits out the exact limit price ladder for tomorrow’s London open. Happy hunting, maestro! 🎯

