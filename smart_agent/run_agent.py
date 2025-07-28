#!/usr/bin/env python3
"""
Smart Trading Agent Runner - Modular Architecture

Advanced script to run the new modular smart trading agent with AI-driven
MCP tool selection and separate step modules.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from smart_agent.orchestrator import SmartTradingOrchestrator
from smart_agent.config import SmartTraderConfig, ConfigManager

def print_banner():
    """Print the application banner"""
    print("""
🤖 SMART TRADING AGENT - MODULAR ARCHITECTURE
═══════════════════════════════════════════════════════════════
Advanced AI-powered trading system with modular step agents that
intelligently use MCP tools and OpenAI O3 for decision making.

The 4-step loop with AI-driven MCP integration:
1. 🔍 SENSE - AI decides what market/portfolio data to gather
2. 🧠 THINK - O3 analyzes data and makes intelligent decisions  
3. ⚡ ACT - AI validates and executes trades with safety checks
4. 🤔 REFLECT - AI learns from outcomes and improves performance
═══════════════════════════════════════════════════════════════
""")

def print_usage():
    """Print usage instructions"""
    print("""
📋 SETUP INSTRUCTIONS:

1. 📊 Start IB Gateway/TWS and log in to your account
2. 🚀 Start the MCP server:
   source .venv/bin/activate && python mcp_server.py
3. 🔑 Set your OpenAI API key (REQUIRED for O3 intelligence):
   export OPENAI_API_KEY="your-api-key-here"
4. ⚙️  Configure your trading preferences in smart_agent/config.json
5. 🏃 Run the modular agent!

🚀 RUNNING THE MODULAR AGENT:

Basic usage:
  python smart_agent/run_agent.py                    # Single session with AI intelligence
  python smart_agent/run_agent.py --continuous       # Continuous AI-driven sessions
  python smart_agent/run_agent.py --config conservative.json  # Custom strategy

Advanced options:
  python smart_agent/run_agent.py --health-check     # System health diagnostics
  python smart_agent/run_agent.py --paper-trading    # Safe mode (recommended)
  python smart_agent/run_agent.py --live-trading     # Live trading mode
  python smart_agent/run_agent.py --interval 6       # Every 6 hours
  python smart_agent/run_agent.py --max-sessions 5   # Limit continuous runs

New modular features:
  python smart_agent/run_agent.py --test-agents      # Test individual step agents
  python smart_agent/run_agent.py --emergency-stop   # Cancel all live orders
  python smart_agent/run_agent.py --performance      # Show performance stats

