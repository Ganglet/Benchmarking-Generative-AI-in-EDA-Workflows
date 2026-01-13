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
    
    def plot_model_comparison_radar(self, output_path: str = None):
        """
        Radar chart: Multi-dimensional model comparison
        """
        from math import pi
        
        # Calculate metrics per model
        metrics = self.df.groupby('model_name').agg({
            'syntax_valid': 'mean',
            'simulation_passed': 'mean',
            'generation_time': lambda x: 1 / (1 + x.mean()),  # Inverse for radar (higher is better)
            'iteration_count': lambda x: 1 / (1 + x.mean()),  # Inverse
        })
        
        # Normalize to 0-100 scale
        metrics['syntax_valid'] *= 100
        metrics['simulation_passed'] *= 100
        metrics['generation_time'] *= 100
        metrics['iteration_count'] *= 100
        
        # Add entropy if available
        if 'confidence_entropy' in self.df.columns:
            metrics['confidence'] = self.df.groupby('model_name')['confidence_entropy'].mean()
            metrics['confidence'] = (1 - metrics['confidence']) * 100  # Inverse entropy
        
        categories = list(metrics.columns)
        N = len(categories)
        
        # Compute angle for each category
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]  # Complete the circle
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        
        for idx, (model, row) in enumerate(metrics.iterrows()):
            values = [row[cat] for cat in categories]
            values += values[:1]  # Complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, label=model, color=colors[idx % len(colors)])
            ax.fill(angles, values, alpha=0.25, color=colors[idx % len(colors)])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories])
        ax.set_ylim(0, 100)
        ax.set_title('Model Performance Radar Chart', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.grid(True)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_task_performance_matrix(self, output_path: str = None):
        """
        Heatmap: Task performance matrix (tasks × models)
        """
        # Calculate simulation pass rate per task per model
        task_perf = self.df.groupby(['task_id', 'model_name'])['simulation_passed'].mean() * 100
        task_perf = task_perf.unstack(fill_value=0)
        
        # Sort tasks by average performance
        task_perf['avg'] = task_perf.mean(axis=1)
        task_perf = task_perf.sort_values('avg', ascending=False)
        task_perf = task_perf.drop('avg', axis=1)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(task_perf) * 0.3)))
        
        sns.heatmap(
            task_perf,
            annot=True,
            fmt='.0f',
            cmap='RdYlGn',
            vmin=0,
            vmax=100,
            ax=ax,
            cbar_kws={'label': 'Simulation Pass Rate (%)'},
            linewidths=0.5
        )
        
        ax.set_xlabel('Model', fontsize=12)
        ax.set_ylabel('Task', fontsize=12)
        ax.set_title('Task Performance Matrix: Simulation Pass Rate by Task and Model', 
                     fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_category_performance_heatmap(self, output_path: str = None):
        """
        Heatmap: Category performance (category × metric × model)
        """
        if 'category' not in self.df.columns:
            print("⚠ No category information available")
            return
        
        # Calculate metrics per category per model
        metrics_data = []
        for category in self.df['category'].unique():
            for model in self.df['model_name'].unique():
                cat_model_df = self.df[(self.df['category'] == category) & 
                                      (self.df['model_name'] == model)]
                if len(cat_model_df) > 0:
                    metrics_data.append({
                        'category': category,
                        'model_name': model,
                        'syntax_valid': cat_model_df['syntax_valid'].mean() * 100,
                        'simulation_passed': cat_model_df['simulation_passed'].mean() * 100,
                    })
        
        metrics_df = pd.DataFrame(metrics_data)
        
        # Create pivot table for simulation passed
        pivot_table = metrics_df.pivot(index='category', columns='model_name', values='simulation_passed')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.heatmap(
            pivot_table,
            annot=True,
            fmt='.1f',
            cmap='YlOrRd',
            vmin=0,
            vmax=100,
            ax=ax,
            cbar_kws={'label': 'Simulation Pass Rate (%)'},
            linewidths=0.5
        )
        
        ax.set_xlabel('Model', fontsize=12)
        ax.set_ylabel('Category', fontsize=12)
        ax.set_title('Category Performance Heatmap', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_category_comparison(self, output_path: str = None):
        """
        Grouped bar chart: Category comparison with syntax and simulation metrics
        """
        if 'category' not in self.df.columns:
            print("⚠ No category information available")
            return
        
        # Calculate metrics per category per model
        cat_metrics = self.df.groupby(['category', 'model_name']).agg({
            'syntax_valid': 'mean',
            'simulation_passed': 'mean',
        }) * 100
        
        cat_metrics = cat_metrics.reset_index()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        categories = cat_metrics['category'].unique()
        models = cat_metrics['model_name'].unique()
        
        x = np.arange(len(categories))
        width = 0.8 / len(models)
        
        # Syntax valid plot
        for i, model in enumerate(models):
            model_data = cat_metrics[cat_metrics['model_name'] == model]
            values = [
                model_data[model_data['category'] == cat]['syntax_valid'].values[0] 
                if len(model_data[model_data['category'] == cat]) > 0 else 0
                for cat in categories
            ]
            ax1.bar(x + i * width, values, width, label=model)
        
        ax1.set_xlabel('Task Category', fontsize=12)
        ax1.set_ylabel('Syntax Valid Rate (%)', fontsize=12)
        ax1.set_title('Syntax Validity by Category', fontsize=14, fontweight='bold')
        ax1.set_xticks(x + width * (len(models) - 1) / 2)
        ax1.set_xticklabels(categories, rotation=45, ha='right')
        ax1.legend(title='Model', fontsize=10)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim(0, 105)
        
        # Simulation passed plot
        for i, model in enumerate(models):
            model_data = cat_metrics[cat_metrics['model_name'] == model]
            values = [
                model_data[model_data['category'] == cat]['simulation_passed'].values[0] 
                if len(model_data[model_data['category'] == cat]) > 0 else 0
                for cat in categories
            ]
            ax2.bar(x + i * width, values, width, label=model)
        
        ax2.set_xlabel('Task Category', fontsize=12)
        ax2.set_ylabel('Simulation Pass Rate (%)', fontsize=12)
        ax2.set_title('Simulation Pass Rate by Category', fontsize=14, fontweight='bold')
        ax2.set_xticks(x + width * (len(models) - 1) / 2)
        ax2.set_xticklabels(categories, rotation=45, ha='right')
        ax2.legend(title='Model', fontsize=10)
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_ylim(0, 105)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_category_gaps_analysis(self, output_path: str = None):
        """
        Bar chart: Gap between syntax validity and simulation pass rate by category
        """
        if 'category' not in self.df.columns:
            print("⚠ No category information available")
            return
        
        # Calculate gap per category per model
        gaps_data = []
        for category in self.df['category'].unique():
            for model in self.df['model_name'].unique():
                cat_model_df = self.df[(self.df['category'] == category) & 
                                      (self.df['model_name'] == model)]
                if len(cat_model_df) > 0:
                    syntax_rate = cat_model_df['syntax_valid'].mean() * 100
                    sim_rate = cat_model_df['simulation_passed'].mean() * 100
                    gap = syntax_rate - sim_rate
                    gaps_data.append({
                        'category': category,
                        'model_name': model,
                        'gap': gap
                    })
        
        gaps_df = pd.DataFrame(gaps_data)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        categories = gaps_df['category'].unique()
        models = gaps_df['model_name'].unique()
        
        x = np.arange(len(categories))
        width = 0.8 / len(models)
        
        for i, model in enumerate(models):
            model_data = gaps_df[gaps_df['model_name'] == model]
            values = [
                model_data[model_data['category'] == cat]['gap'].values[0] 
                if len(model_data[model_data['category'] == cat]) > 0 else 0
                for cat in categories
            ]
            ax.bar(x + i * width, values, width, label=model)
        
        ax.set_xlabel('Task Category', fontsize=12)
        ax.set_ylabel('Gap (%)', fontsize=12)
        ax.set_title('Category Gaps Analysis: Syntax Validity - Simulation Pass Rate', 
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * (len(models) - 1) / 2)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(title='Model', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_task_difficulty_ranking(self, output_path: str = None):
        """
        Bar chart: Task difficulty ranking based on average pass rate
        """
        # Calculate average simulation pass rate per task across all models
        task_difficulty = self.df.groupby('task_id')['simulation_passed'].mean() * 100
        task_difficulty = task_difficulty.sort_values(ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(task_difficulty) * 0.4)))
        
        colors = plt.cm.RdYlGn(task_difficulty.values / 100)
        bars = ax.barh(range(len(task_difficulty)), task_difficulty.values, color=colors)
        
        ax.set_yticks(range(len(task_difficulty)))
        ax.set_yticklabels(task_difficulty.index, fontsize=9)
        ax.set_xlabel('Average Simulation Pass Rate (%)', fontsize=12)
        ax.set_title('Task Difficulty Ranking', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0, 105)
        
        # Add value labels
        for i, (idx, val) in enumerate(task_difficulty.items()):
            ax.text(val + 1, i, f'{val:.1f}%', va='center', fontsize=8)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_iteration_entropy_analysis(self, output_path: str = None):
        """
        Scatter plot: Iteration count vs entropy analysis
        """
        if 'confidence_entropy' not in self.df.columns or 'iteration_count' not in self.df.columns:
            print("⚠ No iteration or entropy data available")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        models = self.df['model_name'].unique()
        colors_map = {'Llama-3-8B-Large': '#3498db', 
                     'StarCoder2-7B-Medium': '#2ecc71', 
                     'TinyLlama-1.1B-Small': '#e74c3c'}
        
        for model in models:
            model_df = self.df[self.df['model_name'] == model]
            ax.scatter(model_df['iteration_count'], 
                      model_df['confidence_entropy'],
                      label=model, 
                      alpha=0.6,
                      s=50,
                      color=colors_map.get(model, None))
        
        ax.set_xlabel('Iteration Count', fontsize=12)
        ax.set_ylabel('Confidence Entropy', fontsize=12)
        ax.set_title('Iteration vs Entropy Analysis', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_fsm_mixed_breakthrough(self, output_path: str = None):
        """
        Bar chart: FSM and Mixed category breakthrough analysis
        """
        if 'category' not in self.df.columns:
            print("⚠ No category information available")
            return
        
        fsm_mixed_df = self.df[self.df['category'].isin(['fsm', 'mixed'])]
        
        if fsm_mixed_df.empty:
            print("⚠ No FSM or Mixed category data available")
            return
        
        # Calculate metrics per category per model
        breakthrough_data = []
        for category in ['fsm', 'mixed']:
            for model in fsm_mixed_df['model_name'].unique():
                cat_model_df = fsm_mixed_df[(fsm_mixed_df['category'] == category) & 
                                           (fsm_mixed_df['model_name'] == model)]
                if len(cat_model_df) > 0:
                    breakthrough_data.append({
                        'category': category.upper(),
                        'model_name': model,
                        'syntax_valid': cat_model_df['syntax_valid'].mean() * 100,
                        'simulation_passed': cat_model_df['simulation_passed'].mean() * 100,
                    })
        
        breakthrough_df = pd.DataFrame(breakthrough_data)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        categories = breakthrough_df['category'].unique()
        models = breakthrough_df['model_name'].unique()
        
        x = np.arange(len(categories))
        width = 0.8 / len(models)
        
        # Syntax valid plot
        for i, model in enumerate(models):
            model_data = breakthrough_df[breakthrough_df['model_name'] == model]
            values = [
                model_data[model_data['category'] == cat]['syntax_valid'].values[0] 
                if len(model_data[model_data['category'] == cat]) > 0 else 0
                for cat in categories
            ]
            ax1.bar(x + i * width, values, width, label=model)
        
        ax1.set_xlabel('Category', fontsize=12)
        ax1.set_ylabel('Syntax Valid Rate (%)', fontsize=12)
        ax1.set_title('FSM/Mixed: Syntax Validity', fontsize=14, fontweight='bold')
        ax1.set_xticks(x + width * (len(models) - 1) / 2)
        ax1.set_xticklabels(categories)
        ax1.legend(title='Model', fontsize=10)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim(0, 105)
        
        # Simulation passed plot
        for i, model in enumerate(models):
            model_data = breakthrough_df[breakthrough_df['model_name'] == model]
            values = [
                model_data[model_data['category'] == cat]['simulation_passed'].values[0] 
                if len(model_data[model_data['category'] == cat]) > 0 else 0
                for cat in categories
            ]
            ax2.bar(x + i * width, values, width, label=model)
        
        ax2.set_xlabel('Category', fontsize=12)
        ax2.set_ylabel('Simulation Pass Rate (%)', fontsize=12)
        ax2.set_title('FSM/Mixed: Simulation Pass Rate', fontsize=14, fontweight='bold')
        ax2.set_xticks(x + width * (len(models) - 1) / 2)
        ax2.set_xticklabels(categories)
        ax2.legend(title='Model', fontsize=10)
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_ylim(0, 105)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_tinylama_breakthrough(self, output_path: str = None):
        """
        Bar chart: TinyLlama-specific performance analysis
        """
        tinylama_df = self.df[self.df['model_name'].str.contains('TinyLlama', case=False, na=False)]
        
        if tinylama_df.empty:
            print("⚠ No TinyLlama data available")
            return
        
        if 'category' not in tinylama_df.columns:
            print("⚠ No category information available")
            return
        
        # Calculate metrics per category
        cat_perf = tinylama_df.groupby('category').agg({
            'syntax_valid': 'mean',
            'simulation_passed': 'mean',
        }) * 100
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(cat_perf))
        width = 0.35
        
        ax.bar(x - width/2, cat_perf['syntax_valid'], width, label='Syntax Valid', color='#3498db')
        ax.bar(x + width/2, cat_perf['simulation_passed'], width, label='Simulation Passed', color='#2ecc71')
        
        ax.set_xlabel('Category', fontsize=12)
        ax.set_ylabel('Rate (%)', fontsize=12)
        ax.set_title('TinyLlama Performance by Category', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(cat_perf.index, rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 105)
        
        # Add value labels
        for i, (idx, row) in enumerate(cat_perf.iterrows()):
            ax.text(i - width/2, row['syntax_valid'] + 2, f'{row["syntax_valid"]:.1f}%', 
                   ha='center', va='bottom', fontsize=9)
            ax.text(i + width/2, row['simulation_passed'] + 2, f'{row["simulation_passed"]:.1f}%', 
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_comprehensive_dashboard(self, output_path: str = None):
        """
        Comprehensive dashboard with multiple subplots
        """
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Overall comparison (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        metrics = self.df.groupby('model_name').agg({
            'syntax_valid': 'mean',
            'simulation_passed': 'mean',
        }) * 100
        metrics.columns = ['Syntax', 'Simulation']
        metrics.plot(kind='bar', ax=ax1, width=0.7, color=['#3498db', '#2ecc71'])
        ax1.set_title('Overall Performance', fontweight='bold')
        ax1.set_ylabel('Rate (%)')
        ax1.legend(fontsize=8)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. Category performance (top middle)
        if 'category' in self.df.columns:
            ax2 = fig.add_subplot(gs[0, 1])
            cat_perf = self.df.groupby(['category', 'model_name'])['simulation_passed'].mean() * 100
            cat_perf = cat_perf.unstack(fill_value=0)
            cat_perf.plot(kind='bar', ax=ax2, width=0.8)
            ax2.set_title('Category Performance', fontweight='bold')
            ax2.set_ylabel('Sim Pass Rate (%)')
            ax2.legend(title='Model', fontsize=7)
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(axis='y', alpha=0.3)
        
        # 3. Generation time (top right)
        ax3 = fig.add_subplot(gs[0, 2])
        time_data = [self.df[self.df['model_name'] == model]['generation_time'].values 
                     for model in self.df['model_name'].unique()]
        ax3.boxplot(time_data, labels=self.df['model_name'].unique())
        ax3.set_title('Generation Time Distribution', fontweight='bold')
        ax3.set_ylabel('Time (s)')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(axis='y', alpha=0.3)
        
        # 4. Task difficulty (middle left)
        ax4 = fig.add_subplot(gs[1, 0])
        task_difficulty = self.df.groupby('task_id')['simulation_passed'].mean() * 100
        task_difficulty = task_difficulty.sort_values(ascending=True).tail(10)  # Top 10 easiest
        ax4.barh(range(len(task_difficulty)), task_difficulty.values)
        ax4.set_yticks(range(len(task_difficulty)))
        ax4.set_yticklabels([t[:20] + '...' if len(t) > 20 else t for t in task_difficulty.index], fontsize=7)
        ax4.set_xlabel('Pass Rate (%)')
        ax4.set_title('Top 10 Easiest Tasks', fontweight='bold')
        ax4.grid(axis='x', alpha=0.3)
        
        # 5. Iteration analysis (middle)
        if 'iteration_count' in self.df.columns:
            ax5 = fig.add_subplot(gs[1, 1])
            iter_data = self.df.groupby('model_name')['iteration_count'].mean()
            iter_data.plot(kind='bar', ax=ax5, color='#9b59b6')
            ax5.set_title('Average Iterations', fontweight='bold')
            ax5.set_ylabel('Iterations')
            ax5.tick_params(axis='x', rotation=45)
            ax5.grid(axis='y', alpha=0.3)
        
        # 6. Entropy analysis (middle right)
        if 'confidence_entropy' in self.df.columns:
            ax6 = fig.add_subplot(gs[1, 2])
            entropy_data = self.df.groupby('model_name')['confidence_entropy'].mean()
            entropy_data.plot(kind='bar', ax=ax6, color='#e74c3c')
            ax6.set_title('Average Confidence Entropy', fontweight='bold')
            ax6.set_ylabel('Entropy')
            ax6.tick_params(axis='x', rotation=45)
            ax6.grid(axis='y', alpha=0.3)
        
        # 7. Failure distribution (bottom left)
        ax7 = fig.add_subplot(gs[2, 0])
        failures = {
            'Pass': (self.df['syntax_valid'] & self.df['simulation_passed']).sum(),
            'Syntax Only': (self.df['syntax_valid'] & ~self.df['simulation_passed']).sum(),
            'Fail': (~self.df['syntax_valid']).sum()
        }
        ax7.pie(failures.values(), labels=failures.keys(), autopct='%1.1f%%', startangle=90)
        ax7.set_title('Failure Distribution', fontweight='bold')
        
        # 8. Category gaps (bottom middle)
        if 'category' in self.df.columns:
            ax8 = fig.add_subplot(gs[2, 1])
            gaps = []
            for cat in self.df['category'].unique():
                cat_df = self.df[self.df['category'] == cat]
                syntax = cat_df['syntax_valid'].mean() * 100
                sim = cat_df['simulation_passed'].mean() * 100
                gaps.append(syntax - sim)
            ax8.bar(self.df['category'].unique(), gaps, color='#f39c12')
            ax8.set_title('Category Gaps', fontweight='bold')
            ax8.set_ylabel('Gap (%)')
            ax8.tick_params(axis='x', rotation=45)
            ax8.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax8.grid(axis='y', alpha=0.3)
        
        # 9. Model comparison summary (bottom right)
        ax9 = fig.add_subplot(gs[2, 2])
        ax9.axis('off')
        summary_text = "Model Summary:\n\n"
        for model in self.df['model_name'].unique():
            model_df = self.df[self.df['model_name'] == model]
            syntax = model_df['syntax_valid'].mean() * 100
            sim = model_df['simulation_passed'].mean() * 100
            summary_text += f"{model}:\n"
            summary_text += f"  Syntax: {syntax:.1f}%\n"
            summary_text += f"  Simulation: {sim:.1f}%\n\n"
        ax9.text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center', 
                family='monospace')
        
        plt.suptitle('Comprehensive Benchmark Dashboard', fontsize=16, fontweight='bold', y=0.995)
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_all_plots(self, output_dir: str):
        """
        Generate all available plots including advanced analytics
        
        Args:
            output_dir: Directory to save all figures
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("GENERATING VISUALIZATIONS")
        print("="*60 + "\n")
        
        # Basic visualizations
        print("Generating basic visualizations...")
        self.plot_overall_comparison(output_path / "overall_comparison.png")
        
        if 'category' in self.df.columns:
            self.plot_pass_rate_by_category(output_path / "pass_rate_by_category.png")
        
        if 'cell_count' in self.df.columns and self.df['cell_count'].notna().any():
            self.plot_synthesis_quality(output_path / "synthesis_quality.png")
        
        self.plot_generation_time(output_path / "generation_time.png")
        
        if 'prompt_template' in self.df.columns:
            self.plot_prompt_sensitivity(output_path / "prompt_sensitivity.png")
        
        self.plot_failure_distribution(output_path / "failure_distribution.png")
        
        # Advanced visualizations
        print("\nGenerating advanced visualizations...")
        
        # Model comparison radar chart
        try:
            self.plot_model_comparison_radar(output_path / "model_comparison_radar.png")
        except Exception as e:
            print(f"⚠ Could not generate radar chart: {e}")
        
        # Task performance matrix
        try:
            self.plot_task_performance_matrix(output_path / "task_performance_matrix.png")
        except Exception as e:
            print(f"⚠ Could not generate task performance matrix: {e}")
        
        # Category performance heatmap
        if 'category' in self.df.columns:
            try:
                self.plot_category_performance_heatmap(output_path / "category_performance_heatmap.png")
            except Exception as e:
                print(f"⚠ Could not generate category heatmap: {e}")
        
        # Category comparison
        if 'category' in self.df.columns:
            try:
                self.plot_category_comparison(output_path / "category_comparison.png")
            except Exception as e:
                print(f"⚠ Could not generate category comparison: {e}")
        
        # Category gaps analysis
        if 'category' in self.df.columns:
            try:
                self.plot_category_gaps_analysis(output_path / "category_gaps_analysis.png")
            except Exception as e:
                print(f"⚠ Could not generate category gaps analysis: {e}")
        
        # Task difficulty ranking
        try:
            self.plot_task_difficulty_ranking(output_path / "task_difficulty_ranking.png")
        except Exception as e:
            print(f"⚠ Could not generate task difficulty ranking: {e}")
        
        # Iteration entropy analysis
        if 'confidence_entropy' in self.df.columns and 'iteration_count' in self.df.columns:
            try:
                self.plot_iteration_entropy_analysis(output_path / "iteration_entropy_analysis.png")
            except Exception as e:
                print(f"⚠ Could not generate iteration entropy analysis: {e}")
        
        # FSM/Mixed breakthrough
        if 'category' in self.df.columns:
            try:
                self.plot_fsm_mixed_breakthrough(output_path / "fsm_mixed_breakthrough.png")
            except Exception as e:
                print(f"⚠ Could not generate FSM/Mixed breakthrough: {e}")
        
        # TinyLlama breakthrough
        if any('TinyLlama' in str(m) for m in self.df['model_name'].unique()):
            try:
                self.plot_tinylama_breakthrough(output_path / "tinylama_breakthrough.png")
            except Exception as e:
                print(f"⚠ Could not generate TinyLlama breakthrough: {e}")
        
        # Comprehensive dashboard
        try:
            self.plot_comprehensive_dashboard(output_path / "comprehensive_dashboard.png")
        except Exception as e:
            print(f"⚠ Could not generate comprehensive dashboard: {e}")
        
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

