import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from defi_health.collectors.defi_collector import DefiDataCollector
from defi_health.analyzers.protocol_analyzer import ProtocolAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolVisualizer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)

    def create_tvl_visualization(self) -> None:
        """Create TVL distribution visualization"""
        # TVL Treemap with updated formatting
        fig = px.treemap(
            self.data,
            values='tvl',
            path=[px.Constant('All Protocols'), 'name'],
            title='Protocol TVL Distribution',
            color='tvl',
            color_continuous_scale='Viridis'
        )
        
        # Update hover template to format values
        fig.update_traces(
            texttemplate="%{label}<br>$%{value:,.0f}",
            hovertemplate="%{label}<br>TVL: $%{value:,.0f}<extra></extra>"
        )
        
        fig.update_layout(
            height=800,
            title={
                'text': "Protocol TVL Distribution",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            }
        )
        
        fig.write_html(self.output_dir / "tvl_distribution.html")

    def create_chain_analysis(self) -> None:
        """Create chain distribution analysis"""
        # Calculate chain frequencies
        chain_counts = {}
        total_tvl_by_chain = {}
        
        for idx, row in self.data.iterrows():
            tvl_per_chain = row['tvl'] / len(row['chains'])
            for chain in row['chains']:
                chain_counts[chain] = chain_counts.get(chain, 0) + 1
                total_tvl_by_chain[chain] = total_tvl_by_chain.get(chain, 0) + tvl_per_chain

        # Create two subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Protocol Count by Chain', 'TVL by Chain (Billions)'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )

        # Protocol Count
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

        # TVL by Chain
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
                'text': "Chain Analysis",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=False
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Chain", row=1, col=1)
        fig.update_xaxes(title_text="Chain", row=1, col=2)
        fig.update_yaxes(title_text="Number of Protocols", row=1, col=1)
        fig.update_yaxes(title_text="TVL (Billions USD)", row=1, col=2)
        
        fig.write_html(self.output_dir / "chain_analysis.html")

    def create_risk_analysis(self) -> None:
        """Create risk analysis visualization"""
        # Extract risk levels and create risk metrics
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
        
        # Create subplot with correct specs for pie charts
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

        # TVL by Risk Level
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

        # Count by Risk Level
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

        # Chain Diversity vs TVL Scatter
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

        # Risk Distribution Bar
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
                'text': "Risk Analysis Dashboard",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=False
        )
        
        # Update axes labels for scatter and bar plots
        fig.update_xaxes(title_text="Number of Chains", row=2, col=1)
        fig.update_xaxes(title_text="Risk Level", row=2, col=2)
        fig.update_yaxes(title_text="TVL (Billions USD)", row=2, col=1)
        fig.update_yaxes(title_text="Number of Protocols", row=2, col=2)
        
        # Update colors and style
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=12)
        )
        
        # Add grid lines to scatter and bar plots
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', row=2)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', row=2)
        
        fig.write_html(self.output_dir / "risk_analysis.html")

async def main():
    """Generate visualizations for protocol analysis"""
    # Collect data
    collector = DefiDataCollector()
    df = await collector.analyze_protocols(top_n=50)  # Increased to 50 for better visualization
    
    if not df.empty:
        # Create visualizations
        visualizer = ProtocolVisualizer(df)
        
        logger.info("Creating visualizations...")
        visualizer.create_tvl_visualization()
        logger.info("Created TVL visualization")
        
        visualizer.create_chain_analysis()
        logger.info("Created chain analysis")
        
        visualizer.create_risk_analysis()
        logger.info("Created risk analysis")
        
        logger.info(f"Visualizations created in {visualizer.output_dir} directory")
        logger.info("Open the HTML files in a web browser to view interactive charts")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())