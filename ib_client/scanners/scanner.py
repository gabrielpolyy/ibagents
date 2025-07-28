from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from decimal import Decimal
import logging

from ..core.session import SessionAdapter
from ..core.http import _get, _post

logger = logging.getLogger(__name__)

class ScannerParam(BaseModel):
    """Scanner parameter definition"""
    code: str
    name: str
    group: str
    type: str

class ScanResult(BaseModel):
    """Individual scan result item"""
    conid: int
    symbol: str
    contractDesc: str
    secType: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    price: Optional[Decimal] = None
    change: Optional[Decimal] = None
    changePercent: Optional[Decimal] = None
    volume: Optional[int] = None
    marketCap: Optional[Decimal] = None
    pe: Optional[Decimal] = None
    dividend: Optional[Decimal] = None

class ScanRequest(BaseModel):
    """Scanner request parameters"""
    instrument: str = "STK"
    location: str = "STK.US.MAJOR"
    type: str = "TOP_PERC_GAIN"
    filter: List[Dict[str, Any]] = []
    size: int = 50

class ScannerAdapter(SessionAdapter):
    """Adapter for market screening and scanning functionality"""
    
    def __init__(self):
        super().__init__()
        self._cached_params: Optional[Dict] = None
    
    async def get_scanner_params(self) -> Dict[str, Any]:
        """Get available scanner parameters and filters"""
        await self._ensure_live()
        
        try:
            if self._cached_params is None:
                data = await _get("/iserver/scanner/params")
                self._cached_params = data
                logger.debug(f"Scanner params: {data}")
            
            return self._cached_params
            
        except Exception as e:
            logger.error(f"Failed to get scanner params: {e}")
            raise
    
    async def run_scan(self, scan_request: ScanRequest) -> List[ScanResult]:
        """Run a market scan with specified parameters"""
        await self._ensure_live()
        
        try:
            # Build scan request payload according to IBKR Web API format
            # The filter field is REQUIRED and must be an array
            scan_data = {
                "instrument": scan_request.instrument,
                "location": scan_request.location,
                "type": scan_request.type,
                "size": scan_request.size,
                "filter": scan_request.filter
            }
            
            logger.debug(f"Scanner request payload: {scan_data}")
            data = await _post("/iserver/scanner/run", json_data=scan_data)
            logger.debug(f"Scan results: {data}")
            
            scan_results = []
            
            # Parse scan results
            if isinstance(data, dict) and "contracts" in data:
                contracts = data["contracts"]
            elif isinstance(data, list):
                contracts = data
            else:
                contracts = []
            
            for contract_data in contracts:
                try:
                    # Map IBKR response fields to our model
                    scan_result = ScanResult(
                        conid=contract_data.get("con_id", contract_data.get("conid", 0)),
                        symbol=contract_data.get("symbol", ""),
                        contractDesc=contract_data.get("contract_description_1", 
                                                     contract_data.get("contractDesc", "")),
                        secType=contract_data.get("sec_type", 
                                                contract_data.get("secType", "")),
                        exchange=contract_data.get("listing_exchange", 
                                                 contract_data.get("exchange")),
                        currency=contract_data.get("currency"),
                        price=self._parse_decimal(contract_data.get("price")),
                        change=self._parse_decimal(contract_data.get("change")),
                        changePercent=self._parse_decimal(contract_data.get("changePercent")),
                        volume=self._parse_int(contract_data.get("volume")),
                        marketCap=self._parse_decimal(contract_data.get("marketCap")),
                        pe=self._parse_decimal(contract_data.get("pe")),
                        dividend=self._parse_decimal(contract_data.get("dividend"))
                    )
                    scan_results.append(scan_result)
                except Exception as e:
                    logger.warning(f"Failed to parse scan result: {contract_data}, error: {e}")
            
            logger.info(f"Scan '{scan_request.type}' returned {len(scan_results)} results")
            return scan_results
            
        except Exception as e:
            logger.error(f"Failed to run scan: {e}")
            raise
    
    async def top_gainers(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get top percentage gainers"""
        scan_request = ScanRequest(
            type="TOP_PERC_GAIN",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def top_losers(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get top percentage losers"""
        scan_request = ScanRequest(
            type="TOP_PERC_LOSE",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def most_active(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get most active stocks by volume"""
        scan_request = ScanRequest(
            type="MOST_ACTIVE",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def most_active_usd(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get most active stocks by USD volume"""
        scan_request = ScanRequest(
            type="MOST_ACTIVE_USD",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def hot_by_volume(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get stocks hot by volume"""
        scan_request = ScanRequest(
            type="HOT_BY_VOLUME",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def top_trade_count(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get stocks with highest trade count"""
        scan_request = ScanRequest(
            type="TOP_TRADE_COUNT",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def high_opt_volume_put_call_ratio(self, max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Get stocks with high options volume put/call ratio"""
        scan_request = ScanRequest(
            type="HIGH_OPT_VOLUME_PUT_CALL_RATIO",
            location=location,
            size=max_results
        )
        return await self.run_scan(scan_request)
    
    async def custom_scan(self, scan_type: str, filters: List[Dict[str, Any]] = None,
                         max_results: int = 50, location: str = "STK.US.MAJOR") -> List[ScanResult]:
        """Run a custom scan with specified scan type and filters"""
        scan_request = ScanRequest(
            type=scan_type,
            location=location,
            size=max_results,
            filter=filters if filters is not None else []
        )
        return await self.run_scan(scan_request)
    
    async def get_available_scan_codes(self) -> List[str]:
        """Get list of available scan codes"""
        params = await self.get_scanner_params()
        
        scan_codes = []
        if isinstance(params, dict) and "scan_type_list" in params:
            for scan_type in params["scan_type_list"]:
                if isinstance(scan_type, dict) and "code" in scan_type:
                    scan_codes.append(scan_type["code"])
        
        return scan_codes
    
    async def get_available_locations(self) -> List[str]:
        """Get list of available scan locations"""
        params = await self.get_scanner_params()
        
        locations = []
        if isinstance(params, dict) and "location_tree" in params:
            for location_group in params["location_tree"]:
                if isinstance(location_group, dict) and "locations" in location_group:
                    for location in location_group["locations"]:
                        if isinstance(location, dict) and "type" in location:
                            locations.append(location["type"])
        
        return locations
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value safely"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer value safely"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None 