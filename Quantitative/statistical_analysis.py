"""
Statistical Analysis Module for Benchmark Results
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from scipy import stats
from collections import defaultdict


class BenchmarkAnalyzer:
    """Statistical analysis of benchmark results"""
    
    def __init__(self, results_json: str):
        """
        Initialize analyzer with results JSON
        
        Args:
            results_json: Path to benchmark_results.json
        """
        self.results_path = Path(results_json)
        self.df = self._load_results()
        
    def _load_results(self) -> pd.DataFrame:
        """Load results from JSON into DataFrame"""
        with open(self.results_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        
        # Add derived columns
        if 'test_cases_passed' in df.columns and 'test_cases_total' in df.columns:
            df['functional_correctness_rate'] = df.apply(
                lambda row: row['test_cases_passed'] / row['test_cases_total'] 
                if row['test_cases_total'] > 0 else 0, 
                axis=1
            )
        
        return df
    
    def compute_summary_statistics(self) -> pd.DataFrame:
        """
        Compute summary statistics per model
        
        Returns:
            DataFrame with aggregated metrics per model
        """
        if self.df.empty:
            print("⚠ No data to analyze")
            return pd.DataFrame()
        
        summary = self.df.groupby('model_name').agg({
            'syntax_valid': ['count', 'sum', 'mean'],
            'simulation_passed': ['sum', 'mean'],
            'test_cases_passed': 'sum',
            'test_cases_total': 'sum',
            'generation_time': ['mean', 'std', 'median'],
            'compile_time': ['mean', 'std'],
            'simulation_time': ['mean', 'std'],
            'cell_count': ['mean', 'std'],
            'estimated_area': ['mean', 'std']
        }).round(3)
        
        # Flatten column names
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        
        # Add percentage columns
        summary['syntax_valid_pct'] = (summary['syntax_valid_sum'] / summary['syntax_valid_count'] * 100).round(1)
        summary['simulation_passed_pct'] = (summary['simulation_passed_sum'] / summary['syntax_valid_count'] * 100).round(1)
        
        return summary
    
    def compute_category_performance(self) -> pd.DataFrame:
        """
        Compute performance metrics by task category
        
        Returns:
            DataFrame with metrics per model and category
        """
        if 'task_id' not in self.df.columns:
            print("⚠ No category information available")
            return pd.DataFrame()
        
        # Extract category from task_id (assumes format: category_name_id)
        self.df['category'] = self.df['task_id'].str.split('_').str[0]
        
        category_perf = self.df.groupby(['model_name', 'category']).agg({
            'syntax_valid': ['count', 'sum', 'mean'],
            'simulation_passed': ['sum', 'mean']
        }).round(3)
        
        return category_perf
    
    def paired_statistical_test(
        self, 
        model_a: str, 
        model_b: str, 
        metric: str = 'simulation_passed'
    ) -> Dict:
        """
        Perform paired statistical test between two models
        
        Args:
            model_a: Name of first model
            model_b: Name of second model
            metric: Metric to compare ('syntax_valid' or 'simulation_passed')
            
        Returns:
            Dictionary with test results
        """
        df_a = self.df[self.df['model_name'] == model_a]
        df_b = self.df[self.df['model_name'] == model_b]
        
        # Align by task_id
        merged = df_a.merge(df_b, on='task_id', suffixes=('_a', '_b'))
        
        if merged.empty:
            return {"error": "No paired data found"}
        
        # Extract metric values
        values_a = merged[f'{metric}_a'].astype(int)
        values_b = merged[f'{metric}_b'].astype(int)
        
        # Wilcoxon signed-rank test (non-parametric)
        try:
            stat_w, p_value_w = stats.wilcoxon(values_a, values_b, zero_method='wilcox')
        except ValueError:
            stat_w, p_value_w = None, None
        
        # Paired t-test (parametric)
        try:
            stat_t, p_value_t = stats.ttest_rel(values_a, values_b)
        except ValueError:
            stat_t, p_value_t = None, None
        
        # Effect size (Cohen's d)
        diff = values_a - values_b
        cohens_d = diff.mean() / diff.std() if diff.std() > 0 else 0
        
        return {
            'model_a': model_a,
            'model_b': model_b,
            'metric': metric,
            'n_pairs': len(merged),
            'mean_a': values_a.mean(),
            'mean_b': values_b.mean(),
            'wilcoxon_statistic': stat_w,
            'wilcoxon_p_value': p_value_w,
            'ttest_statistic': stat_t,
            'ttest_p_value': p_value_t,
            'cohens_d': cohens_d,
            'significant_at_0.05': p_value_w < 0.05 if p_value_w else False
        }
    
    def compute_confidence_interval(
        self, 
        model_name: str, 
        metric: str = 'simulation_passed',
        confidence: float = 0.95
    ) -> Tuple[float, float, float]:
        """
        Compute bootstrap confidence interval for a metric
        
        Args:
            model_name: Name of model
            metric: Metric to analyze
            confidence: Confidence level (default 0.95)
            
        Returns:
            Tuple of (mean, lower_bound, upper_bound)
        """
        df_model = self.df[self.df['model_name'] == model_name]
        
        if df_model.empty:
            return (0.0, 0.0, 0.0)
        
        values = df_model[metric].astype(int).values
        
        # Bootstrap resampling
        n_bootstrap = 10000
        bootstrap_means = []
        
        for _ in range(n_bootstrap):
            sample = np.random.choice(values, size=len(values), replace=True)
            bootstrap_means.append(sample.mean())
        
        bootstrap_means = np.array(bootstrap_means)
        
        # Calculate confidence interval
        alpha = 1 - confidence
        lower = np.percentile(bootstrap_means, alpha/2 * 100)
        upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
        mean = values.mean()
        
        return (mean, lower, upper)
    
    def compute_prompt_sensitivity(self) -> pd.DataFrame:
        """
        Analyze variance across different prompt templates
        Note: Requires 'prompt_template' column in data
        
        Returns:
            DataFrame with variance metrics
        """
        if 'prompt_template' not in self.df.columns:
            print("⚠ No prompt template information in results")
            return pd.DataFrame()
        
        sensitivity = self.df.groupby(['model_name', 'prompt_template']).agg({
            'simulation_passed': ['mean', 'std']
        })
        
        return sensitivity
    
    def generate_comparison_table(self) -> str:
        """
        Generate formatted comparison table of all models
        
        Returns:
            Markdown-formatted table string
        """
        summary = self.compute_summary_statistics()
        
        if summary.empty:
            return "No data available"
        
        table = "\n## Model Performance Comparison\n\n"
        table += "| Model | Tasks | Syntax Valid | Functional Pass | Avg Gen Time | Avg Cell Count |\n"
        table += "|-------|-------|--------------|-----------------|--------------|----------------|\n"
        
        for model_name in summary.index:
            row = summary.loc[model_name]
            table += f"| {model_name:20s} | "
            table += f"{int(row['syntax_valid_count']):3d} | "
            table += f"{row['syntax_valid_pct']:5.1f}% | "
            table += f"{row['simulation_passed_pct']:5.1f}% | "
            table += f"{row['generation_time_mean']:6.2f}s | "
            
            if not pd.isna(row.get('cell_count_mean', np.nan)):
                table += f"{row['cell_count_mean']:7.1f} |\n"
            else:
                table += "N/A |\n"
        
        return table
    
    def export_results(self, output_dir: Path):
        """
        Export analysis results to various formats
        
        Args:
            output_dir: Directory to save outputs
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Summary statistics
        summary = self.compute_summary_statistics()
        summary.to_csv(output_dir / "summary_statistics.csv")
        print(f"✓ Saved: {output_dir / 'summary_statistics.csv'}")
        
        # Category performance
        cat_perf = self.compute_category_performance()
        if not cat_perf.empty:
            cat_perf.to_csv(output_dir / "category_performance.csv")
            print(f"✓ Saved: {output_dir / 'category_performance.csv'}")
        
        # Comparison table (markdown)
        table = self.generate_comparison_table()
        with open(output_dir / "comparison_table.md", 'w') as f:
            f.write(table)
        print(f"✓ Saved: {output_dir / 'comparison_table.md'}")
        
        # Statistical tests (if multiple models)
        models = self.df['model_name'].unique()
        if len(models) >= 2:
            tests_results = []
            for i, model_a in enumerate(models):
                for model_b in models[i+1:]:
                    result = self.paired_statistical_test(model_a, model_b, 'simulation_passed')
                    tests_results.append(result)
            
            tests_df = pd.DataFrame(tests_results)
            tests_df.to_csv(output_dir / "statistical_tests.csv", index=False)
            print(f"✓ Saved: {output_dir / 'statistical_tests.csv'}")
        
        print(f"\n✓ Analysis results exported to: {output_dir}")
    
    def print_summary_report(self):
        """Print formatted summary report to console"""
        print("\n" + "="*70)
        print("BENCHMARK ANALYSIS SUMMARY")
        print("="*70)
        
        summary = self.compute_summary_statistics()
        
        if summary.empty:
            print("No results to analyze")
            return
        
        print(f"\nTotal Tasks Evaluated: {int(summary['syntax_valid_count'].max())}")
        print(f"Number of Models: {len(summary)}")
        
        print("\n" + "-"*70)
        print("Per-Model Results:")
        print("-"*70)
        
        for model_name in summary.index:
            row = summary.loc[model_name]
            print(f"\n{model_name}")
            print(f"  Syntax Validity:       {row['syntax_valid_sum']:3.0f}/{row['syntax_valid_count']:.0f} ({row['syntax_valid_pct']:.1f}%)")
            print(f"  Functional Pass:       {row['simulation_passed_sum']:3.0f}/{row['syntax_valid_count']:.0f} ({row['simulation_passed_pct']:.1f}%)")
            print(f"  Avg Generation Time:   {row['generation_time_mean']:.3f}s (±{row['generation_time_std']:.3f}s)")
            print(f"  Median Generation Time:{row['generation_time_median']:.3f}s")
            
            if not pd.isna(row.get('cell_count_mean', np.nan)):
                print(f"  Avg Cell Count:        {row['cell_count_mean']:.1f} (±{row['cell_count_std']:.1f})")
        
        print("\n" + "="*70)


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python statistical_analysis.py <path_to_benchmark_results.json>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    if not Path(results_file).exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)
    
    print(f"Analyzing results from: {results_file}\n")
    
    analyzer = BenchmarkAnalyzer(results_file)
    analyzer.print_summary_report()
    
    # Export results
    output_dir = Path(results_file).parent / "analysis"
    analyzer.export_results(output_dir)

