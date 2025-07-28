# Interactive Brokers Client Portal Web API

A comprehensive, async-first Python client for the Interactive Brokers Client Portal Web API that provides everything you need for data-driven stock/ETF decisions and portfolio management.

## Features

### 🔐 Core Session Management
- **SessionAdapter**: Automatic authentication, session keep-alive, and re-authentication
- **Robust HTTP Layer**: Retry logic, proper error handling, and rate limiting
- **SSL Support**: Handles self-signed certificates for local IB Gateway connections

### 📊 Portfolio & Account Management
- **AccountsAdapter**: List accounts and get account information
- **PortfolioAdapter**: Get positions, account summary, buying power, and ledger data  
- **PnLAdapter**: Live intraday P&L tracking by asset class and individual positions

### 📈 Market Data Intelligence
- **MarketDataAdapter**: Real-time quotes, historical bars, and depth-of-book
- **Snapshot Data**: Live prices, bid/ask, volume, and market statistics
- **Historical Data**: OHLCV bars with configurable time periods
- **Order Book**: Level 2 market depth data

### 💼 Trading & Execution
- **OrderAdapter**: Complete order lifecycle management
- **What-If Analysis**: Risk preview before order placement
- **Order Types**: Market, limit, stop, and stop-limit orders
- **Order Management**: Place, modify, cancel, and track orders

### 🔍 Market Scanning
- **ScannerAdapter**: Built-in market screeners and custom scans
- **Pre-built Scans**: Top gainers, losers, most active, high volume
- **Custom Filters**: Create your own screening criteria

## Quick Start

### Prerequisites

1. **Interactive Brokers Account**: Paper trading or live account
2. **IB Gateway or TWS**: Download and install from Interactive Brokers
3. **Python 3.8+**: Async/await support required

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Basic Setup

```bash
# Start IB Gateway and configure it to listen on localhost:8765
# Complete authentication through IB Gateway interface
```

### Basic Usage

```python
import asyncio
from ib_client import IBClient

async def main():
    # Initialize IB client
    client = IBClient()
    
    # Get accounts
    accounts = await client.accounts.get_accounts()
    print(f"Found accounts: {[acc.id for acc in accounts]}")
    
    # Get portfolio summary
    account_id = accounts[0].id
    summary = await client.portfolio.summary(account_id)
    print(f"Net Liquidation: ${summary.netliquidation}")
    print(f"Buying Power: ${summary.buyingpower}")
    
    # Get current positions
    positions = await client.portfolio.all_positions(account_id)
    for pos in positions:
        print(f"{pos.contractDesc}: {pos.position} @ ${pos.mktPrice}")
    
    # Get market data
    from ib_client import search_contract
    contract = await search_contract("AAPL")
    snapshot = await client.market_data.snapshot(contract.conid)
    print(f"AAPL: ${snapshot.last_price} ({snapshot.change_percent}%)")
    
    # Cleanup
    await client.logout()

if __name__ == "__main__":
    asyncio.run(main())
```

### Testing the Integration

```bash
# Run MCP Server
python server.py

# In another terminal, list all available tools
python mcp_tools.py
```

The MCP server provides comprehensive IB Tools for portfolio management, trading, and market data analysis.

## Architecture

The client is organized into focused adapters that can be used independently or together:

```
ib_client/
├── core/
│   ├── session.py      # SessionAdapter mixin
│   └── http.py         # HTTP utilities with retry logic
├── portfolio/
│   ├── accounts.py     # AccountsAdapter  
│   ├── positions.py    # PortfolioAdapter
│   └── pnl.py         # PnLAdapter
├── market/
│   └── market_data.py  # MarketDataAdapter
├── trading/
│   └── orders.py       # OrderAdapter
└── scanners/
    └── scanner.py      # ScannerAdapter
```

### Design Principles

- **Async-First**: All operations are async for maximum performance
- **Session Management**: Automatic authentication and keep-alive  
- **Error Handling**: Comprehensive error handling with retries
- **Type Safety**: Full Pydantic models for all data structures
- **Composable**: Use individual adapters or the unified IBClient
- **Backwards Compatible**: Legacy functions maintained for existing code

## Complete API Coverage

### Decision Ingredients Mapping

