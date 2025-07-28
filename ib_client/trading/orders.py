from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from decimal import Decimal
from enum import Enum
import logging

from ..core.session import SessionAdapter
from ..core.http import _get, _post, _delete

logger = logging.getLogger(__name__)

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP_LMT"

class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"

class OrderStatus(str, Enum):
    SUBMITTED = "Submitted"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    PENDING_SUBMIT = "PendingSubmit"
    PRE_SUBMITTED = "PreSubmitted"
    PENDING_CANCEL = "PendingCancel"

class OrderRequest(BaseModel):
    """Order request model"""
    conid: int
    orderType: OrderType
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal] = None
    auxPrice: Optional[Decimal] = None  # Stop price for stop orders
    tif: TimeInForce = TimeInForce.DAY
    outsideRTH: bool = False
    useAdaptive: bool = True

class WhatIfResult(BaseModel):
    """What-if order preview result"""
    equity: Optional[Decimal] = None
    initial: Optional[Decimal] = None
    maintenance: Optional[Decimal] = None
    warn: Optional[str] = None
    error: Optional[str] = None

class OrderResult(BaseModel):
    """Order placement result"""
    order_id: Optional[str] = None
    local_order_id: Optional[str] = None
    order_status: Optional[str] = None
    encrypt_message: Optional[str] = None

class LiveOrder(BaseModel):
    """Live order information"""
    orderId: str
    conid: int
    symbol: Optional[str] = None
    side: str
    orderType: str
    quantity: Decimal
    price: Optional[Decimal] = None
    auxPrice: Optional[Decimal] = None
    status: str
    filled: Optional[Decimal] = None
    remaining: Optional[Decimal] = None
    avgPrice: Optional[Decimal] = None
    lastExecutionTime: Optional[str] = None
    orderRef: Optional[str] = None
    timeInForce: Optional[str] = None
    account: Optional[str] = None

