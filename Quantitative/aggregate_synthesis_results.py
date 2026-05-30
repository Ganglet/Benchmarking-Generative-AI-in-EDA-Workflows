"""
Aggregate Yosys synthesis results into paper-ready tables.

Reports:
  1. Per-model synthesis-pass rate (out of ALL 450 runs, not just syntax-valid)
  2. Per-category synthesis-pass rate
  3. Mean cell count and wire count for synthesizable runs
  4. LaTeX table snippet ready for the paper
"""
import json
import numpy as np
from collections import defaultdict
from pathlib import Path

ROOT     = Path("/Users/angshumansmac/Desktop/Actual Projects/EDA")
SYNTH    = ROOT / "results" / "Benchmark_12_Synthesis" / "synthesis_metrics.json"
RUNS     = ROOT / "results" / "Benchmark_12_Results" / "individual_runs.json"
TASKS    = ROOT / "Quantitative" / "dataset" / "tasks.json"

with open(SYNTH) as f:
    synth_results = json.load(f)
with open(RUNS) as f:
    all_runs = json.load(f)
with open(TASKS) as f:
    tasks_list = json.load(f)

CAT_MAP = {t["task_id"]: t["category"] for t in tasks_list}

MODELS = ["TinyLlama-1.1B-Small", "Llama-3-8B-Large", "StarCoder2-7B-Medium"]
LABELS = {"TinyLlama-1.1B-Small": "TinyLlama-1.1B",
          "Llama-3-8B-Large":     "Llama-3-8B",
          "StarCoder2-7B-Medium": "StarCoder2-7B"}
CATS = ["combinational", "sequential", "fsm", "mixed"]

# Index synthesis results by (model, task, rep)
synth_idx = {(s["model_name"], s["task_id"], s["repetition"]): s for s in synth_results}

print("=" * 80)
print("PER-MODEL SYNTHESIS METRICS (Benchmark 12, full pipeline)")
print("=" * 80)
print(f"{'Model':<16} {'Synth-pass / total':<22} {'Rate':<10} {'Avg cells':<12} {'Avg wires':<12}")
print("-" * 80)

per_model = {}
for m in MODELS:
    model_runs = [r for r in all_runs if r["model_name"] == m]
    total = len(model_runs)
    synth_runs = [synth_idx.get((m, r["task_id"], r["repetition"])) for r in model_runs]
    synth_yes  = [s for s in synth_runs if s and s["synthesizable"]]
    n_synth    = len(synth_yes)
    rate       = n_synth / total * 100
    cells      = [s["cell_count"] for s in synth_yes if s["cell_count"] is not None]
    wires      = [s["wire_count"] for s in synth_yes if s["wire_count"] is not None]
    avg_cells  = np.mean(cells) if cells else 0
    avg_wires  = np.mean(wires) if wires else 0
    per_model[m] = (n_synth, total, rate, avg_cells, avg_wires)
    print(f"{LABELS[m]:<16} {n_synth:>3}/{total:<3}                {rate:5.1f}%    "
          f"{avg_cells:>6.1f}      {avg_wires:>6.1f}")

print()
print("=" * 80)
print("PER-CATEGORY SYNTHESIS-PASS RATE (averaged across 3 models)")
print("=" * 80)
print(f"{'Category':<16} {'Synth-pass / total':<22} {'Rate':<10}")
print("-" * 80)

for c in CATS:
    cat_runs = [r for r in all_runs if CAT_MAP.get(r["task_id"]) == c]
    total = len(cat_runs)
    n_synth = sum(1 for r in cat_runs
                  if (s := synth_idx.get((r["model_name"], r["task_id"], r["repetition"])))
                  and s["synthesizable"])
    rate = n_synth / total * 100 if total else 0
    print(f"{c.capitalize():<16} {n_synth:>3}/{total:<3}                {rate:5.1f}%")

# Overall
total_all = len(all_runs)
total_synth = sum(1 for r in all_runs
                  if (s := synth_idx.get((r["model_name"], r["task_id"], r["repetition"])))
                  and s["synthesizable"])
print(f"{'OVERALL':<16} {total_synth:>3}/{total_all:<3}                {total_synth/total_all*100:5.1f}%")

print()
print("=" * 80)
print("LaTeX TABLE SNIPPET (drop into your paper):")
print("=" * 80)
print(r"""
\begin{table}[!t]
  \centering
  \caption{Per-Model Synthesis Metrics for Benchmark 12 (Yosys Generic Synthesis)}
  \scriptsize
  \setlength{\tabcolsep}{4pt}
  \renewcommand{\arraystretch}{1}
  \resizebox{\columnwidth}{!}{
    \begin{tabular}{|c|c|c|c|c|}
      \hline
      \textbf{Model} & \textbf{Syntax} & \textbf{Sim. Pass} & \textbf{Synth. Pass} & \textbf{Avg Cells}\\
      \hline""")
syn_sim_data = {
    "TinyLlama-1.1B-Small":  ("80.0", "60.7"),
    "Llama-3-8B-Large":      ("72.0", "59.3"),
    "StarCoder2-7B-Medium":  ("59.3", "35.3"),
}
for m in MODELS:
    n_synth, total, rate, avg_cells, _ = per_model[m]
    syn, sim = syn_sim_data[m]
    print(f"      {LABELS[m]} & {syn}\\% & {sim}\\% & {rate:.1f}\\% & {avg_cells:.1f}\\\\")
print(r"""      \hline
    \end{tabular}%
  }
  \label{tab:synthesis_b12}
\end{table}""")
