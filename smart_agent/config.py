#!/usr/bin/env python3
"""
Configuration management for the Smart Trading Agent
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class TradingRuleConfig:
    """Configuration for a trading rule"""
    name: str
    description: str
    target_allocation: float  # percentage (0-100)
    symbols: List[str]
    max_position_size: float = 10.0  # max % of portfolio per position
    stop_loss: float = -30.0  # stop loss percentage
    take_profit: float = 50.0  # take profit percentage
    enabled: bool = True

@dataclass
class SmartTraderConfig:
    """Main configuration for the Smart Trading Agent"""
    
    # API Configuration
    mcp_url: str = "http://127.0.0.1:8001/mcp"
    openai_api_key: Optional[str] = None
    
    # Trading Parameters
    risk_threshold: float = 1000.0  # max dollar risk per trade
    paper_trading: bool = True
    max_positions: int = 50
    
    # Loop Configuration
    loop_interval_hours: int = 24
    enable_continuous_loop: bool = False
    
    # Safety Settings
    max_trade_value: float = 10000.0  # max dollar value per trade
    max_portfolio_change: float = 5.0  # max % portfolio change per loop
    require_whatif: bool = True
    
    # Logging
    log_level: str = "INFO"
    save_reflections: bool = True
    log_file: str = "smart_agent/trading_log.log"
    
    # Trading Rules
    trading_rules: List[TradingRuleConfig] = None
    
    def __post_init__(self):
        """Initialize default trading rules if none provided"""
        if self.trading_rules is None:
            self.trading_rules = self._get_default_trading_rules()
    
    def _get_default_trading_rules(self) -> List[TradingRuleConfig]:
        """Get the default 70/15/15 trading strategy"""
        return [
            TradingRuleConfig(
                name="Broad ETFs",
                description="Diversified ETF holdings for stability and broad market exposure",
                target_allocation=70.0,
                symbols=["SPY", "VTI", "VOO", "QQQ", "IWM"],
                max_position_size=25.0,
                stop_loss=-20.0,
                take_profit=30.0
            ),
            TradingRuleConfig(
                name="Dividend Stocks",
                description="Steady dividend-paying stocks for income",
                target_allocation=15.0,
                symbols=["JNJ", "PG", "KO", "T", "VZ", "PFE", "XOM"],
                max_position_size=5.0,
                stop_loss=-25.0,
                take_profit=20.0
            ),
            TradingRuleConfig(
                name="Growth/Speculative",
                description="Higher growth potential with higher risk",
                target_allocation=15.0,
                symbols=["TSLA", "NVDA", "AMZN", "GOOGL", "MSFT", "AAPL"],
                max_position_size=8.0,
                stop_loss=-35.0,
                take_profit=60.0
            )
        ]
    
    @classmethod
    def from_env(cls) -> 'SmartTraderConfig':
        """Create configuration from environment variables"""
        return cls(
            mcp_url=os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            risk_threshold=float(os.getenv("RISK_THRESHOLD", "1000.0")),
            paper_trading=os.getenv("PAPER_TRADING", "true").lower() == "true",
            max_positions=int(os.getenv("MAX_POSITIONS", "50")),
            loop_interval_hours=int(os.getenv("LOOP_INTERVAL_HOURS", "24")),
            enable_continuous_loop=os.getenv("ENABLE_CONTINUOUS_LOOP", "false").lower() == "true",
            max_trade_value=float(os.getenv("MAX_TRADE_VALUE", "10000.0")),
            max_portfolio_change=float(os.getenv("MAX_PORTFOLIO_CHANGE", "5.0")),
            require_whatif=os.getenv("REQUIRE_WHATIF", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            save_reflections=os.getenv("SAVE_REFLECTIONS", "true").lower() == "true",
            log_file=os.getenv("LOG_FILE", "smart_agent/trading_log.log")
        )
    
    @classmethod
    def from_file(cls, config_path: str = "smart_agent/config.json") -> 'SmartTraderConfig':
        """Load configuration from JSON file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Create default config file
            default_config = cls.from_env()
            default_config.save_to_file(config_path)
            return default_config
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Handle trading rules separately
            trading_rules = []
            if "trading_rules" in config_data:
                for rule_data in config_data["trading_rules"]:
                    trading_rules.append(TradingRuleConfig(**rule_data))
                config_data["trading_rules"] = trading_rules
            
            return cls(**config_data)
            
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            print("Using default configuration...")
            return cls.from_env()
    
    def save_to_file(self, config_path: str = "smart_agent/config.json"):
        """Save configuration to JSON file"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for JSON serialization
        config_dict = asdict(self)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            print(f"Configuration saved to {config_path}")
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate allocations sum to ~100%
        total_allocation = sum(rule.target_allocation for rule in self.trading_rules if rule.enabled)
        if abs(total_allocation - 100.0) > 1.0:
            issues.append(f"Total allocation is {total_allocation}%, should be close to 100%")
        
        # Validate risk parameters
        if self.risk_threshold <= 0:
            issues.append("Risk threshold must be positive")
        
        if self.max_trade_value <= 0:
            issues.append("Max trade value must be positive")
        
        if not (0 < self.max_portfolio_change <= 100):
            issues.append("Max portfolio change must be between 0 and 100%")
        
        # Validate trading rules
        for rule in self.trading_rules:
            if not rule.symbols:
                issues.append(f"Rule '{rule.name}' has no symbols")
            
            if not (0 <= rule.target_allocation <= 100):
                issues.append(f"Rule '{rule.name}' allocation must be 0-100%")
            
            if not (0 < rule.max_position_size <= 100):
                issues.append(f"Rule '{rule.name}' max position size must be 0-100%")
        
        # Validate API configuration
        if not self.mcp_url:
            issues.append("MCP URL is required")
        
        return issues
    
    def get_all_symbols(self) -> List[str]:
        """Get all unique symbols from all enabled trading rules"""
        symbols = set()
        for rule in self.trading_rules:
            if rule.enabled:
                symbols.update(rule.symbols)
        return sorted(list(symbols))
    
    def get_rule_by_symbol(self, symbol: str) -> Optional[TradingRuleConfig]:
        """Get the trading rule that contains a specific symbol"""
        for rule in self.trading_rules:
            if rule.enabled and symbol in rule.symbols:
                return rule
        return None
    
    def print_summary(self):
        """Print a summary of the configuration"""
        print("=" * 60)
        print("🔧 SMART TRADER CONFIGURATION")
        print("=" * 60)
        print(f"MCP URL: {self.mcp_url}")
        print(f"OpenAI Enabled: {'Yes' if self.openai_api_key else 'No'}")
        print(f"Paper Trading: {'ENABLED' if self.paper_trading else 'DISABLED'}")
        print(f"Risk Threshold: ${self.risk_threshold:,.2f}")
        print(f"Max Trade Value: ${self.max_trade_value:,.2f}")
        print(f"Loop Interval: {self.loop_interval_hours} hours")
        print()
        
        print("📊 TRADING RULES:")
        total_allocation = 0
        for i, rule in enumerate(self.trading_rules, 1):
            status = "✅" if rule.enabled else "❌"
            print(f"{status} {i}. {rule.name}")
            print(f"    Target: {rule.target_allocation}%")
            print(f"    Symbols: {', '.join(rule.symbols)}")
            print(f"    Max Position: {rule.max_position_size}%")
            print(f"    Stop Loss: {rule.stop_loss}%")
            print(f"    Take Profit: {rule.take_profit}%")
            print()
            if rule.enabled:
                total_allocation += rule.target_allocation
        
        print(f"📈 Total Allocation: {total_allocation}%")
        print(f"📝 Total Symbols: {len(self.get_all_symbols())}")
        
        # Validation
        issues = self.validate()
        if issues:
            print("\n⚠️  CONFIGURATION ISSUES:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("\n✅ Configuration is valid!")
        
        print("=" * 60)

class ConfigManager:
    """Helper class for managing configuration"""
    
    @staticmethod
    def create_sample_configs():
        """Create sample configuration files"""
        
        # Conservative strategy
        conservative_config = SmartTraderConfig(
            risk_threshold=500.0,
            paper_trading=True,
            trading_rules=[
                TradingRuleConfig(
                    name="Safe ETFs",
                    description="Very safe, broad market ETFs",
                    target_allocation=80.0,
                    symbols=["SPY", "VTI", "BND"],
                    max_position_size=30.0,
                    stop_loss=-15.0,
                    take_profit=20.0
                ),
                TradingRuleConfig(
                    name="Dividend Stocks",
                    description="Stable dividend payers",
                    target_allocation=20.0,
                    symbols=["JNJ", "PG", "KO"],
                    max_position_size=8.0,
                    stop_loss=-20.0,
                    take_profit=15.0
                )
            ]
        )
        conservative_config.save_to_file("smart_agent/config_conservative.json")
        
        # Aggressive strategy
        aggressive_config = SmartTraderConfig(
            risk_threshold=2000.0,
            paper_trading=True,
            trading_rules=[
                TradingRuleConfig(
                    name="Tech Growth",
                    description="High-growth technology stocks",
                    target_allocation=50.0,
                    symbols=["NVDA", "TSLA", "AMZN", "GOOGL", "MSFT"],
                    max_position_size=15.0,
                    stop_loss=-40.0,
                    take_profit=80.0
                ),
                TradingRuleConfig(
                    name="Market ETFs",
                    description="Broad market exposure",
                    target_allocation=30.0,
                    symbols=["QQQ", "IWM", "VTI"],
                    max_position_size=15.0,
                    stop_loss=-25.0,
                    take_profit=40.0
                ),
                TradingRuleConfig(
                    name="Speculative",
                    description="High-risk, high-reward positions",
                    target_allocation=20.0,
                    symbols=["ARKK", "PLTR", "AMD", "CRM"],
                    max_position_size=10.0,
                    stop_loss=-50.0,
                    take_profit=100.0
                )
            ]
        )
        aggressive_config.save_to_file("smart_agent/config_aggressive.json")
        
        print("Sample configuration files created:")
        print("  • smart_agent/config_conservative.json")
        print("  • smart_agent/config_aggressive.json")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-samples":
            ConfigManager.create_sample_configs()
        elif sys.argv[1] == "validate":
            config_file = sys.argv[2] if len(sys.argv) > 2 else "smart_agent/config.json"
            config = SmartTraderConfig.from_file(config_file)
            config.print_summary()
        else:
            print("Usage:")
            print("  python config.py create-samples   # Create sample config files")
            print("  python config.py validate [file]  # Validate and show config")
    else:
        # Create default config and show summary
        config = SmartTraderConfig.from_env()
        config.save_to_file()
        config.print_summary()