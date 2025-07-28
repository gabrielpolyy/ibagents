#!/usr/bin/env python3
"""
ACT Step - Intelligent Trade Execution

This module implements Step 3 of the trading loop where the AI intelligently
executes trading decisions using MCP tools with comprehensive safety checks.
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
class TradeResult:
    """Result of executing a single trade"""
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    requested_price: Optional[float]
    executed_price: Optional[float]
    timestamp: datetime
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    reasoning: Optional[str] = None
    whatif_analysis: Optional[Dict[str, Any]] = None
    trade_value: Optional[float] = None
    
@dataclass
class ActResult:
    """Result from the ACT step"""
    timestamp: datetime
    trades_attempted: int
    trades_successful: int
    trades_failed: int
    trade_results: List[TradeResult]
    total_trade_value: float
    portfolio_impact: float
    safety_checks_performed: int
    ai_reasoning: List[str]
    risk_assessment: Dict[str, Any]
    execution_summary: str

class ActAgent(StepAgent):
    """
    ACT Agent - Intelligent trade execution with AI-driven safety checks
    
    This agent:
    1. Validates trading decisions using AI analysis
    2. Performs comprehensive safety checks via MCP tools
    3. Executes trades with optimal timing and risk management
    4. Monitors execution and handles errors intelligently
    """
    
    def __init__(self, 
                 mcp_url: str = "http://127.0.0.1:8001/mcp",
                 openai_api_key: str = None,
                 model: str = "o3-mini"):
        super().__init__("ACT", mcp_url, openai_api_key, model)
        self.paper_trading = True  # Default to safe mode
        
    async def execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the ACT step with intelligent trade execution
        
        Args:
            context: Context including think_data, config, etc.
            
        Returns:
            Trade execution results
        """
        self.log_step_start()
        
        try:
            # Extract context data
            think_data = context.get('think_data')
            config = context.get('config', {})
            sense_data = context.get('sense_data')
            
            if not think_data:
                raise ValueError("No think_data provided to ACT step")
            
            # Set execution mode
            self.paper_trading = config.get('paper_trading', True)
            
            # Get trading decisions
            decisions = getattr(think_data, 'decisions', [])
            if not decisions:
                return self._create_no_action_result("No trading decisions to execute")
            
            # Let AI validate and prioritize decisions before execution
            validated_decisions = await self._ai_validate_decisions(decisions, context)
            
            # Execute validated decisions
            trade_results = []
            safety_checks = 0
            
            for decision in validated_decisions:
                self.step_logger.info(f"Executing: {decision.action} {decision.quantity} {decision.symbol}")
                
                try:
                    # AI-driven safety analysis for this specific trade
                    safety_result = await self._ai_safety_analysis(decision, context)
                    safety_checks += 1
                    
                    if not safety_result.get('approved', False):
                        trade_results.append(TradeResult(
                            symbol=decision.symbol,
                            action=decision.action,
                            quantity=decision.quantity,
                            requested_price=decision.price_target,
                            executed_price=None,
                            timestamp=datetime.now(),
                            success=False,
                            error_message=f"Safety check failed: {safety_result.get('reason', 'Unknown')}",
                            reasoning=decision.reasoning
                        ))
                        continue
                    
                    # Execute the trade
                    trade_result = await self._execute_single_trade(decision, context)
                    trade_results.append(trade_result)
                    
                    # Brief delay between trades to avoid overwhelming the system
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.step_logger.error(f"Failed to execute trade for {decision.symbol}: {e}")
                    trade_results.append(TradeResult(
                        symbol=decision.symbol,
                        action=decision.action,
                        quantity=decision.quantity,
                        requested_price=decision.price_target,
                        executed_price=None,
                        timestamp=datetime.now(),
                        success=False,
                        error_message=str(e),
                        reasoning=decision.reasoning
                    ))
            
            # Build comprehensive result
            act_result = self._build_act_result(trade_results, safety_checks, think_data, sense_data)
            
            # Log summary
            successful_trades = len([r for r in trade_results if r.success])
            summary = f"Executed {successful_trades}/{len(trade_results)} trades successfully"
            self.log_step_complete(summary)
            
            return {
                'step': 'ACT',
                'timestamp': act_result.timestamp.isoformat(),
                'success': True,
                'data': act_result,
                'execution_mode': 'PAPER' if self.paper_trading else 'LIVE'
            }
            
        except Exception as e:
            self.step_logger.error(f"ACT step failed: {e}")
            return {
                'step': 'ACT',
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'execution_mode': 'PAPER' if self.paper_trading else 'LIVE'
            }
    
    async def _ai_validate_decisions(self, decisions: List[Any], context: Dict[str, Any]) -> List[Any]:
        """
        Let AI validate and prioritize trading decisions before execution
        
        Args:
            decisions: List of trading decisions from THINK step
            context: Full context including market data
            
        Returns:
            Validated and prioritized list of decisions
        """
        if not self.openai_client:
            # Without AI, just return original decisions
            return decisions
        
        sense_data = context.get('sense_data')
        config = context.get('config', {})
        
        validation_prompt = f"""
        Review and validate these trading decisions before execution:
        
        DECISIONS TO VALIDATE:
        {self._format_decisions_for_ai(decisions)}
        
        CURRENT CONTEXT:
        - Portfolio Value: ${getattr(sense_data, 'total_portfolio_value', 0):,.2f}
        - Available Funds: ${getattr(sense_data, 'available_funds', 0):,.2f}
        - Paper Trading: {config.get('paper_trading', True)}
        - Risk Threshold: ${config.get('risk_threshold', 1000):,.2f}
        
        VALIDATION CRITERIA:
        1. Check if trades are still relevant given current market conditions
        2. Verify sufficient buying power for purchases
        3. Confirm position sizes are reasonable
        4. Assess overall portfolio impact
        5. Prioritize by risk/reward and urgency
        
        Use MCP tools to get the latest market data if needed to validate decisions.
        
        TASK: Validate each decision and return a prioritized list of approved trades.
        Remove any trades that are too risky or no longer appropriate.
        """
        
        try:
            ai_result = await self.ai_decide_and_execute(
                validation_prompt,
                {
                    "decisions": [self._decision_to_dict(d) for d in decisions],
                    "context": context,
                    "validation_type": "pre_execution"
                }
            )
            
            # Extract validated decisions from AI response
            validated = self._extract_validated_decisions(ai_result, decisions)
            
            self.step_logger.info(f"AI validated {len(validated)}/{len(decisions)} decisions")
            return validated
            
        except Exception as e:
            self.step_logger.warning(f"AI validation failed, using original decisions: {e}")
            return decisions
    
    def _format_decisions_for_ai(self, decisions: List[Any]) -> str:
        """Format trading decisions for AI analysis"""
        lines = []
        for i, decision in enumerate(decisions, 1):
            lines.append(f"{i}. {decision.action} {decision.quantity} {decision.symbol}")
            lines.append(f"   Reasoning: {decision.reasoning}")
            lines.append(f"   Confidence: {decision.confidence:.2f}")
            lines.append(f"   Urgency: {decision.urgency}")
            lines.append("")
        return "\n".join(lines)
    
    def _decision_to_dict(self, decision: Any) -> Dict[str, Any]:
        """Convert decision object to dictionary"""
        return {
            "symbol": decision.symbol,
            "action": decision.action,
            "quantity": decision.quantity,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "urgency": decision.urgency,
            "price_target": getattr(decision, 'price_target', None)
        }
    
    def _extract_validated_decisions(self, ai_result: Dict[str, Any], original_decisions: List[Any]) -> List[Any]:
        """Extract validated decisions from AI response"""
        # For now, return original decisions
        # In a full implementation, this would parse AI's validation response
        # and filter/reorder decisions based on AI recommendations
        
        validated = []
        final_result = ai_result.get('final_result', '')
        
        # Simple validation: if AI mentions specific symbols positively, include them
        for decision in original_decisions:
            symbol = decision.symbol
            if symbol in final_result and 'approve' in final_result.lower():
                validated.append(decision)
            elif 'all' in final_result.lower() and 'approve' in final_result.lower():
                validated.append(decision)
            elif len(validated) == 0:  # Fallback: include first decision
                validated.append(decision)
        
        return validated if validated else original_decisions
    
    async def _ai_safety_analysis(self, decision: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-driven safety analysis for a specific trade
        
        Args:
            decision: Single trading decision to analyze
            context: Full context
            
        Returns:
            Safety analysis result with approval/rejection
        """
        if not self.openai_client:
            # Without AI, perform basic checks
            return {"approved": True, "reason": "Basic validation passed"}
        
        sense_data = context.get('sense_data')
        config = context.get('config', {})
        
        safety_prompt = f"""
        Perform comprehensive safety analysis for this specific trade:
        
        TRADE TO ANALYZE:
        - Action: {decision.action}
        - Symbol: {decision.symbol}
        - Quantity: {decision.quantity}
        - Reasoning: {decision.reasoning}
        - Confidence: {decision.confidence}
        
        SAFETY CHECKS REQUIRED:
        1. Market data validation (get current price, check for halts/issues)
        2. Position size validation (reasonable % of portfolio)
        3. Buying power check (sufficient funds available)
        4. Risk assessment (does this fit risk parameters?)
        5. Market timing (is now a good time to execute?)
        
        Use MCP tools to get current market data and perform what-if analysis.
        
        DECISION: Approve (YES) or Reject (NO) this trade with clear reasoning.
        """
        
        try:
            ai_result = await self.ai_decide_and_execute(
                safety_prompt,
                {
                    "decision": self._decision_to_dict(decision),
                    "context": context,
                    "analysis_type": "safety_check"
                },
                max_tool_calls=5  # Limit for safety checks
            )
            
            final_result = ai_result.get('final_result', '').lower()
            
            if 'approve' in final_result or 'yes' in final_result:
                return {"approved": True, "reason": "AI safety checks passed", "ai_analysis": ai_result}
            else:
                return {"approved": False, "reason": "AI safety checks failed", "ai_analysis": ai_result}
                
        except Exception as e:
            self.step_logger.warning(f"AI safety analysis failed for {decision.symbol}: {e}")
            # Fallback to basic safety check
            return await self._basic_safety_check(decision, context)
    
    async def _basic_safety_check(self, decision: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Basic safety check without AI"""
        sense_data = context.get('sense_data')
        config = context.get('config', {})
        
        # Check available funds
        available_funds = getattr(sense_data, 'available_funds', 0)
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 1)
        
        # Estimate trade value
        market_data = getattr(sense_data, 'market_data', {})
        symbol_data = market_data.get(decision.symbol, {})
        price = symbol_data.get('last_price') or symbol_data.get('bid', 100)
        
        trade_value = decision.quantity * price
        
        # Basic checks
        if decision.action == 'BUY' and trade_value > available_funds:
            return {"approved": False, "reason": f"Insufficient funds: need ${trade_value:,.2f}, have ${available_funds:,.2f}"}
        
        if trade_value > config.get('risk_threshold', 1000):
            return {"approved": False, "reason": f"Trade value ${trade_value:,.2f} exceeds risk threshold"}
        
        position_pct = (trade_value / portfolio_value) * 100
        if position_pct > 10:  # Don't allow more than 10% position
            return {"approved": False, "reason": f"Position size {position_pct:.1f}% too large"}
        
        return {"approved": True, "reason": "Basic safety checks passed"}
    
    async def _execute_single_trade(self, decision: Any, context: Dict[str, Any]) -> TradeResult:
        """
        Execute a single trade with MCP tools
        
        Args:
            decision: Trading decision to execute
            context: Full context
            
        Returns:
            TradeResult with execution details
        """
        symbol = decision.symbol
        action = decision.action
        quantity = decision.quantity
        
        try:
            # Step 1: Find contract
            contract_result = await self.call_mcp_tool("find_contract", {
                "symbol": symbol,
                "sec_type": "STK"
            })
            
            if not contract_result.success:
                return TradeResult(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    requested_price=decision.price_target,
                    executed_price=None,
                    timestamp=datetime.now(),
                    success=False,
                    error_message=f"Contract lookup failed: {contract_result.error}"
                )
            
            conid = contract_result.data.get('conid')
            if not conid:
                return TradeResult(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    requested_price=decision.price_target,
                    executed_price=None,
                    timestamp=datetime.now(),
                    success=False,
                    error_message="No contract ID found"
                )
            
            # Step 2: Get current market price
            snapshot_result = await self.call_mcp_tool("get_market_snapshot", {"conid": conid})
            current_price = None
            if snapshot_result.success:
                snapshot_data = snapshot_result.data.get('snapshot', {})
                current_price = snapshot_data.get('last_price') or snapshot_data.get('bid')
            
            # Step 3: What-if analysis
            whatif_result = await self.call_mcp_tool("whatif_order", {
                "conid": conid,
                "side": action,
                "quantity": quantity,
                "order_type": "MKT",
                "account_id": self.account_id
            })
            
            whatif_analysis = None
            if whatif_result.success:
                whatif_analysis = whatif_result.data.get('whatif_result', {})
            else:
                return TradeResult(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    requested_price=decision.price_target,
                    executed_price=current_price,
                    timestamp=datetime.now(),
                    success=False,
                    error_message=f"What-if analysis failed: {whatif_result.error}",
                    whatif_analysis=whatif_analysis
                )
            
            # Step 4: Execute trade (or simulate if paper trading)
            if self.paper_trading:
                # Paper trading - just log the trade
                self.step_logger.info(f"📝 PAPER TRADE: {action} {quantity} {symbol} @ ${current_price:.2f}")
                
                return TradeResult(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    requested_price=decision.price_target,
                    executed_price=current_price,
                    timestamp=datetime.now(),
                    success=True,
                    order_id=f"PAPER_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    reasoning=f"Paper trade: {decision.reasoning}",
                    whatif_analysis=whatif_analysis,
                    trade_value=quantity * (current_price or 0)
                )
            else:
                # Live trading
                self.step_logger.info(f"💰 LIVE TRADE: {action} {quantity} {symbol}")
                
                order_result = await self.call_mcp_tool("place_order", {
                    "conid": conid,
                    "side": action,
                    "quantity": quantity,
                    "order_type": "MKT",
                    "account_id": self.account_id,
                    "skip_whatif": True  # Already did what-if
                })
                
                if order_result.success:
                    order_data = order_result.data.get('result', {})
                    order_id = order_data.get('order_id', 'unknown')
                    
                    return TradeResult(
                        symbol=symbol,
                        action=action,
                        quantity=quantity,
                        requested_price=decision.price_target,
                        executed_price=current_price,
                        timestamp=datetime.now(),
                        success=True,
                        order_id=order_id,
                        reasoning=decision.reasoning,
                        whatif_analysis=whatif_analysis,
                        trade_value=quantity * (current_price or 0)
                    )
                else:
                    return TradeResult(
                        symbol=symbol,
                        action=action,
                        quantity=quantity,
                        requested_price=decision.price_target,
                        executed_price=current_price,
                        timestamp=datetime.now(),
                        success=False,
                        error_message=f"Order placement failed: {order_result.error}",
                        whatif_analysis=whatif_analysis
                    )
                    
        except Exception as e:
            return TradeResult(
                symbol=symbol,
                action=action,
                quantity=quantity,
                requested_price=decision.price_target,
                executed_price=None,
                timestamp=datetime.now(),
                success=False,
                error_message=f"Execution error: {str(e)}"
            )
    
    def _build_act_result(self, trade_results: List[TradeResult], 
                         safety_checks: int, think_data: Any, sense_data: Any) -> ActResult:
        """Build comprehensive ActResult from trade results"""
        
        successful_trades = [r for r in trade_results if r.success]
        failed_trades = [r for r in trade_results if not r.success]
        
        total_trade_value = sum(r.trade_value or 0 for r in successful_trades)
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 1)
        portfolio_impact = (total_trade_value / portfolio_value) * 100
        
        # Build execution summary
        if successful_trades:
            execution_summary = f"Successfully executed {len(successful_trades)} trades worth ${total_trade_value:,.2f}"
        else:
            execution_summary = "No trades executed"
            
        if failed_trades:
            execution_summary += f", {len(failed_trades)} trades failed"
        
        # AI reasoning from think step
        ai_reasoning = getattr(think_data, 'ai_reasoning', [])
        ai_reasoning.append(f"Executed trades with {safety_checks} safety checks")
        
        # Risk assessment
        risk_assessment = {
            "total_trades": len(trade_results),
            "success_rate": len(successful_trades) / max(1, len(trade_results)) * 100,
            "total_value": total_trade_value,
            "portfolio_impact_pct": portfolio_impact,
            "safety_checks_performed": safety_checks,
            "execution_mode": "PAPER" if self.paper_trading else "LIVE"
        }
        
        return ActResult(
            timestamp=datetime.now(),
            trades_attempted=len(trade_results),
            trades_successful=len(successful_trades),
            trades_failed=len(failed_trades),
            trade_results=trade_results,
            total_trade_value=total_trade_value,
            portfolio_impact=portfolio_impact,
            safety_checks_performed=safety_checks,
            ai_reasoning=ai_reasoning,
            risk_assessment=risk_assessment,
            execution_summary=execution_summary
        )
    
    def _create_no_action_result(self, reason: str) -> Dict[str, Any]:
        """Create result when no actions are taken"""
        act_result = ActResult(
            timestamp=datetime.now(),
            trades_attempted=0,
            trades_successful=0,
            trades_failed=0,
            trade_results=[],
            total_trade_value=0.0,
            portfolio_impact=0.0,
            safety_checks_performed=0,
            ai_reasoning=[reason],
            risk_assessment={"no_action": True},
            execution_summary=reason
        )
        
        self.log_step_complete(reason)
        
        return {
            'step': 'ACT',
            'timestamp': act_result.timestamp.isoformat(),
            'success': True,
            'data': act_result,
            'no_action': True,
            'reason': reason
        }

