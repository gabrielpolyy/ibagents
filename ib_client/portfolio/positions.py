from typing import List, Optional, Any, Dict
from pydantic import BaseModel, field_validator
from decimal import Decimal
import logging

from ..core.session import SessionAdapter
from ..core.http import _get

logger = logging.getLogger(__name__)

class Position(BaseModel):
    acctId: str
    conid: int
    contractDesc: str
    position: Decimal
    mktPrice: Optional[Decimal] = None
    mktValue: Optional[Decimal] = None
    currency: str = "USD"
    avgCost: Optional[Decimal] = None
    avgPrice: Optional[Decimal] = None
    realizedPnl: Optional[Decimal] = None
    unrealizedPnl: Optional[Decimal] = None
    exchs: Optional[str] = None
    expiry: Optional[str] = None
    putOrCall: Optional[str] = None
    multiplier: Optional[Decimal] = None
    strike: Optional[Decimal] = None
    exerciseStyle: Optional[str] = None
    conExchMap: Optional[List[str]] = None
    assetClass: Optional[str] = None
    undConid: Optional[int] = None

class Summary(BaseModel):
    accountcode: str
    accountready: str
    accounttype: str
    accruedcash: Optional[Decimal] = None
    accruedcash_c: Optional[str] = None
    accruedcash_s: Optional[str] = None
    availablefunds: Optional[Decimal] = None
    availablefunds_c: Optional[str] = None
    availablefunds_s: Optional[str] = None
    buyingpower: Optional[Decimal] = None
    cushion: Optional[Decimal] = None
    daytradesremaining: Optional[int] = None
    daytradesremainingt1: Optional[int] = None
    daytradesremainingt2: Optional[int] = None
    daytradesremainingt3: Optional[int] = None
    daytradesremainingt4: Optional[int] = None
    equitywithloanvalue: Optional[Decimal] = None
    equitywithloanvalue_c: Optional[str] = None
    equitywithloanvalue_s: Optional[str] = None
    excessliquidity: Optional[Decimal] = None
    excessliquidity_c: Optional[str] = None
    excessliquidity_s: Optional[str] = None
    fullavailablefunds: Optional[Decimal] = None
    fullavailablefunds_c: Optional[str] = None
    fullavailablefunds_s: Optional[str] = None
    fullexcessliquidity: Optional[Decimal] = None
    fullexcessliquidity_c: Optional[str] = None
    fullexcessliquidity_s: Optional[str] = None
    fullinitmarginreq: Optional[Decimal] = None
    fullinitmarginreq_c: Optional[str] = None
    fullinitmarginreq_s: Optional[str] = None
    fullmaintmarginreq: Optional[Decimal] = None
    fullmaintmarginreq_c: Optional[str] = None
    fullmaintmarginreq_s: Optional[str] = None
    grosspositionvalue: Optional[Decimal] = None
    grosspositionvalue_s: Optional[str] = None
    initmarginreq: Optional[Decimal] = None
    initmarginreq_c: Optional[str] = None
    initmarginreq_s: Optional[str] = None
    lookaheadavailablefunds: Optional[Decimal] = None
    lookaheadavailablefunds_c: Optional[str] = None
    lookaheadavailablefunds_s: Optional[str] = None
    lookaheadexcessliquidity: Optional[Decimal] = None
    lookaheadexcessliquidity_c: Optional[str] = None
    lookaheadexcessliquidity_s: Optional[str] = None
    lookaheadinitmarginreq: Optional[Decimal] = None
    lookaheadinitmarginreq_c: Optional[str] = None
    lookaheadinitmarginreq_s: Optional[str] = None
    lookaheadmaintmarginreq: Optional[Decimal] = None
    lookaheadmaintmarginreq_c: Optional[str] = None
    lookaheadmaintmarginreq_s: Optional[str] = None
    maintmarginreq: Optional[Decimal] = None
    maintmarginreq_c: Optional[str] = None
    maintmarginreq_s: Optional[str] = None
    netliquidation: Optional[Decimal] = None
    netliquidation_c: Optional[str] = None
    netliquidation_s: Optional[str] = None
    nlvandmargininreview: Optional[bool] = None
    totalcashvalue: Optional[Decimal] = None
    totalcashvalue_c: Optional[str] = None
    totalcashvalue_s: Optional[str] = None
    tradingtype_s: Optional[str] = None

    @field_validator('accountcode', 'accountready', 'accounttype', mode='before')
    @classmethod
    def extract_string_value(cls, v):
        """Extract string value from IB API response format"""
        if isinstance(v, dict) and 'value' in v:
            return v['value']
        return v

    @field_validator(
        'accruedcash', 'availablefunds', 'buyingpower', 'cushion', 
        'equitywithloanvalue', 'excessliquidity', 'fullavailablefunds',
        'fullexcessliquidity', 'fullinitmarginreq', 'fullmaintmarginreq',
        'grosspositionvalue', 'initmarginreq', 'lookaheadavailablefunds',
        'lookaheadexcessliquidity', 'lookaheadinitmarginreq', 'lookaheadmaintmarginreq',
        'maintmarginreq', 'netliquidation', 'totalcashvalue', mode='before'
    )
    @classmethod
    def extract_decimal_value(cls, v):
        """Extract decimal value from IB API response format"""
        if isinstance(v, dict) and 'amount' in v:
            return Decimal(str(v['amount']))
        elif isinstance(v, dict) and 'value' in v:
            try:
                return Decimal(str(v['value']))
            except:
                return None
        elif v is not None:
            try:
                return Decimal(str(v))
            except:
                return None
        return v

    @field_validator('nlvandmargininreview', mode='before')
    @classmethod
    def extract_bool_value(cls, v):
        """Extract boolean value from IB API response format"""
        if isinstance(v, dict) and 'value' in v:
            return v['value'].lower() == 'true' if isinstance(v['value'], str) else v['value']
        elif isinstance(v, str):
            return v.lower() == 'true'
        return v

