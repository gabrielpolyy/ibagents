# server.py
from fastmcp import FastMCP
from typing import Optional, List
import logging

from ib_client import (
    IBClient, search_contract, 
    OrderRequest, OrderSide, OrderType, TimeInForce
)


# Configure logging
logging.basicConfig(level=logging.INFO)

mcp = FastMCP(
    name="IBKR-Web-MCP",
    description="Interactive Brokers Client Portal Web API - Portfolio, Trading, Analysis & Market Intelligence"
)

# Global client instance
client = IBClient()


# ============================================================================
# REFERENCE & CONTRACT TOOLS
# ============================================================================

@mcp.tool(tags=["reference"])
async def find_contract(symbol: str, sec_type: str = "STK") -> dict:
    """Resolve symbol → IB contract with conid, exchange info."""
    try:
        contract = await search_contract(symbol, sec_type)
        return contract.model_dump()
    except ValueError as e:
        # Handle expected validation errors (invalid symbols, etc.)
        return {"error": f"Contract not found for {symbol}: {str(e)}"}
    except Exception as e:
        # Handle unexpected errors
        return {"error": f"Failed to find contract for {symbol}: {str(e)}"}

# ============================================================================
# PORTFOLIO & ACCOUNT TOOLS
# ============================================================================

@mcp.tool(tags=["portfolio"])
async def get_accounts() -> dict:
    """Get list of available IB accounts."""
    try:
        accounts = await client.accounts.get_accounts()
        return {
            "accounts": [acc.model_dump() for acc in accounts],
            "count": len(accounts)
        }
    except Exception as e:
        return {"error": f"Failed to get accounts: {str(e)}"}

@mcp.tool(tags=["portfolio"])
async def get_portfolio_summary(account_id: Optional[str] = None) -> dict:
    """Get portfolio summary: net liquidation, buying power, margin."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        summary = await client.portfolio.summary(account_id)
        return {
            "account_id": account_id,
            "summary": summary.model_dump()
        }
    except Exception as e:
        return {"error": f"Failed to get portfolio summary: {str(e)}"}

@mcp.tool(tags=["portfolio"])
async def get_positions(account_id: Optional[str] = None, max_positions: int = 50) -> dict:
    """Get current portfolio positions."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        positions = await client.portfolio.all_positions(account_id)
        
        # Limit results and convert to dict
        limited_positions = positions[:max_positions]
        return {
            "account_id": account_id,
            "positions": [pos.model_dump() for pos in limited_positions],
            "count": len(limited_positions),
            "total_positions": len(positions)
        }
    except Exception as e:
        return {"error": f"Failed to get positions: {str(e)}"}

@mcp.tool(tags=["portfolio"])
async def get_pnl() -> dict:
    """Get live P&L partitioned by asset class."""
    try:
        pnl_data = await client.pnl.get_partitioned_pnl()
        return {
            "pnl": [pnl.model_dump() for pnl in pnl_data],
            "count": len(pnl_data)
        }
    except Exception as e:
        return {"error": f"Failed to get P&L: {str(e)}"}

