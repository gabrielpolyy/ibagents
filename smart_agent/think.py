#!/usr/bin/env python3
"""
THINK Step - AI-Powered Trading Decision Making

This module implements Step 2 of the trading loop where OpenAI O3 analyzes
market data and makes intelligent trading decisions using MCP tools for
additional analysis as needed.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .base_agent import StepAgent

logger = logging.getLogger(__name__)

@dataclass
class TradingDecision:
    """Represents a trading decision from the AI"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: int
    reasoning: str
    confidence: float
    urgency: str  # LOW, MEDIUM, HIGH
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    allocation_impact: Optional[float] = None  # Expected % change in allocation
    risk_score: Optional[float] = None  # 0-100, higher = riskier

@dataclass
class ThinkResult:
    """Result from the THINK step"""
    timestamp: datetime
    decisions: List[TradingDecision]
    market_analysis: Dict[str, Any]
    portfolio_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    ai_reasoning: List[str]
    confidence_score: float
    recommended_actions: List[str]

class ThinkAgent(StepAgent):
    """
    THINK Agent - AI-powered trading decision making
    
    This agent uses OpenAI O3 to:
    1. Analyze market data and portfolio state
    2. Make intelligent trading decisions
    3. Assess risk and portfolio allocation
    4. Use MCP tools for additional analysis when needed
    """
    
    def __init__(self, 
                 mcp_url: str = "http://127.0.0.1:8001/mcp",
                 openai_api_key: str = None,
                 model: str = "o3-mini"):
        super().__init__("THINK", mcp_url, openai_api_key, model)
        
    async def execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the THINK step using AI for trading decisions
        
        Args:
            context: Context including sense_data, trading_rules, config
            
        Returns:
            Trading decisions and analysis
        """
        self.log_step_start()
        
        if not self.openai_client:
            return await self._fallback_rule_based_thinking(context)
        
        try:
            # Extract context data
            sense_data = context.get('sense_data')
            trading_rules = context.get('trading_rules', [])
            config = context.get('config', {})
            
            if not sense_data:
                raise ValueError("No sense_data provided to THINK step")
            
            # Prepare comprehensive analysis prompt
            analysis_prompt = self._create_analysis_prompt(sense_data, trading_rules, config)
            
            # Let AI analyze and decide
            ai_result = await self.ai_decide_and_execute(analysis_prompt, {
                "sense_data": sense_data,
                "trading_rules": trading_rules,
                "config": config,
                "analysis_type": "comprehensive_trading_decision"
            })
            
            # Process AI results into structured decisions
            think_result = await self._process_ai_analysis(ai_result, sense_data, trading_rules)
            
            # Log summary
            decision_count = len(think_result.decisions)
            avg_confidence = sum(d.confidence for d in think_result.decisions) / max(1, decision_count)
            summary = f"Generated {decision_count} decisions, avg confidence: {avg_confidence:.2f}"
            self.log_step_complete(summary)
            
            return {
                'step': 'THINK',
                'timestamp': think_result.timestamp.isoformat(),
                'success': True,
                'data': think_result,
                'ai_reasoning': think_result.ai_reasoning,
                'tool_calls_made': len(ai_result.get('tool_calls', [])),
                'raw_ai_result': ai_result
            }
            
        except Exception as e:
            self.step_logger.error(f"THINK step failed: {e}")
            
            # Fallback to rule-based thinking
            fallback_result = await self._fallback_rule_based_thinking(context)
            fallback_result['fallback_used'] = True
            fallback_result['error'] = str(e)
            
            return fallback_result
    
    def _create_analysis_prompt(self, sense_data: Any, trading_rules: List[Dict], config: Dict) -> str:
        """
        Create comprehensive analysis prompt for AI
        
        Args:
            sense_data: Data from SENSE step
            trading_rules: Trading rules and target allocations
            config: Configuration settings
            
        Returns:
            Detailed prompt for AI analysis
        """
        # Extract key metrics from sense data
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 0)
        available_funds = getattr(sense_data, 'available_funds', 0)
        positions = getattr(sense_data, 'positions', [])
        market_data = getattr(sense_data, 'market_data', {})
        
        # Calculate current allocations
        current_allocations = self._calculate_current_allocations(sense_data, trading_rules)
        
        prompt = f"""
