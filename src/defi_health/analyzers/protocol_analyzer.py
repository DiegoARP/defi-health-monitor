import sys
from pathlib import Path

# Add the src directory to Python path
src_path = str(Path(__file__).parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from datetime import datetime, timedelta
from defi_health.collectors.defi_collector import DefiDataCollector

# Rest of the code remains the same...

logger = logging.getLogger(__name__)

class ProtocolAnalyzer:
    """Analyzes DeFi protocol data and generates insights"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.metrics = {}
    
    def calculate_market_metrics(self) -> Dict:
        """Calculate market-wide metrics"""
        try:
            self.metrics['market'] = {
                'total_tvl': self.data['tvl'].sum(),
                'average_tvl': self.data['tvl'].mean(),
                'tvl_concentration': self._calculate_concentration(self.data['tvl']),
                'chain_distribution': self._analyze_chain_distribution(),
                'risk_distribution': self._analyze_risk_distribution(),
                'top_protocols_dominance': self._calculate_top_dominance()
            }
            return self.metrics['market']
        except Exception as e:
            logger.error(f"Error calculating market metrics: {str(e)}")
            return {}
    
    def _calculate_concentration(self, values: pd.Series) -> float:
        """Calculate Herfindahl-Hirschman Index for concentration"""
        total = values.sum()
        if total == 0:
            return 0
        shares = values / total
        return (shares ** 2).sum()
    
    def _analyze_chain_distribution(self) -> Dict:
        """Analyze distribution across chains"""
        chain_counts = {}
        for chains in self.data['chains']:
            for chain in chains:
                chain_counts[chain] = chain_counts.get(chain, 0) + 1
                
        return {
            'most_popular_chains': sorted(chain_counts.items(), 
                                        key=lambda x: x[1], 
                                        reverse=True)[:5],
            'chain_diversity': len(chain_counts),
            'average_chains_per_protocol': sum(len(chains) for chains in self.data['chains']) / len(self.data)
        }
    
    def _analyze_risk_distribution(self) -> Dict:
        """Analyze risk levels distribution"""
        risk_counts = self.data['health_metrics'].apply(lambda x: x['risk_level']).value_counts()
        return {
            'risk_distribution': risk_counts.to_dict(),
            'high_risk_tvl': self.data[self.data['health_metrics'].apply(
                lambda x: x['risk_level'] == 'High')]['tvl'].sum()
        }
    
    def _calculate_top_dominance(self) -> Dict:
        """Calculate market dominance of top protocols"""
        total_tvl = self.data['tvl'].sum()
        return {
            'top_3_dominance': (self.data['tvl'].nlargest(3).sum() / total_tvl) * 100,
            'top_5_dominance': (self.data['tvl'].nlargest(5).sum() / total_tvl) * 100,
            'top_10_dominance': (self.data['tvl'].nlargest(10).sum() / total_tvl) * 100
        }
    
    def generate_protocol_insights(self) -> List[Dict]:
        """Generate specific insights for each protocol"""
        insights = []
        
        for _, protocol in self.data.iterrows():
            protocol_insights = {
                'name': protocol['name'],
                'insights': []
            }
            
            # TVL Size
            if protocol['tvl'] > 10_000_000_000:  # $10B
                protocol_insights['insights'].append({
                    'type': 'size',
                    'level': 'high',
                    'message': f"Major protocol with ${protocol['tvl']/1e9:.1f}B TVL"
                })
                
            # Chain Diversity
            chain_count = len(protocol['chains'])
            if chain_count > 10:
                protocol_insights['insights'].append({
                    'type': 'diversity',
                    'level': 'positive',
                    'message': f"High chain diversity with {chain_count} chains"
                })
            elif chain_count < 3:
                protocol_insights['insights'].append({
                    'type': 'diversity',
                    'level': 'warning',
                    'message': f"Limited chain diversity with only {chain_count} chains"
                })
                
            # Risk Level
            risk_level = protocol['health_metrics']['risk_level']
            if risk_level == 'High':
                protocol_insights['insights'].append({
                    'type': 'risk',
                    'level': 'warning',
                    'message': "High risk protocol - extra caution advised"
                })
            
            insights.append(protocol_insights)
            
        return insights

def main():
    """Test the analyzer with sample data"""
    # Import collector and get data
    from defi_health.collectors.defi_collector import DefiDataCollector
    import asyncio
    
    async def analyze():
        collector = DefiDataCollector()
        df = await collector.analyze_protocols(top_n=10)
        
        if not df.empty:
            analyzer = ProtocolAnalyzer(df)
            
            # Calculate market metrics
            market_metrics = analyzer.calculate_market_metrics()
            
            # Generate insights
            insights = analyzer.generate_protocol_insights()
            
            # Print results
            logger.info("\n=== Market Metrics ===")
            logger.info(f"Total TVL: ${market_metrics['total_tvl']/1e9:.2f}B")
            logger.info(f"Top 3 Dominance: {market_metrics['top_protocols_dominance']['top_3_dominance']:.1f}%")
            
            logger.info("\n=== Chain Distribution ===")
            for chain, count in market_metrics['chain_distribution']['most_popular_chains']:
                logger.info(f"{chain}: {count} protocols")
            
            logger.info("\n=== Protocol Insights ===")
            for protocol in insights:
                if protocol['insights']:
                    logger.info(f"\n{protocol['name']}:")
                    for insight in protocol['insights']:
                        logger.info(f"- {insight['message']} ({insight['level']})")
    
    asyncio.run(analyze())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()