@mcp.tool(tags=["portfolio"])
async def get_ledger(account_id: Optional[str] = None) -> dict:
    """Get account ledger (cash, FX balances)."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        ledger = await client.portfolio.ledger(account_id)
        return {
            "account_id": account_id,
            "ledger": [line.model_dump() for line in ledger],
            "count": len(ledger)
        }
    except Exception as e:
        return {"error": f"Failed to get ledger: {str(e)}"}

# ============================================================================
# MARKET DATA TOOLS
# ============================================================================

@mcp.tool(tags=["market-data"])
async def get_market_snapshot(conid: int) -> dict:
    """Get real-time market data snapshot for a contract."""
    try:
        snapshot = await client.market_data.snapshot(conid)
        return {
            "conid": conid,
            "snapshot": snapshot.model_dump()
        }
    except Exception as e:
        return {"error": f"Failed to get market snapshot for conid {conid}: {str(e)}"}

@mcp.tool(tags=["market-data"])
async def get_history(conid: int, bar: str = "1d", period: str = "1m", outside_rth: bool = True) -> dict:
    """Fetch OHLCV historical bars."""
    try:
        bars = await client.market_data.history(conid, bar, period, outside_rth)
        return {
            "conid": conid,
            "bar": bar,
            "period": period,
            "bars": [bar.model_dump() for bar in bars],
            "count": len(bars)
        }
    except Exception as e:
        return {"error": f"Failed to get history for conid {conid}: {str(e)}"}

@mcp.tool(tags=["market-data"])
async def get_order_book(conid: int, exchange: Optional[str] = None) -> dict:
    """Get order book (depth of market) for a contract."""
    try:
        book = await client.market_data.book(conid, exchange)
        return {
            "conid": conid,
            "order_book": book.model_dump()
        }
    except Exception as e:
        return {"error": f"Failed to get order book for conid {conid}: {str(e)}"}

# ============================================================================
# TRADING TOOLS
# ============================================================================

@mcp.tool(tags=["trading"])
async def get_live_orders() -> dict:
    """Get all live orders across accounts."""
    try:
        orders = await client.orders.get_live_orders()
        return {
            "orders": [order.model_dump() for order in orders],
            "count": len(orders)
        }
    except Exception as e:
        return {"error": f"Failed to get live orders: {str(e)}"}

@mcp.tool(tags=["trading"])
async def whatif_order(conid: int, side: str, quantity: float, order_type: str = "MKT", 
                      price: Optional[float] = None, account_id: Optional[str] = None) -> dict:
    """Get what-if analysis for an order (risk preview)."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        # Convert string enums
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        order_type_enum = OrderType(order_type.upper())
        
        order_request = OrderRequest(
            conid=conid,
            orderType=order_type_enum,
            side=order_side,
            quantity=quantity,
            price=price,
            tif=TimeInForce.DAY
        )
        
        whatif_result = await client.orders.whatif(account_id, order_request)
        return {
            "account_id": account_id,
            "order_request": {
                "conid": conid,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "price": price
            },
            "whatif_result": whatif_result.model_dump()
        }
    except Exception as e:
        return {"error": f"Failed to get what-if analysis: {str(e)}"}

@mcp.tool(tags=["trading"])
async def place_order(conid: int, side: str, quantity: float, order_type: str = "MKT", 
                     price: Optional[float] = None, account_id: Optional[str] = None, 
                     skip_whatif: bool = False) -> dict:
    """Place an order (with optional what-if preview first)."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        # Convert string enums
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        order_type_enum = OrderType(order_type.upper())
        
        order_request = OrderRequest(
            conid=conid,
            orderType=order_type_enum,
            side=order_side,
            quantity=quantity,
            price=price,
            tif=TimeInForce.DAY
        )
        
        result = await client.orders.place_order(account_id, order_request, skip_whatif)
        return {
            "account_id": account_id,
            "order_request": {
                "conid": conid,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "price": price
            },
            "result": result.model_dump()
        }
    except Exception as e:
        return {"error": f"Failed to place order: {str(e)}"}

@mcp.tool(tags=["trading"])
async def cancel_order(order_id: str, account_id: Optional[str] = None) -> dict:
    """Cancel an order."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        result = await client.orders.cancel_order(account_id, order_id)
        return {
            "account_id": account_id,
            "order_id": order_id,
            "result": result
        }
    except Exception as e:
        return {"error": f"Failed to cancel order {order_id}: {str(e)}"}

# ============================================================================
# SCANNER TOOLS
# ============================================================================

@mcp.tool(tags=["scanner"])
async def scan_top_gainers(max_results: int = 20, location: str = "STK.US") -> dict:
    """Get top percentage gainers."""
    try:
        results = await client.scanner.top_gainers(max_results, location)
        return {
            "scan_type": "top_gainers",
            "location": location,
            "results": [result.model_dump() for result in results],
            "count": len(results)
        }
    except Exception as e:
        return {"error": f"Failed to get top gainers: {str(e)}"}

@mcp.tool(tags=["scanner"])
async def scan_top_losers(max_results: int = 20, location: str = "STK.US") -> dict:
    """Get top percentage losers."""
    try:
        results = await client.scanner.top_losers(max_results, location)
        return {
            "scan_type": "top_losers",
            "location": location,
            "results": [result.model_dump() for result in results],
            "count": len(results)
        }
    except Exception as e:
        return {"error": f"Failed to get top losers: {str(e)}"}

