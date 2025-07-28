# 🤖 Smart Trading Agent

A smart, tireless assistant that reads, reasons and acts on your behalf using the Interactive Brokers API and OpenAI for intelligent portfolio management.

## 🎯 What It Does

Think of this as your personal AI intern who:
- **🔍 Reads** your account, positions, and current market prices
- **🧠 Reasons** about optimal allocation using your rules and AI
- **⚡ Acts** by placing trades (with safety checks)
- **🤔 Reflects** on results and learns for next time

## 🔄 The 4-Step Loop

| Step | What the agent does | Analogy |
|------|-------------------|---------|
| **1. SENSE** | Uses IB MCP calls to get positions, prices, account info | Looking in the fridge and checking today's grocery prices |
| **2. THINK** | Runs your rules + asks OpenAI for optimal allocation | Deciding tonight's menu: mostly veggies, a bit of protein, small dessert |
| **3. ACT** | Creates orders, runs what-if analysis, executes if safe | Filling grocery cart, previewing bill, only checkout if reasonable |
| **4. REFLECT** | Logs results, tracks P&L, learns from outcomes | Reviewing yesterday's diet and tweaking today's meal plan |

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Make sure you have these running:
# - IB Gateway/TWS (logged in)
# - MCP server: python mcp_server.py
# - OpenAI API key (optional, but recommended)

# Set your OpenAI key
export OPENAI_API_KEY="your-api-key-here"
```

### 2. Create Configuration

```bash
# Create default config
python smart_agent/run_agent.py --create-config

# Or create sample configs (conservative/aggressive)
python smart_agent/config.py create-samples
```

### 3. Run the Agent

```bash
# Single run (paper trading by default)
python smart_agent/run_agent.py

# Continuous mode (runs every 24 hours)
python smart_agent/run_agent.py --continuous

# Use specific config
python smart_agent/run_agent.py --config smart_agent/config_conservative.json

# Run every 6 hours
python smart_agent/run_agent.py --continuous --interval 6
```

## ⚙️ Configuration

The agent uses a flexible configuration system with three built-in strategies:

### Default Strategy (70/15/15)
- **70%** Broad ETFs (SPY, VTI, VOO, QQQ, IWM)
- **15%** Dividend Stocks (JNJ, PG, KO, T, VZ, PFE, XOM)  
- **15%** Growth/Speculative (TSLA, NVDA, AMZN, GOOGL, MSFT, AAPL)

### Conservative Strategy (80/20)
- **80%** Safe ETFs (SPY, VTI, BND)
- **20%** Dividend Stocks (JNJ, PG, KO)

### Aggressive Strategy (50/30/20)
- **50%** Tech Growth (NVDA, TSLA, AMZN, GOOGL, MSFT)
- **30%** Market ETFs (QQQ, IWM, VTI)
- **20%** Speculative (ARKK, PLTR, AMD, CRM)

### Customize Your Strategy

Edit `smart_agent/config.json`:

```json
{
  "risk_threshold": 1000.0,
  "paper_trading": true,
  "trading_rules": [
    {
      "name": "My ETF Rule",
      "description": "Core ETF holdings",
      "target_allocation": 60.0,
      "symbols": ["SPY", "QQQ", "VTI"],
      "max_position_size": 25.0,
      "stop_loss": -20.0,
      "take_profit": 30.0,
      "enabled": true
    }
  ]
}
```

## 🛡️ Safety Features

### Built-in Protections
- **Paper Trading**: Enabled by default, no real money at risk
- **What-if Analysis**: Every trade is simulated first
- **Risk Limits**: Configurable max $ per trade and portfolio change %
- **Position Limits**: Max % of portfolio per position
- **Stop Loss/Take Profit**: Configurable per trading rule

### Manual Overrides
```bash
# Force paper trading (safer)
python smart_agent/run_agent.py --paper-trading

# Force live trading (requires confirmation)
python smart_agent/run_agent.py --live-trading

# Limit risk per trade
python smart_agent/run_agent.py --risk-threshold 500
```

## 📊 Monitoring & Logs

### Real-time Output
The agent provides detailed logging of each step:
```
🔍 SENSE: Gathering market and portfolio data...
Portfolio Value: $50,000.00
Available Funds: $5,000.00
Positions: 8
Market Data: 15 symbols

🧠 THINK: Analyzing data and making decisions...
AI generated 3 trading decisions

⚡ ACT: Executing 3 trading decisions...
📝 PAPER TRADE: BUY 10 SPY
✅ Completed 3/3 trades successfully

🤔 REFLECT: Analyzing results and logging outcomes...
```

### Persistent Logs
- **Trading Log**: `smart_agent/trading_log.log`
- **Reflections**: `smart_agent/reflection_YYYYMMDD_HHMMSS.json`
- **Trade History**: Tracked in memory and logs

### Analysis Files
Each run creates a reflection file with:
- Portfolio performance
- Trade decisions and outcomes
- Lessons learned
- Next actions recommended

## 🔧 Advanced Usage

### Environment Variables
```bash
export OPENAI_API_KEY="your-key"           # Enable AI decisions
export MCP_URL="http://127.0.0.1:8001/mcp" # MCP server URL
export PAPER_TRADING="true"                # Safe mode
export RISK_THRESHOLD="1000"               # Max $ risk per trade
export LOG_LEVEL="INFO"                    # Logging detail
```

### Command Line Options
```bash
# Configuration management
python smart_agent/run_agent.py --help-setup        # Detailed setup guide
python smart_agent/run_agent.py --create-config     # Create default config
python smart_agent/run_agent.py --validate-config   # Check config
python smart_agent/config.py create-samples         # Create sample configs

