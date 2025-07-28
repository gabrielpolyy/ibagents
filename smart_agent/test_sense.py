#!/usr/bin/env python3
"""
SENSE Step Tester

Dedicated test script for the SENSE agent to validate data gathering
and AI-driven MCP tool selection.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from smart_agent.sense import SenseAgent
from smart_agent.config import SmartTraderConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_sense_basic():
    """Test basic SENSE functionality"""
    print("🔍 Testing SENSE Agent - Basic Functionality")
    print("=" * 60)
    
    # Create SENSE agent
    agent = SenseAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="o3"
    )
    
    try:
        # Initialize agent
        print("Initializing SENSE agent...")
        await agent.initialize()
        print(f"✅ Agent initialized with {len(agent.get_available_tools())} MCP tools")
        
        # Basic context for testing
        test_context = {
            'trading_rules': [
                {
                    'name': 'Broad ETFs',
                    'target_allocation': 70.0,
                    'symbols': ['SPY', 'VTI', 'QQQ'],
                    'description': 'Core market exposure'
                },
                {
                    'name': 'Dividend Stocks',
                    'target_allocation': 30.0,
                    'symbols': ['JNJ', 'PG', 'KO'],
                    'description': 'Income generating stocks'
                }
            ],
            'config': {
                'risk_threshold': 1000.0,
                'paper_trading': True,
                'max_positions': 20
            }
        }
        
        # Execute SENSE step
        print("\n🤖 Executing SENSE step with AI-driven tool selection...")
        result = await agent.execute_step(test_context)
        
        print("\n📊 SENSE Results:")
        print(f"Success: {'✅' if result['success'] else '❌'}")
        print(f"Tool calls made: {result.get('tool_calls_made', 0)}")
        
        if result['success']:
            sense_data = result['data']
            print(f"Portfolio Value: ${sense_data.total_portfolio_value:,.2f}")
            print(f"Available Funds: ${sense_data.available_funds:,.2f}")
            print(f"Position Count: {sense_data.position_count}")
            print(f"Symbols Tracked: {len(sense_data.symbols_tracked)}")
            print(f"Cash Percentage: {sense_data.cash_percentage:.1f}%")
            
            if sense_data.symbols_tracked:
                print(f"Market Data Symbols: {', '.join(sense_data.symbols_tracked)}")
        
        # Show AI reasoning
        ai_reasoning = result.get('ai_reasoning', [])
        if ai_reasoning:
            print(f"\n🧠 AI Reasoning ({len(ai_reasoning)} insights):")
            for i, reason in enumerate(ai_reasoning[:3], 1):
                print(f"  {i}. {reason}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

async def test_sense_enhanced():
    """Test enhanced SENSE functionality with specific analysis"""
    print("\n🔍 Testing SENSE Agent - Enhanced Analysis")
    print("=" * 60)
    
    agent = SenseAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="o3-mini"
    )
    
    try:
        await agent.initialize()
        
        # Test enhanced market analysis
        symbols = ['SPY', 'QQQ', 'NVDA', 'JNJ']
        print(f"🔬 Testing enhanced market analysis for: {', '.join(symbols)}")
        
        enhanced_result = await agent.get_enhanced_market_analysis(symbols)
        
        print("Enhanced Analysis Results:")
        print(f"Tool calls made: {len(enhanced_result.get('tool_calls', []))}")
        print(f"Final analysis: {enhanced_result.get('final_result', 'No result')[:200]}...")
        
        return enhanced_result
        
    except Exception as e:
        print(f"❌ Enhanced test failed: {e}")
        return None

async def test_sense_portfolio_drift():
    """Test portfolio drift analysis"""
    print("\n🔍 Testing SENSE Agent - Portfolio Drift Analysis")
    print("=" * 60)
    
    agent = SenseAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="o3-mini"
    )
    
    try:
        await agent.initialize()
        
        # Mock trading rules for drift analysis
        trading_rules = [
            {
                'name': 'Technology',
                'target_allocation': 40.0,
                'symbols': ['AAPL', 'MSFT', 'GOOGL'],
                'description': 'Tech sector exposure'
            },
            {
                'name': 'Healthcare',
                'target_allocation': 30.0,
                'symbols': ['JNJ', 'PFE', 'UNH'],
                'description': 'Healthcare sector'
            },
            {
                'name': 'ETFs',
                'target_allocation': 30.0,
                'symbols': ['SPY', 'VTI'],
                'description': 'Broad market ETFs'
            }
        ]
        
        print("🎯 Analyzing portfolio drift vs target allocations...")
        drift_result = await agent.get_portfolio_drift_analysis(trading_rules)
        
        print("Portfolio Drift Analysis:")
        print(f"Tool calls made: {len(drift_result.get('tool_calls', []))}")
        print(f"Analysis summary: {drift_result.get('final_result', 'No result')[:300]}...")
        
        return drift_result
        
    except Exception as e:
        print(f"❌ Drift analysis failed: {e}")
        return None

async def test_sense_tool_selection():
    """Test AI tool selection capabilities"""
    print("\n🔍 Testing SENSE Agent - AI Tool Selection")
    print("=" * 60)
    
    agent = SenseAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="o3-mini"
    )
    
    try:
        await agent.initialize()
        
        # Show available tools
        tools = agent.get_available_tools()
        print(f"📋 Available MCP Tools ({len(tools)}):")
        
        # Group tools by category
        tool_categories = {}
        for tool_name, tool_info in tools.items():
            tags = tool_info.get('tags', ['general'])
            for tag in tags:
                if tag not in tool_categories:
                    tool_categories[tag] = []
                tool_categories[tag].append(tool_name)
        
        for category, tool_names in tool_categories.items():
            print(f"  📂 {category.upper()}: {', '.join(tool_names)}")
        
        # Test AI decision making for tool selection
        print(f"\n🤖 Testing AI-driven tool selection...")
        
        test_task = """
        I need to understand my current portfolio allocation and get market data 
        for the top 5 technology stocks. Focus on tools that will help assess 
        whether I should rebalance my tech allocation.
        """
        
        ai_result = await agent.ai_decide_and_execute(
            test_task,
            {"analysis_type": "tech_allocation_assessment"},
            max_tool_calls=8
        )
        
        print(f"AI Tool Selection Results:")
        print(f"Total tool calls: {len(ai_result.get('tool_calls', []))}")
        print(f"Successful calls: {len([t for t in ai_result.get('tool_calls', []) if t.get('success')])}")
        
        print(f"\n🛠️ Tools Used by AI:")
        for i, tool_call in enumerate(ai_result.get('tool_calls', []), 1):
            tool_name = tool_call['tool_name']
            success = '✅' if tool_call['success'] else '❌'
            reasoning = tool_call.get('reasoning', 'No reasoning provided')
            print(f"  {i}. {success} {tool_name}")
            print(f"     Reasoning: {reasoning}")
        
        return ai_result
        
    except Exception as e:
        print(f"❌ Tool selection test failed: {e}")
        return None

async def test_sense_fallback():
    """Test SENSE fallback functionality when AI is not available"""
    print("\n🔍 Testing SENSE Agent - Fallback Mode")
    print("=" * 60)
    
    # Create agent without OpenAI key to test fallback
    agent = SenseAgent(
        openai_api_key=None,  # No AI - should use fallback
        model="o3-mini"
    )
    
    try:
        await agent.initialize()
        
        test_context = {
            'trading_rules': [
                {
                    'name': 'Basic ETFs',
                    'target_allocation': 100.0,
                    'symbols': ['SPY', 'QQQ'],
                    'description': 'Simple ETF allocation'
                }
            ],
            'config': {
                'risk_threshold': 500.0,
                'paper_trading': True
            }
        }
        
        print("🔄 Testing fallback mode (no AI)...")
        result = await agent.execute_step(test_context)
        
        print(f"Fallback Success: {'✅' if result['success'] else '❌'}")
        print(f"Used fallback: {result.get('fallback_used', False)}")
        
        if result['success']:
            sense_data = result['data']
            if sense_data:
                print(f"Portfolio Value: ${sense_data.total_portfolio_value:,.2f}")
                print(f"Symbols Tracked: {len(sense_data.symbols_tracked)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return None

async def run_all_tests():
    """Run all SENSE tests"""
    print("🧪 SENSE AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: No OPENAI_API_KEY found. Some tests will use fallback mode.")
    
    test_results = {}
    
    # Run tests
    tests = [
        ("Basic Functionality", test_sense_basic),
        ("Enhanced Analysis", test_sense_enhanced),
        ("Portfolio Drift", test_sense_portfolio_drift),
        ("AI Tool Selection", test_sense_tool_selection),
        ("Fallback Mode", test_sense_fallback)
    ]
    
    for test_name, test_func in tests:
        print(f"\n" + "="*80)
        try:
            result = await test_func()
            test_results[test_name] = {
                'success': result is not None,
                'result': result
            }
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results[test_name] = {
                'success': False,
                'error': str(e)
            }
    
    # Summary
    print(f"\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = len([r for r in test_results.values() if r['success']])
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not result['success'] and 'error' in result:
            print(f"    Error: {result['error']}")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return test_results

def print_usage():
    """Print usage information"""
    print("""