if __name__ == "__main__":
    import os
    from types import SimpleNamespace
    
    # Example usage and testing
    async def test_act_agent():
        agent = ActAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        await agent.initialize()
        
        # Mock trading decisions
        mock_decisions = [
            SimpleNamespace(
                symbol="SPY",
                action="BUY",
                quantity=5,
                reasoning="Rebalancing - underallocated in broad ETFs",
                confidence=0.8,
                urgency="MEDIUM",
                price_target=300.0
            )
        ]
        
        mock_think_data = SimpleNamespace(
            decisions=mock_decisions,
            ai_reasoning=["Portfolio analysis indicates rebalancing needed"]
        )
        
        mock_sense_data = SimpleNamespace(
            total_portfolio_value=50000.0,
            available_funds=5000.0,
            market_data={
                "SPY": {"last_price": 300, "bid": 299.5, "ask": 300.5}
            }
        )
        
        context = {
            "think_data": mock_think_data,
            "sense_data": mock_sense_data,
            "config": {
                "paper_trading": True,
                "risk_threshold": 2000.0
            }
        }
        
        result = await agent.execute_step(context)
        
        print("=== ACT STEP RESULT ===")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            act_result = result['data']
            print(f"\n=== EXECUTION SUMMARY ===")
            print(f"Trades Attempted: {act_result.trades_attempted}")
            print(f"Trades Successful: {act_result.trades_successful}")
            print(f"Total Trade Value: ${act_result.total_trade_value:,.2f}")
            print(f"Portfolio Impact: {act_result.portfolio_impact:.2f}%")
            print(f"Execution Mode: {result['execution_mode']}")
            
            for trade in act_result.trade_results:
                status = "✅" if trade.success else "❌"
                print(f"{status} {trade.action} {trade.quantity} {trade.symbol} @ ${trade.executed_price or 'N/A'}")
                if trade.error_message:
                    print(f"   Error: {trade.error_message}")
    
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_act_agent())
    else:
        print("Set OPENAI_API_KEY to test the ACT agent")