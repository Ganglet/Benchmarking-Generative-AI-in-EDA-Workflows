"""
Compute mean ±σ for Table III (per-model Benchmark 12 results).
σ is across the 3 repetitions (rep1, rep2, rep3) per model — measures
reproducibility of the pipeline at fixed temperature 0.0.
"""
import json
import numpy as np
from collections import defaultdict

RESULTS = "/Users/angshumansmac/Desktop/Actual Projects/EDA/results/Benchmark_12_Results/individual_runs.json"

with open(RESULTS) as f:
    runs = json.load(f)

MODELS = ["TinyLlama-1.1B-Small", "Llama-3-8B-Large", "StarCoder2-7B-Medium"]
LABELS = {"TinyLlama-1.1B-Small": "TinyLlama-1.1B",
          "Llama-3-8B-Large":     "Llama-3-8B",
          "StarCoder2-7B-Medium": "StarCoder2-7B"}

print(f"{'Model':<16} {'Syntax (mean ± σ)':<22} {'Sim Pass (mean ± σ)':<24} {'Avg Gen Time (s)':<16}")
print("-" * 80)

for m in MODELS:
    sub = [r for r in runs if r["model_name"] == m]
    # group by repetition
    by_rep = defaultdict(list)
    for r in sub:
        by_rep[r["repetition"]].append(r)

    syn_rates = []
    sim_rates = []
    for rep_num, rep_runs in sorted(by_rep.items()):
        syn = sum(1 for r in rep_runs if r["syntax_valid"]) / len(rep_runs) * 100
        sim = sum(1 for r in rep_runs if r["simulation_passed"]) / len(rep_runs) * 100
        syn_rates.append(syn)
        sim_rates.append(sim)

    syn_mean, syn_std = np.mean(syn_rates), np.std(syn_rates, ddof=1)
    sim_mean, sim_std = np.mean(sim_rates), np.std(sim_rates, ddof=1)
    gen_time = np.mean([r["generation_time"] for r in sub])

    print(f"{LABELS[m]:<16} {syn_mean:5.1f}% ± {syn_std:4.2f}%       "
          f"{sim_mean:5.1f}% ± {sim_std:4.2f}%        {gen_time:.2f}")
