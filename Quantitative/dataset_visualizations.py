"""
Dataset Visualization Script
Generates publication-quality figures for dataset documentation
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter

# Set publication-quality style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")

def load_dataset_stats(tasks_json_path: str):
    """Load and compute dataset statistics"""
    with open(tasks_json_path, 'r') as f:
        tasks = json.load(f)
    
    # Extract statistics
    categories = [task['category'] for task in tasks]
    difficulties = [task['difficulty'] for task in tasks]
    
    category_counts = Counter(categories)
    difficulty_counts = Counter(difficulties)
    
    return {
        'total_tasks': len(tasks),
        'category_counts': category_counts,
        'difficulty_counts': difficulty_counts,
        'tasks': tasks
    }

def plot_dataset_distribution(stats: dict, output_path: str = None):
    """
    Create a comprehensive dataset distribution figure
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # 1. Category Distribution (Pie Chart)
    ax1 = axes[0]
    categories = list(stats['category_counts'].keys())
    counts = list(stats['category_counts'].values())
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
    
    wedges, texts, autotexts = ax1.pie(
        counts,
        labels=[cat.title() for cat in categories],
        autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*stats["total_tasks"])})',
        startangle=90,
        colors=colors[:len(categories)],
        textprops={'fontsize': 11, 'fontweight': 'bold'}
    )
    ax1.set_title('Task Distribution by Category', fontsize=14, fontweight='bold', pad=20)
    
    # 2. Difficulty Distribution (Bar Chart)
    ax2 = axes[1]
    difficulties = ['Easy', 'Medium', 'Hard']
    difficulty_counts_ordered = [
        stats['difficulty_counts'].get('easy', 0),
        stats['difficulty_counts'].get('medium', 0),
        stats['difficulty_counts'].get('hard', 0)
    ]
    
    bars = ax2.bar(difficulties, difficulty_counts_ordered, 
                   color=['#2ecc71', '#f39c12', '#e74c3c'], width=0.6)
    ax2.set_ylabel('Number of Tasks', fontsize=12)
    ax2.set_title('Task Distribution by Difficulty', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # 3. Category vs Difficulty Heatmap
    ax3 = axes[2]
    
    # Create cross-tabulation
    task_df = pd.DataFrame(stats['tasks'])
    if not task_df.empty:
        crosstab = pd.crosstab(task_df['category'], task_df['difficulty'])
        crosstab = crosstab.reindex(columns=['easy', 'medium', 'hard'], fill_value=0)
        
        sns.heatmap(
            crosstab,
            annot=True,
            fmt='d',
            cmap='YlOrRd',
            ax=ax3,
            cbar_kws={'label': 'Number of Tasks'},
            linewidths=0.5
        )
        ax3.set_xlabel('Difficulty Level', fontsize=12)
        ax3.set_ylabel('Category', fontsize=12)
        ax3.set_title('Category × Difficulty Matrix', fontsize=14, fontweight='bold')
        ax3.set_xticklabels(['Easy', 'Medium', 'Hard'])
        ax3.set_yticklabels([cat.title() for cat in crosstab.index], rotation=0)
    
    plt.suptitle(f'Dataset Overview: {stats["total_tasks"]} Tasks', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    else:
        plt.show()
    
    plt.close()

def plot_task_structure_diagram(output_path: str = None):
    """
    Create a flow diagram showing task structure
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Define boxes
    boxes = [
        {'xy': (0.5, 4), 'width': 2, 'height': 1, 'label': 'Natural Language\nSpecification', 'color': '#3498db'},
        {'xy': (3.5, 4), 'width': 2, 'height': 1, 'label': 'Reference\nVerilog Module', 'color': '#2ecc71'},
        {'xy': (6.5, 4), 'width': 2, 'height': 1, 'label': 'Self-Checking\nTestbench', 'color': '#e74c3c'},
        {'xy': (3.5, 1.5), 'width': 2, 'height': 1, 'label': 'Task Metadata\n(task_id, category,\ndifficulty, I/O)', 'color': '#f39c12'},
    ]
    
    # Draw boxes
    for box in boxes:
        fancy_box = FancyBboxPatch(
            (box['xy'][0], box['xy'][1]),
            box['width'], box['height'],
            boxstyle="round,pad=0.1",
            edgecolor='black',
            facecolor=box['color'],
            linewidth=2
        )
        ax.add_patch(fancy_box)
        
        # Add text
        ax.text(box['xy'][0] + box['width']/2, box['xy'][1] + box['height']/2,
               box['label'],
               ha='center', va='center',
               fontsize=11, fontweight='bold', color='white')
    
    # Draw arrows
    arrows = [
        {'start': (2.5, 4.5), 'end': (3.5, 4.5), 'label': '→'},
        {'start': (5.5, 4.5), 'end': (6.5, 4.5), 'label': '→'},
        {'start': (4.5, 4), 'end': (4.5, 2.5), 'label': '↓'},
    ]
    
    for arrow in arrows:
        arr = FancyArrowPatch(
            arrow['start'], arrow['end'],
            arrowstyle='->', mutation_scale=20,
            linewidth=2, color='black'
        )
        ax.add_patch(arr)
    
    # Add title
    ax.text(5, 5.5, 'Task Structure in Benchmark Dataset', 
           ha='center', fontsize=16, fontweight='bold')
    
    # Add legend/description
    desc_text = (
        "Each task consists of:\n"
        "• Specification: Natural language description\n"
        "• Reference HDL: Verified Verilog-2001 implementation\n"
        "• Testbench: Self-checking validation suite\n"
        "• Metadata: Structured task information"
    )
    ax.text(8.5, 3, desc_text, fontsize=10, 
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
           verticalalignment='top')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    else:
        plt.show()
    
    plt.close()

def plot_dataset_statistics_dashboard(stats: dict, output_path: str = None):
    """
    Create a comprehensive statistics dashboard
    """
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Category breakdown (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    categories = list(stats['category_counts'].keys())
    counts = list(stats['category_counts'].values())
    ax1.barh([cat.title() for cat in categories], counts, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    ax1.set_xlabel('Number of Tasks', fontsize=11)
    ax1.set_title('Tasks by Category', fontweight='bold', fontsize=12)
    ax1.grid(axis='x', alpha=0.3)
    for i, (cat, count) in enumerate(zip(categories, counts)):
        ax1.text(count + 0.5, i, str(count), va='center', fontweight='bold')
    
    # 2. Difficulty breakdown (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    difficulties = ['Easy', 'Medium', 'Hard']
    diff_counts = [
        stats['difficulty_counts'].get('easy', 0),
        stats['difficulty_counts'].get('medium', 0),
        stats['difficulty_counts'].get('hard', 0)
    ]
    ax2.pie(diff_counts, labels=difficulties, autopct='%1.1f%%', 
           colors=['#2ecc71', '#f39c12', '#e74c3c'], startangle=90)
    ax2.set_title('Tasks by Difficulty', fontweight='bold', fontsize=12)
    
    # 3. Summary statistics (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    summary_text = (
        f"Dataset Summary\n\n"
        f"Total Tasks: {stats['total_tasks']}\n\n"
        f"Categories:\n"
    )
    for cat, count in sorted(stats['category_counts'].items()):
        pct = (count / stats['total_tasks']) * 100
        summary_text += f"  {cat.title()}: {count} ({pct:.1f}%)\n"
    summary_text += f"\nDifficulties:\n"
    for diff in ['easy', 'medium', 'hard']:
        count = stats['difficulty_counts'].get(diff, 0)
        if count > 0:
            pct = (count / stats['total_tasks']) * 100
            summary_text += f"  {diff.title()}: {count} ({pct:.1f}%)\n"
    
    ax3.text(0.1, 0.5, summary_text, fontsize=11, 
            verticalalignment='center', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # 4. Category × Difficulty heatmap (middle row, spanning)
    ax4 = fig.add_subplot(gs[1, :])
    task_df = pd.DataFrame(stats['tasks'])
    if not task_df.empty:
        crosstab = pd.crosstab(task_df['category'], task_df['difficulty'])
        crosstab = crosstab.reindex(columns=['easy', 'medium', 'hard'], fill_value=0)
        
        sns.heatmap(
            crosstab,
            annot=True,
            fmt='d',
            cmap='YlOrRd',
            ax=ax4,
            cbar_kws={'label': 'Number of Tasks'},
            linewidths=1,
            square=False
        )
        ax4.set_xlabel('Difficulty Level', fontsize=12)
        ax4.set_ylabel('Category', fontsize=12)
        ax4.set_title('Category × Difficulty Distribution', fontsize=14, fontweight='bold')
        ax4.set_xticklabels(['Easy', 'Medium', 'Hard'])
        ax4.set_yticklabels([cat.title() for cat in crosstab.index], rotation=0)
    
    # 5. Task naming pattern examples (bottom left)
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.axis('off')
    examples = [
        "Task ID Examples:",
        "",
        "comb_and_gate_001",
        "seq_counter_4bit_002",
        "fsm_sequence_detector_101_003",
        "mixed_priority_encoder_4to2_001",
        "",
        "Pattern:",
        "{category}_{design}_{variant}"
    ]
    ax5.text(0.1, 0.5, '\n'.join(examples), fontsize=10,
           verticalalignment='center', family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    # 6. Dataset characteristics (bottom middle)
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.axis('off')
    characteristics = [
        "Dataset Characteristics:",
        "",
        "• Synthesizable Verilog-2001",
        "• Self-checking testbenches",
        "• Multiple specification variants",
        "• Category-balanced design",
        "• Difficulty gradient",
        "• Open-source tools compatible"
    ]
    ax6.text(0.1, 0.5, '\n'.join(characteristics), fontsize=10,
            verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 7. File structure (bottom right)
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')
    structure = [
        "File Organization:",
        "",
        "dataset/",
        "├── tasks.json",
        "├── combinational/",
        "│   └── {design}/",
        "│       ├── reference.v",
        "│       └── testbench.v",
        "├── sequential/",
        "├── fsm/",
        "└── mixed/"
    ]
    ax7.text(0.1, 0.5, '\n'.join(structure), fontsize=9,
            verticalalignment='center', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.5))
    
    plt.suptitle('Dataset Statistics Dashboard', fontsize=16, fontweight='bold', y=0.995)
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    else:
        plt.show()
    
    plt.close()

def main():
    """Generate all dataset visualizations"""
    # Path to tasks.json
    tasks_json = Path(__file__).parent / "dataset" / "tasks.json"
    
    if not tasks_json.exists():
        print(f"Error: {tasks_json} not found")
        return
    
    # Load statistics
    print("Loading dataset statistics...")
    stats = load_dataset_stats(str(tasks_json))
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "figures" / "dataset_figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating dataset visualizations...")
    
    # Generate all plots
    plot_dataset_distribution(stats, output_dir / "dataset_distribution.png")
    plot_task_structure_diagram(output_dir / "task_structure_diagram.png")
    plot_dataset_statistics_dashboard(stats, output_dir / "dataset_statistics_dashboard.png")
    
    print(f"\nAll visualizations saved to: {output_dir}")

if __name__ == "__main__":
    main()

