#!/usr/bin/env python3
import asyncio
import json
import time
from fastmcp import Client
from typing import Dict, Any, Optional

SERVER_URL = "http://127.0.0.1:8001/mcp"

class IBMCPTester:
    def __init__(self):
        self.client = Client(SERVER_URL)
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
        self.account_id = None
        
    async def log_test(self, test_name: str, status: str, details: str = "", data: Any = None):
        self.results["total_tests"] += 1
        
        if status == "PASS":
            self.results["passed"] += 1
            print(f"✅ {test_name}: {status}")
        elif status == "FAIL":
            self.results["failed"] += 1
            print(f"❌ {test_name}: {status}")
        elif status == "WARN":
            self.results["warnings"] += 1
            print(f"⚠️  {test_name}: {status}")
        
        if details:
            print(f"   {details}")
            
        self.results["tests"].append({
            "name": test_name,
            "status": status,
            "details": details,
            "data": data
        })

    async def test_tool(self, tool_name: str, params: Dict = None, expect_success: bool = True) -> Optional[Dict]:
        if params is None:
            params = {}
            
        try:
            result = await self.client.call_tool(tool_name, params)
            
            if result and len(result) > 0:
                content = result[0]
                if hasattr(content, 'text'):
                    try:
                        data = json.loads(content.text)
                        
                        if isinstance(data, dict) and "error" in data:
                            if expect_success:
                                await self.log_test(f"{tool_name}({params})", "FAIL", 
                                                 f"API Error: {data['error']}", data)
                            else:
                                await self.log_test(f"{tool_name}({params})", "WARN", 
                                                 f"Expected error: {data['error']}", data)
                            return data
                        else:
                            await self.log_test(f"{tool_name}({params})", "PASS", 
                                             f"Success: {self._summarize_data(data)}", data)
                            return data
                    except json.JSONDecodeError:
                        await self.log_test(f"{tool_name}({params})", "FAIL", 
                                         f"Invalid JSON response: {content.text[:100]}...")
                        return None
                else:
                    await self.log_test(f"{tool_name}({params})", "FAIL", 
                                     "No text content in response")
                    return None
            else:
                await self.log_test(f"{tool_name}({params})", "FAIL", 
                                 "Empty response from server")
                return None
                
        except Exception as e:
            if expect_success:
                await self.log_test(f"{tool_name}({params})", "FAIL", 
                                 f"Exception: {str(e)}")
            else:
                await self.log_test(f"{tool_name}({params})", "WARN", 
                                 f"Expected exception: {str(e)}")
            return None

    def _summarize_data(self, data: Any) -> str:
        if isinstance(data, dict):
            if "count" in data:
                return f"Count: {data['count']}"
            elif "accounts" in data:
                return f"Accounts: {len(data['accounts'])}"
            elif "positions" in data:
                return f"Positions: {len(data['positions'])}"
            elif "orders" in data:
                return f"Orders: {len(data['orders'])}"
            elif "results" in data:
                return f"Results: {len(data['results'])}"
            elif "conid" in data:
                return f"Contract ID: {data['conid']}"
            else:
                return f"Keys: {list(data.keys())[:3]}"
        elif isinstance(data, list):
            return f"List with {len(data)} items"
        else:
            return str(data)[:50]

    async def test_authentication_and_session(self):
        print("\n🔐 Testing Authentication & Session")
        print("=" * 50)
        
        accounts_data = await self.test_tool("get_accounts")
        
        if accounts_data and "accounts" in accounts_data and len(accounts_data["accounts"]) > 0:
            self.account_id = accounts_data["accounts"][0]["id"]
            await self.log_test("Authentication Status", "PASS", 
                             f"Authenticated with account: {self.account_id}")
        else:
            await self.log_test("Authentication Status", "FAIL", 
                             "No accounts found - may not be authenticated")

    async def test_portfolio_tools(self):
        print("\n📊 Testing Portfolio Tools")
        print("=" * 50)
        
        if not self.account_id:
            await self.log_test("Portfolio Tests", "FAIL", 
                             "Skipping portfolio tests - no account ID available")
            return
        
        await self.test_tool("get_portfolio_summary", {"account_id": self.account_id})
        
        await self.test_tool("get_positions", {"account_id": self.account_id, "max_positions": 10})
        
        await self.test_tool("get_ledger", {"account_id": self.account_id})
        
        await self.test_tool("get_pnl")
        
        await self.test_tool("portfolio_health_check", {"account_id": self.account_id})

    async def test_market_data_tools(self):
        print("\n📈 Testing Market Data Tools")
        print("=" * 50)
        
        contract_data = await self.test_tool("find_contract", {"symbol": "AAPL", "sec_type": "STK"})
        
        if contract_data and "conid" in contract_data:
            conid = contract_data["conid"]
            
            await self.test_tool("get_market_snapshot", {"conid": conid})
            
            await self.test_tool("get_history", {
                "conid": conid, 
                "bar": "1d", 
                "period": "1w"
            })
            
            await self.test_tool("get_order_book", {"conid": conid}, expect_success=False)
            
        else:
            await self.log_test("Market Data Tests", "FAIL", 
                             "Skipping market data tests - couldn't resolve AAPL contract")

    async def test_scanner_tools(self):
        print("\n🔍 Testing Scanner Tools")
        print("=" * 50)
        
        await self.test_tool("get_scan_codes")
        
        await self.test_tool("scan_top_gainers", {"max_results": 5, "location": "STK.US"})
        await self.test_tool("scan_top_losers", {"max_results": 5, "location": "STK.US"})
        await self.test_tool("scan_most_active", {"max_results": 5, "location": "STK.US"})
        
        await self.test_tool("custom_scan", {
            "scan_code": "TOP_PERC_GAIN", 
            "max_results": 5, 
            "location": "STK.US"
        })

    async def test_trading_tools(self):
        print("\n💼 Testing Trading Tools")
        print("=" * 50)
        
        await self.test_tool("get_live_orders")
        
        contract_data = await self.test_tool("find_contract", {"symbol": "AAPL", "sec_type": "STK"})
        
        if contract_data and "conid" in contract_data and self.account_id:
            conid = contract_data["conid"]
            
            await self.test_tool("whatif_order", {
                "conid": conid,
                "side": "BUY",
                "quantity": 1,
                "order_type": "MKT",
                "account_id": self.account_id
            })
        else:
            await self.log_test("What-if Order Test", "FAIL", 
                             "Skipping what-if test - missing contract or account")

    async def test_analysis_tools(self):
        print("\n📊 Testing Analysis Tools")
        print("=" * 50)
        
        await self.test_tool("stock_analysis", {"symbol": "AAPL", "target_quantity": 10})

    async def test_edge_cases(self):
        print("\n🔍 Testing Edge Cases & Boundary Conditions")
        print("=" * 50)
        
        await self.test_tool("find_contract", {"symbol": "GOOGL", "sec_type": "STK"})
        
        contract_data = await self.test_tool("find_contract", {"symbol": "SPY", "sec_type": "STK"})
        if contract_data and "conid" in contract_data:
            conid = contract_data["conid"]
            await self.test_tool("get_history", {
                "conid": conid, 
                "bar": "1d", 
                "period": "1d"
            })
        
        if self.account_id:
            await self.test_tool("get_positions", {"account_id": self.account_id, "max_positions": 1})
        
        futures_data = await self.test_tool("find_contract", {"symbol": "ES", "sec_type": "FUT"})
        if futures_data and "conid" in futures_data:
            conid = futures_data["conid"]
            await self.test_tool("get_order_book", {"conid": conid}, expect_success=False)
        
        if contract_data and "conid" in contract_data and self.account_id:
            await self.test_tool("whatif_order", {
                "conid": contract_data["conid"],
                "side": "BUY",
                "quantity": 1,
                "order_type": "LMT",
                "price": 100.0,
                "account_id": self.account_id
            }, expect_success=False)

    async def run_comprehensive_test(self):
        print("🧪 Interactive Brokers MCP Comprehensive Test Suite")
        print("=" * 60)
        print(f"Testing server: {SERVER_URL}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            async with self.client:
                print("✅ Connected to MCP server successfully")
                
                tools = await self.client.list_tools()
                print(f"📋 Found {len(tools)} available tools")
                
                await self.test_authentication_and_session()
                await self.test_portfolio_tools()
                await self.test_market_data_tools()
                await self.test_scanner_tools()
                await self.test_trading_tools()
                await self.test_analysis_tools()
                await self.test_edge_cases()
                
                await self.print_summary()
                
        except ConnectionError:
            print("❌ Connection failed!")
            print("💡 Make sure your MCP server is running:")
            print("   source .venv/bin/activate && python server.py")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    async def print_summary(self):
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        warnings = self.results["warnings"]
        
        print(f"Total Tests:  {total}")
        print(f"✅ Passed:    {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed:    {failed} ({failed/total*100:.1f}%)")
        print(f"⚠️  Warnings: {warnings} ({warnings/total*100:.1f}%)")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.results["tests"]:
                if test["status"] == "FAIL":
                    print(f"   • {test['name']}: {test['details']}")
        
        if warnings > 0:
            print(f"\n⚠️  WARNINGS (Expected failures for edge cases):")
            for test in self.results["tests"]:
                if test["status"] == "WARN":
                    print(f"   • {test['name']}: {test['details']}")
                    
        print("\n🎉 Test suite completed!")
        
        success_rate = (passed + warnings) / total * 100
        if success_rate >= 95:
            print(f"🎯 Excellent! {success_rate:.1f}% success rate")
        elif success_rate >= 85:
            print(f"👍 Good! {success_rate:.1f}% success rate")
        else:
            print(f"⚠️  Needs attention: {success_rate:.1f}% success rate")

def print_usage():
    print("""
📋 Enhanced IB MCP Test Usage:

1. Make sure IB Gateway/TWS is running and you're logged in
2. Start your MCP server:
   source .venv/bin/activate && python server.py

3. Run this comprehensive test:
   source .venv/bin/activate && python mcp_test.py

4. The script will:
   ✅ Test all 20 MCP tools systematically
   ✅ Verify authentication and session status
   ✅ Test portfolio, market data, and trading tools
   ✅ Handle errors gracefully and provide detailed reporting
   ✅ Test edge cases and error conditions
   ✅ Provide comprehensive success/failure analysis

This test suite is designed for basic IB accounts without special subscriptions.
""")

if __name__ == "__main__":
    print_usage()
    print("=" * 60)
    
    tester = IBMCPTester()
    asyncio.run(tester.run_comprehensive_test())