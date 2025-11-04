"""
Dataset loader for HDL benchmarking tasks
"""

import json
from pathlib import Path
from typing import List
from dataclasses import dataclass

@dataclass
class BenchmarkTask:
    """Represents a single HDL design task"""
    task_id: str
    spec: str
    reference_hdl: str
    reference_tb: str
    category: str
    difficulty: str
    inputs: List[str]
    outputs: List[str]


def load_tasks_from_json(json_path: str, dataset_root: str = None) -> List[BenchmarkTask]:
    """
    Load benchmark tasks from JSON file
    
    Args:
        json_path: Path to tasks.json file
        dataset_root: Root directory for dataset (auto-detected if None)
        
    Returns:
        List of BenchmarkTask objects
    """
    json_file = Path(json_path)
    
    if dataset_root is None:
        dataset_root = json_file.parent
    else:
        dataset_root = Path(dataset_root)
    
    with open(json_file, 'r') as f:
        tasks_data = json.load(f)
    
    tasks = []
    for task_data in tasks_data:
        # Convert relative paths to absolute paths
        ref_hdl = dataset_root / task_data['reference_hdl']
        ref_tb = dataset_root / task_data['reference_tb']
        
        task = BenchmarkTask(
            task_id=task_data['task_id'],
            spec=task_data['specification'],
            reference_hdl=str(ref_hdl),
            reference_tb=str(ref_tb),
            category=task_data['category'],
            difficulty=task_data.get('difficulty', 'medium'),
            inputs=task_data.get('inputs', []),
            outputs=task_data.get('outputs', [])
        )
        tasks.append(task)
    
    return tasks


def validate_dataset(tasks: List[BenchmarkTask]) -> bool:
    """
    Validate that all reference files exist
    
    Args:
        tasks: List of BenchmarkTask objects
        
    Returns:
        True if all files exist, False otherwise
    """
    all_valid = True
    
    for task in tasks:
        hdl_file = Path(task.reference_hdl)
        tb_file = Path(task.reference_tb)
        
        if not hdl_file.exists():
            print(f"⚠ Missing reference HDL: {task.task_id} - {hdl_file}")
            all_valid = False
        
        if not tb_file.exists():
            print(f"⚠ Missing testbench: {task.task_id} - {tb_file}")
            all_valid = False
    
    if all_valid:
        print(f"✓ All {len(tasks)} tasks validated successfully")
    else:
        print(f"✗ Some files are missing")
    
    return all_valid


def get_tasks_by_category(tasks: List[BenchmarkTask], category: str) -> List[BenchmarkTask]:
    """Filter tasks by category"""
    return [task for task in tasks if task.category == category]


def get_tasks_by_difficulty(tasks: List[BenchmarkTask], difficulty: str) -> List[BenchmarkTask]:
    """Filter tasks by difficulty"""
    return [task for task in tasks if task.difficulty == difficulty]


def print_dataset_stats(tasks: List[BenchmarkTask]):
    """Print statistics about the dataset"""
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    
    print(f"Total tasks: {len(tasks)}")
    
    # By category
    categories = {}
    for task in tasks:
        categories[task.category] = categories.get(task.category, 0) + 1
    
    print("\nBy Category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:15s}: {count:3d} tasks")
    
    # By difficulty
    difficulties = {}
    for task in tasks:
        difficulties[task.difficulty] = difficulties.get(task.difficulty, 0) + 1
    
    print("\nBy Difficulty:")
    for diff, count in sorted(difficulties.items()):
        print(f"  {diff:15s}: {count:3d} tasks")
    
    print("="*60 + "\n")


# Example usage
if __name__ == "__main__":
    import sys
    
    # Default path
    dataset_path = Path(__file__).parent / "dataset" / "tasks.json"
    
    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])
    
    print(f"Loading tasks from: {dataset_path}")
    
    try:
        tasks = load_tasks_from_json(str(dataset_path))
        print_dataset_stats(tasks)
        validate_dataset(tasks)
        
        # Show first task as example
        if tasks:
            print("\nExample Task:")
            print("-" * 60)
            task = tasks[0]
            print(f"ID: {task.task_id}")
            print(f"Category: {task.category}")
            print(f"Difficulty: {task.difficulty}")
            print(f"Specification: {task.spec[:100]}...")
            print(f"Reference HDL: {task.reference_hdl}")
            print(f"Testbench: {task.reference_tb}")
        
    except FileNotFoundError:
        print(f"Error: Could not find {dataset_path}")
    except Exception as e:
        print(f"Error loading dataset: {e}")