You are an expert portfolio manager and trading strategist. Analyze the current market and portfolio situation to make intelligent trading decisions.

PORTFOLIO OVERVIEW:
- Total Value: ${portfolio_value:,.2f}
- Available Funds: ${available_funds:,.2f}
- Current Positions: {len(positions)}
- Cash Percentage: {getattr(sense_data, 'cash_percentage', 0):.1f}%

CURRENT ALLOCATIONS VS TARGETS:
{self._format_allocation_analysis(current_allocations, trading_rules)}

MARKET DATA:
{self._format_market_data(market_data)}

TRADING RULES & CONSTRAINTS:
- Risk Threshold: ${config.get('risk_threshold', 1000):,.2f} per trade
- Paper Trading: {config.get('paper_trading', True)}
- Max Portfolio Change: {config.get('max_portfolio_change', 5.0)}% per session

ANALYSIS OBJECTIVES:
1. Identify allocation drift and rebalancing opportunities
2. Assess market conditions and timing for each symbol
3. Generate specific trading decisions with reasoning
4. Evaluate risk/reward for each potential trade
5. Consider portfolio diversification and concentration risk

DECISION FRAMEWORK:
- Only recommend trades that meaningfully improve portfolio allocation (>2% impact)
- Prioritize high-confidence, low-risk opportunities
- Consider market momentum, volatility, and trends
- Factor in transaction costs and slippage
- Maintain diversification principles

Use MCP tools if you need additional analysis like:
- Historical price data for trend analysis
- Enhanced stock analysis for specific symbols
- Scanner tools to find better opportunities
- What-if analysis for complex scenarios

Your final output should be specific trading recommendations with:
- Symbol, action (BUY/SELL), quantity
- Clear reasoning and confidence level
- Risk assessment and expected impact
- Priority/urgency level

