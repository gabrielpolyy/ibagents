#!/usr/bin/env python3
"""
Smart Trading Agent - Modular Architecture

A sophisticated AI-powered trading system that uses OpenAI O3 and 
Interactive Brokers MCP tools for intelligent portfolio management.

This package implements a 4-step trading loop with separate AI agents:
- SENSE: Intelligently gathers market and portfolio data
- THINK: Analyzes data and makes trading decisions using AI
- ACT: Executes trades with comprehensive safety checks  
- REFLECT: Learns from outcomes and improves performance

Each agent can intelligently decide when and how to use MCP tools
rather than having hardcoded tool usage.
"""

from .config import SmartTraderConfig, TradingRuleConfig, ConfigManager
from .orchestrator import SmartTradingOrchestrator, TradingSession
from .base_agent import MCPAgent, StepAgent, MCPToolResult
from .sense import SenseAgent, SenseData
from .think import ThinkAgent, TradingDecision, ThinkResult
from .act import ActAgent, TradeResult, ActResult
from .reflect import ReflectAgent, LessonLearned, PerformanceMetric, ReflectResult

__version__ = "2.0.0"
__author__ = "Smart Trading Agent"
__description__ = "AI-powered modular trading system with OpenAI O3 and MCP integration"

# Export main classes for easy import
__all__ = [
    # Main orchestrator
    'SmartTradingOrchestrator',
    'TradingSession',
    
    # Configuration
    'SmartTraderConfig', 
    'TradingRuleConfig',
    'ConfigManager',
    
    # Base agent classes
    'MCPAgent',
    'StepAgent', 
    'MCPToolResult',
    
    # Step agents
    'SenseAgent',
    'ThinkAgent', 
    'ActAgent',
    'ReflectAgent',
    
    # Data structures
    'SenseData',
    'TradingDecision',
    'ThinkResult',
    'TradeResult', 
    'ActResult',
    'LessonLearned',
    'PerformanceMetric',
    'ReflectResult'
]

# Quick start helper
def create_default_agent(openai_api_key: str = None, 
                        paper_trading: bool = True,
                        risk_threshold: float = 1000.0) -> SmartTradingOrchestrator:
    """
    Create a default smart trading agent with sensible settings
    
    Args:
        openai_api_key: OpenAI API key for AI features
        paper_trading: Whether to use paper trading (safer)
        risk_threshold: Maximum dollar risk per trade
        
    Returns:
        Configured SmartTradingOrchestrator ready to use
    """
    config = SmartTraderConfig(
        openai_api_key=openai_api_key,
        paper_trading=paper_trading,
        risk_threshold=risk_threshold
    )
    
    return SmartTradingOrchestrator(config)