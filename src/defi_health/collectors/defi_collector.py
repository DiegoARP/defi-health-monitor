import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DefiDataCollector:
    """Collects and processes DeFi protocol data"""
    
    def __init__(self):
        self.defillama_base_url = "https://api.llama.fi"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
    async def fetch_data(self, url: str) -> Dict:
        """Generic data fetcher with error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching {url}: Status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Exception fetching {url}: {str(e)}")
            return None

    async def get_protocol_data(self, protocol_name: Optional[str] = None) -> List[Dict]:
        """Fetch protocol data from DeFiLlama"""
        url = f"{self.defillama_base_url}/protocols"
        data = await self.fetch_data(url)
        
        if not data:
            logger.error("No data received from DeFiLlama")
            return []
            
        # Log the first protocol data for debugging
        if data:
            logger.debug(f"Sample protocol data: {data[0]}")
            
        if protocol_name:
            return [p for p in data if p['name'].lower() == protocol_name.lower()]
        return data

    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    
    async def get_protocol_health_metrics(self, protocol_data: Dict) -> Dict:
        """Calculate health metrics for a protocol"""
        try:
            # Debug log
            logger.debug(f"Processing protocol: {protocol_data.get('name')}")
            
            # Safely get TVL and mcap
            tvl = self._safe_float(protocol_data.get('tvl', 0))
            mcap = self._safe_float(protocol_data.get('mcap', 0))
            
            metrics = {
                'name': protocol_data.get('name', 'Unknown'),
                'tvl': tvl,
                'mcap': mcap,
                'mcap_tvl_ratio': mcap/tvl if tvl > 0 else 0.0,
                'chains': protocol_data.get('chains', []),
                'category': protocol_data.get('category', 'Unknown'),
                'health_metrics': {
                    'diversification_score': self._calculate_diversification_score(protocol_data),
                    'stability_score': self._calculate_stability_score(protocol_data),
                    'risk_level': self._assess_risk_level(protocol_data)
                }
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating metrics for {protocol_data.get('name', 'Unknown')}: {str(e)}")
            return None

    def _calculate_diversification_score(self, protocol_data: Dict) -> float:
        """Calculate diversification score based on chains and token distribution"""
        try:
            chain_count = len(protocol_data.get('chains', []))
            chain_score = min(chain_count / 10, 0.5)
            return chain_score + 0.5  # Adding default token score
        except Exception as e:
            logger.error(f"Error calculating diversification score: {str(e)}")
            return 0.5

    def _calculate_stability_score(self, protocol_data: Dict) -> float:
        """Calculate stability score based on TVL and age"""
        try:
            tvl = self._safe_float(protocol_data.get('tvl', 0))
            
            # Some protocols might not have created_at
            created_at = protocol_data.get('created_at', datetime.now().timestamp())
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '')).timestamp()
                except:
                    created_at = datetime.now().timestamp()
                    
            age_days = (datetime.now().timestamp() - created_at) / (24 * 3600)
            
            tvl_score = min(tvl / 1_000_000_000, 0.6)
            age_score = min(age_days / 365, 0.4)
            
            return tvl_score + age_score
        except Exception as e:
            logger.error(f"Error calculating stability score: {str(e)}")
            return 0.5

    def _assess_risk_level(self, protocol_data: Dict) -> str:
        """Assess risk level based on various factors"""
        try:
            risk_score = 0
            
            # TVL factor
            tvl = self._safe_float(protocol_data.get('tvl', 0))
            if tvl > 1_000_000_000:  # >$1B
                risk_score += 1
            elif tvl > 100_000_000:  # >$100M
                risk_score += 2
            else:
                risk_score += 3
                
            # Chain factor
            chain_count = len(protocol_data.get('chains', []))
            if chain_count > 5:
                risk_score += 1
            elif chain_count > 2:
                risk_score += 2
            else:
                risk_score += 3
                
            return 'Low' if risk_score <= 3 else 'Medium' if risk_score <= 5 else 'High'
        except Exception as e:
            logger.error(f"Error assessing risk level: {str(e)}")
            return 'Unknown'

    async def analyze_protocols(self, top_n: int = 10) -> pd.DataFrame:
        """Analyze top protocols and return structured data"""
        try:
            # Fetch all protocols
            protocols = await self.get_protocol_data()
            if not protocols:
                logger.error("No protocols fetched")
                return pd.DataFrame()
                
            logger.info(f"Fetched {len(protocols)} protocols")
            
            # Sort by TVL and get top N
            sorted_protocols = sorted(
                protocols,
                key=lambda x: self._safe_float(x.get('tvl', 0)),
                reverse=True
            )[:top_n]
            
            # Calculate health metrics for each
            results = []
            for protocol in sorted_protocols:
                metrics = await self.get_protocol_health_metrics(protocol)
                if metrics:
                    results.append(metrics)
            
            if not results:
                logger.error("No results after processing protocols")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Add timestamp
            df['timestamp'] = datetime.now().isoformat()
            
            return df
            
        except Exception as e:
            logger.error(f"Error analyzing protocols: {str(e)}")
            logger.exception("Detailed traceback:")
            return pd.DataFrame()

async def main():
    """Test the collector"""
    collector = DefiDataCollector()
    
    logger.info("Fetching and analyzing top DeFi protocols...")
    df = await collector.analyze_protocols(top_n=5)
    
    if not df.empty:
        logger.info("\nTop 5 Protocols Analysis:")
        for _, row in df.iterrows():
            logger.info(f"\nProtocol: {row['name']}")
            logger.info(f"TVL: ${row['tvl']:,.2f}")
            logger.info(f"Risk Level: {row['health_metrics']['risk_level']}")
            logger.info(f"Diversification Score: {row['health_metrics']['diversification_score']:.2f}")
            logger.info(f"Stability Score: {row['health_metrics']['stability_score']:.2f}")
            logger.info(f"Chains: {', '.join(row['chains'][:3])}{'...' if len(row['chains']) > 3 else ''}")
    else:
        logger.error("No data was collected")

if __name__ == "__main__":
    # Set debug logging
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    asyncio.run(main())