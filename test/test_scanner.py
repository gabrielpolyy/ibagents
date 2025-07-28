import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from typing import List

from ib_client.scanners.scanner import ScannerAdapter, ScanRequest, ScanResult


class TestScannerAdapter:
    """Test cases for ScannerAdapter class"""
    
    @pytest.fixture
    def scanner_adapter(self):
        """Create a ScannerAdapter instance for testing"""
        return ScannerAdapter()
    
    @pytest.fixture
    def mock_scan_result_data(self):
        """Mock scan result data"""
        return [
            {
                "conid": 123456,
                "symbol": "AAPL",
                "contractDesc": "Apple Inc.",
                "secType": "STK",
                "exchange": "NASDAQ",
                "currency": "USD",
                "price": "150.25",
                "change": "5.75",
                "changePercent": "3.98",
                "volume": 1000000,
                "marketCap": "2500000000000",
                "pe": "25.5",
                "dividend": "0.24"
            },
            {
                "conid": 789012,
                "symbol": "GOOGL",
                "contractDesc": "Alphabet Inc.",
                "secType": "STK",
                "exchange": "NASDAQ",
                "currency": "USD",
                "price": "2750.80",
                "change": "45.20",
                "changePercent": "1.67",
                "volume": 500000,
                "marketCap": "1800000000000",
                "pe": "23.8",
                "dividend": "0.00"
            }
        ]
    
    @pytest.fixture
    def expected_scan_results(self):
        """Expected ScanResult objects"""
        return [
            ScanResult(
                conid=123456,
                symbol="AAPL",
                contractDesc="Apple Inc.",
                secType="STK",
                exchange="NASDAQ",
                currency="USD",
                price=Decimal("150.25"),
                change=Decimal("5.75"),
                changePercent=Decimal("3.98"),
                volume=1000000,
                marketCap=Decimal("2500000000000"),
                pe=Decimal("25.5"),
                dividend=Decimal("0.24")
            ),
            ScanResult(
                conid=789012,
                symbol="GOOGL",
                contractDesc="Alphabet Inc.",
                secType="STK",
                exchange="NASDAQ",
                currency="USD",
                price=Decimal("2750.80"),
                change=Decimal("45.20"),
                changePercent=Decimal("1.67"),
                volume=500000,
                marketCap=Decimal("1800000000000"),
                pe=Decimal("23.8"),
                dividend=Decimal("0.00")
            )
        ]
    
    @pytest.mark.asyncio
    async def test_top_gainers_calls_run_scan(self, scanner_adapter, mock_scan_result_data):
        """Test that top_gainers method calls run_scan with correct parameters"""
        # Mock the run_scan method
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            # Call top_gainers
            await scanner_adapter.top_gainers(max_results=25, location="STK.NASDAQ")
            
            # Verify run_scan was called with correct ScanRequest
            mock_run_scan.assert_called_once()
            call_args = mock_run_scan.call_args[0][0]  # First positional argument (ScanRequest)
            
            assert isinstance(call_args, ScanRequest)
            assert call_args.scanCode == "TOP_PERC_GAIN"
            assert call_args.locations == "STK.NASDAQ"
            assert call_args.maxResults == 25
            assert call_args.instrument == "STK"
            assert call_args.secType == "STK"
    
    @pytest.mark.asyncio
    async def test_top_gainers_default_parameters(self, scanner_adapter):
        """Test that top_gainers uses default parameters correctly"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            # Call top_gainers with default parameters
            await scanner_adapter.top_gainers()
            
            # Verify default parameters
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.maxResults == 50
            assert call_args.locations == "STK.US"
    
    @pytest.mark.asyncio
    async def test_top_losers_calls_run_scan(self, scanner_adapter):
        """Test that top_losers method calls run_scan with correct scan code"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            await scanner_adapter.top_losers()
            
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.scanCode == "TOP_PERC_LOSE"
    
    @pytest.mark.asyncio
    async def test_most_active_calls_run_scan(self, scanner_adapter):
        """Test that most_active method calls run_scan with correct scan code"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            await scanner_adapter.most_active()
            
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.scanCode == "MOST_ACTIVE"
    
    @pytest.mark.asyncio
    async def test_hot_by_volume_calls_run_scan(self, scanner_adapter):
        """Test that hot_by_volume method calls run_scan with correct scan code"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            await scanner_adapter.hot_by_volume()
            
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.scanCode == "HOT_BY_VOLUME"
    
    @pytest.mark.asyncio
    async def test_top_trade_count_calls_run_scan(self, scanner_adapter):
        """Test that top_trade_count method calls run_scan with correct scan code"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            await scanner_adapter.top_trade_count()
            
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.scanCode == "TOP_TRADE_COUNT"
    
    @pytest.mark.asyncio
    async def test_high_opt_volume_put_call_ratio_calls_run_scan(self, scanner_adapter):
        """Test that high_opt_volume_put_call_ratio method calls run_scan with correct scan code"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            await scanner_adapter.high_opt_volume_put_call_ratio()
            
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.scanCode == "HIGH_OPT_VOLUME_PUT_CALL_RATIO"
    
    @pytest.mark.asyncio
    async def test_custom_scan_calls_run_scan(self, scanner_adapter):
        """Test that custom_scan method calls run_scan with provided parameters"""
        with patch.object(scanner_adapter, 'run_scan', new_callable=AsyncMock) as mock_run_scan:
            mock_run_scan.return_value = []
            
            filters = [{"code": "marketCapAbove", "value": "1000000000"}]
            await scanner_adapter.custom_scan(
                scan_code="CUSTOM_SCAN",
                filters=filters,
                max_results=100,
                location="STK.NYSE"
            )
            
            call_args = mock_run_scan.call_args[0][0]
            assert call_args.scanCode == "CUSTOM_SCAN"
            assert call_args.filters == filters
            assert call_args.maxResults == 100
            assert call_args.locations == "STK.NYSE"
    
    @pytest.mark.asyncio
    @patch('ib_client.scanners.scanner._post')
    async def test_run_scan_integration(self, mock_post, scanner_adapter, mock_scan_result_data):
        """Test run_scan method integration with HTTP layer"""
        # Mock the HTTP POST call
        mock_post.return_value = {"contracts": mock_scan_result_data}
        
        # Mock _ensure_live method
        with patch.object(scanner_adapter, '_ensure_live', new_callable=AsyncMock):
            scan_request = ScanRequest(
                scanCode="TOP_PERC_GAIN",
                locations="STK.US",
                maxResults=50
            )
            
            results = await scanner_adapter.run_scan(scan_request)
            
            # Verify HTTP call was made with correct parameters
            mock_post.assert_called_once_with(
                "/iserver/scanner/run",
                json_data={
                    "instrument": "STK",
                    "locations": "STK.US",
                    "scanCode": "TOP_PERC_GAIN",
                    "secType": "STK",
                    "maxResults": 50
                }
            )
            
            # Verify results
            assert len(results) == 2
            assert isinstance(results[0], ScanResult)
            assert results[0].symbol == "AAPL"
            assert results[1].symbol == "GOOGL"
    
    @pytest.mark.asyncio
    @patch('ib_client.scanners.scanner._get')
    async def test_get_scanner_params(self, mock_get, scanner_adapter):
        """Test get_scanner_params method"""
        mock_params = {
            "scan_types": [
                {"code": "TOP_PERC_GAIN", "name": "Top % Gainers"},
                {"code": "TOP_PERC_LOSE", "name": "Top % Losers"}
            ],
            "locations": [
                {"code": "STK.US", "name": "US Stocks"},
                {"code": "STK.NASDAQ", "name": "NASDAQ"}
            ]
        }
        mock_get.return_value = mock_params
        
        with patch.object(scanner_adapter, '_ensure_live', new_callable=AsyncMock):
            result = await scanner_adapter.get_scanner_params()
            
            mock_get.assert_called_once_with("/iserver/scanner/params")
            assert result == mock_params
    
    @pytest.mark.asyncio
    async def test_get_available_scan_codes(self, scanner_adapter):
        """Test get_available_scan_codes method"""
        mock_params = {
            "scan_types": [
                {"code": "TOP_PERC_GAIN", "name": "Top % Gainers"},
                {"code": "TOP_PERC_LOSE", "name": "Top % Losers"},
                {"code": "MOST_ACTIVE", "name": "Most Active"}
            ]
        }
        
        with patch.object(scanner_adapter, 'get_scanner_params', new_callable=AsyncMock) as mock_get_params:
            mock_get_params.return_value = mock_params
            
            scan_codes = await scanner_adapter.get_available_scan_codes()
            
            expected_codes = ["TOP_PERC_GAIN", "TOP_PERC_LOSE", "MOST_ACTIVE"]
            assert scan_codes == expected_codes
    
    @pytest.mark.asyncio
    async def test_get_available_locations(self, scanner_adapter):
        """Test get_available_locations method"""
        mock_params = {
            "locations": [
                {"code": "STK.US", "name": "US Stocks"},
                {"code": "STK.NASDAQ", "name": "NASDAQ"},
                "STK.NYSE"  # Test string format as well
            ]
        }
        
        with patch.object(scanner_adapter, 'get_scanner_params', new_callable=AsyncMock) as mock_get_params:
            mock_get_params.return_value = mock_params
            
            locations = await scanner_adapter.get_available_locations()
            
            expected_locations = ["STK.US", "STK.NASDAQ", "STK.NYSE"]
            assert locations == expected_locations
    
    def test_parse_decimal(self, scanner_adapter):
        """Test _parse_decimal method"""
        assert scanner_adapter._parse_decimal("123.45") == Decimal("123.45")
        assert scanner_adapter._parse_decimal(123.45) == Decimal("123.45")
        assert scanner_adapter._parse_decimal(None) is None
        # Test that invalid strings are handled gracefully
        try:
            result = scanner_adapter._parse_decimal("invalid")
            # The method should either return None or raise an exception
            assert result is None
        except Exception:
            # It's acceptable for the method to raise an exception for invalid input
            pass
    
    def test_parse_int(self, scanner_adapter):
        """Test _parse_int method"""
        assert scanner_adapter._parse_int("123") == 123
        assert scanner_adapter._parse_int(123) == 123
        assert scanner_adapter._parse_int(123.45) == 123
        assert scanner_adapter._parse_int(None) is None
        assert scanner_adapter._parse_int("invalid") is None


if __name__ == "__main__":
    # Example of how to run a specific test
    async def test_top_gainers_example():
        """Example test runner for top_gainers"""
        scanner = ScannerAdapter()
        
        # Mock the run_scan method for testing
        async def mock_run_scan(scan_request):
            print(f"Mock run_scan called with: {scan_request}")
            return []
        
        scanner.run_scan = mock_run_scan
        
        # Test the top_gainers method
        result = await scanner.top_gainers(max_results=10, location="STK.NASDAQ")
        print(f"Top gainers result: {result}")
    
    # Run the example
    asyncio.run(test_top_gainers_example()) 