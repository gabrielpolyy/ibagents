"""
Pytest configuration file for IB Client tests
"""
import pytest
import asyncio
import sys
import os

# Add the project root to Python path so we can import ib_client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close() 