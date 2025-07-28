#!/usr/bin/env python3
"""
Smart Trading Agent Orchestrator

This module coordinates the 4-step trading loop using modular AI agents
that intelligently decide when to use MCP tools.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .sense import SenseAgent
from .think import ThinkAgent
from .act import ActAgent
from .reflect import ReflectAgent
from .config import SmartTraderConfig

logger = logging.getLogger(__name__)

@dataclass
class TradingSession:
    """Result of a complete trading session"""
    session_id: str
    start_time: datetime
    end_time: datetime
    success: bool
    sense_result: Dict[str, Any]
    think_result: Dict[str, Any]
    act_result: Dict[str, Any]
    reflect_result: Dict[str, Any]
    total_runtime: float
    error_message: Optional[str] = None

class SmartTradingOrchestrator:
    """
    Orchestrates the 4-step trading loop with AI agents
    
    This class:
    1. Initializes all step agents
    2. Coordinates the SENSE → THINK → ACT → REFLECT flow
    3. Handles errors and fallbacks
    4. Manages configuration and state
    5. Provides continuous loop functionality
    """
    
    def __init__(self, config: SmartTraderConfig):
        """
        Initialize the orchestrator with configuration
        
        Args:
            config: SmartTraderConfig object with all settings
        """
        self.config = config
        self.session_history: List[TradingSession] = []
        
        # Initialize step agents
        self.sense_agent = SenseAgent(
            mcp_url=config.mcp_url,
            openai_api_key=config.openai_api_key,
            model="o3-mini"
        )
        
        self.think_agent = ThinkAgent(
            mcp_url=config.mcp_url,
            openai_api_key=config.openai_api_key,
            model="o3-mini"
        )
        
        self.act_agent = ActAgent(
            mcp_url=config.mcp_url,
            openai_api_key=config.openai_api_key,
            model="o3-mini"
        )
        
        self.reflect_agent = ReflectAgent(
            mcp_url=config.mcp_url,
            openai_api_key=config.openai_api_key,
            model="o3-mini"
        )
        
        # Trading state
        self.initialized = False
        
    async def initialize(self):
        """Initialize all agents and connections"""
        if self.initialized:
            return
        
        logger.info("🤖 Initializing Smart Trading Orchestrator...")
        
        try:
            # Initialize all agents in parallel for speed
            await asyncio.gather(
                self.sense_agent.initialize(),
                self.think_agent.initialize(),
                self.act_agent.initialize(),
                self.reflect_agent.initialize()
            )
            
            self.initialized = True
            logger.info("✅ All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            raise
    
    async def run_single_session(self) -> TradingSession:
        """
        Run a single complete trading session (all 4 steps)
        
        Returns:
            TradingSession with complete results
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"🚀 Starting trading session: {session_id}")
        
        # Ensure agents are initialized
        await self.initialize()
        
        try:
            # Prepare base context
            context = {
                'session_id': session_id,
                'config': self.config.__dict__,
                'trading_rules': [
                    {
                        'name': rule.name,
                        'description': rule.description,
                        'target_allocation': rule.target_allocation,
                        'symbols': rule.symbols,
                        'max_position_size': rule.max_position_size,
                        'stop_loss': rule.stop_loss,
                        'take_profit': rule.take_profit,
                        'enabled': rule.enabled
                    }
                    for rule in self.config.trading_rules if rule.enabled
                ]
            }
            
            # STEP 1: SENSE
            logger.info("=" * 60)
            sense_result = await self.sense_agent.execute_step(context)
            context['sense_data'] = sense_result.get('data')
            
            # STEP 2: THINK
            logger.info("=" * 60)
            think_result = await self.think_agent.execute_step(context)
            context['think_data'] = think_result.get('data')
            
            # STEP 3: ACT
            logger.info("=" * 60)
            act_result = await self.act_agent.execute_step(context)
            context['act_data'] = act_result.get('data')
            
            # STEP 4: REFLECT
            logger.info("=" * 60)
            reflect_result = await self.reflect_agent.execute_step(context)
            
            # Create session result
            end_time = datetime.now()
            runtime = (end_time - start_time).total_seconds()
            
            session = TradingSession(
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                success=True,
                sense_result=sense_result,
                think_result=think_result,
                act_result=act_result,
                reflect_result=reflect_result,
                total_runtime=runtime
            )
            
            # Add to history
            self.session_history.append(session)
            
            # Log session summary
            self._log_session_summary(session)
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Trading session failed: {e}")
            
            end_time = datetime.now()
            runtime = (end_time - start_time).total_seconds()
            
            # Create failed session
            session = TradingSession(
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                success=False,
                sense_result={},
                think_result={},
                act_result={},
                reflect_result={},
                total_runtime=runtime,
                error_message=str(e)
            )
            
            self.session_history.append(session)
            return session
    
    async def run_continuous_loop(self, interval_hours: int = 24, max_sessions: int = None):
        """
        Run continuous trading sessions at specified intervals
        
        Args:
            interval_hours: Hours between sessions
            max_sessions: Maximum number of sessions (None for unlimited)
        """
        logger.info(f"🔄 Starting continuous trading loop")
        logger.info(f"📅 Interval: {interval_hours} hours")
        logger.info(f"📊 Max sessions: {max_sessions or 'unlimited'}")
        logger.info(f"🎯 Paper trading: {self.config.paper_trading}")
        
        session_count = 0
        
        try:
            while True:
                # Check if we've hit the session limit
                if max_sessions and session_count >= max_sessions:
                    logger.info(f"🛑 Reached maximum sessions limit: {max_sessions}")
                    break
                
                # Run trading session
                session = await self.run_single_session()
                session_count += 1
                
                if session.success:
                    logger.info(f"✅ Session {session_count} completed successfully")
                else:
                    logger.error(f"❌ Session {session_count} failed: {session.error_message}")
                
                # Calculate next run time
                next_run = datetime.now() + timedelta(hours=interval_hours)
                logger.info(f"💤 Next session scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
        except KeyboardInterrupt:
            logger.info("👋 Continuous loop stopped by user")
        except Exception as e:
            logger.error(f"❌ Continuous loop error: {e}")
    
    def _log_session_summary(self, session: TradingSession):
        """Log a comprehensive session summary"""
        logger.info("=" * 60)
        logger.info("📊 TRADING SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Session ID: {session.session_id}")
        logger.info(f"Runtime: {session.total_runtime:.1f} seconds")
        logger.info(f"Success: {'✅' if session.success else '❌'}")
        
        if session.success:
            # Extract key metrics
            sense_data = session.sense_result.get('data')
            think_data = session.think_result.get('data')
            act_data = session.act_result.get('data')
            reflect_data = session.reflect_result.get('data')
            
            # Portfolio metrics
            if sense_data:
                portfolio_value = getattr(sense_data, 'total_portfolio_value', 0)
                available_funds = getattr(sense_data, 'available_funds', 0)
                position_count = getattr(sense_data, 'position_count', 0)
                
                logger.info(f"Portfolio Value: ${portfolio_value:,.2f}")
                logger.info(f"Available Funds: ${available_funds:,.2f}")
                logger.info(f"Positions: {position_count}")
            
            # Decision metrics
            if think_data:
                decisions = getattr(think_data, 'decisions', [])
                confidence = getattr(think_data, 'confidence_score', 0)
                
                logger.info(f"Decisions Generated: {len(decisions)}")
                logger.info(f"AI Confidence: {confidence:.2f}")
            
            # Execution metrics
            if act_data:
                trades_attempted = getattr(act_data, 'trades_attempted', 0)
                trades_successful = getattr(act_data, 'trades_successful', 0)
                trade_value = getattr(act_data, 'total_trade_value', 0)
                
                logger.info(f"Trades Executed: {trades_successful}/{trades_attempted}")
                logger.info(f"Trade Value: ${trade_value:,.2f}")
            
            # Learning metrics
            if reflect_data:
                lessons = getattr(reflect_data, 'lessons_learned', [])
                recommendations = getattr(reflect_data, 'recommendations', [])
                
                logger.info(f"Lessons Learned: {len(lessons)}")
                logger.info(f"Recommendations: {len(recommendations)}")
        
        logger.info("=" * 60)
    
    def get_session_history(self, limit: int = 10) -> List[TradingSession]:
        """Get recent session history"""
        return self.session_history[-limit:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        if not self.session_history:
            return {"no_data": True}
        
        successful_sessions = [s for s in self.session_history if s.success]
        total_sessions = len(self.session_history)
        success_rate = len(successful_sessions) / total_sessions * 100
        
        avg_runtime = sum(s.total_runtime for s in self.session_history) / total_sessions
        
        # Calculate trading metrics from successful sessions
        total_trades = 0
        successful_trades = 0
        total_trade_value = 0.0
        
        for session in successful_sessions:
            act_data = session.act_result.get('data')
            if act_data:
                total_trades += getattr(act_data, 'trades_attempted', 0)
                successful_trades += getattr(act_data, 'trades_successful', 0)
                total_trade_value += getattr(act_data, 'total_trade_value', 0)
        
        trade_success_rate = (successful_trades / max(1, total_trades)) * 100
        
        return {
            "total_sessions": total_sessions,
            "successful_sessions": len(successful_sessions),
            "session_success_rate": success_rate,
            "average_runtime_seconds": avg_runtime,
            "total_trades_attempted": total_trades,
            "total_trades_successful": successful_trades,
            "trade_success_rate": trade_success_rate,
            "total_trade_value": total_trade_value,
            "last_session": self.session_history[-1].session_id if self.session_history else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator_status": "healthy",
            "agents_status": {},
            "mcp_connectivity": False,
            "ai_connectivity": False,
            "configuration_valid": True,
            "issues": []
        }
        
        try:
            # Check agent initialization
            if not self.initialized:
                await self.initialize()
            
            # Test MCP connectivity
            try:
                test_result = await self.sense_agent.call_mcp_tool("get_accounts")
                health["mcp_connectivity"] = test_result.success
                if not test_result.success:
                    health["issues"].append(f"MCP connectivity issue: {test_result.error}")
            except Exception as e:
                health["issues"].append(f"MCP test failed: {str(e)}")
            
            # Test AI connectivity
            if self.config.openai_api_key:
                try:
                    # Simple AI test
                    response = self.think_agent.openai_client.chat.completions.create(
                        model="o3-mini",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    health["ai_connectivity"] = True
                except Exception as e:
                    health["issues"].append(f"AI connectivity issue: {str(e)}")
            else:
                health["issues"].append("No OpenAI API key configured")
            
            # Validate configuration
            config_issues = self.config.validate()
            if config_issues:
                health["configuration_valid"] = False
                health["issues"].extend(config_issues)
            
            # Agent status
            for agent_name, agent in [
                ("sense", self.sense_agent),
                ("think", self.think_agent),
                ("act", self.act_agent),
                ("reflect", self.reflect_agent)
            ]:
                health["agents_status"][agent_name] = {
                    "initialized": hasattr(agent, 'account_id') and agent.account_id is not None,
                    "tools_available": len(agent.get_available_tools()) if hasattr(agent, 'get_available_tools') else 0
                }
            
            # Overall health assessment
            if health["issues"]:
                health["orchestrator_status"] = "degraded" if len(health["issues"]) < 3 else "unhealthy"
            
        except Exception as e:
            health["orchestrator_status"] = "unhealthy"
            health["issues"].append(f"Health check failed: {str(e)}")
        
        return health
    
    async def emergency_stop(self):
        """Emergency stop all operations"""
        logger.warning("🛑 Emergency stop initiated")
        
        try:
            # Cancel any pending orders (if in live trading mode)
            if not self.config.paper_trading:
                logger.info("Checking for live orders to cancel...")
                live_orders_result = await self.act_agent.call_mcp_tool("get_live_orders")
                
                if live_orders_result.success:
                    orders = live_orders_result.data.get('orders', [])
                    for order in orders:
                        order_id = order.get('orderId')
                        if order_id:
                            cancel_result = await self.act_agent.call_mcp_tool("cancel_order", {
                                "order_id": order_id
                            })
                            if cancel_result.success:
                                logger.info(f"Cancelled order: {order_id}")
                            else:
                                logger.error(f"Failed to cancel order {order_id}: {cancel_result.error}")
            
            logger.info("✅ Emergency stop completed")
            
        except Exception as e:
            logger.error(f"❌ Emergency stop failed: {e}")

if __name__ == "__main__":
    import os
    from .config import SmartTraderConfig
    
    # Example usage
    async def test_orchestrator():
        # Create test configuration
        config = SmartTraderConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            paper_trading=True,
            risk_threshold=500.0
        )
        
        # Create orchestrator
        orchestrator = SmartTradingOrchestrator(config)
        
        # Health check
        health = await orchestrator.health_check()
        print("=== HEALTH CHECK ===")
        print(json.dumps(health, indent=2))
        
        if health["orchestrator_status"] == "healthy":
            # Run single session
            print("\n=== RUNNING SINGLE SESSION ===")
            session = await orchestrator.run_single_session()
            
            print(f"Session completed: {session.success}")
            print(f"Runtime: {session.total_runtime:.1f} seconds")
            
            # Performance stats
            stats = orchestrator.get_performance_stats()
            print("\n=== PERFORMANCE STATS ===")
            print(json.dumps(stats, indent=2))
        else:
            print("❌ System not healthy, skipping session")
    
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_orchestrator())
    else:
        print("Set OPENAI_API_KEY to test the orchestrator")