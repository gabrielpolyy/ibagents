Hey Gabi!
Below is a plain-English decoding of every tag that showed up in the JSON you pasted. I kept the phrasing tight but sufficiently technical, so you can map each field straight to the margin logic IBKR (Interactive Brokers) uses.

⸻

How the names are built
	•	Core tag – e.g. NetLiquidation
	•	Segment suffix (optional) –
	•	-S  securities segment (stocks, stock-options, bonds)
	•	-C  commodities/futures segment
	•	-F  FX/CFD segment
When no suffix is present the figure is “whole-portfolio”.

⸻

Account identity / status

Tag	What it means
accountcode	Your IBKR account number (here U20513451).
accountready	"true" once the server has delivered a complete snapshot; "false" during login or resets.
accounttype	Regulatory account classification. INDIVIDUAL, IRA, JOINT, etc.
segmenttitle-s	The legal/reg-segment this value belongs to – e.g. CFD or STK.
tradingtype-s	Trading regime of the segment (STKCASH, MARGIN, PORTFOLIO_MARGIN, …).


⸻

Cash that has accrued but is not yet settled

Tag	Explanation
accruedcash, accrueddividend	Interest on idle cash and dividends declared but not yet paid.
incentivecoupons	Unused “commission rebates” or zero-commission coupons that IBKR occasionally grants.
depositoncredithold	Funds you wired-in that are still in bank-clearing limbo; they raise Net Liq but are not yet usable.


⸻

Liquid cash & buying power

Tag	Explanation
totalcashvalue	Cash balance converted into the base currency.
availablefunds	Equity-With-Loan Value – Initial Margin – the cash you could immediately deploy in new trades.
buyingpower	IBKR multiplies Available Funds by 4 (Reg-T day) or 2 (overnight) for equities, or by portfolio-margin scalars, to tell you the notional you can still buy.
billable	Amount currently accruing interest expense (negative cash) or income (positive).
totaldebitcardpendingcharges	If you have an IBKR debit card, authorizations that have not posted yet.


⸻

Core equity / margin math

Tag	Formula & intuition
equitywithloanvalue (ELV)	Positions ± cash after deducting any stock-borrow debit. It is IBKR’s definition of “equity” for margin.
grosspositionvalue (GPV)	Absolute market value of all long plus short positions – ignores cash.
netliquidation (NLV)	GPV + cash; the mark-to-market value you would have if everything closed now.
initmarginreq	Initial margin currently demanded.
maintmarginreq	Maintenance margin currently demanded.
excessliquidity	ELV – Maintenance Margin; the “distance” to a margin call.
availablefunds	ELV – Initial Margin; distance to opening a new trade.
cushion	Excess Liquidity / NLV; shown as 0–1 (or %). A quick risk gauge; IBKR sends margin-cushion alerts below ~10 %.
leverage-s	GPV / NLV in the securities segment – 1 = no leverage; 2 = 50 % margin, etc.
fullinitmarginreq / fullmaintmarginreq	The margin that will apply after all intraday credits wear off (i.e., overnight).
fullavailablefunds / fullexcessliquidity	The same “distance” metrics but using the full (overnight) requirements.
lookaheadinit/maintmarginreq, lookaheadavailablefunds, lookaheadexcessliquidity, lookaheadnextchange	Pro-forma values at the next scheduled margin time-slice (IBKR re-prices roughly every 3 min).
postexpirationexcess / postexpirationmargin	Margin picture immediately after the next derivative expiration batch.
netliquidationuncertainty	A stress-tested delta IBKR adds when quotes are moving too fast or are NBBO-stale.
nlvandmargininreview	Flag (true/false) telling you corporate-actions or unusual option events are under manual review, freezing some margin.


⸻

Haircuts, regulatory add-ons & special items

Tag	Meaning
indianstockhaircut	Extra haircut applied only to IB-IN (India-resident) accounts trading Indian equities; it inflates margin the way Reg T inflates U.S. equities.
guarantee	Cash or Treasury collateral you pledged to back futures/FX; reduces margin but is tracked separately.
pasharesvalue	Value of employee “personal-account” shares if you trade under an adviser umbrella that segregates PA holdings.
physicalcertificatevalue	Face value of any paper stock certificates held with IBKR for safekeeping.
incentivecoupons	(see above)
columnprio-s	IBKR’s internal presentation order when showing multiple segments – not financially relevant.
highestseverity	0 = all good; 1 = warning; 2 = violation. Used for margin alerts across segments.


⸻

“Look-ahead” / risk-control helpers

These tags are IBKR’s way of telling algo-traders “if nothing changes, at the next margin recalculation your A/F/E may jump to X” – useful when you submit working orders that will settle intraday.

⸻

Odds-and-ends

Tag	Purpose
depositoncredithold	(see earlier)
incentivecoupons	(see earlier)
totaldebitcardpendingcharges	(see earlier)
physicalcertificatevalue	(see earlier)
columnprio-s	(see earlier)


⸻

Putting it all together
	•	If you watch only three lines in TWS/IB Gateway: Excess Liquidity, Available Funds, and Cushion. Those tell you “can I open more?” and “am I close to a call?” in one glance.
	•	-S, -C, -F versions let you see which segment is tight.
	•	Haircuts like IndianStockHaircut rarely matter in EU-based INDIVIDUAL accounts, but they show up as zero so that code consuming the API doesn’t crash.