🔧 ENVIRONMENT VARIABLES:
  OPENAI_API_KEY       - Your OpenAI API key (REQUIRED for AI features)
  MCP_URL             - MCP server URL (default: http://127.0.0.1:8001/mcp)
  PAPER_TRADING       - Enable paper trading (default: true)
  RISK_THRESHOLD      - Max $ risk per trade (default: 1000)
  LOG_LEVEL           - Logging level (default: INFO)
""")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Smart Trading Agent - Modular AI-powered portfolio management",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Running mode
    parser.add_argument("--continuous", action="store_true",
                       help="Run continuously at intervals")
    parser.add_argument("--interval", type=int, default=None,
                       help="Hours between runs in continuous mode (default: 24)")
    parser.add_argument("--max-sessions", type=int, default=None,
                       help="Maximum number of sessions in continuous mode")
    
    # Configuration
    parser.add_argument("--config", type=str, default="smart_agent/config.json",
                       help="Configuration file path")
    parser.add_argument("--create-config", action="store_true",
                       help="Create default configuration and exit")
    parser.add_argument("--validate-config", action="store_true",
                       help="Validate configuration and exit")
    
    # Override options
    parser.add_argument("--paper-trading", action="store_true",
                       help="Force paper trading mode")
    parser.add_argument("--live-trading", action="store_true",
                       help="Force live trading mode")
    parser.add_argument("--risk-threshold", type=float,
                       help="Override risk threshold")
    parser.add_argument("--mcp-url", type=str,
                       help="Override MCP server URL")
    parser.add_argument("--openai-key", type=str,
                       help="Override OpenAI API key")
    
    # New modular features
    parser.add_argument("--health-check", action="store_true",
                       help="Perform system health check and exit")
    parser.add_argument("--test-agents", action="store_true",
                       help="Test individual step agents and exit")
    parser.add_argument("--emergency-stop", action="store_true",
                       help="Emergency stop all operations and cancel orders")
    parser.add_argument("--performance", action="store_true",
                       help="Show performance statistics and exit")
    
    # Utilities
    parser.add_argument("--help-setup", action="store_true",
                       help="Show detailed setup instructions")
    parser.add_argument("--create-samples", action="store_true",
                       help="Create sample configuration files")
    
    args = parser.parse_args()
    
    # Handle utility commands
    if args.help_setup:
        print_banner()
        print_usage()
        return
    
    if args.create_samples:
        ConfigManager.create_sample_configs()
        return
    
    if args.create_config:
        config = SmartTraderConfig.from_env()
        config.save_to_file(args.config)
        print(f"✅ Default configuration created at {args.config}")
        config.print_summary()
        return
    
    # Load configuration
    try:
        config = SmartTraderConfig.from_file(args.config)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("💡 Try: python smart_agent/run_agent.py --create-config")
        return
    
    if args.validate_config:
        config.print_summary()
        return
    
    # Apply command line overrides
    if args.paper_trading and args.live_trading:
        print("❌ Cannot specify both --paper-trading and --live-trading")
        return
    
    if args.paper_trading:
        config.paper_trading = True
    elif args.live_trading:
        config.paper_trading = False
    
    if args.risk_threshold:
        config.risk_threshold = args.risk_threshold
    
    if args.mcp_url:
        config.mcp_url = args.mcp_url
    
    if args.openai_key:
        config.openai_api_key = args.openai_key
    
    if args.interval:
        config.loop_interval_hours = args.interval
    
    # Validate configuration
    issues = config.validate()
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 Fix these issues before running the agent")
        return
    
    # Show configuration summary
    print_banner()
    config.print_summary()
    
    # Safety confirmation for live trading
    if not config.paper_trading:
        print("\n⚠️  WARNING: LIVE TRADING MODE ENABLED!")
        print("This will place real trades with real money.")
        response = input("\nDo you want to continue? (type 'YES' to confirm): ")
        if response != "YES":
            print("👋 Aborted by user")
            return
    
    # Handle new modular features first
    if args.health_check or args.test_agents or args.emergency_stop or args.performance:
        orchestrator = SmartTradingOrchestrator(config)
        
        if args.health_check:
            print("\n🔍 Performing system health check...")
            health = await orchestrator.health_check()
            print("\n=== SYSTEM HEALTH REPORT ===")
            print(json.dumps(health, indent=2))
            
            if health["orchestrator_status"] == "healthy":
                print("\n✅ System is healthy and ready for trading")
            else:
                print(f"\n⚠️  System status: {health['orchestrator_status']}")
                if health["issues"]:
                    print("Issues found:")
                    for issue in health["issues"]:
                        print(f"  • {issue}")
            return
        
        if args.test_agents:
            print("\n🧪 Testing individual step agents...")
            try:
                await orchestrator.initialize()
                
                # Test each agent with minimal context
                test_context = {
                    'config': config.__dict__,
                    'trading_rules': [
                        {
                            'name': rule.name,
                            'symbols': rule.symbols[:2],  # Limit symbols for testing
                            'target_allocation': rule.target_allocation
                        }
                        for rule in config.trading_rules[:1] if rule.enabled  # Test with one rule
                    ]
                }
                
                print("Testing SENSE agent...")
                sense_result = await orchestrator.sense_agent.execute_step(test_context)
                print(f"  SENSE: {'✅' if sense_result.get('success') else '❌'}")
                
                if sense_result.get('success'):
                    test_context['sense_data'] = sense_result.get('data')
                    
                    print("Testing THINK agent...")
                    think_result = await orchestrator.think_agent.execute_step(test_context)
                    print(f"  THINK: {'✅' if think_result.get('success') else '❌'}")
                    
                    if think_result.get('success'):
                        test_context['think_data'] = think_result.get('data')
                        
                        print("Testing ACT agent...")
                        act_result = await orchestrator.act_agent.execute_step(test_context)
                        print(f"  ACT: {'✅' if act_result.get('success') else '❌'}")
                        
                        test_context['act_data'] = act_result.get('data')
                        
                        print("Testing REFLECT agent...")
                        reflect_result = await orchestrator.reflect_agent.execute_step(test_context)
                        print(f"  REFLECT: {'✅' if reflect_result.get('success') else '❌'}")
                
                print("\n✅ Agent testing completed")
                
            except Exception as e:
                print(f"❌ Agent testing failed: {e}")
            return
        
        if args.emergency_stop:
            print("\n🛑 Initiating emergency stop...")
            try:
                await orchestrator.emergency_stop()
                print("✅ Emergency stop completed")
            except Exception as e:
                print(f"❌ Emergency stop failed: {e}")
            return
        
        if args.performance:
            print("\n📊 Performance statistics...")
            try:
                stats = orchestrator.get_performance_stats()
                print("\n=== PERFORMANCE STATS ===")
                print(json.dumps(stats, indent=2))
            except Exception as e:
                print(f"❌ Failed to get performance stats: {e}")
            return
    
    # Create and initialize orchestrator for normal operation
    try:
        print("\n🤖 Initializing Smart Trading Orchestrator...")
        
        orchestrator = SmartTradingOrchestrator(config)
        
        # Run the orchestrator
        if args.continuous:
            interval = args.interval or config.loop_interval_hours
            print(f"🔄 Starting continuous mode (every {interval} hours)")
            if args.max_sessions:
                print(f"📊 Limited to {args.max_sessions} sessions")
            
            await orchestrator.run_continuous_loop(
                interval_hours=interval,
                max_sessions=args.max_sessions
            )
        else:
            print("🚀 Running single trading session...")
            session = await orchestrator.run_single_session()
            
            print(f"\n🎉 Trading session completed!")
            print(f"Success: {'✅' if session.success else '❌'}")
            print(f"Runtime: {session.total_runtime:.1f} seconds")
            
            if session.success:
                # Extract key metrics
                sense_data = session.sense_result.get('data')
                think_data = session.think_result.get('data')
                act_data = session.act_result.get('data')
                reflect_data = session.reflect_result.get('data')
                
                if think_data:
                    decisions = getattr(think_data, 'decisions', [])
                    print(f"Decisions: {len(decisions)}")
                
                if act_data:
                    trades_attempted = getattr(act_data, 'trades_attempted', 0)
                    trades_successful = getattr(act_data, 'trades_successful', 0)
                    print(f"Trades: {trades_successful}/{trades_attempted}")
                
                if reflect_data:
                    lessons = getattr(reflect_data, 'lessons_learned', [])
                    print(f"Lessons learned: {len(lessons)}")
            else:
                print(f"Error: {session.error_message}")
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running orchestrator: {e}")
        print("💡 Check that:")
        print("   • IB Gateway/TWS is running and logged in")
        print("   • MCP server is running (python mcp_server.py)")
        print("   • OpenAI API key is valid and has credits")
        print("   • Network connection is stable")

if __name__ == "__main__":
    asyncio.run(main())