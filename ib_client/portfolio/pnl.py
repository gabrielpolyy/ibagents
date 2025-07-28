from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
import logging

from ..core.session import SessionAdapter
from ..core.http import _get

logger = logging.getLogger(__name__)

class PnLRow(BaseModel):
    acctId: str
    model: Optional[str] = None
    dpl: Optional[Decimal] = None  # Daily P&L
    nl: Optional[Decimal] = None   # Net Liquidation
    upl: Optional[Decimal] = None  # Unrealized P&L
    el: Optional[Decimal] = None   # Excess Liquidity
    mv: Optional[Decimal] = None   # Market Value
    

class PnLByInstrument(BaseModel):
    acctId: str
    conid: int
    contractDesc: str
    position: Decimal
    dailyPnL: Optional[Decimal] = None
    unrealizedPnL: Optional[Decimal] = None
    realizedPnL: Optional[Decimal] = None
    value: Optional[Decimal] = None

class PnLAdapter(SessionAdapter):
    """Adapter for live intraday P&L tracking"""
    
    def __init__(self):
        super().__init__()
    
    async def get_partitioned_pnl(self) -> List[PnLRow]:
        """Get live intraday P&L partitioned by asset class"""
        await self._ensure_live()
        
        try:
            data = await _get("/iserver/account/pnl/partitioned")
            logger.debug(f"Partitioned P&L data: {data}")
            
            pnl_rows = []
            
            # Handle different response structures
            if isinstance(data, dict):
                # Single account or summary format
                if "upnl" in data or "dpl" in data:
                    # Direct P&L data - handle dict values in fields
                    pnl_row = PnLRow(
                        acctId=data.get("acctId", ""),
                        model=data.get("model"),
                        dpl=self._safe_parse_decimal(data.get("dpl")),
                        nl=self._safe_parse_decimal(data.get("nl")),
                        upl=self._safe_parse_decimal(data.get("upnl", data.get("upl"))),
                        el=self._safe_parse_decimal(data.get("el")),
                        mv=self._safe_parse_decimal(data.get("mv"))
                    )
                    pnl_rows.append(pnl_row)
                else:
                    # Nested structure
                    for key, value in data.items():
                        if isinstance(value, dict) and ("upnl" in value or "dpl" in value):
                            pnl_row = PnLRow(
                                acctId=value.get("acctId", key),
                                model=value.get("model"),
                                dpl=self._safe_parse_decimal(value.get("dpl")),
                                nl=self._safe_parse_decimal(value.get("nl")),
                                upl=self._safe_parse_decimal(value.get("upnl", value.get("upl"))),
                                el=self._safe_parse_decimal(value.get("el")),
                                mv=self._safe_parse_decimal(value.get("mv"))
                            )
                            pnl_rows.append(pnl_row)
            
            elif isinstance(data, list):
                # List of P&L entries
                for pnl_data in data:
                    try:
                        # Create row with safe parsing
                        pnl_row = PnLRow(
                            acctId=pnl_data.get("acctId", ""),
                            model=pnl_data.get("model"),
                            dpl=self._safe_parse_decimal(pnl_data.get("dpl")),
                            nl=self._safe_parse_decimal(pnl_data.get("nl")),
                            upl=self._safe_parse_decimal(pnl_data.get("upnl", pnl_data.get("upl"))),
                            el=self._safe_parse_decimal(pnl_data.get("el")),
                            mv=self._safe_parse_decimal(pnl_data.get("mv"))
                        )
                        pnl_rows.append(pnl_row)
                    except Exception as e:
                        logger.warning(f"Failed to parse P&L data: {pnl_data}, error: {e}")
            
            logger.info(f"Found {len(pnl_rows)} P&L entries")
            return pnl_rows
            
        except Exception as e:
            logger.error(f"Failed to get partitioned P&L: {e}")
            raise
    
    def _safe_parse_decimal(self, value) -> Optional[Decimal]:
        """Safely parse a value to Decimal, handling various input types"""
        if value is None:
            return None
        
        # Handle empty dict (which was causing the error)
        if isinstance(value, dict):
            if not value:  # Empty dict
                return None
            # If dict has a single value, try to extract it
            if len(value) == 1:
                return self._safe_parse_decimal(list(value.values())[0])
            return None
        
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                if value.strip() == "" or value.lower() in ["n/a", "null", "none"]:
                    return None
                return Decimal(value)
            elif isinstance(value, Decimal):
                return value
            else:
                return None
        except Exception:
            logger.debug(f"Could not parse decimal value: {value} (type: {type(value)})")
            return None
    
    async def get_pnl_by_position(self, account: str) -> List[PnLByInstrument]:
        """Get P&L breakdown by individual positions"""
        await self._ensure_live()
        
        try:
            # Try different endpoints for position P&L data
            endpoints_to_try = [
                f"/portfolio/{account}/positions/0",  # Standard positions endpoint
                f"/portfolio/{account}/positions",    # Alternative positions endpoint
                f"/portfolio/{account}/summary",      # Portfolio summary might have P&L info
            ]
            
            pnl_positions = []
            
            for endpoint in endpoints_to_try:
                try:
                    data = await _get(endpoint)
                    logger.debug(f"P&L by position data from {endpoint}: {data}")
                    
                    if isinstance(data, list):
                        for pos_data in data:
                            try:
                                # Extract P&L information from position data with safe parsing
                                pnl_pos = PnLByInstrument(
                                    acctId=pos_data.get("acctId", account),
                                    conid=pos_data.get("conid", 0),
                                    contractDesc=pos_data.get("contractDesc", pos_data.get("desc", "")),
                                    position=self._safe_parse_decimal(pos_data.get("position", 0)) or Decimal(0),
                                    dailyPnL=self._safe_parse_decimal(pos_data.get("dailyPnL", pos_data.get("dpl"))),
                                    unrealizedPnL=self._safe_parse_decimal(pos_data.get("unrealizedPnL", pos_data.get("upl", pos_data.get("unrealizedPnl")))),
                                    realizedPnL=self._safe_parse_decimal(pos_data.get("realizedPnL", pos_data.get("rpl", pos_data.get("realizedPnl")))),
                                    value=self._safe_parse_decimal(pos_data.get("mktValue", pos_data.get("value", pos_data.get("marketValue"))))
                                )
                                
                                # Only add positions that have meaningful data
                                if pnl_pos.position != 0 or pnl_pos.dailyPnL or pnl_pos.unrealizedPnL or pnl_pos.value:
                                    pnl_positions.append(pnl_pos)
                                    
                            except Exception as e:
                                logger.warning(f"Failed to parse position P&L data: {pos_data}, error: {e}")
                    
                    elif isinstance(data, dict):
                        # Sometimes positions are returned as a dict
                        positions_data = data.get("positions", [])
                        if positions_data:
                            for pos_data in positions_data:
                                try:
                                    pnl_pos = PnLByInstrument(
                                        acctId=pos_data.get("acctId", account),
                                        conid=pos_data.get("conid", 0),
                                        contractDesc=pos_data.get("contractDesc", pos_data.get("desc", "")),
                                        position=self._safe_parse_decimal(pos_data.get("position", 0)) or Decimal(0),
                                        dailyPnL=self._safe_parse_decimal(pos_data.get("dailyPnL", pos_data.get("dpl"))),
                                        unrealizedPnL=self._safe_parse_decimal(pos_data.get("unrealizedPnL", pos_data.get("upl", pos_data.get("unrealizedPnl")))),
                                        realizedPnL=self._safe_parse_decimal(pos_data.get("realizedPnL", pos_data.get("rpl", pos_data.get("realizedPnl")))),
                                        value=self._safe_parse_decimal(pos_data.get("mktValue", pos_data.get("value", pos_data.get("marketValue"))))
                                    )
                                    
                                    if pnl_pos.position != 0 or pnl_pos.dailyPnL or pnl_pos.unrealizedPnL or pnl_pos.value:
                                        pnl_positions.append(pnl_pos)
                                        
                                except Exception as e:
                                    logger.warning(f"Failed to parse position P&L data: {pos_data}, error: {e}")
                    
                    if pnl_positions:
                        break  # Success, don't try other endpoints
                        
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            logger.info(f"Found {len(pnl_positions)} position P&L entries for account {account}")
            return pnl_positions
            
        except Exception as e:
            logger.error(f"Failed to get P&L by position for {account}: {e}")
            raise
    
    async def get_account_pnl_summary(self, account: str) -> dict:
        """Get P&L summary for a specific account"""
        await self._ensure_live()
        
        try:
            # Try different endpoints for account P&L summary
            endpoints_to_try = [
                f"/portfolio/{account}/summary",      # Portfolio summary endpoint
                f"/portfolio/{account}/ledger",       # Account ledger might have P&L info
                f"/iserver/account/pnl/partitioned",  # General P&L endpoint
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    data = await _get(endpoint)
                    logger.debug(f"Account P&L summary for {account} from {endpoint}: {data}")
                    
                    # If we get data, return it
                    if data:
                        return data
                        
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed for account {account}: {e}")
                    continue
            
            # If all endpoints fail, return empty dict
            logger.warning(f"No P&L summary data available for account {account}")
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get P&L summary for {account}: {e}")
            raise 