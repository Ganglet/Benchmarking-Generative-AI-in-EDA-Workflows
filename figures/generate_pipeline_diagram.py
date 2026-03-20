"""
Generate pipeline flow diagram for the Benchmarking Generative AI in EDA Workflows paper.
Based on architecture.md — shows Phase 1 baseline and Phase 4+ iterative refinement paths.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

# ── colour palette ────────────────────────────────────────────────────────────
C_SPEC      = "#4A90D9"   # blue  – input / dataset
C_MODEL     = "#7B68EE"   # purple – AI inference
C_PROC      = "#5FAD56"   # green  – post-processing / repair
C_TOOL      = "#E07B39"   # orange – EDA tools
C_METRIC    = "#C0392B"   # red    – metrics / output
C_FEEDBACK  = "#8E44AD"   # violet – feedback / refinement
C_PHASE4    = "#2ECC71"   # bright green – Phase 4+ box background
C_BG        = "#FAFAFA"
C_ARROW     = "#333333"
C_DASHED    = "#888888"

def rounded_box(ax, x, y, w, h, text, color, fontsize=9, text_color="white",
                bold=False, subtext=None, radius=0.04):
    """Draw a rounded rectangle with centred text."""
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad={radius}",
                         facecolor=color, edgecolor="white",
                         linewidth=1.2, zorder=3)
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    if subtext:
        ax.text(x, y + h*0.12, text, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight=weight, zorder=4)
        ax.text(x, y - h*0.22, subtext, ha="center", va="center",
                fontsize=fontsize - 1.5, color=text_color, fontstyle="italic",
                alpha=0.85, zorder=4)
    else:
        ax.text(x, y, text, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight=weight, zorder=4)

def arrow(ax, x0, y0, x1, y1, color=C_ARROW, lw=1.5, style="->",
          dashed=False, label=None, label_side="top"):
    """Draw an arrow between two points."""
    ls = (0, (4, 3)) if dashed else "solid"
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, linestyle=ls),
                zorder=2)
    if label:
        mx, my = (x0+x1)/2, (y0+y1)/2
        dy = 0.06 if label_side == "top" else -0.07
        dx = 0.0
        # for vertical arrows, shift label to the right
        if abs(x1-x0) < 0.05:
            dx = 0.18
            dy = 0
        ax.text(mx + dx, my + dy, label, ha="center", va="center",
                fontsize=7.5, color=color, style="italic", zorder=5)


# ── figure setup ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 8))
ax.set_facecolor(C_BG)
fig.patch.set_facecolor(C_BG)
ax.set_xlim(0, 16)
ax.set_ylim(0, 7.8)
ax.axis("off")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE (horizontal, y=6.5)
# ═══════════════════════════════════════════════════════════════════════════════
MAIN_Y  = 6.5
BW, BH  = 1.55, 0.68   # box width, height
GAP     = 0.28          # gap between boxes

nodes = [
    # (centre_x,  label,             sublabel,            colour)
    (1.10,  "Task Spec",       "tasks.json",        C_SPEC),
    (2.95,  "Model Inference", "Ollama / HF",       C_MODEL),
    (4.80,  "Raw Verilog",     "AI output",         C_MODEL),
    (6.65,  "Post-Processing", "Phase 2+",          C_PROC),
    (8.50,  "Verilator",       "Syntax check",      C_TOOL),
    (10.35, "Icarus Verilog",  "Simulation",        C_TOOL),
    (12.20, "Metrics",         "EvaluationMetrics", C_METRIC),
]

# Draw boxes
for (cx, lbl, sub, col) in nodes:
    rounded_box(ax, cx, MAIN_Y, BW, BH, lbl, col,
                fontsize=9, bold=True, subtext=sub)

# Draw arrows between consecutive boxes
xs = [n[0] for n in nodes]
for i in range(len(xs)-1):
    x0 = xs[i]   + BW/2
    x1 = xs[i+1] - BW/2
    arrow(ax, x0, MAIN_Y, x1, MAIN_Y, lw=2.0)

# ── "pass" label above Icarus→Metrics arrow ──────────────────────────────────
ax.text((xs[-2]+xs[-1])/2, MAIN_Y + 0.45, "pass", ha="center",
        fontsize=8, color="#2ECC71", fontweight="bold")

# ═══════════════════════════════════════════════════════════════════════════════
# SYNTAX-FAIL FEEDBACK LOOP  (Verilator → Feedback Gen → Re-generate → model)
# ═══════════════════════════════════════════════════════════════════════════════
LOOP1_Y  = 4.7
VER_X    = xs[4]   # Verilator cx
MODEL_X  = xs[1]   # Model Inference cx

# Verilator  → down
arrow(ax, VER_X, MAIN_Y - BH/2, VER_X, LOOP1_Y + BH/2, color="#E07B39", lw=1.8,
      label="fail", label_side="right")

# Feedback generator box
rounded_box(ax, VER_X, LOOP1_Y, 1.70, BH,
            "Feedback\nGenerator", C_FEEDBACK, fontsize=8.5, bold=True)

# Horizontal arrow left → to model x
arrow(ax, VER_X - BW/2 - 0.15, LOOP1_Y,
      MODEL_X + BW/2 + 0.12, LOOP1_Y,
      color=C_FEEDBACK, lw=1.8, label="re-prompt", label_side="top")

# Small intermediate label "Phase 4+"
ax.text((VER_X + MODEL_X)/2, LOOP1_Y - 0.42, "Phase 4+ — syntax refinement loop",
        ha="center", fontsize=7.8, color=C_FEEDBACK, style="italic")

# Model Inference → up (back to MAIN_Y)
arrow(ax, MODEL_X, LOOP1_Y + BH/2, MODEL_X, MAIN_Y - BH/2,
      color=C_FEEDBACK, lw=1.8, label="regenerate")

# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATION-FAIL SEMANTIC REPAIR LOOP  (Icarus → Semantic Repair → Post-Proc)
# ═══════════════════════════════════════════════════════════════════════════════
LOOP2_Y  = 3.0
ICUS_X   = xs[5]   # Icarus cx
PROC_X   = xs[3]   # Post-Processing cx

# Phase 4+ Semantic Repair box (wider, centred between Icarus and Post-Proc)
REPAIR_X = (ICUS_X + PROC_X) / 2
REPAIR_W = 4.8
REPAIR_H = 1.35

# Icarus → down (all the way to repair box top edge — no gap)
arrow(ax, ICUS_X, MAIN_Y - BH/2, ICUS_X, LOOP2_Y + REPAIR_H/2,
      color="#E07B39", lw=1.8, label="fail", label_side="right")

repair_bg = FancyBboxPatch(
    (REPAIR_X - REPAIR_W/2, LOOP2_Y - REPAIR_H/2),
    REPAIR_W, REPAIR_H,
    boxstyle="round,pad=0.06",
    facecolor="#E8F8F0", edgecolor="#2ECC71", linewidth=1.5,
    linestyle="--", zorder=2
)
ax.add_patch(repair_bg)
ax.text(REPAIR_X, LOOP2_Y + REPAIR_H/2 - 0.18,
        "Phase 4+  —  Semantic Repair Layer",
        ha="center", va="center", fontsize=8, color="#1A7A4A",
        fontweight="bold", zorder=4)

# Three sub-boxes inside
sub_labels = [
    ("Waveform\nAnalyzer",   C_PROC),
    ("Formal\nVerifier",     C_PROC),
    ("AST\nRepair",          C_PROC),
]
sub_xs = [REPAIR_X - 1.5, REPAIR_X, REPAIR_X + 1.5]
sub_y  = LOOP2_Y - 0.12
sub_w, sub_h = 1.20, 0.55
for sx, (slbl, scol) in zip(sub_xs, sub_labels):
    rounded_box(ax, sx, sub_y, sub_w, sub_h, slbl, scol,
                fontsize=8, bold=False)
    # arrows between sub-boxes
for i in range(len(sub_xs)-1):
    arrow(ax, sub_xs[i]+sub_w/2, sub_y, sub_xs[i+1]-sub_w/2, sub_y,
          color="#2ECC71", lw=1.2)

# Arrow from repair box left → Post-Processing (up back to main)
arrow(ax, REPAIR_X - REPAIR_W/2, LOOP2_Y,
      PROC_X + BW/2 + 0.05, LOOP2_Y,
      color=C_PROC, lw=1.8, label="repaired Verilog", label_side="top")

# Post-Processing → up (back to MAIN_Y)
arrow(ax, PROC_X, LOOP2_Y, PROC_X, MAIN_Y - BH/2,
      color=C_PROC, lw=1.8, label="re-evaluate")

# ── Confidence / adaptive stopping note ──────────────────────────────────────
ax.text(REPAIR_X + REPAIR_W/2 + 0.12, LOOP2_Y,
        "ConfidenceTracker\n& Adaptive Stopping\n(max iter = 6)",
        ha="left", va="center", fontsize=7.5, color="#555555",
        style="italic", zorder=4)

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE LEGEND  (bottom row)
# ═══════════════════════════════════════════════════════════════════════════════
LEGEND_Y = 1.15

phases = [
    ("Phase 1", "Baseline few-shot prompting\n(no post-processing, no feedback)",       C_SPEC),
    ("Phase 2+", "Constrained prompts + comprehensive\npost-processing & normalisation", C_PROC),
    ("Phase 4+", "Semantic-aware iterative refinement\n(waveform, formal, AST repair)",  C_FEEDBACK),
    ("Phase 5",  "Strict mode (formal on, max_iter=6,\nlower entropy threshold)",        C_METRIC),
]

lx_start = 1.0
pw = 3.4
for i, (title, desc, col) in enumerate(phases):
    cx = lx_start + i * pw + pw/2
    rounded_box(ax, cx, LEGEND_Y, pw - 0.2, 0.80, "", col,
                fontsize=8, bold=False)
    ax.text(cx, LEGEND_Y + 0.16, title, ha="center", va="center",
            fontsize=9, color="white", fontweight="bold", zorder=5)
    ax.text(cx, LEGEND_Y - 0.16, desc, ha="center", va="center",
            fontsize=7.5, color="white", zorder=5)

ax.text(8, 0.38, "Metrics always collected: Syntax Validity · Simulation Pass Rate · Generation Time · Compile Time · Simulation Time",
        ha="center", fontsize=8, color="#444444", style="italic")
ax.text(8, 0.18, "Phase 4+ additional: Iteration Count · Confidence Entropy · Waveform Diff · Formal Equiv Status · Semantic Repair Applied",
        ha="center", fontsize=8, color="#1A7A4A", style="italic")

# ── separator line above legend ──────────────────────────────────────────────
ax.axhline(1.65, color="#CCCCCC", lw=0.8, xmin=0.03, xmax=0.97)

# ── save ─────────────────────────────────────────────────────────────────────
out = "/Users/angshumansmac/Desktop/Actual Projects/EDA/figures/pipeline_flow_diagram.png"
plt.savefig(out, dpi=200, bbox_inches="tight",
            facecolor=C_BG, edgecolor="none")
print(f"Saved: {out}")
plt.close()