class LedgerLine(BaseModel):
    commoditymarketvalue: Optional[Decimal] = None
    futuremarketvalue: Optional[Decimal] = None
    settledcash: Optional[Decimal] = None
    exchangerate: Optional[Decimal] = None
    sessionid: Optional[int] = None
    cashbalance: Optional[Decimal] = None
    corporatebondsmarketvalue: Optional[Decimal] = None
    warrantsmarketvalue: Optional[Decimal] = None
    netliquidationvalue: Optional[Decimal] = None
    interest: Optional[Decimal] = None
    unrealizedpnl: Optional[Decimal] = None
    stockmarketvalue: Optional[Decimal] = None
    moneyfunds: Optional[Decimal] = None
    currency: Optional[str] = None
    realizedpnl: Optional[Decimal] = None
    funds: Optional[Decimal] = None
    acctcode: Optional[str] = None
    issueroptionsmarketvalue: Optional[Decimal] = None
    key: Optional[str] = None
    timestamp: Optional[int] = None
    severity: Optional[int] = None
    stockoptionmarketvalue: Optional[Decimal] = None
    futureoptionmarketvalue: Optional[Decimal] = None
    commodityoptionmarketvalue: Optional[Decimal] = None
    tbondsmarketvalue: Optional[Decimal] = None
    tbillsmarketvalue: Optional[Decimal] = None
    dividends: Optional[Decimal] = None

class PortfolioAdapter(SessionAdapter):
    """Adapter for portfolio positions, summary, and ledger data"""
    
    def __init__(self):
        super().__init__()
    
    async def positions(self, account: str, page: int = 0) -> List[Position]:
        """Get positions for an account (paginated)"""
        await self._ensure_live()
        
        try:
            data = await _get(f"/portfolio/{account}/positions/{page}")
            logger.debug(f"Positions data for {account}: {data}")
            
            positions = []
            for pos_data in data:
                try:
                    position = Position(**pos_data)
                    positions.append(position)
                except Exception as e:
                    logger.warning(f"Failed to parse position data: {pos_data}, error: {e}")
                    # Continue with other positions
            
            logger.info(f"Found {len(positions)} positions for account {account}")
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions for {account}: {e}")
            raise
    
    async def summary(self, account: str) -> Summary:
        """Get account summary (Net Liq, buying power, margin)"""
        await self._ensure_live()
        
        try:
            data = await _get(f"/portfolio/{account}/summary")
            logger.debug(f"Summary data for {account}: {data}")
            
            return Summary(**data)
            
        except Exception as e:
            logger.error(f"Failed to get summary for {account}: {e}")
            raise
    
    async def ledger(self, account: str) -> List[LedgerLine]:
        """Get account ledger (cash, FX)"""
        await self._ensure_live()
        
        try:
            data = await _get(f"/portfolio/{account}/ledger")
            logger.debug(f"Ledger data for {account}: {data}")
            
            ledger_lines = []
            # The API may return different structures
            if isinstance(data, dict):
                # Handle single currency case
                ledger_lines.append(LedgerLine(**data))
            elif isinstance(data, list):
                # Handle multiple currencies
                for ledger_data in data:
                    try:
                        ledger_line = LedgerLine(**ledger_data)
                        ledger_lines.append(ledger_line)
                    except Exception as e:
                        logger.warning(f"Failed to parse ledger data: {ledger_data}, error: {e}")
            
            logger.info(f"Found {len(ledger_lines)} ledger lines for account {account}")
            return ledger_lines
            
        except Exception as e:
            logger.error(f"Failed to get ledger for {account}: {e}")
            raise
    
    async def all_positions(self, account: str) -> List[Position]:
        """Get all positions for an account by fetching all pages"""
        all_positions = []
        page = 0
        
        while True:
            try:
                positions = await self.positions(account, page)
                if not positions:
                    break
                
                all_positions.extend(positions)
                page += 1
                
                # Safety check to avoid infinite loops
                if page > 100:
                    logger.warning(f"Stopped fetching positions after 100 pages for account {account}")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching page {page} for account {account}: {e}")
                break
        
        return all_positions 