| Decision Ingredient | Where it comes from |
|---|---|
| Cash & buying power | `PortfolioAdapter.summary()` |
| Current exposures & P&L | `PortfolioAdapter.positions()` + `PnLAdapter` |
| Live price & depth | `MarketDataAdapter.snapshot()` + `.book()` |
| Historical performance | `MarketDataAdapter.history()` |
| Screening universe | `ScannerAdapter` (top gainers, most active, etc.) |
| Risk preview & execution | `OrderAdapter.whatif()` + `.place_order()` |

### Core Adapters

#### 🏦 Portfolio Management
```python
# Get accounts
accounts = await client.accounts.get_accounts()

# Portfolio positions and summary  
positions = await client.portfolio.all_positions(account_id)
summary = await client.portfolio.summary(account_id)
ledger = await client.portfolio.ledger(account_id)

# Live P&L tracking
pnl = await client.pnl.get_partitioned_pnl()
position_pnl = await client.pnl.get_pnl_by_position(account_id)
```

#### 📊 Market Data
```python
# Real-time quotes
snapshot = await client.market_data.snapshot(conid)

# Historical data
bars = await client.market_data.history(conid, bar="1d", period="1m")

# Order book depth
book = await client.market_data.book(conid)

# Subscriptions
await client.market_data.subscribe_market_data([conid1, conid2])
```

#### 💼 Order Management
```python
from ib_client import OrderRequest, OrderSide, OrderType

# Create order
order = OrderRequest(
    conid=265598,
    orderType=OrderType.LIMIT,
    side=OrderSide.BUY,
    quantity=100,
    price=150.00
)

# Risk preview
whatif = await client.orders.whatif(account_id, order)

# Place order (with automatic what-if check)
result = await client.orders.place_order(account_id, order)

# Monitor orders
live_orders = await client.orders.get_live_orders()

# Cancel order
await client.orders.cancel_order(account_id, order_id)
```

#### 🔍 Market Scanning
```python
# Built-in scans
gainers = await client.scanner.top_gainers(max_results=20)
active = await client.scanner.most_active(max_results=20)
losers = await client.scanner.top_losers(max_results=20)

# Custom scan
results = await client.scanner.custom_scan(
    scan_code="HIGH_OPT_VOLUME_PUT_CALL_RATIO",
    max_results=50
)
```

## Configuration

### Environment Variables

```bash
# IB Gateway URL (default: https://localhost:8765/v1/api)
export IB_BASE="https://localhost:8765/v1/api"

# For paper trading
export IB_BASE="https://localhost:8765/v1/api"

# For live trading  
export IB_BASE="https://localhost:8765/v1/api"
```

### Connection Setup

1. **Start IB Gateway**:
   ```bash
   # Configure IB Gateway to listen on localhost:8765
   # Enable API connections
   # Set up paper trading or live account
   ```

2. **Login through IB Gateway**: Complete the authentication flow in the IB Gateway interface

3. **Test Connection**:
   ```python
   client = IBClient()
   session_info = await client.get_session_info()
   print(f"Authenticated: {session_info.get('authenticated', False)}")
   ```

## Error Handling

The client provides comprehensive error handling:

```python
from ib_client import IBAPIError

try:
    snapshot = await client.market_data.snapshot(conid)
except IBAPIError as e:
    if e.status_code == 401:
        print("Authentication required - please log in to IB Gateway")
    elif e.status_code == 403:
        print("Access forbidden - check permissions")
    else:
        print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Cache Contract Lookups**: Store conid mappings to avoid repeated searches
2. **Batch Market Data**: Subscribe to multiple instruments at once
3. **Use Connection Pooling**: The HTTP client automatically manages connections
4. **Monitor Rate Limits**: The API has built-in rate limiting and retry logic

## Regional Support

The client works with all IB regions:
- **US**: Default configuration
- **EMEA**: Same endpoints, automatic MiFID II compliance
- **Asia**: Regional gateway support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **IB API Documentation**: [Interactive Brokers Client Portal API](https://interactivebrokers.github.io/cpwebapi/)
- **Issues**: GitHub Issues for bugs and feature requests
- **Community**: Discussions for questions and examples

---

*This client provides everything needed for data-driven stock/ETF decisions and portfolio management without ever leaving Python.* 🐍📈