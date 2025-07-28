#!/usr/bin/env python3
"""
Market Data Demo - Interactive demonstration of IB Client Market Data functionality

This demo shows how to use various market data methods to get real-time and historical data.
Run this script to see examples of different market data features in action.

NOTE: This demo focuses on core market data features that work without requiring subscriptions:
- Real-time snapshots (basic market data)
- Historical bar data (OHLC + volume)
- Advanced snapshot field requests
"""

import asyncio
import logging
from typing import List, Dict
from decimal import Decimal
import time

from .market_data import MarketDataAdapter, Snapshot, Bar

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataDemo:
    """Demo class to showcase market data functionality"""
    
    def __init__(self):
        self.market_data = MarketDataAdapter()
        
        # Popular stock conids for demo purposes
        # These are real IBKR contract IDs for major stocks
        self.demo_stocks = {
            "AAPL": 265598,     # Apple Inc
            "TSLA": 76792991,   # Tesla Inc
            "NVDA": 4815747,    # NVIDIA Corp
            "MSFT": 272093,     # Microsoft Corp
            "GOOGL": 208813720, # Alphabet Inc
            "AMZN": 3691937,    # Amazon.com Inc
            "META": 107113386,  # Meta Platforms Inc
            "SPY": 756733,      # SPDR S&P 500 ETF
            "QQQ": 320227571,   # Invesco QQQ Trust
            "HOOD": 504546674   # Robinhood Markets Inc
        }
    
    def print_snapshot_results(self, snapshots: Dict[str, Snapshot]):
        """Print snapshot results in a nice table format"""
        print("\n" + "="*100)
        print(f"{'Symbol':<8} {'Last':<10} {'Bid':<10} {'Ask':<10} {'Volume':<12} {'Change':<10} {'Change%':<10}")
        print("="*100)
        
        for symbol, snapshot in snapshots.items():
            last = f"${snapshot.last_price:.2f}" if snapshot.last_price else "N/A"
            bid = f"${snapshot.bid:.2f}" if snapshot.bid else "N/A"
            ask = f"${snapshot.ask:.2f}" if snapshot.ask else "N/A"
            volume = f"{snapshot.volume:,}" if snapshot.volume else "N/A"
            change = f"${snapshot.change:.2f}" if snapshot.change else "N/A"
            change_pct = f"{snapshot.change_percent:.2f}%" if snapshot.change_percent else "N/A"
            
            print(f"{symbol:<8} {last:<10} {bid:<10} {ask:<10} {volume:<12} {change:<10} {change_pct:<10}")
        
        print("="*100)
    
    def print_historical_results(self, symbol: str, bars: List[Bar], timeframe: str):
        """Print historical data results"""
        print(f"\n📊 Historical Data for {symbol} ({timeframe})")
        print("="*80)
        print(f"{'Time':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
        print("="*80)
        
        for bar in bars[-10:]:  # Show last 10 bars
            # Convert milliseconds to seconds for time.localtime()
            timestamp = time.strftime('%Y-%m-%d', time.localtime(bar.t / 1000))
            open_price = f"${bar.o:.2f}" if bar.o else "N/A"
            high_price = f"${bar.h:.2f}" if bar.h else "N/A"
            low_price = f"${bar.l:.2f}" if bar.l else "N/A"
            close_price = f"${bar.c:.2f}" if bar.c else "N/A"
            volume = f"{bar.v:.2f}" if bar.v else "N/A"
            
            print(f"{timestamp:<12} {open_price:<10} {high_price:<10} {low_price:<10} {close_price:<10} {volume:<12}")
        
        if len(bars) > 10:
            print(f"... and {len(bars) - 10} more bars")
        print("="*80)
    
    async def demo_snapshots(self):
        """Demo real-time market data snapshots"""
        print("\n🚀 Running Market Data Snapshots...")
        print("📊 Real-time Market Data Snapshots Demo")
        
        snapshots = {}
        
        # Get snapshots for top 5 stocks
        demo_symbols = list(self.demo_stocks.items())[:5]
        
        for symbol, conid in demo_symbols:
            try:
                snapshot = await self.market_data.snapshot(conid)
                snapshots[symbol] = snapshot
                print(f"✅ Got snapshot for {symbol} (conid: {conid})")
            except Exception as e:
                print(f"❌ Failed to get snapshot for {symbol}: {e}")
        
        if snapshots:
            self.print_snapshot_results(snapshots)
            print(f"\nTotal snapshots retrieved: {len(snapshots)}")
    
    async def demo_historical_data(self):
        """Demo historical market data"""
        print("\n🚀 Running Historical Data...")
        print("📈 Historical Market Data Demo")
        
        # Demo different timeframes for AAPL
        symbol = "AAPL"
        conid = self.demo_stocks[symbol]
        
        timeframes = [
            ("1d", "1m"),    # Daily bars for 1 month
            ("1h", "1w"),    # Hourly bars for 1 week
            ("5min", "1d")   # 5-minute bars for 1 day
        ]
        
        for bar_size, period in timeframes:
            try:
                print(f"\n🔍 Getting {bar_size} bars for {symbol} over {period}...")
                bars = await self.market_data.history(conid, bar=bar_size, period=period)
                
                if bars:
                    self.print_historical_results(symbol, bars, f"{bar_size} bars, {period}")
                    print(f"✅ Retrieved {len(bars)} bars")
                else:
                    print(f"❌ No historical data available for {symbol}")
                    
            except Exception as e:
                print(f"❌ Failed to get historical data for {symbol} ({bar_size}): {e}")
    
    async def demo_advanced_snapshots(self):
        """Demo advanced snapshot features with specific fields"""
        print("\n🚀 Running Advanced Snapshots...")
        print("🎯 Advanced Snapshot Features Demo")
        
        # Get specific fields for a stock
        symbol = "TSLA"
        conid = self.demo_stocks[symbol]
        
        # Different field combinations
        field_sets = [
            (["31", "84", "86"], "Price Fields (Last, Bid, Ask)"),
            (["87", "82", "83"], "Volume & Change Fields"),
            (["70", "71", "77"], "High, Low, Close Fields")
        ]
        
        for fields, description in field_sets:
            try:
                print(f"\n🔍 Getting {description} for {symbol}...")
                snapshot = await self.market_data.snapshot(conid, fields=fields)
                
                print(f"✅ {symbol} Snapshot ({description}):")
                if snapshot.last_price: print(f"   Last Price: ${snapshot.last_price:.2f}")
                if snapshot.bid: print(f"   Bid: ${snapshot.bid:.2f}")
                if snapshot.ask: print(f"   Ask: ${snapshot.ask:.2f}")
                if snapshot.volume: print(f"   Volume: {snapshot.volume:,}")
                if snapshot.change: print(f"   Change: ${snapshot.change:.2f}")
                if snapshot.change_percent: print(f"   Change%: {snapshot.change_percent:.2f}%")
                if snapshot.high: print(f"   High: ${snapshot.high:.2f}")
                if snapshot.low: print(f"   Low: ${snapshot.low:.2f}")
                if snapshot.close: print(f"   Close: ${snapshot.close:.2f}")
                
            except Exception as e:
                print(f"❌ Failed to get {description} for {symbol}: {e}")
    
    async def demo_market_comparison(self):
        """Demo comparing multiple stocks side by side"""
        print("\n🚀 Running Market Comparison...")
        print("⚖️  Stock Comparison Demo")
        
        # Compare tech giants
        comparison_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        snapshots = {}
        
        print(f"\n📊 Comparing: {', '.join(comparison_stocks)}")
        
        for symbol in comparison_stocks:
            conid = self.demo_stocks[symbol]
            try:
                snapshot = await self.market_data.snapshot(conid)
                snapshots[symbol] = snapshot
            except Exception as e:
                print(f"❌ Failed to get data for {symbol}: {e}")
        
        if snapshots:
            self.print_snapshot_results(snapshots)
            
            # Calculate some basic stats
            prices = [s.last_price for s in snapshots.values() if s.last_price]
            if prices:
                avg_price = sum(prices) / len(prices)
                max_price = max(prices)
                min_price = min(prices)
                
                print(f"\n📈 Comparison Stats:")
                print(f"   Average Price: ${avg_price:.2f}")
                print(f"   Highest Price: ${max_price:.2f}")
                print(f"   Lowest Price: ${min_price:.2f}")
    
    async def run_all_demos(self):
        """Run all market data demos"""
        print("🎬 Starting Market Data Demo Suite...")
        print("="*80)
        
        demos = [
            ("Market Data Snapshots", self.demo_snapshots),
            ("Historical Data", self.demo_historical_data),
            ("Advanced Snapshots", self.demo_advanced_snapshots),
            ("Market Comparison", self.demo_market_comparison)
        ]
        
        for demo_name, demo_func in demos:
            try:
                print(f"\n🚀 Running {demo_name}...")
                await demo_func()
            except Exception as e:
                print(f"❌ {demo_name} failed: {e}")
                logger.exception(f"Demo {demo_name} failed")
        
        print("\n🎉 Market Data Demo Suite Complete!")
        print("="*80)

async def main():
    """Main demo function"""
    demo = MarketDataDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 