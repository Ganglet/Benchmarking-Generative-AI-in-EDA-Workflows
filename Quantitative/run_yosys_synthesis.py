"""
Lightweight Yosys synthesis check for Benchmark 12 generated Verilog.

For each run (model × task × rep), finds the final iteration's .v file, runs
Yosys generic synthesis, and reports:
  - synthesizable (bool, based on Yosys exit code)
  - cell_count (post-synth cells)
  - wire_count (interconnect proxy)
  - logic_levels (depth proxy from abc -fast)

Output: results/Benchmark_12_Synthesis/synthesis_metrics.json
"""
import json, os, re, subprocess, tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT     = Path("/Users/angshumansmac/Desktop/Actual Projects/EDA")
B12_DIR  = ROOT / "results" / "Benchmark_12_Results"
RUNS     = B12_DIR / "individual_runs.json"
OUT_DIR  = ROOT / "results" / "Benchmark_12_Synthesis"
OUT_FILE = OUT_DIR / "synthesis_metrics.json"
TIMEOUT  = 30   # seconds per Yosys invocation

# Yosys script template — generic synthesis flow, no liberty file needed
YOSYS_SCRIPT = """
read_verilog -sv "{vfile}"
hierarchy -auto-top
proc
opt
fsm
opt
memory
opt
techmap
opt
abc -fast
stat
"""

# Map JSON model names → directory prefix
MODEL_DIR = {
    "Llama-3-8B-Large":      "Llama_3_8B_Large",
    "StarCoder2-7B-Medium":  "StarCoder2_7B_Medium",
    "TinyLlama-1.1B-Small":  "TinyLlama_1.1B_Small",
}


def find_final_v(model_name, task_id, rep):
    """Locate the .v file from the highest attempt in this rep."""
    base = B12_DIR / f"{MODEL_DIR[model_name]}_{task_id}" / f"rep{rep}"
    if not base.exists():
        return None
    attempts = sorted(
        [d for d in base.iterdir() if d.is_dir() and d.name.startswith("attempt_")],
        key=lambda p: int(p.name.split("_")[1])
    )
    if not attempts:
        return None
    vfiles = list(attempts[-1].glob("*.v"))
    # exclude testbenches
    vfiles = [v for v in vfiles if "tb" not in v.name.lower()]
    return vfiles[0] if vfiles else None


def parse_stat(stdout):
    """Extract cell/wire counts and AND-gate count from Yosys stat + abc output."""
    cells = wires = and_gates = None

    # Yosys stat block format: "        N cells" (indented, after === module ===)
    # Find the last occurrence (top module summary)
    cell_matches = re.findall(r"^\s+(\d+)\s+cells\s*$", stdout, re.MULTILINE)
    if cell_matches:
        cells = int(cell_matches[-1])
    wire_matches = re.findall(r"^\s+(\d+)\s+wires\s*$", stdout, re.MULTILINE)
    if wire_matches:
        wires = int(wire_matches[-1])
    # ABC RESULTS:               AND cells:        N
    m = re.search(r"ABC RESULTS:\s+AND cells:\s+(\d+)", stdout)
    if m:
        and_gates = int(m.group(1))

    return cells, wires, and_gates


def synthesize(run):
    """Run Yosys synthesis on one (model, task, rep) tuple. Return result dict."""
    model = run["model_name"]
    task  = run["task_id"]
    rep   = run["repetition"]

    result = {
        "task_id": task,
        "model_name": model,
        "repetition": rep,
        "syntax_valid_orig": run["syntax_valid"],
        "simulation_passed_orig": run["simulation_passed"],
        "synthesizable": False,
        "cell_count": None,
        "wire_count": None,
        "and_gate_count": None,
        "error": None,
    }

    vfile = find_final_v(model, task, rep)
    if vfile is None:
        result["error"] = "no_v_file"
        return result

    # Write yosys script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ys", delete=False) as ys:
        ys.write(YOSYS_SCRIPT.format(vfile=str(vfile)))
        script_path = ys.name

    try:
        proc = subprocess.run(
            ["yosys", "-s", script_path],
            capture_output=True, text=True, timeout=TIMEOUT
        )
        combined = proc.stdout + proc.stderr
        if proc.returncode == 0:
            result["synthesizable"] = True
            cells, wires, ands = parse_stat(combined)
            result["cell_count"] = cells
            result["wire_count"] = wires
            result["and_gate_count"] = ands
        else:
            # Capture short error
            err_lines = [l for l in combined.splitlines() if "ERROR" in l]
            result["error"] = err_lines[0][:200] if err_lines else "non_zero_exit"
    except subprocess.TimeoutExpired:
        result["error"] = "timeout"
    except Exception as e:
        result["error"] = f"exception: {e}"
    finally:
        os.unlink(script_path)

    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(RUNS) as f:
        runs = json.load(f)

    # Only synthesize syntax-valid runs (others would always fail).
    # But we still record the rate for the full set.
    candidates = [r for r in runs if r.get("syntax_valid")]
    print(f"Total runs: {len(runs)}  |  Syntax-valid (will synthesize): {len(candidates)}")

    results = []
    done = 0
    # Use 4 workers — Yosys is single-threaded per invocation
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(synthesize, r): r for r in candidates}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            if done % 20 == 0:
                synth_yes = sum(1 for x in results if x["synthesizable"])
                print(f"  [{done:>3}/{len(candidates)}]  synthesizable: {synth_yes}")

    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    total_runs    = len(runs)
    total_synth   = sum(1 for r in results if r["synthesizable"])
    synth_rate    = total_synth / total_runs * 100
    print(f"\nFinal: {total_synth}/{total_runs} runs synthesizable ({synth_rate:.1f}%)")
    print(f"Saved: {OUT_FILE}")


if __name__ == "__main__":
    main()
