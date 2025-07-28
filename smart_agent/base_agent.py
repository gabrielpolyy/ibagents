#!/usr/bin/env python3
"""
Base Agent with MCP Tool Access

This module provides a base class that allows AI agents to intelligently
decide when and how to use MCP tools for Interactive Brokers operations.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from fastmcp import Client
import openai

logger = logging.getLogger(__name__)

@dataclass
class MCPToolResult:
    """Result from an MCP tool call"""
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None

class MCPAgent:
    """
    Base agent class that provides MCP tool access with AI-driven decision making.
    
    The AI can intelligently choose which MCP tools to use and when, rather than
    having tools hardcoded into specific methods.
    """
    
    def __init__(self, 
                 mcp_url: str = "http://127.0.0.1:8001/mcp",
                 openai_api_key: str = None,
                 model: str = "o3-mini"):  # Use O3 model
        """
        Initialize the MCP agent
        
        Args:
            mcp_url: URL of the MCP server
            openai_api_key: OpenAI API key
            model: OpenAI model to use (default: o3-mini)
        """
        self.mcp_client = Client(mcp_url)
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.model = model
        self.available_tools = {}
        self.account_id = None
        
    async def initialize(self):
        """Initialize the agent and discover available MCP tools"""
        try:
            # Connect to MCP server and get available tools
            async with self.mcp_client:
                tools = await self.mcp_client.list_tools()
                
                # Build tool registry
                for tool in tools:
                    self.available_tools[tool.name] = {
                        'name': tool.name,
                        'description': tool.description,
                        'parameters': tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                        'tags': getattr(tool, 'tags', [])
                    }
                
                logger.info(f"Discovered {len(self.available_tools)} MCP tools")
                
                # Get account information
                await self._get_account_info()
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP agent: {e}")
            raise
    
    async def _get_account_info(self):
        """Get account information on initialization"""
        try:
            result = await self.call_mcp_tool("get_accounts")
            if result.success and result.data:
                accounts = result.data.get("accounts", [])
                if accounts:
                    self.account_id = accounts[0]["id"]
                    logger.info(f"Using account: {self.account_id}")
        except Exception as e:
            logger.warning(f"Could not get account info: {e}")
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> MCPToolResult:
        """
        Call an MCP tool directly
        
        Args:
            tool_name: Name of the MCP tool to call
            parameters: Parameters to pass to the tool
            
        Returns:
            MCPToolResult with the outcome
        """
        if parameters is None:
            parameters = {}
            
        try:
            async with self.mcp_client:
                result = await self.mcp_client.call_tool(tool_name, parameters)
                
                if result and len(result) > 0:
                    content = result[0]
                    if hasattr(content, 'text'):
                        try:
                            data = json.loads(content.text)
                            
                            if isinstance(data, dict) and "error" in data:
                                return MCPToolResult(
                                    tool_name=tool_name,
                                    success=False,
                                    error=data["error"],
                                    raw_response=content.text
                                )
                            else:
                                return MCPToolResult(
                                    tool_name=tool_name,
                                    success=True,
                                    data=data,
                                    raw_response=content.text
                                )
                        except json.JSONDecodeError:
                            return MCPToolResult(
                                tool_name=tool_name,
                                success=False,
                                error=f"Invalid JSON response: {content.text[:200]}...",
                                raw_response=content.text
                            )
                    else:
                        return MCPToolResult(
                            tool_name=tool_name,
                            success=False,
                            error="No text content in response"
                        )
                else:
                    return MCPToolResult(
                        tool_name=tool_name,
                        success=False,
                        error="Empty response from server"
                    )
                    
        except Exception as e:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e)
            )
    
    async def ai_decide_and_execute(self, 
                                   task_description: str, 
                                   context: Dict[str, Any] = None,
                                   max_tool_calls: int = 10) -> Dict[str, Any]:
        """
        Let the AI decide which MCP tools to use to accomplish a task
        
        Args:
            task_description: What the AI should accomplish
            context: Additional context for the AI
            max_tool_calls: Maximum number of tool calls to prevent infinite loops
            
        Returns:
            Dictionary with results and tool calls made
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not configured - cannot use AI decision making")
        
        if context is None:
            context = {}
        
        # Build the system prompt with available tools
        tools_description = self._format_tools_for_ai()
        
        system_prompt = f"""
You are an intelligent trading assistant with access to Interactive Brokers MCP tools.

AVAILABLE MCP TOOLS:
{tools_description}

Your task is to accomplish the following goal by intelligently choosing which tools to use:
{task_description}

GUIDELINES:
1. Think step by step about what information you need
2. Choose the most appropriate MCP tools for each step
3. Make tool calls one at a time, analyzing results before proceeding
4. If a tool call fails, try alternative approaches
5. Provide clear reasoning for each tool choice
6. Stop when you have sufficient information to complete the task

CONTEXT:
{json.dumps(context, indent=2, default=str)}

Account ID (if available): {self.account_id}

Respond with your next action. Format tool calls as:
TOOL_CALL: tool_name
PARAMETERS: {{"param": "value"}}
REASONING: Why you're making this call

Or if you're done:
COMPLETE: Summary of what was accomplished
"""

        conversation_history = [
            {"role": "system", "content": system_prompt}
        ]
        
        results = {
            "task": task_description,
            "tool_calls": [],
            "final_result": None,
            "success": False,
            "reasoning": []
        }
        
        tool_call_count = 0
        
        while tool_call_count < max_tool_calls:
            try:
                # Get AI response
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=conversation_history,
                    temperature=0.3,
                    max_tokens=2000
                )
                
                ai_response = response.choices[0].message.content
                conversation_history.append({"role": "assistant", "content": ai_response})
                
                logger.debug(f"AI Response: {ai_response}")
                
                # Parse AI response
                if "COMPLETE:" in ai_response:
                    # AI is done
                    completion_text = ai_response.split("COMPLETE:", 1)[1].strip()
                    results["final_result"] = completion_text
                    results["success"] = True
                    break
                
                elif "TOOL_CALL:" in ai_response:
                    # AI wants to make a tool call
                    tool_call_count += 1
                    
                    # Parse tool call
                    lines = ai_response.split('\n')
                    tool_name = None
                    parameters = {}
                    reasoning = ""
                    
                    for line in lines:
                        if line.startswith("TOOL_CALL:"):
                            tool_name = line.split(":", 1)[1].strip()
                        elif line.startswith("PARAMETERS:"):
                            try:
                                param_text = line.split(":", 1)[1].strip()
                                parameters = json.loads(param_text)
                            except json.JSONDecodeError:
                                parameters = {}
                        elif line.startswith("REASONING:"):
                            reasoning = line.split(":", 1)[1].strip()
                    
                    if tool_name:
                        logger.info(f"AI calling tool: {tool_name} with params: {parameters}")
                        logger.info(f"Reasoning: {reasoning}")
                        
                        # Add account_id if not provided and available
                        if self.account_id and "account_id" not in parameters:
                            # Check if this tool typically needs account_id
                            if any(tag in self.available_tools.get(tool_name, {}).get('tags', []) 
                                  for tag in ['portfolio', 'trading']):
                                parameters["account_id"] = self.account_id
                        
                        # Execute the tool call
                        tool_result = await self.call_mcp_tool(tool_name, parameters)
                        
                        # Record the tool call
                        results["tool_calls"].append({
                            "tool_name": tool_name,
                            "parameters": parameters,
                            "reasoning": reasoning,
                            "success": tool_result.success,
                            "result": tool_result.data if tool_result.success else tool_result.error
                        })
                        
                        results["reasoning"].append(reasoning)
                        
                        # Add result to conversation
                        if tool_result.success:
                            result_text = f"Tool call successful. Result: {json.dumps(tool_result.data, indent=2, default=str)}"
                        else:
                            result_text = f"Tool call failed. Error: {tool_result.error}"
                        
                        conversation_history.append({"role": "user", "content": result_text})
                    else:
                        conversation_history.append({"role": "user", "content": "Tool call format was unclear. Please specify TOOL_CALL: tool_name"})
                
                else:
                    # AI response doesn't match expected format
                    conversation_history.append({"role": "user", "content": "Please either make a TOOL_CALL or declare COMPLETE with your findings."})
                
            except Exception as e:
                logger.error(f"Error in AI decision loop: {e}")
                results["final_result"] = f"Error: {str(e)}"
                break
        
        if tool_call_count >= max_tool_calls:
            results["final_result"] = f"Reached maximum tool calls ({max_tool_calls})"
        
        return results
    
    def _format_tools_for_ai(self) -> str:
        """Format available MCP tools for AI consumption"""
        tool_descriptions = []
        
        for tool_name, tool_info in self.available_tools.items():
            description = f"• {tool_name}: {tool_info['description']}"
            if tool_info.get('tags'):
                description += f" (Tags: {', '.join(tool_info['tags'])})"
            tool_descriptions.append(description)
        
        return "\n".join(tool_descriptions)
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get dictionary of available MCP tools"""
        return self.available_tools.copy()
    
    def get_tools_by_tag(self, tag: str) -> List[str]:
        """Get list of tool names that have a specific tag"""
        return [
            tool_name for tool_name, tool_info 
            in self.available_tools.items()
            if tag in tool_info.get('tags', [])
        ]

class StepAgent(MCPAgent):
    """
    Base class for step-specific agents (Sense, Think, Act, Reflect)
    """
    
    def __init__(self, 
                 step_name: str,
                 mcp_url: str = "http://127.0.0.1:8001/mcp",
                 openai_api_key: str = None,
                 model: str = "o3-mini"):
        """
        Initialize step agent
        
        Args:
            step_name: Name of the step (e.g., "SENSE", "THINK", "ACT", "REFLECT")
            mcp_url: MCP server URL
            openai_api_key: OpenAI API key
            model: OpenAI model to use
        """
        super().__init__(mcp_url, openai_api_key, model)
        self.step_name = step_name
        self.step_logger = logging.getLogger(f"smart_agent.{step_name.lower()}")
    
    async def execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this step - to be implemented by subclasses
        
        Args:
            context: Context from previous steps
            
        Returns:
            Result of this step
        """
        raise NotImplementedError("Subclasses must implement execute_step")
    
    def log_step_start(self):
        """Log the start of this step"""
        icon_map = {
            "SENSE": "🔍",
            "THINK": "🧠", 
            "ACT": "⚡",
            "REFLECT": "🤔"
        }
        icon = icon_map.get(self.step_name, "🔄")
        self.step_logger.info(f"{icon} {self.step_name}: Starting...")
    
    def log_step_complete(self, summary: str = ""):
        """Log the completion of this step"""
        self.step_logger.info(f"✅ {self.step_name}: Complete. {summary}")

if __name__ == "__main__":
    import os
    
    # Example usage
    async def test_agent():
        agent = MCPAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        await agent.initialize()
        
        # Let AI decide how to get portfolio information
        result = await agent.ai_decide_and_execute(
            "Get my current portfolio summary including positions and market value"
        )
        
        print("AI Decision Result:")
        print(json.dumps(result, indent=2, default=str))
    
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_agent())
    else:
        print("Set OPENAI_API_KEY to test the agent")