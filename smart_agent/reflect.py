#!/usr/bin/env python3
"""
REFLECT Step - AI-Powered Learning and Analysis

This module implements Step 4 of the trading loop where OpenAI O3 analyzes
trading outcomes, learns from results, and provides insights for future decisions.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

from .base_agent import StepAgent

logger = logging.getLogger(__name__)

@dataclass
class LessonLearned:
    """A specific lesson learned from trading outcomes"""
    category: str  # EXECUTION, TIMING, ALLOCATION, RISK, MARKET
    lesson: str
    evidence: str
    confidence: float
    actionable: bool
    impact_level: str  # LOW, MEDIUM, HIGH

@dataclass
class PerformanceMetric:
    """Performance tracking metric"""
    name: str
    value: float
    benchmark: Optional[float] = None
    trend: str = "STABLE"  # IMPROVING, DECLINING, STABLE
    significance: str = "MEDIUM"  # LOW, MEDIUM, HIGH

@dataclass
class ReflectResult:
    """Result from the REFLECT step"""
    timestamp: datetime
    session_summary: Dict[str, Any]
    performance_metrics: List[PerformanceMetric]
    lessons_learned: List[LessonLearned]
    portfolio_analysis: Dict[str, Any]
    market_insights: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    ai_insights: List[str]
    confidence_score: float
    next_session_guidance: Dict[str, Any]

class ReflectAgent(StepAgent):
    """
    REFLECT Agent - AI-powered learning and performance analysis
    
    This agent uses OpenAI O3 to:
    1. Analyze trading session outcomes and performance
    2. Learn from successes and failures
    3. Identify patterns and improve future decisions
    4. Track portfolio evolution and risk metrics
    5. Generate actionable insights for next session
    """
    
    def __init__(self, 
                 mcp_url: str = "http://127.0.0.1:8001/mcp",
                 openai_api_key: str = None,
                 model: str = "o3-mini"):
        super().__init__("REFLECT", mcp_url, openai_api_key, model)
        self.reflection_history = []
        
    async def execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the REFLECT step with AI-powered analysis and learning
        
        Args:
            context: Context including all previous step results
            
        Returns:
            Comprehensive reflection and learning insights
        """
        self.log_step_start()
        
        try:
            # Extract all step results
            sense_data = context.get('sense_data')
            think_data = context.get('think_data')
            act_data = context.get('act_data')
            config = context.get('config', {})
            
            # Load historical performance if available
            historical_data = await self._load_historical_reflections()
            
            # Let AI perform comprehensive analysis
            reflection_result = await self._ai_comprehensive_analysis(
                sense_data, think_data, act_data, config, historical_data
            )
            
            # Save reflection for future reference
            await self._save_reflection(reflection_result)
            
            # Log summary
            lessons_count = len(reflection_result.lessons_learned)
            recommendations_count = len(reflection_result.recommendations)
            summary = f"Generated {lessons_count} lessons, {recommendations_count} recommendations"
            self.log_step_complete(summary)
            
            return {
                'step': 'REFLECT',
                'timestamp': reflection_result.timestamp.isoformat(),
                'success': True,
                'data': reflection_result,
                'insights_generated': lessons_count + recommendations_count,
                'confidence_score': reflection_result.confidence_score
            }
            
        except Exception as e:
            self.step_logger.error(f"REFLECT step failed: {e}")
            
            # Fallback reflection
            fallback_result = await self._fallback_reflection(context)
            return fallback_result
    
    async def _ai_comprehensive_analysis(self, sense_data: Any, think_data: Any, 
                                       act_data: Any, config: Dict[str, Any],
                                       historical_data: List[Dict[str, Any]]) -> ReflectResult:
        """
        AI-powered comprehensive analysis of the trading session
        
        Args:
            sense_data: Results from SENSE step
            think_data: Results from THINK step  
            act_data: Results from ACT step
            config: Configuration used
            historical_data: Previous reflection data
            
        Returns:
            Comprehensive ReflectResult
        """
        if not self.openai_client:
            return await self._fallback_analysis(sense_data, think_data, act_data, config)
        
        # Prepare comprehensive analysis prompt
        analysis_prompt = self._create_reflection_prompt(
            sense_data, think_data, act_data, config, historical_data
        )
        
        # Let AI analyze everything
        ai_result = await self.ai_decide_and_execute(
            analysis_prompt,
            {
                "sense_data": sense_data,
                "think_data": think_data,
                "act_data": act_data,
                "config": config,
                "historical_data": historical_data,
                "analysis_type": "comprehensive_reflection"
            },
            max_tool_calls=15  # Allow extensive analysis
        )
        
        # Process AI results into structured reflection
        reflection_result = await self._process_ai_reflection(
            ai_result, sense_data, think_data, act_data
        )
        
        return reflection_result
    
    def _create_reflection_prompt(self, sense_data: Any, think_data: Any, 
                                act_data: Any, config: Dict[str, Any],
                                historical_data: List[Dict[str, Any]]) -> str:
        """Create comprehensive reflection prompt for AI"""
        
        # Extract key metrics from the session
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 0)
        decisions_made = len(getattr(think_data, 'decisions', []))
        trades_executed = getattr(act_data, 'trades_successful', 0)
        total_trade_value = getattr(act_data, 'total_trade_value', 0)
        
        prompt = f"""
You are an expert trading coach and performance analyst. Conduct a comprehensive reflection and analysis of this trading session to extract maximum learning value.

SESSION OVERVIEW:
- Portfolio Value: ${portfolio_value:,.2f}
- Decisions Made: {decisions_made}
- Trades Executed: {trades_executed}
- Total Trade Value: ${total_trade_value:,.2f}
- Execution Mode: {'PAPER' if config.get('paper_trading', True) else 'LIVE'}

DETAILED SESSION DATA:
{self._format_session_data(sense_data, think_data, act_data)}

HISTORICAL CONTEXT:
{self._format_historical_context(historical_data)}

COMPREHENSIVE ANALYSIS OBJECTIVES:

1. PERFORMANCE EVALUATION:
   - Assess decision quality and execution effectiveness
   - Measure portfolio allocation improvements
   - Evaluate risk management and safety protocols
   - Calculate session ROI and impact metrics

2. LEARNING EXTRACTION:
   - Identify what worked well and why
   - Analyze failures and missed opportunities  
   - Extract actionable patterns and insights
   - Categorize lessons by importance and confidence

3. STRATEGIC INSIGHTS:
   - Market timing and condition assessment
   - Portfolio allocation effectiveness
   - Risk management performance
   - AI decision-making quality

4. FUTURE OPTIMIZATION:
   - Recommend strategy adjustments
   - Suggest parameter tuning
   - Identify areas for improvement
   - Provide guidance for next session

Use MCP tools to gather additional data if needed:
- Get updated portfolio positions to see actual changes
- Retrieve latest P&L to measure session impact
- Analyze market movements since trades were made
- Compare portfolio allocation to targets

DELIVERABLES:
1. Specific lessons learned with evidence and confidence levels
2. Performance metrics with trends and benchmarks
3. Actionable recommendations for improvement
4. Strategic insights for future sessions
5. Risk assessment and safety evaluation

Be thorough, evidence-based, and focus on actionable insights that will improve future performance.
"""
        
        return prompt
    
    def _format_session_data(self, sense_data: Any, think_data: Any, act_data: Any) -> str:
        """Format session data for AI analysis"""
        lines = []
        
        # SENSE data summary
        lines.append("SENSE PHASE RESULTS:")
        if sense_data:
            lines.append(f"- Portfolio positions: {getattr(sense_data, 'position_count', 0)}")
            lines.append(f"- Market data gathered: {len(getattr(sense_data, 'symbols_tracked', []))}")
            lines.append(f"- Cash percentage: {getattr(sense_data, 'cash_percentage', 0):.1f}%")
        
        # THINK data summary  
        lines.append("\nTHINK PHASE RESULTS:")
        if think_data:
            decisions = getattr(think_data, 'decisions', [])
            lines.append(f"- Trading decisions generated: {len(decisions)}")
            if decisions:
                avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
                lines.append(f"- Average confidence: {avg_confidence:.2f}")
                lines.append("- Decision breakdown:")
                for d in decisions:
                    lines.append(f"  • {d.action} {d.quantity} {d.symbol} (confidence: {d.confidence:.2f})")
        
        # ACT data summary
        lines.append("\nACT PHASE RESULTS:")
        if act_data:
            lines.append(f"- Trades attempted: {getattr(act_data, 'trades_attempted', 0)}")
            lines.append(f"- Trades successful: {getattr(act_data, 'trades_successful', 0)}")
            lines.append(f"- Total trade value: ${getattr(act_data, 'total_trade_value', 0):,.2f}")
            lines.append(f"- Portfolio impact: {getattr(act_data, 'portfolio_impact', 0):.2f}%")
            
            trade_results = getattr(act_data, 'trade_results', [])
            if trade_results:
                lines.append("- Trade details:")
                for trade in trade_results:
                    status = "✅" if trade.success else "❌"
                    lines.append(f"  {status} {trade.action} {trade.quantity} {trade.symbol}")
                    if not trade.success and trade.error_message:
                        lines.append(f"     Error: {trade.error_message}")
        
        return "\n".join(lines)
    
    def _format_historical_context(self, historical_data: List[Dict[str, Any]]) -> str:
        """Format historical context for AI"""
        if not historical_data:
            return "No historical reflection data available."
        
        lines = []
        lines.append(f"Previous {len(historical_data)} reflection sessions:")
        
        for i, session in enumerate(historical_data[-5:], 1):  # Last 5 sessions
            timestamp = session.get('timestamp', 'Unknown')
            lessons = len(session.get('lessons_learned', []))
            performance = session.get('session_summary', {})
            lines.append(f"{i}. {timestamp}: {lessons} lessons, {performance}")
        
        return "\n".join(lines)
    
    async def _process_ai_reflection(self, ai_result: Dict[str, Any],
                                   sense_data: Any, think_data: Any, act_data: Any) -> ReflectResult:
        """Process AI reflection results into structured ReflectResult"""
        
        # Extract lessons learned from AI analysis
        lessons_learned = await self._extract_lessons_from_ai(ai_result)
        
        # Build performance metrics
        performance_metrics = self._build_performance_metrics(sense_data, think_data, act_data)
        
        # Create session summary
        session_summary = {
            "portfolio_value": getattr(sense_data, 'total_portfolio_value', 0),
            "decisions_made": len(getattr(think_data, 'decisions', [])),
            "trades_executed": getattr(act_data, 'trades_successful', 0),
            "success_rate": (getattr(act_data, 'trades_successful', 0) / 
                           max(1, getattr(act_data, 'trades_attempted', 1))) * 100,
            "total_trade_value": getattr(act_data, 'total_trade_value', 0),
            "portfolio_impact": getattr(act_data, 'portfolio_impact', 0)
        }
        
        # Extract recommendations and insights
        recommendations = self._extract_recommendations_from_ai(ai_result)
        ai_insights = ai_result.get('reasoning', [])
        
        # Build portfolio and market analysis from AI tools
        portfolio_analysis = await self._build_portfolio_analysis_from_ai(ai_result)
        market_insights = await self._build_market_insights_from_ai(ai_result)
        risk_assessment = self._build_risk_assessment(act_data, lessons_learned)
        
        # Calculate confidence score
        confidence_score = self._calculate_reflection_confidence(ai_result, lessons_learned)
        
        # Generate next session guidance
        next_session_guidance = self._generate_next_session_guidance(
            lessons_learned, recommendations, performance_metrics
        )
        
        return ReflectResult(
            timestamp=datetime.now(),
            session_summary=session_summary,
            performance_metrics=performance_metrics,
            lessons_learned=lessons_learned,
            portfolio_analysis=portfolio_analysis,
            market_insights=market_insights,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            ai_insights=ai_insights,
            confidence_score=confidence_score,
            next_session_guidance=next_session_guidance
        )
    
    async def _extract_lessons_from_ai(self, ai_result: Dict[str, Any]) -> List[LessonLearned]:
        """Extract structured lessons from AI analysis"""
        lessons = []
        
        # Parse lessons from AI final result
        final_result = ai_result.get('final_result', '')
        
        # Look for lesson patterns in AI response
        lines = final_result.split('\n')
        current_category = "GENERAL"
        
        for line in lines:
            line = line.strip()
            
            # Detect category headers
            for category in ["EXECUTION", "TIMING", "ALLOCATION", "RISK", "MARKET"]:
                if category.lower() in line.lower():
                    current_category = category
                    break
            
            # Look for lesson indicators
            if any(indicator in line.lower() for indicator in ["learned:", "insight:", "lesson:", "finding:"]):
                lesson_text = line.split(":", 1)[-1].strip()
                if lesson_text:
                    lessons.append(LessonLearned(
                        category=current_category,
                        lesson=lesson_text,
                        evidence="From AI analysis",
                        confidence=0.8,
                        actionable=True,
                        impact_level="MEDIUM"
                    ))
        
        # If no structured lessons found, create from tool calls
        if not lessons:
            for tool_call in ai_result.get('tool_calls', []):
                if tool_call.get('success'):
                    tool_name = tool_call['tool_name']
                    lessons.append(LessonLearned(
                        category="EXECUTION",
                        lesson=f"Successfully used {tool_name} for analysis",
                        evidence=f"Tool call succeeded: {tool_call.get('reasoning', '')}",
                        confidence=0.7,
                        actionable=True,
                        impact_level="LOW"
                    ))
        
        return lessons
    
    def _build_performance_metrics(self, sense_data: Any, think_data: Any, act_data: Any) -> List[PerformanceMetric]:
        """Build performance metrics from session data"""
        metrics = []
        
        # Decision making metrics
        decisions = getattr(think_data, 'decisions', [])
        if decisions:
            avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
            metrics.append(PerformanceMetric(
                name="Decision Confidence",
                value=avg_confidence,
                benchmark=0.7,
                trend="STABLE",
                significance="HIGH"
            ))
        
        # Execution metrics
        trades_attempted = getattr(act_data, 'trades_attempted', 0)
        trades_successful = getattr(act_data, 'trades_successful', 0)
        
        if trades_attempted > 0:
            success_rate = (trades_successful / trades_attempted) * 100
            metrics.append(PerformanceMetric(
                name="Execution Success Rate",
                value=success_rate,
                benchmark=90.0,
                trend="STABLE",
                significance="HIGH"
            ))
        
        # Portfolio impact
        portfolio_impact = getattr(act_data, 'portfolio_impact', 0)
        metrics.append(PerformanceMetric(
            name="Portfolio Impact %",
            value=portfolio_impact,
            benchmark=2.0,
            trend="STABLE",
            significance="MEDIUM"
        ))
        
        # Risk metrics
        total_trade_value = getattr(act_data, 'total_trade_value', 0)
        portfolio_value = getattr(sense_data, 'total_portfolio_value', 1)
        risk_exposure = (total_trade_value / portfolio_value) * 100
        
        metrics.append(PerformanceMetric(
            name="Risk Exposure %",
            value=risk_exposure,
            benchmark=5.0,
            trend="STABLE",
            significance="HIGH"
        ))
        
        return metrics
    
    def _extract_recommendations_from_ai(self, ai_result: Dict[str, Any]) -> List[str]:
        """Extract recommendations from AI analysis"""
        recommendations = []
        
        final_result = ai_result.get('final_result', '')
        lines = final_result.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(word in line.lower() for word in ["recommend", "suggest", "should", "consider"]):
                if len(line) > 10:  # Filter out short/incomplete lines
                    recommendations.append(line)
        
        # Default recommendations if none found
        if not recommendations:
            recommendations = [
                "Continue monitoring portfolio allocation drift",
                "Review and adjust risk parameters based on market conditions",
                "Consider market timing for future trades"
            ]
        
        return recommendations
    
    async def _build_portfolio_analysis_from_ai(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build portfolio analysis from AI tool calls"""
        analysis = {
            "allocation_status": "unknown",
            "diversification": "adequate",
            "concentration_risk": "low",
            "cash_level": "appropriate"
        }
        
        # Extract insights from AI tool calls
        for tool_call in ai_result.get('tool_calls', []):
            if tool_call['tool_name'] in ['get_positions', 'portfolio_health_check']:
                if tool_call.get('success'):
                    # Portfolio analysis was performed
                    analysis["allocation_status"] = "analyzed"
        
        return analysis
    
    async def _build_market_insights_from_ai(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build market insights from AI analysis"""
        insights = {
            "market_sentiment": "neutral",
            "volatility_level": "moderate",
            "trend_assessment": "mixed",
            "opportunities": [],
            "risks": []
        }
        
        # Extract market insights from AI tool calls
        for tool_call in ai_result.get('tool_calls', []):
            if tool_call['tool_name'] in ['get_market_snapshot', 'scan_top_gainers', 'scan_top_losers']:
                if tool_call.get('success'):
                    insights["opportunities"].append(f"Market data analyzed via {tool_call['tool_name']}")
        
        return insights
    
    def _build_risk_assessment(self, act_data: Any, lessons_learned: List[LessonLearned]) -> Dict[str, Any]:
        """Build risk assessment from execution results and lessons"""
        
        safety_checks = getattr(act_data, 'safety_checks_performed', 0)
        trades_failed = getattr(act_data, 'trades_failed', 0)
        portfolio_impact = getattr(act_data, 'portfolio_impact', 0)
        
        risk_level = "LOW"
        if portfolio_impact > 5:
            risk_level = "HIGH"
        elif portfolio_impact > 2 or trades_failed > 0:
            risk_level = "MEDIUM"
        
        risk_lessons = [l for l in lessons_learned if l.category == "RISK"]
        
        return {
            "overall_risk_level": risk_level,
            "safety_checks_performed": safety_checks,
            "failed_trades": trades_failed,
            "portfolio_impact_pct": portfolio_impact,
            "risk_lessons_count": len(risk_lessons),
            "risk_management_effectiveness": "good" if trades_failed == 0 else "needs_improvement"
        }
    
    def _calculate_reflection_confidence(self, ai_result: Dict[str, Any], 
                                       lessons_learned: List[LessonLearned]) -> float:
        """Calculate confidence in the reflection analysis"""
        
        base_confidence = 0.7
        
        # Bonus for AI tool usage
        tool_calls = len(ai_result.get('tool_calls', []))
        successful_tools = len([t for t in ai_result.get('tool_calls', []) if t.get('success')])
        
        if tool_calls > 0:
            tool_success_rate = successful_tools / tool_calls
            base_confidence += (tool_success_rate * 0.2)
        
        # Bonus for lesson quality
        high_confidence_lessons = len([l for l in lessons_learned if l.confidence > 0.8])
        if high_confidence_lessons > 0:
            base_confidence += min(0.1, high_confidence_lessons * 0.02)
        
        # Bonus for reasoning quality
        reasoning_count = len(ai_result.get('reasoning', []))
        if reasoning_count > 5:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    def _generate_next_session_guidance(self, lessons_learned: List[LessonLearned],
                                      recommendations: List[str],
                                      performance_metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Generate guidance for the next trading session"""
        
        # Key areas to focus on
        focus_areas = []
        for lesson in lessons_learned:
            if lesson.impact_level == "HIGH" and lesson.actionable:
                focus_areas.append(lesson.category.lower())
        
        # Parameter adjustments
        adjustments = []
        for metric in performance_metrics:
            if metric.value < (metric.benchmark or 0.8):
                adjustments.append(f"Improve {metric.name.lower()}")
        
        # Priority actions
        priority_actions = recommendations[:3]  # Top 3 recommendations
        
        return {
            "focus_areas": list(set(focus_areas)),
            "parameter_adjustments": adjustments,
            "priority_actions": priority_actions,
            "confidence_level": "medium",
            "estimated_readiness": "ready"
        }
    
    async def _load_historical_reflections(self) -> List[Dict[str, Any]]:
        """Load historical reflection data"""
        try:
            reflections_dir = Path("smart_agent/reflections")
            if not reflections_dir.exists():
                return []
            
            reflections = []
            for file_path in sorted(reflections_dir.glob("reflection_*.json"))[-10:]:  # Last 10
                try:
                    with open(file_path, 'r') as f:
                        reflection = json.load(f)
                        reflections.append(reflection)
                except Exception as e:
                    self.step_logger.warning(f"Failed to load {file_path}: {e}")
            
            return reflections
        except Exception as e:
            self.step_logger.warning(f"Failed to load historical reflections: {e}")
            return []
    
    async def _save_reflection(self, reflection_result: ReflectResult):
        """Save reflection result for future reference"""
        try:
            reflections_dir = Path("smart_agent/reflections")
            reflections_dir.mkdir(exist_ok=True)
            
            timestamp_str = reflection_result.timestamp.strftime("%Y%m%d_%H%M%S")
            file_path = reflections_dir / f"reflection_{timestamp_str}.json"
            
            # Convert to serializable format
            reflection_dict = {
                "timestamp": reflection_result.timestamp.isoformat(),
                "session_summary": reflection_result.session_summary,
                "performance_metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "benchmark": m.benchmark,
                        "trend": m.trend,
                        "significance": m.significance
                    } for m in reflection_result.performance_metrics
                ],
                "lessons_learned": [
                    {
                        "category": l.category,
                        "lesson": l.lesson,
                        "evidence": l.evidence,
                        "confidence": l.confidence,
                        "actionable": l.actionable,
                        "impact_level": l.impact_level
                    } for l in reflection_result.lessons_learned
                ],
                "recommendations": reflection_result.recommendations,
                "ai_insights": reflection_result.ai_insights,
                "confidence_score": reflection_result.confidence_score,
                "next_session_guidance": reflection_result.next_session_guidance
            }
            
            with open(file_path, 'w') as f:
                json.dump(reflection_dict, f, indent=2)
            
            self.step_logger.info(f"Reflection saved to {file_path}")
            
        except Exception as e:
            self.step_logger.error(f"Failed to save reflection: {e}")
    
    async def _fallback_reflection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback reflection when AI analysis fails"""
        self.step_logger.info("Using fallback reflection analysis...")
        
        try:
            sense_data = context.get('sense_data')
            think_data = context.get('think_data')
            act_data = context.get('act_data')
            
            # Basic reflection without AI
            fallback_result = await self._fallback_analysis(sense_data, think_data, act_data, {})
            
            return {
                'step': 'REFLECT',
                'timestamp': fallback_result.timestamp.isoformat(),
                'success': True,
                'data': fallback_result,
                'fallback_used': True
            }
            
        except Exception as e:
            self.step_logger.error(f"Fallback reflection failed: {e}")
            return {
                'step': 'REFLECT',
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'fallback_used': True
            }
    
    async def _fallback_analysis(self, sense_data: Any, think_data: Any, 
                                act_data: Any, config: Dict[str, Any]) -> ReflectResult:
        """Basic reflection analysis without AI"""
        
        # Basic session summary
        session_summary = {
            "portfolio_value": getattr(sense_data, 'total_portfolio_value', 0),
            "decisions_made": len(getattr(think_data, 'decisions', [])),
            "trades_executed": getattr(act_data, 'trades_successful', 0),
            "total_trade_value": getattr(act_data, 'total_trade_value', 0)
        }
        
        # Basic lessons
        trades_successful = getattr(act_data, 'trades_successful', 0)
        trades_attempted = getattr(act_data, 'trades_attempted', 0)
        
        lessons = []
        if trades_attempted > 0:
            success_rate = trades_successful / trades_attempted
            if success_rate >= 0.8:
                lessons.append(LessonLearned(
                    category="EXECUTION",
                    lesson="High execution success rate indicates good trade validation",
                    evidence=f"Success rate: {success_rate:.1%}",
                    confidence=0.8,
                    actionable=True,
                    impact_level="MEDIUM"
                ))
            else:
                lessons.append(LessonLearned(
                    category="EXECUTION",
                    lesson="Low execution success rate suggests need for better validation",
                    evidence=f"Success rate: {success_rate:.1%}",
                    confidence=0.8,
                    actionable=True,
                    impact_level="HIGH"
                ))
        
        # Basic metrics
        performance_metrics = self._build_performance_metrics(sense_data, think_data, act_data)
        
        # Basic recommendations
        recommendations = [
            "Review trade execution patterns",
            "Monitor portfolio allocation drift",
            "Assess risk management effectiveness"
        ]
        
        return ReflectResult(
            timestamp=datetime.now(),
            session_summary=session_summary,
            performance_metrics=performance_metrics,
            lessons_learned=lessons,
            portfolio_analysis={"fallback": True},
            market_insights={"fallback": True},
            risk_assessment={"fallback": True},
            recommendations=recommendations,
            ai_insights=["Used fallback analysis - no AI available"],
            confidence_score=0.6,
            next_session_guidance={"fallback": True}
        )

if __name__ == "__main__":
    import os
    from types import SimpleNamespace
    
    # Example usage and testing
    async def test_reflect_agent():
        agent = ReflectAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        await agent.initialize()
        
        # Mock session data
        mock_sense_data = SimpleNamespace(
            total_portfolio_value=50000.0,
            position_count=5,
            symbols_tracked=["SPY", "JNJ", "QQQ"],
            cash_percentage=10.0
        )
        
        mock_think_data = SimpleNamespace(
            decisions=[
                SimpleNamespace(symbol="SPY", action="BUY", quantity=5, confidence=0.8, urgency="MEDIUM"),
                SimpleNamespace(symbol="JNJ", action="SELL", quantity=2, confidence=0.7, urgency="LOW")
            ],
            confidence_score=0.75,
            ai_reasoning=["Portfolio rebalancing needed", "Market conditions favorable"]
        )
        
        mock_act_data = SimpleNamespace(
            trades_attempted=2,
            trades_successful=2,
            trades_failed=0,
            total_trade_value=1500.0,
            portfolio_impact=3.0,
            safety_checks_performed=2,
            trade_results=[
                SimpleNamespace(symbol="SPY", action="BUY", success=True),
                SimpleNamespace(symbol="JNJ", action="SELL", success=True)
            ]
        )
        
        context = {
            "sense_data": mock_sense_data,
            "think_data": mock_think_data,
            "act_data": mock_act_data,
            "config": {
                "paper_trading": True,
                "risk_threshold": 1000.0
            }
        }
        
        result = await agent.execute_step(context)
        
        print("=== REFLECT STEP RESULT ===")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            reflect_result = result['data']
            print(f"\n=== REFLECTION SUMMARY ===")
            print(f"Lessons Learned: {len(reflect_result.lessons_learned)}")
            print(f"Performance Metrics: {len(reflect_result.performance_metrics)}")
            print(f"Recommendations: {len(reflect_result.recommendations)}")
            print(f"Confidence Score: {reflect_result.confidence_score:.2f}")
            
            print(f"\n=== KEY LESSONS ===")
            for lesson in reflect_result.lessons_learned[:3]:
                print(f"• [{lesson.category}] {lesson.lesson}")
                print(f"  Evidence: {lesson.evidence}")
                print(f"  Confidence: {lesson.confidence:.2f}")
                print()
    
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_reflect_agent())
    else:
        print("Set OPENAI_API_KEY to test the REFLECT agent")