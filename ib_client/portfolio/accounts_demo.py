#!/usr/bin/env python3
"""
Accounts Demo - Interactive demonstration of IB Client Accounts functionality

This demo shows how to use the accounts methods to retrieve account information.
Run this script to see examples of different account operations in action.
"""

import asyncio
import logging
from typing import List, Dict, Any
import json

from .accounts import AccountsAdapter, Account

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AccountsDemo:
    """Demo class to showcase accounts functionality"""
    
    def __init__(self):
        self.accounts_adapter = AccountsAdapter()
    
    def print_accounts(self, accounts: List[Account], title: str):
        """Print accounts in a formatted table"""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
        
        if not accounts:
            print("No accounts found.")
            return
        
        # Print header
        print(f"{'Account ID':<12} {'Type':<15} {'Description':<30} {'Covestor':<8}")
        print(f"{'-'*12} {'-'*15} {'-'*30} {'-'*8}")
        
        # Print accounts
        for account in accounts:
            account_id = account.id[:12] if account.id else "N/A"
            account_type = account.type[:15] if account.type else "N/A"
            desc = (account.desc or "N/A")[:30]
            covestor = "Yes" if account.covestor else "No"
            
            print(f"{account_id:<12} {account_type:<15} {desc:<30} {covestor:<8}")
        
        print(f"\nTotal accounts: {len(accounts)}")
    
    def print_account_summary(self, summary: Dict[str, Any], account_id: str):
        """Print account summary in a formatted way"""
        print(f"\n{'='*80}")
        print(f"ACCOUNT SUMMARY - {account_id}")
        print(f"{'='*80}")
        
        if not summary:
            print("No summary data available.")
            return
        
        # Pretty print the summary as JSON
        try:
            print(json.dumps(summary, indent=2, default=str))
        except Exception as e:
            print(f"Error formatting summary: {e}")
            print(f"Raw summary: {summary}")
    
    async def demo_get_accounts(self):
        """Demo: Get list of available accounts"""
        print("\n💼 Getting Available Accounts...")
        
        try:
            accounts = await self.accounts_adapter.get_accounts()
            self.print_accounts(accounts, "📋 AVAILABLE ACCOUNTS")
            
            if accounts:
                print("✅ Accounts retrieved successfully!")
                return accounts
            else:
                print("⚠️  No accounts found")
                return []
            
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
            logger.error(f"Get accounts error: {e}")
            return []
    
    async def demo_account_summaries(self, accounts: List[Account]):
        """Demo: Get account summaries for all accounts"""
        print("\n📊 Getting Account Summaries...")
        
        if not accounts:
            print("⚠️  No accounts available for summary retrieval")
            return
        
        for account in accounts:
            try:
                print(f"\n🔍 Getting summary for account: {account.id}")
                summary = await self.accounts_adapter.get_account_summary(account.id)
                self.print_account_summary(summary, account.id)
                
                # Brief pause between requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error getting summary for account {account.id}: {e}")
                logger.error(f"Account summary error for {account.id}: {e}")
                continue
    
    async def demo_account_types_analysis(self, accounts: List[Account]):
        """Demo: Analyze account types and characteristics"""
        print("\n📈 Account Types Analysis...")
        
        if not accounts:
            print("⚠️  No accounts available for analysis")
            return
        
        # Count account types
        type_counts = {}
        covestor_count = 0
        
        for account in accounts:
            account_type = account.type or "UNKNOWN"
            type_counts[account_type] = type_counts.get(account_type, 0) + 1
            
            if account.covestor:
                covestor_count += 1
        
        print(f"\n📊 Account Type Distribution:")
        print(f"{'Type':<20} {'Count':<8}")
        print(f"{'-'*20} {'-'*8}")
        
        for account_type, count in sorted(type_counts.items()):
            print(f"{account_type:<20} {count:<8}")
        
        print(f"\n🏆 Covestor Accounts: {covestor_count} out of {len(accounts)}")
        
        if covestor_count > 0:
            covestor_percentage = (covestor_count / len(accounts)) * 100
            print(f"📊 Covestor Percentage: {covestor_percentage:.1f}%")
    
    async def demo_single_account_detail(self, accounts: List[Account]):
        """Demo: Focus on detailed information for the first account"""
        print("\n🎯 Single Account Detail Demo...")
        
        if not accounts:
            print("⚠️  No accounts available for detailed analysis")
            return
        
        # Use the first account
        account = accounts[0]
        
        print(f"\n🔍 Detailed Analysis for Account: {account.id}")
        print(f"Type: {account.type}")
        print(f"Description: {account.desc or 'No description'}")
        print(f"Covestor: {'Yes' if account.covestor else 'No'}")
        
        try:
            print(f"\n📊 Getting detailed summary...")
            summary = await self.accounts_adapter.get_account_summary(account.id)
            
            # Extract key information if available
            if isinstance(summary, dict):
                print(f"\n📋 Key Summary Information:")
                
                # Common fields to look for
                key_fields = [
                    "accountId", "account_id", "id",
                    "totalCashValue", "total_cash_value", 
                    "netLiquidation", "net_liquidation",
                    "accountType", "account_type",
                    "currency", "baseCurrency", "base_currency"
                ]
                
                for field in key_fields:
                    if field in summary:
                        print(f"  {field}: {summary[field]}")
            
            self.print_account_summary(summary, account.id)
            
        except Exception as e:
            print(f"❌ Error getting detailed summary: {e}")
            logger.error(f"Detailed summary error: {e}")
    
    async def run_all_demos(self):
        """Run all accounts demos"""
        print("🎬 Starting Accounts Demo Suite...")
        print("=" * 80)
        
        # First get accounts
        accounts = await self.demo_get_accounts()
        
        if not accounts:
            print("❌ Cannot continue demos without accounts")
            return
        
        demos = [
            ("Account Summaries", lambda: self.demo_account_summaries(accounts)),
            ("Account Types Analysis", lambda: self.demo_account_types_analysis(accounts)),
            ("Single Account Detail", lambda: self.demo_single_account_detail(accounts))
        ]
        
        for demo_name, demo_func in demos:
            try:
                print(f"\n🚀 Running {demo_name}...")
                await demo_func()
                await asyncio.sleep(1)  # Brief pause between demos
                
            except Exception as e:
                print(f"❌ Demo '{demo_name}' failed: {e}")
                logger.error(f"Demo '{demo_name}' failed: {e}")
                continue
        
        print(f"\n🎉 Accounts Demo Suite Complete!")
        print("=" * 80)

async def main():
    """Main demo function"""
    demo = AccountsDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 