class OrderAdapter(SessionAdapter):
    """Adapter for order management with risk preview and execution"""
    
    def __init__(self):
        super().__init__()
    
    async def whatif(self, account: str, order: OrderRequest) -> WhatIfResult:
        """Get what-if order preview for risk assessment"""
        await self._ensure_live()
        
        try:
            order_data = {
                "orders": [{
                    "conid": order.conid,
                    "orderType": order.orderType.value,
                    "side": order.side.value,
                    "quantity": float(order.quantity),
                    "tif": order.tif.value,
                    "outsideRTH": order.outsideRTH,
                    "useAdaptive": order.useAdaptive
                }]
            }
            
            # Add price fields if provided
            if order.price is not None:
                order_data["orders"][0]["price"] = float(order.price)
            if order.auxPrice is not None:
                order_data["orders"][0]["auxPrice"] = float(order.auxPrice)
            
            data = await _post(f"/iserver/account/{account}/orders/whatif", 
                             json_data=order_data)
            
            logger.debug(f"What-if result for account {account}: {data}")
            
            # Parse what-if result
            if isinstance(data, dict):
                return WhatIfResult(
                    equity=self._parse_decimal(data.get("equity")),
                    initial=self._parse_decimal(data.get("initial")),
                    maintenance=self._parse_decimal(data.get("maintenance")),
                    warn=data.get("warn"),
                    error=data.get("error")
                )
            elif isinstance(data, list) and len(data) > 0:
                result_data = data[0]
                return WhatIfResult(
                    equity=self._parse_decimal(result_data.get("equity")),
                    initial=self._parse_decimal(result_data.get("initial")),
                    maintenance=self._parse_decimal(result_data.get("maintenance")),
                    warn=result_data.get("warn"),
                    error=result_data.get("error")
                )
            
            return WhatIfResult()
            
        except Exception as e:
            logger.error(f"Failed to get what-if preview for account {account}: {e}")
            raise
    
    async def place_order(self, account: str, order: OrderRequest, 
                         skip_whatif: bool = False) -> OrderResult:
        """
        Place an order with optional what-if preview first.
        Recommended to use what-if preview for risk checks.
        """
        await self._ensure_live()
        
        # Optional what-if check first
        if not skip_whatif:
            whatif_result = await self.whatif(account, order)
            if whatif_result.error:
                raise ValueError(f"What-if preview failed: {whatif_result.error}")
            if whatif_result.warn:
                logger.warning(f"What-if warning: {whatif_result.warn}")
        
        try:
            order_data = {
                "orders": [{
                    "conid": order.conid,
                    "orderType": order.orderType.value,
                    "side": order.side.value,
                    "quantity": float(order.quantity),
                    "tif": order.tif.value,
                    "outsideRTH": order.outsideRTH,
                    "useAdaptive": order.useAdaptive
                }]
            }
            
            # Add price fields if provided
            if order.price is not None:
                order_data["orders"][0]["price"] = float(order.price)
            if order.auxPrice is not None:
                order_data["orders"][0]["auxPrice"] = float(order.auxPrice)
            
            data = await _post(f"/iserver/account/{account}/orders", 
                             json_data=order_data)
            
            logger.debug(f"Order placement result for account {account}: {data}")
            
            # Parse order result
            if isinstance(data, list) and len(data) > 0:
                result_data = data[0]
                order_result = OrderResult(
                    order_id=result_data.get("order_id"),
                    local_order_id=result_data.get("local_order_id"),
                    order_status=result_data.get("order_status"),
                    encrypt_message=result_data.get("encrypt_message")
                )
            else:
                order_result = OrderResult()
            
            logger.info(f"Order placed for account {account}: {order_result.order_id}")
            return order_result
            
        except Exception as e:
            logger.error(f"Failed to place order for account {account}: {e}")
            raise
    
    async def cancel_order(self, account: str, order_id: str) -> dict:
        """Cancel an order"""
        await self._ensure_live()
        
        try:
            data = await _delete(f"/iserver/account/{account}/order/{order_id}")
            logger.info(f"Order {order_id} cancelled for account {account}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id} for account {account}: {e}")
            raise
    
    async def get_live_orders(self) -> List[LiveOrder]:
        """Get all live orders across accounts"""
        await self._ensure_live()
        
        try:
            data = await _get("/iserver/account/orders")
            logger.debug(f"Live orders data: {data}")
            
            live_orders = []
            if isinstance(data, dict) and "orders" in data:
                orders_data = data["orders"]
            elif isinstance(data, list):
                orders_data = data
            else:
                orders_data = []
            
            for order_data in orders_data:
                try:
                    live_order = LiveOrder(
                        orderId=order_data.get("orderId", ""),
                        conid=order_data.get("conid", 0),
                        symbol=order_data.get("symbol"),
                        side=order_data.get("side", ""),
                        orderType=order_data.get("orderType", ""),
                        quantity=Decimal(str(order_data.get("quantity", 0))),
                        price=self._parse_decimal(order_data.get("price")),
                        auxPrice=self._parse_decimal(order_data.get("auxPrice")),
                        status=order_data.get("status", ""),
                        filled=self._parse_decimal(order_data.get("filled")),
                        remaining=self._parse_decimal(order_data.get("remaining")),
                        avgPrice=self._parse_decimal(order_data.get("avgPrice")),
                        lastExecutionTime=order_data.get("lastExecutionTime"),
                        orderRef=order_data.get("orderRef"),
                        timeInForce=order_data.get("timeInForce"),
                        account=order_data.get("account")
                    )
                    live_orders.append(live_order)
                except Exception as e:
                    logger.warning(f"Failed to parse live order data: {order_data}, error: {e}")
            
            logger.info(f"Found {len(live_orders)} live orders")
            return live_orders
            
        except Exception as e:
            logger.error(f"Failed to get live orders: {e}")
            raise
    
    async def get_order_status(self, order_id: str) -> dict:
        """Get status of a specific order"""
        await self._ensure_live()
        
        try:
            data = await _get(f"/iserver/account/order/status/{order_id}")
            logger.debug(f"Order status for {order_id}: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            raise
    
    async def modify_order(self, account: str, order_id: str, order: OrderRequest) -> OrderResult:
        """Modify an existing order"""
        await self._ensure_live()
        
        try:
            order_data = {
                "conid": order.conid,
                "orderType": order.orderType.value,
                "side": order.side.value,
                "quantity": float(order.quantity),
                "tif": order.tif.value,
                "outsideRTH": order.outsideRTH,
                "useAdaptive": order.useAdaptive
            }
            
            # Add price fields if provided
            if order.price is not None:
                order_data["price"] = float(order.price)
            if order.auxPrice is not None:
                order_data["auxPrice"] = float(order.auxPrice)
            
            data = await _post(f"/iserver/account/{account}/order/{order_id}", 
                             json_data=order_data)
            
            logger.info(f"Order {order_id} modified for account {account}")
            
            # Parse modify result
            if isinstance(data, list) and len(data) > 0:
                result_data = data[0]
                return OrderResult(
                    order_id=result_data.get("order_id"),
                    local_order_id=result_data.get("local_order_id"),
                    order_status=result_data.get("order_status"),
                    encrypt_message=result_data.get("encrypt_message")
                )
            
            return OrderResult()
            
        except Exception as e:
            logger.error(f"Failed to modify order {order_id} for account {account}: {e}")
            raise
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value from various formats"""
        if value is None:
            return None
        try:
            # Handle different value formats from IB API
            if isinstance(value, dict):
                # Handle IB API format like {'amount': 1000.0, 'currency': 'USD'}
                if 'amount' in value:
                    return Decimal(str(value['amount']))
                elif 'value' in value:
                    return Decimal(str(value['value']))
            
            # Handle string/numeric values
            str_value = str(value).strip()
            if not str_value or str_value.lower() in ('n/a', 'na', '', '-'):
                return None
            
            # Remove currency symbols and other formatting
            import re
            clean_value = re.sub(r'[^0-9.\-]', '', str_value)
            if not clean_value or clean_value == '-':
                return None
                
            return Decimal(clean_value)
            
        except (ValueError, TypeError, Exception) as e:
            logger.warning(f"Could not parse decimal value: {value}, error: {e}")
            return None 