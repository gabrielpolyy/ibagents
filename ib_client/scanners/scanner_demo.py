#!/usr/bin/env python3
"""
Scanner Demo - Interactive demonstration of IB Client Scanner functionality

This demo shows how to use various scanner methods to find market opportunities.
Run this script to see examples of different scan types in action.
"""

import asyncio
import logging
from typing import List
from decimal import Decimal

from .scanner import ScannerAdapter, ScanResult, ScanRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScannerDemo:
    """Demo class to showcase scanner functionality"""
    
    def __init__(self):
        self.scanner = ScannerAdapter()
    
    def print_scan_results(self, results: List[ScanResult], title: str):
        """Print scan results in a formatted table"""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
        
        if not results:
            print("No results found.")
            return
        
        # Print header
        print(f"{'Symbol':<8} {'Company':<30} {'Exchange':<8} {'SecType':<8}")
        print(f"{'-'*8} {'-'*30} {'-'*8} {'-'*8}")
        
        # Print results
        for result in results[:10]:  # Show top 10 results
            symbol = result.symbol or "N/A"
            desc = (result.contractDesc or "N/A")[:30]
            exchange = (result.exchange or "N/A")[:8]
            sec_type = (result.secType or "N/A")[:8]
            
            print(f"{symbol:<8} {desc:<30} {exchange:<8} {sec_type:<8}")
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more results")
        
        print(f"\nTotal results: {len(results)}")
    
    async def demo_scanner_params(self):
        """Demo: Get scanner parameters and available options"""
        print("\n🔍 Getting Scanner Parameters...")
        
        try:
            params = await self.scanner.get_scanner_params()
            
            print("✅ Scanner parameters retrieved successfully!")
            
            # Show available scan types
            if isinstance(params, dict) and "scan_type_list" in params:
                scan_types = params["scan_type_list"]
                print(f"\n📊 Available Scan Types ({len(scan_types)}):")
                for i, scan_type in enumerate(scan_types[:10]):  # Show first 10
                    if isinstance(scan_type, dict):
                        name = scan_type.get("display_name", "Unknown")
                        code = scan_type.get("code", "Unknown") 
                        print(f"  {i+1}. {name} ({code})")
                if len(scan_types) > 10:
                    print(f"  ... and {len(scan_types) - 10} more scan types")
            
            # Show available locations
            if isinstance(params, dict) and "location_tree" in params:
                locations = []
                for location_group in params["location_tree"]:
                    if isinstance(location_group, dict) and "locations" in location_group:
                        for location in location_group["locations"]:
                            if isinstance(location, dict) and "type" in location:
                                locations.append(location)
                
                print(f"\n🌍 Available Locations ({len(locations)}):")
                for i, location in enumerate(locations[:10]):  # Show first 10
                    name = location.get("display_name", "Unknown")
                    type_code = location.get("type", "Unknown")
                    print(f"  {i+1}. {name} ({type_code})")
                if len(locations) > 10:
                    print(f"  ... and {len(locations) - 10} more locations")
                    
        except Exception as e:
            print(f"❌ Error getting scanner parameters: {e}")
            logger.error(f"Scanner params error: {e}")
    
    async def demo_top_gainers(self):
        """Demo: Get top percentage gainers"""
        print("\n📈 Top Percentage Gainers Demo")
        
        try:
            results = await self.scanner.top_gainers(max_results=20)
            self.print_scan_results(results, "🚀 TOP PERCENTAGE GAINERS")
            
        except Exception as e:
            print(f"❌ Error getting top gainers: {e}")
            logger.error(f"Top gainers error: {e}")
    
    async def demo_top_losers(self):
        """Demo: Get top percentage losers"""
        print("\n📉 Top Percentage Losers Demo")
        
        try:
            results = await self.scanner.top_losers(max_results=20)
            self.print_scan_results(results, "📉 TOP PERCENTAGE LOSERS")
            
        except Exception as e:
            print(f"❌ Error getting top losers: {e}")
            logger.error(f"Top losers error: {e}")
    
    async def demo_most_active(self):
        """Demo: Get most active stocks"""
        print("\n📊 Most Active Stocks Demo")
        
        try:
            results = await self.scanner.most_active(max_results=20)
            self.print_scan_results(results, "🔥 MOST ACTIVE STOCKS")
            
        except Exception as e:
            print(f"❌ Error getting most active: {e}")
            logger.error(f"Most active error: {e}")
    
    async def demo_most_active_usd(self):
        """Demo: Get most active stocks by USD volume"""
        print("\n💰 Most Active USD Volume Demo")
        
        try:
            results = await self.scanner.most_active_usd(max_results=20)
            self.print_scan_results(results, "💰 MOST ACTIVE BY USD VOLUME")
            
        except Exception as e:
            print(f"❌ Error getting most active USD: {e}")
            logger.error(f"Most active USD error: {e}")
    
    async def demo_custom_scan_with_filters(self):
        """Demo: Custom scan with price and volume filters"""
        print("\n🎯 Custom Scan with Filters Demo")
        
        try:
            # Example filters: price above $5 and volume above 500k
            filters = [
                {
                    "code": "priceAbove",
                    "value": 5.0
                },
                {
                    "code": "volumeAbove", 
                    "value": 500000
                }
            ]
            
            results = await self.scanner.custom_scan(
                scan_type="MOST_ACTIVE_USD",
                filters=filters,
                max_results=15
            )
            self.print_scan_results(results, "🎯 MOST ACTIVE USD (Price > $5, Volume > 500K)")
            
        except Exception as e:
            print(f"❌ Error running custom scan: {e}")
            logger.error(f"Custom scan error: {e}")
    
    async def demo_different_locations(self):
        """Demo: Scan different market locations"""
        print("\n🌍 Different Market Locations Demo")
        
        locations_to_try = [
            "STK.US.MAJOR",    # US Major Markets
            "STK.NASDAQ",      # NASDAQ
            "STK.NYSE"         # NYSE
        ]
        
        for location in locations_to_try:
            try:
                print(f"\n🔍 Scanning {location}...")
                results = await self.scanner.top_gainers(max_results=5, location=location)
                self.print_scan_results(results, f"📈 TOP GAINERS - {location}")
                
            except Exception as e:
                print(f"❌ Error scanning {location}: {e}")
                logger.error(f"Location scan error for {location}: {e}")
    
    async def demo_available_scan_codes(self):
        """Demo: Show available scan codes"""
        print("\n📋 Available Scan Codes Demo")
        
        try:
            scan_codes = await self.scanner.get_available_scan_codes()
            
            if scan_codes:
                print(f"✅ Found {len(scan_codes)} available scan codes:")
                for i, code in enumerate(scan_codes[:20]):  # Show first 20
                    print(f"  {i+1}. {code}")
                if len(scan_codes) > 20:
                    print(f"  ... and {len(scan_codes) - 20} more scan codes")
            else:
                print("⚠️  No scan codes found (may indicate API issue)")
                
        except Exception as e:
            print(f"❌ Error getting scan codes: {e}")
            logger.error(f"Scan codes error: {e}")
    
    async def demo_available_locations(self):
        """Demo: Show available scan locations"""
        print("\n🗺️  Available Locations Demo")
        
        try:
            locations = await self.scanner.get_available_locations()
            
            if locations:
                print(f"✅ Found {len(locations)} available locations:")
                for i, location in enumerate(locations[:15]):  # Show first 15
                    print(f"  {i+1}. {location}")
                if len(locations) > 15:
                    print(f"  ... and {len(locations) - 15} more locations")
            else:
                print("⚠️  No locations found (may indicate API issue)")
                
        except Exception as e:
            print(f"❌ Error getting locations: {e}")
            logger.error(f"Locations error: {e}")
    
    async def run_all_demos(self):
        """Run all scanner demos"""
        print("🎬 Starting Scanner Demo Suite...")
        print("=" * 80)
        
        demos = [
            ("Scanner Parameters", self.demo_scanner_params),
            ("Available Scan Codes", self.demo_available_scan_codes), 
            ("Available Locations", self.demo_available_locations),
            ("Top Gainers", self.demo_top_gainers),
            ("Top Losers", self.demo_top_losers),
            ("Most Active", self.demo_most_active),
            ("Most Active USD", self.demo_most_active_usd),
            ("Custom Scan with Filters", self.demo_custom_scan_with_filters),
            ("Different Locations", self.demo_different_locations)
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
        
        print(f"\n🎉 Scanner Demo Suite Complete!")
        print("=" * 80)

async def main():
    """Main demo function"""
    demo = ScannerDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 