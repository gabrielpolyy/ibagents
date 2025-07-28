#!/usr/bin/env python3
"""
PnL Demo - Interactive demonstration of IB Client P&L functionality

This demo shows how to use the P&L methods to retrieve profit/loss information.
Run this script to see examples of different P&L operations in action.
"""

import asyncio
import logging
from typing import List, Dict, Any
import json
from decimal import Decimal

from .pnl import PnLAdapter, PnLRow, PnLByInstrument
from .accounts import AccountsAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PnLDemo:
    """Demo class to showcase P&L functionality"""
    
    def __init__(self):
        self.pnl_adapter = PnLAdapter()
        self.accounts_adapter = AccountsAdapter()
    
    def format_currency(self, value: Decimal) -> str:
        """Format currency values for display"""
        if value is None:
            return "N/A"
        try:
            return f"${value:,.2f}"
        except:
            return str(value)
    
    def print_pnl_rows(self, pnl_rows: List[PnLRow], title: str):
        """Print P&L rows in a formatted table"""
        print(f"\n{'='*100}")
        print(f"{title}")
        print(f"{'='*100}")
        
        if not pnl_rows:
            print("No P&L data found.")
            return
        
        # Print header
        print(f"{'Account ID':<12} {'Model':<10} {'Daily P&L':<12} {'Unrealized P&L':<15} {'Net Liq':<12} {'Market Value':<12}")
        print(f"{'-'*12} {'-'*10} {'-'*12} {'-'*15} {'-'*12} {'-'*12}")
        
        # Print P&L data
        total_dpl = Decimal(0)
        total_upl = Decimal(0)
        
        for pnl in pnl_rows:
            account_id = pnl.acctId[:12] if pnl.acctId else "N/A"
            model = (pnl.model or "N/A")[:10]
            dpl = self.format_currency(pnl.dpl)[:12]
            upl = self.format_currency(pnl.upl)[:15]
            nl = self.format_currency(pnl.nl)[:12]
            mv = self.format_currency(pnl.mv)[:12]
            
            print(f"{account_id:<12} {model:<10} {dpl:<12} {upl:<15} {nl:<12} {mv:<12}")
            
            # Add to totals
            if pnl.dpl:
                total_dpl += pnl.dpl
            if pnl.upl:
                total_upl += pnl.upl
        
        print(f"{'-'*12} {'-'*10} {'-'*12} {'-'*15} {'-'*12} {'-'*12}")
        print(f"{'TOTALS':<12} {'':<10} {self.format_currency(total_dpl):<12} {self.format_currency(total_upl):<15}")
        
        print(f"\nTotal P&L entries: {len(pnl_rows)}")
    
    def print_position_pnl(self, positions: List[PnLByInstrument], title: str):
        """Print position P&L in a formatted table"""
        print(f"\n{'='*120}")
        print(f"{title}")
        print(f"{'='*120}")
        
        if not positions:
            print("No position P&L data found.")
            return
        
        # Print header
        print(f"{'Contract':<25} {'Position':<12} {'Daily P&L':<12} {'Unrealized':<12} {'Realized':<12} {'Value':<12}")
        print(f"{'-'*25} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
        
        # Print position data
        total_daily = Decimal(0)
        total_unrealized = Decimal(0)
        total_realized = Decimal(0)
        
        for pos in positions:
            contract = (pos.contractDesc or f"ConID:{pos.conid}")[:25]
            position = f"{pos.position:,.0f}" if pos.position else "0"
            daily = self.format_currency(pos.dailyPnL)[:12]
            unrealized = self.format_currency(pos.unrealizedPnL)[:12]
            realized = self.format_currency(pos.realizedPnL)[:12]
            value = self.format_currency(pos.value)[:12]
            
            print(f"{contract:<25} {position:<12} {daily:<12} {unrealized:<12} {realized:<12} {value:<12}")
            
            # Add to totals
            if pos.dailyPnL:
                total_daily += pos.dailyPnL
            if pos.unrealizedPnL:
                total_unrealized += pos.unrealizedPnL
            if pos.realizedPnL:
                total_realized += pos.realizedPnL
        
        print(f"{'-'*25} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
        print(f"{'TOTALS':<25} {'':<12} {self.format_currency(total_daily):<12} {self.format_currency(total_unrealized):<12} {self.format_currency(total_realized):<12}")
        
        print(f"\nTotal positions: {len(positions)}")
    
    def print_pnl_summary(self, summary: Dict[str, Any], account_id: str):
        """Print P&L summary in a formatted way"""
        print(f"\n{'='*80}")
        print(f"P&L SUMMARY - {account_id}")
        print(f"{'='*80}")
        
        if not summary:
            print("No P&L summary data available.")
            return
        
        # Pretty print the summary as JSON
        try:
            print(json.dumps(summary, indent=2, default=str))
        except Exception as e:
            print(f"Error formatting summary: {e}")
            print(f"Raw summary: {summary}")
    
    async def demo_partitioned_pnl(self):
        """Demo: Get partitioned P&L data"""
        print("\n💰 Getting Partitioned P&L Data...")
        
        try:
            pnl_rows = await self.pnl_adapter.get_partitioned_pnl()
            self.print_pnl_rows(pnl_rows, "📊 PARTITIONED P&L DATA")
            
            if pnl_rows:
                print("✅ Partitioned P&L retrieved successfully!")
                return pnl_rows
            else:
                print("⚠️  No partitioned P&L data found")
                return []
            
        except Exception as e:
            print(f"❌ Error getting partitioned P&L: {e}")
            logger.error(f"Partitioned P&L error: {e}")
            return []
    
    async def demo_position_pnl_for_accounts(self):
        """Demo: Get P&L by position for all accounts"""
        print("\n🎯 Getting P&L by Position for All Accounts...")
        
        try:
            # First get available accounts
            accounts = await self.accounts_adapter.get_accounts()
            
            if not accounts:
                print("⚠️  No accounts available for position P&L retrieval")
                return
            
            all_positions = []
            
            for account in accounts:
                try:
                    print(f"\n🔍 Getting position P&L for account: {account.id}")
                    positions = await self.pnl_adapter.get_pnl_by_position(account.id)
                    
                    if positions:
                        self.print_position_pnl(positions, f"📈 POSITION P&L - {account.id}")
                        all_positions.extend(positions)
                    else:
                        print(f"⚠️  No positions found for account {account.id}")
                    
                    # Brief pause between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Error getting position P&L for account {account.id}: {e}")
                    logger.error(f"Position P&L error for {account.id}: {e}")
                    continue
            
            return all_positions
            
        except Exception as e:
            print(f"❌ Error getting position P&L: {e}")
            logger.error(f"Position P&L error: {e}")
            return []
    
    async def demo_account_pnl_summaries(self):
        """Demo: Get P&L summaries for all accounts"""
        print("\n📋 Getting P&L Summaries for All Accounts...")
        
        try:
            # First get available accounts
            accounts = await self.accounts_adapter.get_accounts()
            
            if not accounts:
                print("⚠️  No accounts available for P&L summary retrieval")
                return
            
            for account in accounts:
                try:
                    print(f"\n🔍 Getting P&L summary for account: {account.id}")
                    summary = await self.pnl_adapter.get_account_pnl_summary(account.id)
                    self.print_pnl_summary(summary, account.id)
                    
                    # Brief pause between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Error getting P&L summary for account {account.id}: {e}")
                    logger.error(f"P&L summary error for {account.id}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error getting P&L summaries: {e}")
            logger.error(f"P&L summaries error: {e}")
    
    async def demo_pnl_analysis(self, pnl_rows: List[PnLRow], positions: List[PnLByInstrument]):
        """Demo: Analyze P&L data and provide insights"""
        print("\n📈 P&L Analysis and Insights...")
        
        if not pnl_rows and not positions:
            print("⚠️  No P&L data available for analysis")
            return
        
        print(f"\n📊 P&L Analysis Summary:")
        print(f"{'='*50}")
        
        # Analyze partitioned P&L
        if pnl_rows:
            total_daily = sum(pnl.dpl for pnl in pnl_rows if pnl.dpl)
            total_unrealized = sum(pnl.upl for pnl in pnl_rows if pnl.upl)
            total_net_liq = sum(pnl.nl for pnl in pnl_rows if pnl.nl)
            
            print(f"💼 Portfolio Overview:")
            print(f"  Total Daily P&L: {self.format_currency(total_daily)}")
            print(f"  Total Unrealized P&L: {self.format_currency(total_unrealized)}")
            print(f"  Total Net Liquidation: {self.format_currency(total_net_liq)}")
            
            # Performance indicators
            if total_net_liq and total_net_liq != 0:
                daily_return_pct = (total_daily / total_net_liq) * 100
                unrealized_return_pct = (total_unrealized / total_net_liq) * 100
                print(f"  Daily Return: {daily_return_pct:.2f}%")
                print(f"  Unrealized Return: {unrealized_return_pct:.2f}%")
        
        # Analyze position P&L
        if positions:
            profitable_positions = [pos for pos in positions if pos.unrealizedPnL and pos.unrealizedPnL > 0]
            losing_positions = [pos for pos in positions if pos.unrealizedPnL and pos.unrealizedPnL < 0]
            
            print(f"\n🎯 Position Analysis:")
            print(f"  Total Positions: {len(positions)}")
            print(f"  Profitable Positions: {len(profitable_positions)}")
            print(f"  Losing Positions: {len(losing_positions)}")
            
            if positions:
                win_rate = (len(profitable_positions) / len(positions)) * 100
                print(f"  Win Rate: {win_rate:.1f}%")
            
            # Top winners and losers
            if profitable_positions:
                top_winner = max(profitable_positions, key=lambda x: x.unrealizedPnL or Decimal(0))
                print(f"  Top Winner: {top_winner.contractDesc} ({self.format_currency(top_winner.unrealizedPnL)})")
            
            if losing_positions:
                top_loser = min(losing_positions, key=lambda x: x.unrealizedPnL or Decimal(0))
                print(f"  Top Loser: {top_loser.contractDesc} ({self.format_currency(top_loser.unrealizedPnL)})")
    
    async def demo_single_account_deep_dive(self):
        """Demo: Deep dive into P&L for a single account"""
        print("\n🔬 Single Account P&L Deep Dive...")
        
        try:
            # Get the first available account
            accounts = await self.accounts_adapter.get_accounts()
            
            if not accounts:
                print("⚠️  No accounts available for deep dive")
                return
            
            account = accounts[0]
            print(f"\n🎯 Deep dive for account: {account.id}")
            
            # Get all P&L data for this account
            summary = await self.pnl_adapter.get_account_pnl_summary(account.id)
            positions = await self.pnl_adapter.get_pnl_by_position(account.id)
            
            print(f"\n📊 Complete P&L Picture for {account.id}:")
            
            if summary:
                self.print_pnl_summary(summary, account.id)
            
            if positions:
                self.print_position_pnl(positions, f"📈 ALL POSITIONS - {account.id}")
                
                # Additional analysis for this account
                total_value = sum(pos.value for pos in positions if pos.value)
                total_unrealized = sum(pos.unrealizedPnL for pos in positions if pos.unrealizedPnL)
                
                print(f"\n💡 Account Insights:")
                print(f"  Portfolio Value: {self.format_currency(total_value)}")
                print(f"  Total Unrealized P&L: {self.format_currency(total_unrealized)}")
                
                if total_value and total_value != 0:
                    unrealized_pct = (total_unrealized / total_value) * 100
                    print(f"  Unrealized Return: {unrealized_pct:.2f}%")
            
        except Exception as e:
            print(f"❌ Error in single account deep dive: {e}")
            logger.error(f"Deep dive error: {e}")
    
    async def run_all_demos(self):
        """Run all P&L demos"""
        print("🎬 Starting P&L Demo Suite...")
        print("=" * 80)
        
        # First get partitioned P&L
        pnl_rows = await self.demo_partitioned_pnl()
        
        demos = [
            ("Position P&L for All Accounts", self.demo_position_pnl_for_accounts),
            ("Account P&L Summaries", self.demo_account_pnl_summaries),
            ("Single Account Deep Dive", self.demo_single_account_deep_dive)
        ]
        
        positions = []
        
        for demo_name, demo_func in demos:
            try:
                print(f"\n🚀 Running {demo_name}...")
                result = await demo_func()
                if demo_name == "Position P&L for All Accounts" and result:
                    positions = result
                await asyncio.sleep(1)  # Brief pause between demos
                
            except Exception as e:
                print(f"❌ Demo '{demo_name}' failed: {e}")
                logger.error(f"Demo '{demo_name}' failed: {e}")
                continue
        
        # Run analysis if we have data
        if pnl_rows or positions:
            try:
                print(f"\n🚀 Running P&L Analysis...")
                await self.demo_pnl_analysis(pnl_rows, positions)
            except Exception as e:
                print(f"❌ P&L Analysis failed: {e}")
                logger.error(f"P&L Analysis failed: {e}")
        
        print(f"\n🎉 P&L Demo Suite Complete!")
        print("=" * 80)

async def main():
    """Main demo function"""
    demo = PnLDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 