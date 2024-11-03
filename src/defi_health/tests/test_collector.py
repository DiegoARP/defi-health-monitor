import pytest
import asyncio
from defi_health.collectors.defi_collector import DefiDataCollector

@pytest.mark.asyncio
async def test_protocol_data_fetch():
    collector = DefiDataCollector()
    data = await collector.get_protocol_data()
    assert data is not None
    assert len(data) > 0
    assert 'name' in data[0]
    assert 'tvl' in data[0]

@pytest.mark.asyncio
async def test_protocol_analysis():
    collector = DefiDataCollector()
    df = await collector.analyze_protocols(top_n=3)
    assert not df.empty
    assert len(df) <= 3
    assert 'name' in df.columns
    assert 'tvl' in df.columns
    assert 'health_metrics' in df.columns