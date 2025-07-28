"""
Interactive Brokers Client Portal Web API
Comprehensive async client for IB's REST API with session management, 
portfolio tracking, market data, and order execution.
"""

from .core.session import SessionAdapter
from .core.http import IBAPIError

# Portfolio adapters
from .portfolio.accounts import AccountsAdapter, Account
from .portfolio.positions import PortfolioAdapter, Position, Summary, LedgerLine
from .portfolio.pnl import PnLAdapter, PnLRow, PnLByInstrument

# Market data adapters
from .market.market_data import MarketDataAdapter, Snapshot, Bar, Tick, OrderBook, BookEntry

# Trading adapters
from .trading.orders import (
    OrderAdapter, OrderRequest, OrderResult, WhatIfResult, LiveOrder,
    OrderSide, OrderType, TimeInForce, OrderStatus
)

# Scanner adapters
from .scanners.scanner import ScannerAdapter, ScanResult, ScanRequest

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class IBClient:
    """
    Unified Interactive Brokers client that provides access to all functionality.
    This is the main entry point for using the IB Client Portal Web API.
    """
    
    def __init__(self):
        # Initialize all adapters
        self.accounts = AccountsAdapter()
        self.portfolio = PortfolioAdapter()
        self.pnl = PnLAdapter()
        self.market_data = MarketDataAdapter()
        self.orders = OrderAdapter()
        self.scanner = ScannerAdapter()
        
        # Track primary account
        self._primary_account: Optional[str] = None
        
    async def get_primary_account(self) -> str:
        """Get the primary account ID (cached after first call)"""
        if self._primary_account is None:
            accounts = await self.accounts.get_accounts()
            if not accounts:
                raise IBAPIError("No accounts found")
            self._primary_account = accounts[0].id
            logger.info(f"Primary account set to: {self._primary_account}")
        
        return self._primary_account
    
    async def set_primary_account(self, account_id: str) -> None:
        """Set the primary account ID"""
        self._primary_account = account_id
        logger.info(f"Primary account set to: {account_id}")
    
    async def get_session_info(self) -> dict:
        """Get current session information"""
        return await self.accounts.get_session_info()
    
    async def logout(self) -> None:
        """Logout and cleanup all sessions"""
        adapters = [
            self.accounts, self.portfolio, self.pnl,
            self.market_data, self.orders, self.scanner
        ]
        
        for adapter in adapters:
            try:
                await adapter.logout()
            except Exception as e:
                logger.warning(f"Error during logout for {adapter.__class__.__name__}: {e}")

# Legacy support - maintain backwards compatibility with existing ib_adapter.py
from pydantic import BaseModel

class Contract(BaseModel):
    conid: int
    symbol: str
    exchange: str

async def search_contract(symbol: str, sec_type: str = "STK") -> Contract:
    """
    Legacy function for contract search.
    For new code, use the market data adapter or dedicated contract search.
    """
    # This would need to be implemented using the contract search endpoints
    # For now, we'll keep the existing logic from ib_adapter.py
    from .core.http import _get
    
    try:
        data = await _get("/iserver/secdef/search", symbol=symbol, secType=sec_type)
    except Exception as e:
        raise ValueError(f"API request failed for symbol {symbol}: {str(e)}")
    
    if not data:
        raise ValueError(f"No contract data found for symbol: {symbol}")
    
    # Handle case where data is not a list or contains no valid items
    if not isinstance(data, list):
        raise ValueError(f"Invalid API response format for symbol: {symbol}")
    
    # Filter out non-dict items and find best exchange
    valid_contracts = [x for x in data if isinstance(x, dict) and 'conid' in x]
    if not valid_contracts:
        raise ValueError(f"No valid contract data found for symbol: {symbol}")
        
    try:
        best = next((x for x in valid_contracts if x.get("exchange") in ("NASDAQ", "SMART")), None)
        if not best:
            best = valid_contracts[0]
            if "exchange" not in best:
                best["exchange"] = "UNKNOWN"
        
        # Ensure required fields exist
        if 'conid' not in best or 'symbol' not in best:
            raise ValueError(f"Incomplete contract data for symbol: {symbol}")
            
        return Contract(**best)
        
    except (TypeError, KeyError) as e:
        raise ValueError(f"Invalid contract data structure for symbol {symbol}: {str(e)}")

async def historical(conid: int, bar: str, period: str):
    """
    Legacy function for historical data.
    For new code, use market_data.history()
    """
    from .core.http import _get
    return await _get("/iserver/marketdata/history",
                      conid=conid, bar=bar, period=period, outsideRth="true")

# Main exports
__all__ = [
    # Main client
    "IBClient",
    
    # Core
    "SessionAdapter", "IBAPIError",
    
    # Portfolio
    "AccountsAdapter", "Account",
    "PortfolioAdapter", "Position", "Summary", "LedgerLine", 
    "PnLAdapter", "PnLRow", "PnLByInstrument",
    
    # Market data
    "MarketDataAdapter", "Snapshot", "Bar", "Tick", "OrderBook", "BookEntry",
    
    # Trading
    "OrderAdapter", "OrderRequest", "OrderResult", "WhatIfResult", "LiveOrder",
    "OrderSide", "OrderType", "TimeInForce", "OrderStatus",
    
    # Scanner
    "ScannerAdapter", "ScanResult", "ScanRequest",
    
    # Legacy support
    "Contract", "search_contract", "historical"
] 