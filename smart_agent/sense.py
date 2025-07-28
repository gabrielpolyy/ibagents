#!/usr/bin/env python3
"""
SENSE Step - Intelligent Market and Portfolio Data Gathering

This module implements Step 1 of the trading loop where the AI intelligently
gathers all necessary market and portfolio information using MCP tools.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_agent import StepAgent

logger = logging.getLogger(__name__)

@dataclass
class SenseData:
    """Structured data from the SENSE step"""
    timestamp: datetime
    account_summary: Dict[str, Any]
    positions: List[Dict[str, Any]]
    market_data: Dict[str, Dict[str, Any]]  # symbol -> market data
    pnl_data: List[Dict[str, Any]]
    portfolio_health: Dict[str, Any]
    total_portfolio_value: float
    available_funds: float
    cash_percentage: float
    position_count: int
    symbols_tracked: List[str]

class SenseAgent(StepAgent):
    """
    SENSE Agent - Intelligently gathers market and portfolio data
    
    This agent uses AI to decide what information to gather based on:
    - Trading rules and symbols of interest
    - Current market conditions
    - Portfolio complexity
    - Risk assessment needs
    """
    
    def __init__(self, 
                 mcp_url: str = "http://127.0.0.1:8001/mcp",
                 openai_api_key: str = None,
                 model: str = "o3-mini"):
        super().__init__("SENSE", mcp_url, openai_api_key, model)
        
    async def execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the SENSE step using AI to intelligently gather data
        
        Args:
            context: Context including trading_rules, config, etc.
            
        Returns:
            Comprehensive market and portfolio data
        """
        self.log_step_start()
        
        # Extract trading rules and symbols of interest
        trading_rules = context.get('trading_rules', [])
        config = context.get('config', {})
        
        # Get all symbols from trading rules
        all_symbols = []
        for rule in trading_rules:
            all_symbols.extend(rule.get('symbols', []))
        all_symbols = list(set(all_symbols))  # Remove duplicates
        
        sense_context = {
            "symbols_of_interest": all_symbols,
            "trading_rules": trading_rules,
            "risk_threshold": config.get('risk_threshold', 1000.0),
            "paper_trading": config.get('paper_trading', True),
            "max_positions": config.get('max_positions', 50)
        }
        
        # Let AI decide what data to gather
        ai_task = f"""
        Gather comprehensive market and portfolio data for intelligent trading decisions.
        
        OBJECTIVES:
        1. Get current account summary and portfolio health
        2. Retrieve all current positions with market values
        3. Get real-time market data for symbols: {', '.join(all_symbols)}
        4. Analyze current P&L and performance
        5. Assess portfolio allocation vs targets
        
        TRADING RULES CONTEXT:
        {json.dumps(trading_rules, indent=2)}
        
        Focus on gathering data that will help with:
        - Allocation analysis (current vs target percentages)
        - Risk assessment (position sizes, concentration)
        - Market timing (current prices, volatility, trends)
        - Performance tracking (P&L, returns)
        
        Gather data systematically, starting with account-level information,
        then positions, then market data for relevant symbols.
        """
        
        try:
            # Let AI decide and execute data gathering
            ai_result = await self.ai_decide_and_execute(ai_task, sense_context)
            
            # Process and structure the gathered data
            sense_data = await self._process_ai_results(ai_result, all_symbols)
            
            # Log summary
            summary = (f"Portfolio: ${sense_data.total_portfolio_value:,.2f}, "
                      f"Positions: {sense_data.position_count}, "
                      f"Symbols: {len(sense_data.symbols_tracked)}")
            self.log_step_complete(summary)
            
            return {
                'step': 'SENSE',
                'timestamp': sense_data.timestamp.isoformat(),
                'success': True,
                'data': sense_data,
                'ai_reasoning': ai_result.get('reasoning', []),
                'tool_calls_made': len(ai_result.get('tool_calls', [])),
                'raw_ai_result': ai_result
            }
            
        except Exception as e:
            self.step_logger.error(f"SENSE step failed: {e}")
            
            # Fallback to basic data gathering
            fallback_data = await self._fallback_data_gathering(all_symbols)
            
            return {
                'step': 'SENSE',
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'data': fallback_data,
                'fallback_used': True
            }
    
    async def _process_ai_results(self, ai_result: Dict[str, Any], symbols: List[str]) -> SenseData:
        """
        Process AI results into structured SenseData
        
        Args:
            ai_result: Results from AI decision making
            symbols: List of symbols we're interested in
            
        Returns:
            Structured SenseData object
        """
        # Extract data from AI tool calls
        account_summary = {}
        positions = []
        market_data = {}
        pnl_data = []
        portfolio_health = {}
        
        for tool_call in ai_result.get('tool_calls', []):
            if not tool_call['success']:
                continue
                
            tool_name = tool_call['tool_name']
            result = tool_call['result']
            
            if tool_name == 'get_portfolio_summary':
                account_summary = result.get('summary', {})
            elif tool_name == 'get_positions':
                positions = result.get('positions', [])
            elif tool_name == 'get_market_snapshot':
                # Extract symbol from the result or parameters
                symbol = self._extract_symbol_from_result(tool_call)
                if symbol:
                    market_data[symbol] = result.get('snapshot', {})
            elif tool_name == 'find_contract':
                # Contract info - might be used for market data
                pass
            elif tool_name == 'get_pnl':
                pnl_data = result.get('pnl', [])
            elif tool_name == 'portfolio_health_check':
                portfolio_health = result.get('health_metrics', {})
        
        # Calculate derived metrics
        total_portfolio_value = float(account_summary.get('netliquidation', 0))
        available_funds = float(account_summary.get('availablefunds', 0))
        cash_percentage = (available_funds / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        position_count = len(positions)
        symbols_tracked = list(market_data.keys())
        
        return SenseData(
            timestamp=datetime.now(),
            account_summary=account_summary,
            positions=positions,
            market_data=market_data,
            pnl_data=pnl_data,
            portfolio_health=portfolio_health,
            total_portfolio_value=total_portfolio_value,
            available_funds=available_funds,
            cash_percentage=cash_percentage,
            position_count=position_count,
            symbols_tracked=symbols_tracked
        )
    
    def _extract_symbol_from_result(self, tool_call: Dict[str, Any]) -> Optional[str]:
        """Extract symbol from tool call parameters or result"""
        # Try to get symbol from parameters
        params = tool_call.get('parameters', {})
        if 'symbol' in params:
            return params['symbol']
        
        # Try to extract from result
        result = tool_call.get('result', {})
        if isinstance(result, dict) and 'contract' in result:
            contract = result['contract']
            if 'symbol' in contract:
                return contract['symbol']
        
        return None
    
    async def _fallback_data_gathering(self, symbols: List[str]) -> Optional[SenseData]:
        """
        Fallback method for basic data gathering if AI fails
        
        Args:
            symbols: List of symbols to get data for
            
        Returns:
            Basic SenseData or None if failed
        """
        self.step_logger.info("Using fallback data gathering method...")
        
        try:
            # Basic account summary
            summary_result = await self.call_mcp_tool("get_portfolio_summary")
            account_summary = summary_result.data.get('summary', {}) if summary_result.success else {}
            
            # Basic positions
            positions_result = await self.call_mcp_tool("get_positions", {"max_positions": 50})
            positions = positions_result.data.get('positions', []) if positions_result.success else []
            
            # Basic P&L
            pnl_result = await self.call_mcp_tool("get_pnl")
            pnl_data = pnl_result.data.get('pnl', []) if pnl_result.success else []
            
            # Try to get market data for key symbols (limit to avoid overload)
            market_data = {}
            for symbol in symbols[:10]:  # Limit to first 10 symbols
                try:
                    # Find contract
                    contract_result = await self.call_mcp_tool("find_contract", {
                        "symbol": symbol, 
                        "sec_type": "STK"
                    })
                    
                    if contract_result.success and 'conid' in contract_result.data:
                        conid = contract_result.data['conid']
                        
                        # Get snapshot
                        snapshot_result = await self.call_mcp_tool("get_market_snapshot", {
                            "conid": conid
                        })
                        
                        if snapshot_result.success:
                            market_data[symbol] = snapshot_result.data.get('snapshot', {})
                            
                except Exception as e:
                    self.step_logger.warning(f"Failed to get market data for {symbol}: {e}")
                    continue
            
            # Calculate basic metrics
            total_portfolio_value = float(account_summary.get('netliquidation', 0))
            available_funds = float(account_summary.get('availablefunds', 0))
            cash_percentage = (available_funds / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            
            return SenseData(
                timestamp=datetime.now(),
                account_summary=account_summary,
                positions=positions,
                market_data=market_data,
                pnl_data=pnl_data,
                portfolio_health={
                    "total_value": total_portfolio_value,
                    "available_funds": available_funds,
                    "cash_percentage": cash_percentage,
                    "total_positions": len(positions)
                },
                total_portfolio_value=total_portfolio_value,
                available_funds=available_funds,
                cash_percentage=cash_percentage,
                position_count=len(positions),
                symbols_tracked=list(market_data.keys())
            )
            
        except Exception as e:
            self.step_logger.error(f"Fallback data gathering failed: {e}")
            return None
    
    async def get_enhanced_market_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Let AI perform enhanced market analysis for specific symbols
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            Enhanced market analysis data
        """
        ai_task = f"""
        Perform enhanced market analysis for the following symbols: {', '.join(symbols)}
        
        For each symbol, gather:
        1. Current market snapshot (price, volume, bid/ask)
        2. Recent historical data (1-week price action)
        3. Stock analysis with portfolio context
        
        Focus on information that would be useful for:
        - Entry/exit timing decisions
        - Risk assessment
        - Portfolio allocation decisions
        
        Prioritize the most liquid and actively traded symbols first.
        """
        
        try:
            result = await self.ai_decide_and_execute(
                ai_task, 
                {"symbols": symbols, "analysis_type": "enhanced_market"}
            )
            return result
        except Exception as e:
            self.step_logger.error(f"Enhanced market analysis failed: {e}")
            return {"error": str(e)}
    
    async def get_portfolio_drift_analysis(self, trading_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how much the portfolio has drifted from target allocations
        
        Args:
            trading_rules: List of trading rules with target allocations
            
        Returns:
            Portfolio drift analysis
        """
        ai_task = """
        Analyze portfolio drift from target allocations.
        
        Steps:
        1. Get current portfolio positions and values
        2. Calculate current allocation percentages by category
        3. Compare against target allocations from trading rules
        4. Identify the biggest deviations that need rebalancing
        
        Provide specific recommendations for which positions are over/under-allocated.
        """
        
        context = {
            "trading_rules": trading_rules,
            "analysis_type": "portfolio_drift"
        }
        
        try:
            result = await self.ai_decide_and_execute(ai_task, context)
            return result
        except Exception as e:
            self.step_logger.error(f"Portfolio drift analysis failed: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    import os
    
    # Example usage and testing
    async def test_sense_agent():
        agent = SenseAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        await agent.initialize()
        
        # Mock trading rules
        context = {
            "trading_rules": [
                {
                    "name": "Broad ETFs",
                    "target_allocation": 70.0,
                    "symbols": ["SPY", "VTI", "QQQ"]
                },
                {
                    "name": "Dividend Stocks", 
                    "target_allocation": 30.0,
                    "symbols": ["JNJ", "PG"]
                }
            ],
            "config": {
                "risk_threshold": 1000.0,
                "paper_trading": True
            }
        }
        
        result = await agent.execute_step(context)
        
        print("=== SENSE STEP RESULT ===")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            sense_data = result['data']
            print(f"\n=== SUMMARY ===")
            print(f"Portfolio Value: ${sense_data.total_portfolio_value:,.2f}")
            print(f"Available Funds: ${sense_data.available_funds:,.2f}")
            print(f"Positions: {sense_data.position_count}")
            print(f"Symbols Tracked: {len(sense_data.symbols_tracked)}")
            print(f"Cash %: {sense_data.cash_percentage:.1f}%")
    
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_sense_agent())
    else:
        print("Set OPENAI_API_KEY to test the SENSE agent")