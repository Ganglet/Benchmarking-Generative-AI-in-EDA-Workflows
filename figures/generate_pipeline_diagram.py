"""
Architecture diagram — compact 5-node pipeline with clean feedback routing.
Generated at IEEE full text-width (7.2 in). Fonts at 9 pt appear correctly in PDF.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches
import os

matplotlib.rcParams.update({"font.family": "DejaVu Sans"})

# ── palette ───────────────────────────────────────────────────────────────────
C_INPUT  = "#1565C0"   # deep blue     — dataset
C_LLM    = "#4A148C"   # deep purple   — LLM
C_PROC   = "#1B5E20"   # deep green    — post-proc
C_EVAL   = "#BF360C"   # deep red-orange — evaluation
C_OUT    = "#004D40"   # deep teal     — results
C_LOOP1  = "#283593"   # indigo        — syntax loop
C_LOOP2  = "#1A237E"   # deep navy     — sim loop
C_BG     = "#FFFFFF"
C_ARR    = "#1A1A1A"   # near-black

# ── helpers ───────────────────────────────────────────────────────────────────
def node(ax, x, y, w, h, line1, line2, color, fs=9):
    ax.add_patch(FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.05",
        facecolor=color, edgecolor="white", linewidth=1.4, zorder=4))
    ax.text(x, y + h * 0.16, line1, ha="center", va="center",
            fontsize=fs, color="white", fontweight="bold", zorder=5)
    ax.text(x, y - h * 0.24, line2, ha="center", va="center",
            fontsize=fs - 1.5, color="white", fontstyle="italic",
            alpha=0.90, zorder=5)

def h_arrow(ax, x0, x1, y, color=C_ARR, lw=1.6, label=None):
    """Horizontal arrow with optional centred label."""
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, mutation_scale=9), zorder=3)
    if label:
        ax.text((x0 + x1) / 2, y + 0.13, label,
                ha="center", va="bottom", fontsize=7.5,
                color=color, fontweight="bold", fontstyle="italic", zorder=6)

def v_arrow(ax, x, y0, y1, color=C_ARR, lw=1.4):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, mutation_scale=9), zorder=3)

def polyline(ax, xs, ys, color, lw=1.4):
    ax.plot(xs, ys, color=color, lw=lw, zorder=2, solid_capstyle="round")

# ── canvas ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.set_xlim(-0.3, 10.3)
ax.set_ylim(0, 7)
ax.set_facecolor(C_BG)
fig.patch.set_facecolor(C_BG)
ax.axis("off")

BW, BH = 1.65, 0.88

# ── 5 pipeline nodes at y = 5.6 ───────────────────────────────────────────────
NY = 5.6
NX = [0.95, 2.85, 4.75, 6.65, 8.55]   # spacing = 1.9, gap = 0.25

node(ax, NX[0], NY, BW, BH, "Task",          "Dataset",         C_INPUT)
node(ax, NX[1], NY, BW, BH, "LLM",           "Inference",       C_LLM)
node(ax, NX[2], NY, BW, BH, "Post-",         "Processing",      C_PROC)
node(ax, NX[3], NY, BW, BH, "Code",          "Evaluation",      C_EVAL)
node(ax, NX[4], NY, BW, BH, "Results &",     "Metrics",         C_OUT)

# forward arrows
for i in range(len(NX) - 1):
    h_arrow(ax, NX[i] + BW/2, NX[i+1] - BW/2, NY, lw=1.8)

# ── phase badges above nodes ───────────────────────────────────────────────────
badges = [
    (NX[0],             C_INPUT, "#DCEEFB", "Phase 1"),
    ((NX[1]+NX[2])/2,   C_PROC,  "#D6EFD8", "Phase 2+"),
    ((NX[3]+NX[4])/2,   C_EVAL,  "#FBE9E7", "Phase 4+"),
]
for bx, fc, bg, txt in badges:
    ax.text(bx, NY + BH/2 + 0.30, txt,
            ha="center", va="center", fontsize=8, color=fc, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.20", facecolor=bg,
                      edgecolor=fc, linewidth=0.9, zorder=6))

# ── "pass" label on last arrow ─────────────────────────────────────────────────
ax.text((NX[3]+NX[4])/2, NY + 0.60, "pass",
        ha="center", fontsize=8, color=C_PROC, fontweight="bold")

# ── FEEDBACK LOOP A — Syntax / Sim Fail → Post-Processing ─────────────────────
# Path: down from Code Evaluation right edge → right margin → below → left →
#       up to Post-Processing bottom
LOOP_A_X_R  = NX[3] + BW/2        # right edge of Code Evaluation  ≈ 7.48
LOOP_A_X_L  = NX[2] - BW/2        # left edge of Post-Processing   ≈ 3.92
LOOP_A_X_MR = 9.80                 # right margin rail
LOOP_A_Y_B  = 4.20                 # vertical rail y (below main row)

# draw the L-shaped path (no arrowhead on the lines)
polyline(ax,
         [LOOP_A_X_R, LOOP_A_X_MR, LOOP_A_X_MR, LOOP_A_X_L],
         [NY,          NY,           LOOP_A_Y_B,   LOOP_A_Y_B],
         color=C_LOOP1, lw=1.4)
# final arrow segment — up into Post-Processing
v_arrow(ax, LOOP_A_X_L, LOOP_A_Y_B, NY - BH/2, color=C_LOOP1, lw=1.4)

# label on right rail
ax.text(LOOP_A_X_MR + 0.10, (NY + LOOP_A_Y_B)/2,
        "Syntax fail\n→ fix & retry",
        ha="left", va="center", fontsize=8, color=C_LOOP1,
        fontweight="bold", fontstyle="italic")

# ── FEEDBACK LOOP B — Persistent Fail → Re-prompt LLM ───────────────────────
LOOP_B_X_R  = NX[3] + BW/2        # same start point
LOOP_B_X_L  = NX[1] - BW/2        # left edge of LLM Inference   ≈ 2.02
LOOP_B_X_RL = -0.10                # left margin rail
LOOP_B_Y_B  = 3.30                 # lower rail (below loop A)

polyline(ax,
         [LOOP_B_X_R, LOOP_B_X_R, LOOP_B_X_RL, LOOP_B_X_RL, LOOP_B_X_L],
         [NY - BH/2,  LOOP_B_Y_B,  LOOP_B_Y_B,  NY,           NY],
         color=C_LOOP2, lw=1.4)
# arrowhead into LLM
h_arrow(ax, LOOP_B_X_RL, LOOP_B_X_L, NY, color=C_LOOP2, lw=1.4)

# label on left rail
ax.text(LOOP_B_X_RL - 0.10, (NY + LOOP_B_Y_B)/2,
        "Persistent fail\n→ re-prompt LLM",
        ha="right", va="center", fontsize=8, color=C_LOOP2,
        fontweight="bold", fontstyle="italic")

# ── "fail" labels on the downward drops ───────────────────────────────────────
ax.text(LOOP_A_X_MR - 0.08, NY - 0.22, "fail",
        ha="right", va="top", fontsize=8, color=C_LOOP1,
        fontweight="bold", fontstyle="italic")
ax.text(NX[3] + BW/2 + 0.08, NY - 0.44, "fail",
        ha="left", va="top", fontsize=8, color=C_LOOP2,
        fontweight="bold", fontstyle="italic")

# ── legend / footer strip ─────────────────────────────────────────────────────
ax.axhline(1.10, color="#BDBDBD", lw=0.6, xmin=0.02, xmax=0.98)

legend_items = [
    mpatches.Patch(color=C_INPUT, label="Dataset / Input"),
    mpatches.Patch(color=C_LLM,   label="LLM Inference"),
    mpatches.Patch(color=C_PROC,  label="Post-Processing"),
    mpatches.Patch(color=C_EVAL,  label="EDA Evaluation"),
    mpatches.Patch(color=C_OUT,   label="Results / Metrics"),
]
ax.legend(handles=legend_items, loc="lower center",
          bbox_to_anchor=(0.5, 0.005), ncol=5, frameon=False,
          fontsize=7.5, handlelength=1.0, handletextpad=0.4, columnspacing=0.8)

# ── metrics caption ────────────────────────────────────────────────────────────
ax.text(5.0, 0.63,
        "Collected metrics: Syntax Validity · Simulation Pass Rate · Generation Time · "
        "Iteration Count · Confidence Entropy",
        ha="center", va="center", fontsize=7.5, color="#424242", fontstyle="italic")

# ── save ──────────────────────────────────────────────────────────────────────
out_dir  = "/Users/angshumansmac/Desktop/Actual Projects/EDA/Research_Paper/My Paper/New_figures"
out_orig = "/Users/angshumansmac/Desktop/Actual Projects/EDA/figures/pipeline_flow_diagram.png"
os.makedirs(out_dir, exist_ok=True)

plt.savefig(out_orig, dpi=200, bbox_inches="tight", facecolor=C_BG)
print(f"Saved preview: {out_orig}")

for ext in ("png", "pdf"):
    path = os.path.join(out_dir, f"fig6_pipeline_diagram.{ext}")
    plt.savefig(path, dpi=(600 if ext == "png" else None),
                bbox_inches="tight", facecolor=C_BG)
    print(f"Saved: {path}")
plt.close()
