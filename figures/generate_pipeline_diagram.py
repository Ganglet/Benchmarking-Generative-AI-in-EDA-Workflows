"""
Generate pipeline flow diagram for the Benchmarking Generative AI in EDA Workflows paper.
Based on architecture.md — shows Phase 1 baseline and Phase 4+ iterative refinement paths.
Journal quality: all text 11pt+, generous spacing, readable at 100%.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   13,
})

# ── colour palette ────────────────────────────────────────────────────────────
C_SPEC     = "#2166AC"   # blue      — input / dataset
C_MODEL    = "#6A3D9A"   # purple    — AI inference
C_PROC     = "#33A02C"   # green     — post-processing / repair
C_TOOL     = "#E07B39"   # orange    — EDA tools
C_METRIC   = "#B2182B"   # red       — metrics / output
C_FEEDBACK = "#7B2D8B"   # violet    — feedback / refinement
C_BG       = "#FFFFFF"
C_ARROW    = "#333333"

def rounded_box(ax, x, y, w, h, text, color, fontsize=13, text_color="white",
                bold=True, subtext=None, radius=0.05):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad={radius}",
                         facecolor=color, edgecolor="white",
                         linewidth=1.5, zorder=3)
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    if subtext:
        ax.text(x, y + h * 0.15, text, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight=weight, zorder=4)
        ax.text(x, y - h * 0.22, subtext, ha="center", va="center",
                fontsize=fontsize - 1.5, color=text_color, fontstyle="italic",
                alpha=0.88, zorder=4)
    else:
        ax.text(x, y, text, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight=weight, zorder=4)

def arrow(ax, x0, y0, x1, y1, color=C_ARROW, lw=2.0, dashed=False,
          label=None, label_side="top"):
    ls = (0, (5, 3)) if dashed else "solid"
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, linestyle=ls,
                                mutation_scale=16),
                zorder=2)
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dy = 0.22 if label_side == "top" else -0.25
        dx = 0.0
        if abs(x1 - x0) < 0.1:   # vertical arrow
            dx = 0.32
            dy = 0
        ax.text(mx + dx, my + dy, label, ha="center", va="center",
                fontsize=12, color=color, fontstyle="italic", zorder=5,
                fontweight="bold")

# ── figure setup ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(24, 15))
ax.set_facecolor(C_BG)
fig.patch.set_facecolor(C_BG)
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis("off")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE  (horizontal, y = MAIN_Y)
# ══════════════════════════════════════════════════════════════════════════════
MAIN_Y = 10.4
BW, BH = 1.75, 0.90

nodes = [
    (1.10,  "Task Spec",       "tasks.json",       C_SPEC),
    (2.95,  "Model Inference", "Ollama / HF",      C_MODEL),
    (4.80,  "Raw Verilog",     "AI output",        C_MODEL),
    (6.65,  "Post-Processing", "Phase 2+",         C_PROC),
    (8.50,  "Verilator",       "Syntax check",     C_TOOL),
    (10.35, "Icarus Verilog",  "Simulation",       C_TOOL),
    (12.20, "Metrics",         "EvalMetrics",      C_METRIC),
]

for (cx, lbl, sub, col) in nodes:
    rounded_box(ax, cx, MAIN_Y, BW, BH, lbl, col,
                fontsize=13, bold=True, subtext=sub)

xs = [n[0] for n in nodes]
for i in range(len(xs) - 1):
    arrow(ax, xs[i] + BW/2, MAIN_Y, xs[i+1] - BW/2, MAIN_Y, lw=2.2)

ax.text((xs[-2] + xs[-1]) / 2, MAIN_Y + 0.62, "pass",
        ha="center", fontsize=13, color=C_PROC, fontweight="bold")

# ══════════════════════════════════════════════════════════════════════════════
# SYNTAX-FAIL FEEDBACK LOOP  (Verilator → Feedback Gen → Model)
# ══════════════════════════════════════════════════════════════════════════════
LOOP1_Y = 8.1
VER_X   = xs[4]
MODEL_X = xs[1]

arrow(ax, VER_X, MAIN_Y - BH/2, VER_X, LOOP1_Y + BH/2,
      color=C_TOOL, lw=2.0, label="fail", label_side="right")

rounded_box(ax, VER_X, LOOP1_Y, 1.90, BH,
            "Feedback\nGenerator", C_FEEDBACK, fontsize=13, bold=True)

arrow(ax, VER_X - BW/2 - 0.18, LOOP1_Y,
      MODEL_X + BW/2 + 0.15, LOOP1_Y,
      color=C_FEEDBACK, lw=2.0, label="re-prompt", label_side="top")

ax.text((VER_X + MODEL_X) / 2, LOOP1_Y - 0.55,
        "Phase 4+  —  syntax refinement loop",
        ha="center", fontsize=12.5, color=C_FEEDBACK, fontstyle="italic")

arrow(ax, MODEL_X, LOOP1_Y + BH/2, MODEL_X, MAIN_Y - BH/2,
      color=C_FEEDBACK, lw=2.0, label="regenerate")

# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION-FAIL SEMANTIC REPAIR LOOP  (Icarus → Semantic Repair → Post-Proc)
# ══════════════════════════════════════════════════════════════════════════════
LOOP2_Y  = 5.6
ICUS_X   = xs[5]
PROC_X   = xs[3]
REPAIR_X = (ICUS_X + PROC_X) / 2
REPAIR_W = 5.0
REPAIR_H = 1.6

arrow(ax, ICUS_X, MAIN_Y - BH/2, ICUS_X, LOOP2_Y + REPAIR_H/2,
      color=C_TOOL, lw=2.0, label="fail", label_side="right")

repair_bg = FancyBboxPatch(
    (REPAIR_X - REPAIR_W/2, LOOP2_Y - REPAIR_H/2),
    REPAIR_W, REPAIR_H,
    boxstyle="round,pad=0.07",
    facecolor="#EEF8F2", edgecolor="#33A02C", linewidth=2.0,
    linestyle="--", zorder=2
)
ax.add_patch(repair_bg)
ax.text(REPAIR_X, LOOP2_Y + REPAIR_H/2 - 0.22,
        "Phase 4+  —  Semantic Repair Layer",
        ha="center", va="center", fontsize=13, color="#1A6E2E",
        fontweight="bold", zorder=4)

sub_labels = [
    ("Waveform\nAnalyzer", C_PROC),
    ("Formal\nVerifier",   C_PROC),
    ("AST\nRepair",        C_PROC),
]
sub_xs  = [REPAIR_X - 1.6, REPAIR_X, REPAIR_X + 1.6]
sub_y   = LOOP2_Y - 0.18
sub_w   = 1.30
sub_h   = 0.68
for sx, (slbl, scol) in zip(sub_xs, sub_labels):
    rounded_box(ax, sx, sub_y, sub_w, sub_h, slbl, scol, fontsize=12.5, bold=False)
for i in range(len(sub_xs) - 1):
    arrow(ax, sub_xs[i] + sub_w/2, sub_y, sub_xs[i+1] - sub_w/2, sub_y,
          color="#33A02C", lw=1.4)

arrow(ax, REPAIR_X - REPAIR_W/2, LOOP2_Y,
      PROC_X + BW/2 + 0.08, LOOP2_Y,
      color=C_PROC, lw=2.0, label="repaired Verilog", label_side="top")

arrow(ax, PROC_X, LOOP2_Y, PROC_X, MAIN_Y - BH/2,
      color=C_PROC, lw=2.0, label="re-evaluate")

ax.text(REPAIR_X + REPAIR_W/2 + 0.16, LOOP2_Y + 0.22,
        "ConfidenceTracker",
        ha="left", va="center", fontsize=12.5, color="#555555",
        fontstyle="italic", zorder=4)
ax.text(REPAIR_X + REPAIR_W/2 + 0.16, LOOP2_Y - 0.12,
        "Adaptive Stopping (max iter = 6)",
        ha="left", va="center", fontsize=12.5, color="#555555",
        fontstyle="italic", zorder=4)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE LEGEND  (bottom row)
# ══════════════════════════════════════════════════════════════════════════════
LEGEND_Y = 2.0
phases = [
    ("Phase 1",  "Baseline few-shot prompting\n(no post-processing, no feedback)",        C_SPEC),
    ("Phase 2+", "Constrained prompts + comprehensive\npost-processing & normalisation",  C_PROC),
    ("Phase 4+", "Semantic-aware iterative refinement\n(waveform, formal, AST repair)",   C_FEEDBACK),
    ("Phase 5",  "Strict mode — formal on, max iter = 6\nlower entropy threshold",        C_METRIC),
]
pw      = 3.5
lx_start = 0.75
for i, (title, desc, col) in enumerate(phases):
    cx = lx_start + i * pw + pw / 2
    rounded_box(ax, cx, LEGEND_Y, pw - 0.22, 0.95, "", col, fontsize=11, bold=False)
    ax.text(cx, LEGEND_Y + 0.22, title, ha="center", va="center",
            fontsize=13.5, color="white", fontweight="bold", zorder=5)
    ax.text(cx, LEGEND_Y - 0.20, desc, ha="center", va="center",
            fontsize=12, color="white", zorder=5)

ax.axhline(2.76, color="#CCCCCC", lw=1.0, xmin=0.02, xmax=0.98)

ax.text(8, 0.98,
        "Metrics always collected: Syntax Validity · Simulation Pass Rate · Generation Time · "
        "Compile Time · Simulation Time",
        ha="center", fontsize=12.5, color="#444444", fontstyle="italic")
ax.text(8, 0.54,
        "Phase 4+ additional: Iteration Count · Confidence Entropy · Waveform Diff · "
        "Formal Equiv. Status · Semantic Repair Applied",
        ha="center", fontsize=12.5, color="#1A6E2E", fontstyle="italic")

# ── save ──────────────────────────────────────────────────────────────────────
out_orig = "/Users/angshumansmac/Desktop/Actual Projects/EDA/figures/pipeline_flow_diagram.png"
plt.savefig(out_orig, dpi=200, bbox_inches="tight", facecolor=C_BG, edgecolor="none")
print(f"Saved: {out_orig}")

out_dir = "/Users/angshumansmac/Desktop/Actual Projects/EDA/Research_Paper/My Paper/New_figures"
os.makedirs(out_dir, exist_ok=True)
for ext in ("png", "pdf"):
    dpi  = 600 if ext == "png" else None
    path = os.path.join(out_dir, f"fig6_pipeline_diagram.{ext}")
    plt.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=C_BG, edgecolor="none")
    print(f"Saved journal {ext.upper()}: {path}")
plt.close()
