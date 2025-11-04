"""
Visualization Module for Benchmark Results
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict

# Set publication-quality style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")

class BenchmarkVisualizer:
    """Generate visualizations for benchmark results"""
    
    def __init__(self, results_json: str = None, df: pd.DataFrame = None):
        """
        Initialize visualizer
        
        Args:
            results_json: Path to benchmark_results.json (or)
            df: DataFrame with results (one must be provided)
        """
        if df is not None:
            self.df = df
        elif results_json:
            with open(results_json, 'r') as f:
                data = json.load(f)
            self.df = pd.DataFrame(data)
        else:
            raise ValueError("Either results_json or df must be provided")
        
        # Extract category from task_id if possible
        if 'task_id' in self.df.columns:
            self.df['category'] = self.df['task_id'].str.split('_').str[0]
    
    def plot_pass_rate_by_category(
        self, 
        output_path: str = None,
        metric: str = 'simulation_passed'
    ):
        """
        Bar chart: Pass rate per model per category
        
        Args:
            output_path: Path to save figure
            metric: Which metric to plot ('syntax_valid' or 'simulation_passed')
        """
        if 'category' not in self.df.columns:
            print("⚠ No category information available")
            return
        
        # Calculate pass rates
        pass_rates = self.df.groupby(['model_name', 'category'])[metric].mean() * 100
        pass_rates = pass_rates.reset_index()
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        categories = pass_rates['category'].unique()
        models = pass_rates['model_name'].unique()
        
        x = np.arange(len(categories))
        width = 0.8 / len(models)
        
        for i, model in enumerate(models):
            model_data = pass_rates[pass_rates['model_name'] == model]
            values = [
                model_data[model_data['category'] == cat][metric].values[0] 
                if len(model_data[model_data['category'] == cat]) > 0 else 0
                for cat in categories
            ]
            ax.bar(x + i * width, values, width, label=model)
        
        ax.set_xlabel('Task Category', fontsize=12)
        ax.set_ylabel(f'{metric.replace("_", " ").title()} Rate (%)', fontsize=12)
        ax.set_title(f'Model Performance by Task Category', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * (len(models) - 1) / 2)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(title='Model', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 105)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_synthesis_quality(self, output_path: str = None):
        """
        Box plot: Cell count distribution per model
        
        Args:
            output_path: Path to save figure
        """
        if 'cell_count' not in self.df.columns:
            print("⚠ No synthesis data available")
            return
        
        # Filter out null values
        df_synth = self.df[self.df['cell_count'].notna()].copy()
        
        if df_synth.empty:
            print("⚠ No synthesis quality data available")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.boxplot(
            data=df_synth,
            x='model_name',
            y='cell_count',
            ax=ax,
            palette='Set2'
        )
        
        ax.set_xlabel('Model', fontsize=12)
        ax.set_ylabel('Cell Count', fontsize=12)
        ax.set_title('Synthesis Quality: Cell Count Distribution', 
                     fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_generation_time(self, output_path: str = None):
        """
        Violin plot: Generation time distribution per model
        
        Args:
            output_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.violinplot(
            data=self.df,
            x='model_name',
            y='generation_time',
            ax=ax,
            palette='muted'
        )
        
        ax.set_xlabel('Model', fontsize=12)
        ax.set_ylabel('Generation Time (seconds)', fontsize=12)
        ax.set_title('Code Generation Time Distribution', 
                     fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_prompt_sensitivity(self, output_path: str = None):
        """
        Heatmap: Variance across prompt templates
        
        Args:
            output_path: Path to save figure
        """
        if 'prompt_template' not in self.df.columns:
            print("⚠ No prompt template information available")
            return
        
        # Calculate pass rates per model and template
        pivot_data = self.df.groupby(['model_name', 'prompt_template'])['simulation_passed'].mean() * 100
        pivot_table = pivot_data.unstack(fill_value=0)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        sns.heatmap(
            pivot_table,
            annot=True,
            fmt='.1f',
            cmap='YlGnBu',
            ax=ax,
            cbar_kws={'label': 'Pass Rate (%)'}
        )
        
        ax.set_xlabel('Prompt Template', fontsize=12)
        ax.set_ylabel('Model', fontsize=12)
        ax.set_title('Prompt Sensitivity: Pass Rate by Template', 
                     fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_failure_distribution(self, output_path: str = None):
        """
        Pie chart: Distribution of failure types
        
        Args:
            output_path: Path to save figure
        """
        # Categorize failures
        failures = {
            'Syntax Valid + Sim Pass': 0,
            'Syntax Valid + Sim Fail': 0,
            'Syntax Error': 0
        }
        
        for _, row in self.df.iterrows():
            if row['syntax_valid']:
                if row['simulation_passed']:
                    failures['Syntax Valid + Sim Pass'] += 1
                else:
                    failures['Syntax Valid + Sim Fail'] += 1
            else:
                failures['Syntax Error'] += 1
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 8))
        
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        explode = (0.05, 0, 0)
        
        wedges, texts, autotexts = ax.pie(
            failures.values(),
            labels=failures.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            explode=explode,
            textprops={'fontsize': 11}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Distribution of Results', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_overall_comparison(self, output_path: str = None):
        """
        Grouped bar chart: Overall comparison of key metrics
        
        Args:
            output_path: Path to save figure
        """
        # Calculate metrics per model
        metrics = self.df.groupby('model_name').agg({
            'syntax_valid': 'mean',
            'simulation_passed': 'mean',
        }) * 100
        
        metrics.columns = ['Syntax Valid', 'Functional Pass']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        metrics.plot(kind='bar', ax=ax, width=0.7, color=['#3498db', '#2ecc71'])
        
        ax.set_xlabel('Model', fontsize=12)
        ax.set_ylabel('Success Rate (%)', fontsize=12)
        ax.set_title('Overall Model Performance Comparison', 
                     fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='lower right')
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on bars
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%', padding=3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_all_plots(self, output_dir: str):
        """
        Generate all available plots
        
        Args:
            output_dir: Directory to save all figures
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("GENERATING VISUALIZATIONS")
        print("="*60 + "\n")
        
        # Overall comparison
        self.plot_overall_comparison(output_path / "overall_comparison.png")
        
        # Pass rate by category
        if 'category' in self.df.columns:
            self.plot_pass_rate_by_category(output_path / "pass_rate_by_category.png")
        
        # Synthesis quality
        if 'cell_count' in self.df.columns and self.df['cell_count'].notna().any():
            self.plot_synthesis_quality(output_path / "synthesis_quality.png")
        
        # Generation time
        self.plot_generation_time(output_path / "generation_time.png")
        
        # Prompt sensitivity
        if 'prompt_template' in self.df.columns:
            self.plot_prompt_sensitivity(output_path / "prompt_sensitivity.png")
        
        # Failure distribution
        self.plot_failure_distribution(output_path / "failure_distribution.png")
        
        print(f"\n✓ All visualizations saved to: {output_dir}")


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python visualizations.py <path_to_benchmark_results.json> [output_dir]")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./figures"
    
    if not Path(results_file).exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)
    
    print(f"Creating visualizations from: {results_file}\n")
    
    viz = BenchmarkVisualizer(results_json=results_file)
    viz.generate_all_plots(output_dir)

