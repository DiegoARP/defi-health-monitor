import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import sys
import asyncio

from defi_health.collectors.defi_collector import DefiDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolVisualizer:
    """Visualizes DeFi protocol data with timestamps"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        # Store timestamp when visualizer is initialized
        self._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(f"Initializing visualizer with data as of {self._timestamp}")

    @property
    def timestamp(self):
        """Get the timestamp for the current data"""
        return self._timestamp

    def create_tvl_visualization(self) -> None:
        """Create TVL distribution visualization"""
        title = f'Protocol TVL Distribution (as of {self.timestamp})'
        logger.info(f"Creating {title}")
        
        fig = px.treemap(
            self.data,
            values='tvl',
            path=[px.Constant('All Protocols'), 'name'],
            title=title,
            color='tvl',
            color_continuous_scale='Viridis'
        )
        
        fig.update_traces(
            texttemplate="%{label}<br>$%{value:,.0f}",
            hovertemplate="%{label}<br>TVL: $%{value:,.0f}<extra></extra>"
        )
        
        fig.update_layout(height=800)
        fig.write_html(self.output_dir / "tvl_distribution.html")

    def create_chain_analysis(self) -> None:
        """Create chain distribution analysis"""
        title = f'Chain Analysis (as of {self.timestamp})'
        logger.info(f"Creating {title}")
        
        chain_counts = {}
        total_tvl_by_chain = {}
        
        for idx, row in self.data.iterrows():
            tvl_per_chain = row['tvl'] / len(row['chains'])
            for chain in row['chains']:
                chain_counts[chain] = chain_counts.get(chain, 0) + 1
                total_tvl_by_chain[chain] = total_tvl_by_chain.get(chain, 0) + tvl_per_chain

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Protocol Count by Chain', 'TVL by Chain (Billions)'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )

        chains_sorted = sorted(chain_counts.items(), key=lambda x: x[1], reverse=True)
        fig.add_trace(
            go.Bar(
                x=[x[0] for x in chains_sorted[:15]],
                y=[x[1] for x in chains_sorted[:15]],
                name="Protocol Count",
                hovertemplate="Chain: %{x}<br>Protocols: %{y}<extra></extra>"
            ),
            row=1, col=1
        )

        tvl_sorted = sorted(total_tvl_by_chain.items(), key=lambda x: x[1], reverse=True)
        fig.add_trace(
            go.Bar(
                x=[x[0] for x in tvl_sorted[:15]],
                y=[x[1] / 1e9 for x in tvl_sorted[:15]],
                name="TVL (Billions)",
                hovertemplate="Chain: %{x}<br>TVL: $%{y:.2f}B<extra></extra>"
            ),
            row=1, col=2
        )

        fig.update_layout(
            height=500,
            title={
                'text': title,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=False
        )
        
        fig.write_html(self.output_dir / "chain_analysis.html")

    def create_risk_analysis(self) -> None:
        """Create risk analysis visualization"""
        title = f'Risk Analysis (as of {self.timestamp})'
        logger.info(f"Creating {title}")
        
        risk_data = []
        for idx, row in self.data.iterrows():
            risk_level = row['health_metrics']['risk_level']
            risk_data.append({
                'name': row['name'],
                'risk_level': risk_level,
                'tvl': row['tvl'],
                'chain_count': len(row['chains'])
            })
        
        risk_df = pd.DataFrame(risk_data)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'TVL by Risk Level',
                'Protocol Count by Risk Level',
                'Chain Diversity vs TVL',
                'Risk Distribution'
            ),
            specs=[
                [{"type": "pie"}, {"type": "pie"}],
                [{"type": "scatter"}, {"type": "bar"}]
            ]
        )

        tvl_by_risk = risk_df.groupby('risk_level')['tvl'].sum()
        fig.add_trace(
            go.Pie(
                labels=tvl_by_risk.index,
                values=tvl_by_risk.values,
                name="TVL Distribution",
                hovertemplate="Risk Level: %{label}<br>TVL: $%{value:,.0f}<extra></extra>"
            ),
            row=1, col=1
        )

        count_by_risk = risk_df['risk_level'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=count_by_risk.index,
                values=count_by_risk.values,
                name="Protocol Count",
                hovertemplate="Risk Level: %{label}<br>Protocols: %{value}<extra></extra>"
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Scatter(
                x=risk_df['chain_count'],
                y=risk_df['tvl'] / 1e9,
                mode='markers',
                text=risk_df['name'],
                name="Protocols",
                hovertemplate="Protocol: %{text}<br>Chains: %{x}<br>TVL: $%{y:.2f}B<extra></extra>",
                marker=dict(
                    size=10,
                    color=risk_df['chain_count'],
                    colorscale='Viridis',
                    showscale=True
                )
            ),
            row=2, col=1
        )

        risk_order = ['Low', 'Medium', 'High']
        risk_colors = {'Low': '#00CC96', 'Medium': '#FFA15A', 'High': '#EF553B'}
        
        fig.add_trace(
            go.Bar(
                x=risk_order,
                y=[count_by_risk.get(level, 0) for level in risk_order],
                marker_color=[risk_colors[level] for level in risk_order],
                name="Risk Distribution",
                hovertemplate="Risk Level: %{x}<br>Protocols: %{y}<extra></extra>"
            ),
            row=2, col=2
        )

        fig.update_layout(
            height=800,
            title={
                'text': title,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=False
        )
        
        fig.write_html(self.output_dir / "risk_analysis.html")

async def main():
    """Generate visualizations for protocol analysis"""
    collector = DefiDataCollector()
    df = await collector.analyze_protocols(top_n=50)
    
    if not df.empty:
        visualizer = ProtocolVisualizer(df)
        
        logger.info(f"Creating visualizations for data as of {visualizer.timestamp}")
        visualizer.create_tvl_visualization()
        logger.info("Created TVL visualization")
        
        visualizer.create_chain_analysis()
        logger.info("Created chain analysis")
        
        visualizer.create_risk_analysis()
        logger.info("Created risk analysis")
        
        logger.info(f"All visualizations created in {visualizer.output_dir} directory")
        logger.info("Open the HTML files in a web browser to view interactive charts")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())