🔍 SENSE AGENT TESTER

Test the SENSE step agent independently to validate data gathering
and AI-driven MCP tool selection.

USAGE:
  python smart_agent/test_sense.py [test_name]

AVAILABLE TESTS:
  basic       - Test basic SENSE functionality
  enhanced    - Test enhanced market analysis
  drift       - Test portfolio drift analysis  
  tools       - Test AI tool selection
  fallback    - Test fallback mode (no AI)
  all         - Run all tests (default)

EXAMPLES:
  python smart_agent/test_sense.py basic
  python smart_agent/test_sense.py tools
  python smart_agent/test_sense.py all

PREREQUISITES:
  • IB Gateway/TWS running and logged in
  • MCP server running (python mcp_server.py)
  • OPENAI_API_KEY set for AI features (optional for fallback test)
""")

async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "help" or test_name == "--help":
            print_usage()
            return
        elif test_name == "basic":
            await test_sense_basic()
        elif test_name == "enhanced":
            await test_sense_enhanced()
        elif test_name == "drift":
            await test_sense_portfolio_drift()
        elif test_name == "tools":
            await test_sense_tool_selection()
        elif test_name == "fallback":
            await test_sense_fallback()
        elif test_name == "all":
            await run_all_tests()
        else:
            print(f"❌ Unknown test: {test_name}")
            print_usage()
    else:
        # Default: run all tests
        await run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())