# Running modes
python smart_agent/run_agent.py                     # Single run
python smart_agent/run_agent.py --continuous        # Continuous mode
python smart_agent/run_agent.py --interval 12       # Every 12 hours

# Safety overrides  
python smart_agent/run_agent.py --paper-trading     # Force paper mode
python smart_agent/run_agent.py --live-trading      # Force live mode
python smart_agent/run_agent.py --risk-threshold 500 # Limit risk
```

### Custom Configurations
```bash
# Create custom config for different strategies
cp smart_agent/config.json smart_agent/my_strategy.json
# Edit my_strategy.json with your rules
python smart_agent/run_agent.py --config smart_agent/my_strategy.json
```

## 🧠 How AI Decisions Work

### With OpenAI (Recommended)
When you provide an `OPENAI_API_KEY`, the agent:
1. Sends current portfolio state + market data + your rules to GPT-4
2. Gets back specific trade recommendations with reasoning
3. Executes trades that make sense and improve allocation

### Without OpenAI (Fallback)
The agent uses simple rule-based logic:
1. Calculates current allocation vs target
2. If >5% off target, suggests rebalancing trades
3. Picks first symbol in each category for simplicity

## 📈 Performance Tracking

### What Gets Tracked
- Every trade decision and outcome
- Portfolio value changes
- Allocation drift over time
- Success/failure rates
- P&L per trade and overall

### Example Reflection Output
```json
{
  "portfolio_value_before": 50000.0,
  "decisions_made": 3,
  "trades_executed": 3,
  "successful_trades": 3,
  "total_trade_value": 2500.0,
  "lessons_learned": [
    "Successfully executed 3 trades",
    "Portfolio now closer to target allocation"
  ],
  "current_allocations": {
    "Broad ETFs": 72.1,
    "Dividend Stocks": 14.8,
    "Growth/Speculative": 13.1
  }
}
```

## 🚨 Important Warnings

### Before Running Live Trades
1. **Test thoroughly** in paper trading mode first
2. **Start small** with low risk thresholds  
3. **Monitor closely** especially first few runs
4. **Have stop-loss** rules configured
5. **Check your IB account** has proper permissions

### What This Agent Does NOT Do
- ❌ Day trading or high-frequency trading
- ❌ Options, futures, or complex derivatives  
- ❌ Market timing or momentum strategies
- ❌ Guarantee profits or prevent losses
- ❌ Replace your investment judgment

### What This Agent DOES Do
- ✅ Maintains your target allocation automatically
- ✅ Rebalances when drift occurs  
- ✅ Removes emotion from portfolio management
- ✅ Trades small, frequently, and cheaply
- ✅ Logs everything for analysis
- ✅ Learns from outcomes over time

## 🛠️ Troubleshooting

### Common Issues

**"No accounts found"**
- Make sure IB Gateway/TWS is running and logged in
- Check that you have the right permissions

**"Connection failed"**  
- Verify MCP server is running: `python mcp_server.py`
- Check the URL: `http://127.0.0.1:8001/mcp`

**"AI generated no decisions"**
- Check your OpenAI API key is valid
- Verify you have API credits
- Agent will fall back to rule-based logic

**"What-if failed"**
- Check you have buying power for the trade
- Verify the symbol is tradeable in your account
- Make sure market is open (or use RTH=false)

### Getting Help

1. **Run with debug logging**: Set `LOG_LEVEL=DEBUG`
2. **Check the logs**: `smart_agent/trading_log.log`
3. **Validate config**: `python smart_agent/run_agent.py --validate-config`
4. **Test MCP**: `python mcp_test.py`

## 📚 Architecture

### File Structure
```
smart_agent/
├── smart_trader.py      # Main 4-step trading loop
├── config.py           # Configuration management  
├── run_agent.py        # Command-line runner
├── README.md           # This file
├── config.json         # Your configuration
├── config_conservative.json  # Sample configs
├── config_aggressive.json
├── trading_log.log     # All activity logs
└── reflection_*.json   # Analysis files
```

### Dependencies
- **FastMCP**: Connects to your IB MCP server
- **OpenAI**: AI decision making (optional)
- **IB Client**: Already integrated via MCP
- **Python 3.8+**: Standard libraries only

### Integration Points
- **IB MCP Server**: All trading operations go through your existing MCP server
- **OpenAI GPT-4**: Intelligent portfolio analysis and trade recommendations  
- **File System**: Configuration, logs, and analysis files
- **Environment**: Configuration via env vars

---

## 🎉 Getting Started Checklist

- [ ] IB Gateway/TWS running and logged in
- [ ] MCP server running (`python mcp_server.py`)
- [ ] OpenAI API key set (optional but recommended)
- [ ] Configuration created (`--create-config`)
- [ ] Test run in paper mode
- [ ] Review logs and reflections
- [ ] Adjust configuration as needed
- [ ] Consider continuous mode for hands-off operation

**Ready to let your AI assistant manage your portfolio? Start with paper trading and let the agent learn your preferences!** 🚀