@mcp.tool(tags=["scanner"])
async def scan_most_active(max_results: int = 20, location: str = "STK.US") -> dict:
    """Get most active stocks by volume."""
    try:
        results = await client.scanner.most_active(max_results, location)
        return {
            "scan_type": "most_active",
            "location": location,
            "results": [result.model_dump() for result in results],
            "count": len(results)
        }
    except Exception as e:
        return {"error": f"Failed to get most active: {str(e)}"}

@mcp.tool(tags=["scanner"])
async def custom_scan(scan_code: str, max_results: int = 20, location: str = "STK.US") -> dict:
    """Run custom market scan with specified scan code."""
    try:
        results = await client.scanner.custom_scan(scan_code, None, max_results, location)
        return {
            "scan_type": "custom",
            "scan_code": scan_code,
            "location": location,
            "results": [result.model_dump() for result in results],
            "count": len(results)
        }
    except Exception as e:
        return {"error": f"Failed to run custom scan {scan_code}: {str(e)}"}

@mcp.tool(tags=["scanner"])
async def get_scan_codes() -> dict:
    """Get available scanner codes."""
    try:
        scan_codes = await client.scanner.get_available_scan_codes()
        return {
            "scan_codes": scan_codes,
            "count": len(scan_codes)
        }
    except Exception as e:
        return {"error": f"Failed to get scan codes: {str(e)}"}

# ============================================================================
# ANALYSIS TOOLS
# ============================================================================

@mcp.tool(tags=["analysis"])
async def portfolio_health_check(account_id: Optional[str] = None) -> dict:
    """Complete portfolio health analysis."""
    try:
        if not account_id:
            account_id = await client.get_primary_account()
        
        # Get portfolio summary
        summary = await client.portfolio.summary(account_id)
        
        # Get positions
        positions = await client.portfolio.all_positions(account_id)
        
        # Get P&L
        pnl_data = await client.pnl.get_partitioned_pnl()
        
        # Calculate basic metrics
        total_positions = len(positions)
        total_value = summary.netliquidation or 0
        buying_power = summary.buyingpower or 0
        available_funds = summary.availablefunds or 0
        
        return {
            "account_id": account_id,
            "health_metrics": {
                "total_value": float(total_value),
                "buying_power": float(buying_power),
                "available_funds": float(available_funds),
                "total_positions": total_positions,
                "cash_percentage": float(available_funds / total_value * 100) if total_value > 0 else 0
            },
            "summary": summary.model_dump(),
            "position_count": total_positions,
            "pnl_summary": [pnl.model_dump() for pnl in pnl_data] if pnl_data else []
        }
    except Exception as e:
        return {"error": f"Failed to perform portfolio health check: {str(e)}"}

@mcp.tool(tags=["analysis"])
async def stock_analysis(symbol: str, target_quantity: int = 100) -> dict:
    """Complete stock analysis combining market data, portfolio context, and risk assessment."""
    try:
        # Find contract
        contract = await search_contract(symbol)
        
        # Get market data
        snapshot = await client.market_data.snapshot(contract.conid)
        
        # Get account info for context
        account_id = await client.get_primary_account()
        summary = await client.portfolio.summary(account_id)
        
        # Calculate position value and percentage
        current_price = snapshot.last_price or snapshot.bid
        position_value = float(current_price * target_quantity) if current_price else 0
        portfolio_value = float(summary.netliquidation or 0)
        position_percentage = (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
        
        return {
            "symbol": symbol,
            "contract": contract.model_dump(),
            "market_data": {
                "current_price": float(current_price) if current_price else None,
                "bid_ask_spread": float(snapshot.ask - snapshot.bid) if (snapshot.ask and snapshot.bid) else None,
                "volume": snapshot.volume,
                "change_percent": float(snapshot.change_percent) if snapshot.change_percent else None,
                "snapshot": snapshot.model_dump()
            },
            "position_analysis": {
                "target_quantity": target_quantity,
                "position_value": position_value,
                "portfolio_percentage": position_percentage,
                "affordable": position_value <= float(summary.availablefunds or 0)
            },
            "portfolio_context": {
                "total_value": float(summary.netliquidation or 0),
                "available_funds": float(summary.availablefunds or 0),
                "buying_power": float(summary.buyingpower or 0)
            }
        }
    except Exception as e:
        return {"error": f"Failed to analyze stock {symbol}: {str(e)}"}

if __name__ == "__main__":
    # runs uvicorn on :8001 with MCP endpoints
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001) 