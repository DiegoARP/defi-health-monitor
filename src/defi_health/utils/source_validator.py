import aiohttp
import asyncio
from typing import Dict, List
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSourceValidator:
    """Validates and tests free DeFi data sources"""
    
    def __init__(self):
        self.sources = {
            "coingecko": {
                "base_url": "https://api.coingecko.com/api/v3",
                "endpoints": [
                    "/ping",
                    "/simple/supported_vs_currencies"
                ]
            },
            "defillama": {
                "base_url": "https://api.llama.fi",
                "endpoints": [
                    "/protocols",
                    "/chains"
                ]
            }
        }
    
    async def test_endpoint(self, url: str) -> Dict:
        """Test a single API endpoint"""
        try:
            start_time = datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    end_time = datetime.now()
                    latency = (end_time - start_time).total_seconds()
                    
                    return {
                        "url": url,
                        "status": response.status,
                        "latency": latency,
                        "working": response.status == 200
                    }
        except Exception as e:
            logger.error(f"Error testing {url}: {str(e)}")
            return {
                "url": url,
                "status": "error",
                "latency": None,
                "working": False,
                "error": str(e)
            }
    
    async def validate_source(self, source_name: str) -> Dict:
        """Validate a specific data source"""
        if source_name not in self.sources:
            raise ValueError(f"Unknown source: {source_name}")
            
        source = self.sources[source_name]
        results = []
        
        for endpoint in source["endpoints"]:
            url = f"{source['base_url']}{endpoint}"
            result = await self.test_endpoint(url)
            results.append(result)
        
        working_endpoints = [r for r in results if r["working"]]
        
        return {
            "name": source_name,
            "total_endpoints": len(results),
            "working_endpoints": len(working_endpoints),
            "average_latency": sum(r["latency"] for r in working_endpoints if r["latency"]) / len(working_endpoints) if working_endpoints else None,
            "results": results
        }
    
    async def validate_all_sources(self) -> Dict[str, Dict]:
        """Validate all configured data sources"""
        tasks = [
            self.validate_source(source_name)
            for source_name in self.sources.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            r["name"]: r for r in results 
            if not isinstance(r, Exception)
        }

async def main():
    """Test all data sources"""
    validator = DataSourceValidator()
    
    logger.info("Starting data source validation...")
    results = await validator.validate_all_sources()
    
    for source_name, result in results.items():
        logger.info(f"\nResults for {source_name}:")
        logger.info(f"Working endpoints: {result['working_endpoints']}/{result['total_endpoints']}")
        if result['average_latency']:
            logger.info(f"Average latency: {result['average_latency']:.2f} seconds")
        
        for endpoint in result['results']:
            status = "✅" if endpoint["working"] else "❌"
            logger.info(f"{status} {endpoint['url']}")
            if not endpoint["working"] and "error" in endpoint:
                logger.info(f"   Error: {endpoint['error']}")

if __name__ == "__main__":
    asyncio.run(main())