Think step by step and be thorough in your analysis.
"""
        
        return prompt
    
    def _calculate_current_allocations(self, sense_data: Any, trading_rules: List[Dict]) -> Dict[str, float]:
        """Calculate current allocation percentages by category"""
        positions = getattr(sense_data, 'positions', [])
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 0)
        
        if portfolio_value <= 0:
            return {}
        
        # Map positions to categories
        allocations = {}
        for rule in trading_rules:
            category_value = 0.0
            rule_symbols = rule.get('symbols', [])
            
            for position in positions:
                symbol = position.get('contractDesc', '').split()[0]  # Extract symbol
                if symbol in rule_symbols:
                    market_value = float(position.get('mktValue', 0))
                    category_value += market_value
            
            allocations[rule['name']] = {
                'current_pct': (category_value / portfolio_value) * 100,
                'target_pct': rule.get('target_allocation', 0),
                'current_value': category_value,
                'deviation': (category_value / portfolio_value) * 100 - rule.get('target_allocation', 0)
            }
        
        return allocations
    
    def _format_allocation_analysis(self, allocations: Dict, trading_rules: List[Dict]) -> str:
        """Format allocation analysis for AI prompt"""
        lines = []
        for category, data in allocations.items():
            current = data['current_pct']
            target = data['target_pct']
            deviation = data['deviation']
            status = "✅" if abs(deviation) < 5 else "⚠️" if abs(deviation) < 10 else "🚨"
            
            lines.append(f"{status} {category}: {current:.1f}% (target: {target:.1f}%, deviation: {deviation:+.1f}%)")
        
        return "\n".join(lines)
    
    def _format_market_data(self, market_data: Dict[str, Dict]) -> str:
        """Format market data for AI prompt"""
        lines = []
        for symbol, data in market_data.items():
            price = data.get('last_price') or data.get('bid', 'N/A')
            change_pct = data.get('change_percent', 0)
            volume = data.get('volume', 'N/A')
            
            trend = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            lines.append(f"{trend} {symbol}: ${price} ({change_pct:+.2f}%), Vol: {volume}")
        
        return "\n".join(lines) if lines else "No market data available"
    
    async def _process_ai_analysis(self, ai_result: Dict[str, Any], 
                                  sense_data: Any, trading_rules: List[Dict]) -> ThinkResult:
        """
        Process AI analysis results into structured ThinkResult
        
        Args:
            ai_result: Results from AI decision making
            sense_data: Original sense data
            trading_rules: Trading rules
            
        Returns:
            Structured ThinkResult
        """
        decisions = []
        reasoning = ai_result.get('reasoning', [])
        
        # Extract decisions from AI final result
        final_result = ai_result.get('final_result', '')
        
        # Try to parse structured decisions from AI response
        decisions = await self._extract_decisions_from_ai_response(final_result, ai_result)
        
        # Build comprehensive analysis
        market_analysis = self._build_market_analysis(ai_result, sense_data)
        portfolio_analysis = self._build_portfolio_analysis(ai_result, sense_data, trading_rules)
        risk_assessment = self._build_risk_assessment(decisions, sense_data)
        
        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(decisions, ai_result)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(decisions, portfolio_analysis)
        
        return ThinkResult(
            timestamp=datetime.now(),
            decisions=decisions,
            market_analysis=market_analysis,
            portfolio_analysis=portfolio_analysis,
            risk_assessment=risk_assessment,
            ai_reasoning=reasoning,
            confidence_score=confidence_score,
            recommended_actions=recommended_actions
        )
    
    async def _extract_decisions_from_ai_response(self, final_result: str, 
                                                ai_result: Dict[str, Any]) -> List[TradingDecision]:
        """Extract trading decisions from AI response"""
        decisions = []
        
        # Look for structured decision data in AI response or tool calls
        for tool_call in ai_result.get('tool_calls', []):
            if tool_call.get('tool_name') == 'stock_analysis':
                # Extract decision insights from stock analysis
                result_data = tool_call.get('result', {})
                if 'position_analysis' in result_data:
                    # This could inform a trading decision
                    pass
        
        # Parse decisions from final_result text
        # Look for patterns like "BUY 10 SPY" or structured JSON
        lines = final_result.split('\n')
        for line in lines:
            line = line.strip()
            if any(action in line.upper() for action in ['BUY', 'SELL', 'HOLD']):
                decision = self._parse_decision_line(line)
                if decision:
                    decisions.append(decision)
        
        # If no decisions found, try to prompt AI for structured output
        if not decisions and self.openai_client:
            decisions = await self._request_structured_decisions(final_result)
        
        return decisions
    
    def _parse_decision_line(self, line: str) -> Optional[TradingDecision]:
        """Parse a single decision line from AI response"""
        try:
            # Simple parsing - can be enhanced
            parts = line.split()
            action = None
            symbol = None
            quantity = 0
            
            for i, part in enumerate(parts):
                if part.upper() in ['BUY', 'SELL', 'HOLD']:
                    action = part.upper()
                    if i + 1 < len(parts):
                        try:
                            quantity = int(parts[i + 1])
                        except ValueError:
                            pass
                    if i + 2 < len(parts):
                        symbol = parts[i + 2]
                    break
            
            if action and symbol and (action == 'HOLD' or quantity > 0):
                return TradingDecision(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    reasoning=line,
                    confidence=0.7,  # Default confidence
                    urgency="MEDIUM"
                )
        except Exception as e:
            logger.debug(f"Failed to parse decision line '{line}': {e}")
        
        return None
    
    async def _request_structured_decisions(self, analysis_text: str) -> List[TradingDecision]:
        """Request structured decisions from AI if none were found"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Convert trading analysis into structured decisions. Return JSON array of decisions."
                    },
                    {
                        "role": "user",
                        "content": f"""
Based on this analysis, provide specific trading decisions in JSON format:

{analysis_text}

Return JSON array like:
[
  {{
    "symbol": "SPY",
    "action": "BUY",
    "quantity": 10,
    "reasoning": "Underallocated in broad ETFs",
    "confidence": 0.8,
    "urgency": "MEDIUM"
  }}
]

Only include actionable decisions (BUY/SELL with quantity > 0).
"""
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract JSON from response
            if '[' in ai_response and ']' in ai_response:
                json_start = ai_response.find('[')
                json_end = ai_response.rfind(']') + 1
                json_text = ai_response[json_start:json_end]
                
                decision_data = json.loads(json_text)
                
                decisions = []
                for item in decision_data:
                    if item.get('action') in ['BUY', 'SELL'] and item.get('quantity', 0) > 0:
                        decisions.append(TradingDecision(
                            symbol=item['symbol'],
                            action=item['action'],
                            quantity=item['quantity'],
                            reasoning=item.get('reasoning', ''),
                            confidence=float(item.get('confidence', 0.5)),
                            urgency=item.get('urgency', 'MEDIUM')
                        ))
                
                return decisions
                
        except Exception as e:
            logger.debug(f"Failed to get structured decisions: {e}")
        
        return []
    
    def _build_market_analysis(self, ai_result: Dict[str, Any], sense_data: Any) -> Dict[str, Any]:
        """Build market analysis from AI results"""
        market_data = getattr(sense_data, 'market_data', {})
        
        analysis = {
            "symbols_analyzed": list(market_data.keys()),
            "market_sentiment": "NEUTRAL",  # Default
            "volatility_assessment": "MODERATE",
            "trend_analysis": {},
            "opportunities": [],
            "risks": []
        }
        
        # Extract insights from AI tool calls
        for tool_call in ai_result.get('tool_calls', []):
            if tool_call['tool_name'] in ['get_market_snapshot', 'get_history']:
                # Extract market insights
                pass
        
        return analysis
    
    def _build_portfolio_analysis(self, ai_result: Dict[str, Any], 
                                 sense_data: Any, trading_rules: List[Dict]) -> Dict[str, Any]:
        """Build portfolio analysis from AI results"""
        current_allocations = self._calculate_current_allocations(sense_data, trading_rules)
        
        analysis = {
            "current_allocations": current_allocations,
            "rebalancing_needed": [],
            "concentration_risk": "LOW",
            "diversification_score": 0.8,
            "allocation_drift": {}
        }
        
        # Identify rebalancing needs
        for category, data in current_allocations.items():
            if abs(data['deviation']) > 5:
                analysis["rebalancing_needed"].append({
                    "category": category,
                    "current": data['current_pct'],
                    "target": data['target_pct'],
                    "deviation": data['deviation']
                })
        
        return analysis
    
    def _build_risk_assessment(self, decisions: List[TradingDecision], sense_data: Any) -> Dict[str, Any]:
        """Build risk assessment for proposed decisions"""
        total_trade_value = 0
        max_single_trade = 0
        high_risk_trades = 0
        
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 0)
        
        for decision in decisions:
            # Estimate trade value (simplified)
            market_data = getattr(sense_data, 'market_data', {})
            symbol_data = market_data.get(decision.symbol, {})
            price = symbol_data.get('last_price') or symbol_data.get('bid', 100)
            
            trade_value = decision.quantity * price
            total_trade_value += trade_value
            max_single_trade = max(max_single_trade, trade_value)
            
            if decision.confidence < 0.6:
                high_risk_trades += 1
        
        portfolio_impact = (total_trade_value / portfolio_value * 100) if portfolio_value > 0 else 0
        
        return {
            "total_trade_value": total_trade_value,
            "max_single_trade": max_single_trade,
            "portfolio_impact_pct": portfolio_impact,
            "high_risk_trades": high_risk_trades,
            "risk_level": "LOW" if portfolio_impact < 2 else "MEDIUM" if portfolio_impact < 5 else "HIGH"
        }
    
    def _calculate_confidence_score(self, decisions: List[TradingDecision], 
                                   ai_result: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        if not decisions:
            return 0.0
        
        avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
        
        # Adjust based on AI tool usage and reasoning quality
        tool_calls = len(ai_result.get('tool_calls', []))
        reasoning_quality = len(ai_result.get('reasoning', []))
        
        # Bonus for thorough analysis
        if tool_calls > 3:
            avg_confidence += 0.1
        if reasoning_quality > 5:
            avg_confidence += 0.1
        
        return min(1.0, avg_confidence)
    
    def _generate_recommended_actions(self, decisions: List[TradingDecision], 
                                     portfolio_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on analysis"""
        actions = []
        
        if decisions:
            actions.append(f"Execute {len(decisions)} trading decisions")
            
            # Prioritize by urgency
            high_urgency = [d for d in decisions if d.urgency == "HIGH"]
            if high_urgency:
                actions.append(f"Prioritize {len(high_urgency)} high-urgency trades")
        
        # Portfolio-level recommendations
        rebalancing_needed = portfolio_analysis.get("rebalancing_needed", [])
        if rebalancing_needed:
            actions.append(f"Rebalance {len(rebalancing_needed)} asset categories")
        
        if not decisions:
            actions.append("No immediate trades recommended - portfolio is well balanced")
        
        return actions
    
    async def _fallback_rule_based_thinking(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback rule-based thinking when AI is not available
        
        Args:
            context: Context with sense_data and trading_rules
            
        Returns:
            Basic trading decisions
        """
        self.step_logger.info("Using fallback rule-based thinking...")
        
        try:
            sense_data = context.get('sense_data')
            trading_rules = context.get('trading_rules', [])
            config = context.get('config', {})
            
            if not sense_data:
                raise ValueError("No sense_data provided")
            
            # Simple rebalancing logic
            current_allocations = self._calculate_current_allocations(sense_data, trading_rules)
            decisions = []
            
            portfolio_value = getattr(sense_data, 'total_portfolio_value', 0)
            
            for rule in trading_rules:
                rule_name = rule['name']
                if rule_name not in current_allocations:
                    continue
                
                allocation_data = current_allocations[rule_name]
                deviation = allocation_data['deviation']
                
                # If more than 5% off target, suggest rebalancing
                if abs(deviation) > 5.0:
                    symbols = rule.get('symbols', [])
                    if symbols:
                        # Pick first symbol for simplicity
                        symbol = symbols[0]
                        
                        # Get current price from market data
                        market_data = getattr(sense_data, 'market_data', {})
                        symbol_data = market_data.get(symbol, {})
                        current_price = symbol_data.get('last_price') or symbol_data.get('bid', 100)
                        
                        # Calculate target adjustment
                        target_value = portfolio_value * (rule['target_allocation'] / 100)
                        current_value = allocation_data['current_value']
                        value_diff = target_value - current_value
                        
                        # Only trade if difference is above risk threshold
                        if abs(value_diff) > config.get('risk_threshold', 1000):
                            if value_diff > 0:
                                # Need to buy
                                quantity = int(value_diff / current_price)
                                if quantity > 0:
                                    decisions.append(TradingDecision(
                                        symbol=symbol,
                                        action="BUY",
                                        quantity=quantity,
                                        reasoning=f"Rebalancing {rule_name}: {allocation_data['current_pct']:.1f}% → {rule['target_allocation']:.1f}%",
                                        confidence=0.7,
                                        urgency="MEDIUM"
                                    ))
                            else:
                                # Need to sell
                                quantity = int(abs(value_diff) / current_price)
                                # Check current position
                                positions = getattr(sense_data, 'positions', [])
                                current_position = 0
                                for pos in positions:
                                    if symbol in pos.get('contractDesc', ''):
                                        current_position = int(pos.get('position', 0))
                                        break
                                
                                quantity = min(quantity, current_position)
                                if quantity > 0:
                                    decisions.append(TradingDecision(
                                        symbol=symbol,
                                        action="SELL",
                                        quantity=quantity,
                                        reasoning=f"Rebalancing {rule_name}: {allocation_data['current_pct']:.1f}% → {rule['target_allocation']:.1f}%",
                                        confidence=0.7,
                                        urgency="MEDIUM"
                                    ))
            
            # Create basic ThinkResult
            think_result = ThinkResult(
                timestamp=datetime.now(),
                decisions=decisions,
                market_analysis={"fallback": True, "symbols_analyzed": list(getattr(sense_data, 'market_data', {}).keys())},
                portfolio_analysis={"current_allocations": current_allocations, "fallback": True},
                risk_assessment={"risk_level": "LOW", "fallback": True},
                ai_reasoning=["Used rule-based fallback logic", "Focused on rebalancing based on allocation drift"],
                confidence_score=0.6,
                recommended_actions=[f"Execute {len(decisions)} rebalancing trades"] if decisions else ["No trades needed"]
            )
            
            summary = f"Generated {len(decisions)} rule-based decisions"
            self.log_step_complete(summary)
            
            return {
                'step': 'THINK',
                'timestamp': think_result.timestamp.isoformat(),
                'success': True,
                'data': think_result,
                'fallback_used': True
            }
            
        except Exception as e:
            self.step_logger.error(f"Fallback thinking failed: {e}")
            return {
                'step': 'THINK',
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'fallback_used': True
            }

if __name__ == "__main__":
    import os
    
    # Example usage and testing
    async def test_think_agent():
        agent = ThinkAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        await agent.initialize()
        
        # Mock context with sense data
        from types import SimpleNamespace
        
        mock_sense_data = SimpleNamespace(
            total_portfolio_value=50000.0,
            available_funds=5000.0,
            cash_percentage=10.0,
            positions=[
                {"contractDesc": "SPY", "mktValue": 30000, "position": 100},
                {"contractDesc": "JNJ", "mktValue": 5000, "position": 50}
            ],
            market_data={
                "SPY": {"last_price": 300, "change_percent": 1.2, "volume": 1000000},
                "JNJ": {"last_price": 100, "change_percent": -0.5, "volume": 500000},
                "QQQ": {"last_price": 250, "change_percent": 2.1, "volume": 800000}
            }
        )
        
        context = {
            "sense_data": mock_sense_data,
            "trading_rules": [
                {
                    "name": "Broad ETFs",
                    "target_allocation": 70.0,
                    "symbols": ["SPY", "QQQ", "VTI"]
                },
                {
                    "name": "Dividend Stocks",
                    "target_allocation": 30.0,
                    "symbols": ["JNJ", "PG"]
                }
            ],
            "config": {
                "risk_threshold": 1000.0,
                "paper_trading": True,
                "max_portfolio_change": 5.0
            }
        }
        
        result = await agent.execute_step(context)
        
        print("=== THINK STEP RESULT ===")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            think_result = result['data']
            print(f"\n=== TRADING DECISIONS ===")
            for decision in think_result.decisions:
                print(f"{decision.action} {decision.quantity} {decision.symbol}")
                print(f"  Reasoning: {decision.reasoning}")
                print(f"  Confidence: {decision.confidence:.2f}")
                print(f"  Urgency: {decision.urgency}")
                print()
    
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_think_agent())
    else:
        print("Set OPENAI_API_KEY to test the THINK agent")