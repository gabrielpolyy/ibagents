from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
import logging

from ..core.session import SessionAdapter
from ..core.http import _get, _post

logger = logging.getLogger(__name__)

class Tick(BaseModel):
    """Individual tick data"""
    field: str
    value: Optional[str] = None
    price: Optional[Decimal] = None
    size: Optional[int] = None
    time: Optional[str] = None

class Snapshot(BaseModel):
    """Market data snapshot"""
    conid: int
    symbol: Optional[str] = None
    last_price: Optional[Decimal] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    volume: Optional[int] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    open: Optional[Decimal] = None
    close: Optional[Decimal] = None
    market_value: Optional[str] = None
    server_id: Optional[str] = None

class Bar(BaseModel):
    """Historical bar data"""
    t: int  # timestamp
    o: Optional[Decimal] = None  # open
    h: Optional[Decimal] = None  # high
    l: Optional[Decimal] = None  # low
    c: Optional[Decimal] = None  # close
    v: Optional[Decimal] = None  # volume (as decimal to handle fractional shares)

class BookEntry(BaseModel):
    """Order book entry"""
    price: Optional[Decimal] = None
    size: Optional[int] = None
    exchange: Optional[str] = None

class OrderBook(BaseModel):
    """Order book (depth of market)"""
    conid: int
    bids: List[BookEntry] = []
    asks: List[BookEntry] = []
    timestamp: Optional[int] = None

class MarketDataAdapter(SessionAdapter):
    """Adapter for market data - snapshots and historical data"""
    
    def __init__(self):
        super().__init__()
    
    async def snapshot(self, conid: int, fields: Optional[List[str]] = None) -> Snapshot:
        """Get real-time market data snapshot"""
        await self._ensure_live()
        
        try:
            params = {"conids": str(conid)}
            if fields:
                params["fields"] = ",".join(fields)
            
            data = await _get("/iserver/marketdata/snapshot", **params)
            logger.debug(f"Snapshot data for conid {conid}: {data}")
            
            if not data or not isinstance(data, list) or len(data) == 0:
                raise ValueError(f"No snapshot data returned for conid {conid}")
            
            # Parse the snapshot data
            snapshot_data = data[0]  # First item in the list
            
            # Extract common fields with various possible names
            snapshot = Snapshot(
                conid=conid,
                symbol=snapshot_data.get("symbol"),
                last_price=self._parse_decimal(snapshot_data.get("31", snapshot_data.get("last"))),
                bid=self._parse_decimal(snapshot_data.get("84", snapshot_data.get("bid"))),
                ask=self._parse_decimal(snapshot_data.get("86", snapshot_data.get("ask"))),
                bid_size=self._parse_int(snapshot_data.get("88", snapshot_data.get("bidSize"))),
                ask_size=self._parse_int(snapshot_data.get("85", snapshot_data.get("askSize"))),
                volume=self._parse_int(snapshot_data.get("87", snapshot_data.get("volume"))),
                change=self._parse_decimal(snapshot_data.get("82", snapshot_data.get("change"))),
                change_percent=self._parse_decimal(snapshot_data.get("83", snapshot_data.get("changePercent"))),
                high=self._parse_decimal(snapshot_data.get("70", snapshot_data.get("high"))),
                low=self._parse_decimal(snapshot_data.get("71", snapshot_data.get("low"))),
                close=self._parse_decimal(snapshot_data.get("77", snapshot_data.get("close"))),
                market_value=snapshot_data.get("market_value"),
                server_id=snapshot_data.get("server_id")
            )
            
            logger.info(f"Got snapshot for conid {conid}: last={snapshot.last_price}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get snapshot for conid {conid}: {e}")
            raise
    
    async def history(self, conid: int, bar: str = "1d", period: str = "1m", outside_rth: bool = True) -> List[Bar]:
        """Get historical bar data"""
        await self._ensure_live()
        
        try:
            data = await _get("/iserver/marketdata/history",
                            conid=conid, 
                            bar=bar, 
                            period=period, 
                            outsideRth=str(outside_rth).lower())
            
            logger.debug(f"Historical data for conid {conid}: {data}")
            
            bars = []
            if isinstance(data, dict) and "data" in data:
                for bar_data in data["data"]:
                    try:
                        bar = Bar(**bar_data)
                        bars.append(bar)
                    except Exception as e:
                        logger.warning(f"Failed to parse bar data: {bar_data}, error: {e}")
            
            logger.info(f"Got {len(bars)} bars for conid {conid}")
            return bars
            
        except Exception as e:
            logger.error(f"Failed to get history for conid {conid}: {e}")
            raise
    
    async def book(self, conid: int, exchange: Optional[str] = None) -> OrderBook:
        """Get order book (depth of market) for a contract"""
        await self._ensure_live()
        
        try:
            params = {"conid": conid}
            if exchange:
                params["exchange"] = exchange
                
            data = await _get("/iserver/marketdata/book", **params)
            logger.debug(f"Order book data for conid {conid}: {data}")
            
            # Parse the order book data
            bids = []
            asks = []
            
            if isinstance(data, dict):
                # Parse bids
                if "bids" in data:
                    for bid_data in data["bids"]:
                        try:
                            bid = BookEntry(
                                price=self._parse_decimal(bid_data.get("price")),
                                size=self._parse_int(bid_data.get("size")),
                                exchange=bid_data.get("exchange")
                            )
                            bids.append(bid)
                        except Exception as e:
                            logger.warning(f"Failed to parse bid data: {bid_data}, error: {e}")
                
                # Parse asks
                if "asks" in data:
                    for ask_data in data["asks"]:
                        try:
                            ask = BookEntry(
                                price=self._parse_decimal(ask_data.get("price")),
                                size=self._parse_int(ask_data.get("size")),
                                exchange=ask_data.get("exchange")
                            )
                            asks.append(ask)
                        except Exception as e:
                            logger.warning(f"Failed to parse ask data: {ask_data}, error: {e}")
            
            order_book = OrderBook(
                conid=conid,
                bids=bids,
                asks=asks,
                timestamp=data.get("timestamp") if isinstance(data, dict) else None
            )
            
            logger.info(f"Got order book for conid {conid}: {len(bids)} bids, {len(asks)} asks")
            return order_book
            
        except Exception as e:
            logger.error(f"Failed to get order book for conid {conid}: {e}")
            raise
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value from various formats"""
        if value is None:
            return None
        try:
            # Convert to string and handle formatted values
            str_value = str(value)
            
            # Handle common IBKR formatting issues
            # Remove currency prefixes (C, $, etc.) and other non-numeric characters
            import re
            # Keep only digits, decimal points, and negative signs
            clean_value = re.sub(r'[^0-9.\-]', '', str_value)
            
            # Handle empty string after cleaning
            if not clean_value or clean_value == '-':
                return None
                
            return Decimal(clean_value)
        except (ValueError, TypeError, Exception):
            # Log the problematic value for debugging
            logger.warning(f"Could not parse decimal value: {value}")
            return None
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer value from various formats"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None 