"""Draw the 4×4 toy example of flow direction and flow accumulation for the slides."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

FIG = Path(__file__).resolve().parents[2] / "assets" / "abm-gis" / "img" / "dem_d8_idea.svg"
TEAL = "#006c66"

DEM = np.array([
    [9, 8, 7, 8],
    [8, 6, 5, 6],
    [7, 5, 3, 4],
    [8, 6, 2, 1],
])
NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def lowest_neighbour(r, c):
    """The neighbour with the steepest drop, or None if every neighbour is higher."""
    best, target = 0.0, None
    for dr, dc in NEIGHBOURS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < 4 and 0 <= cc < 4:
            drop = (DEM[r, c] - DEM[rr, cc]) / np.hypot(dr, dc)
            if drop > best:
                best, target = drop, (rr, cc)
    return target


targets = {(r, c): lowest_neighbour(r, c) for r in range(4) for c in range(4)}
accumulation = np.ones((4, 4), dtype=int)
for r, c in sorted(targets, key=lambda cell: -DEM[cell]):
    if targets[(r, c)]:
        accumulation[targets[(r, c)]] += accumulation[r, c]


def draw_grid(ax, values, title, shade):
    ax.imshow(shade, cmap="Blues", vmin=0, vmax=shade.max() * 1.3)
    for r in range(4):
        for c in range(4):
            ax.text(c, r - 0.05, values[r, c], ha="center", va="center", fontsize=22,
                    fontweight="bold", color="#222")
            if targets[(r, c)]:
                rr, cc = targets[(r, c)]
                ax.annotate("", xy=(c + 0.42 * (cc - c), r + 0.42 * (rr - r)),
                            xytext=(c + 0.18 * (cc - c), r + 0.18 * (rr - r)),
                            arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=2.5))
    ax.set_xticks(np.arange(-0.5, 4), minor=True)
    ax.set_yticks(np.arange(-0.5, 4), minor=True)
    ax.grid(which="minor", color="#b8c9c8", lw=2)
    ax.set_axisbelow(False)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_title(title, fontsize=16, loc="left", color=TEAL, fontweight="bold")


fig, (left, right) = plt.subplots(1, 2, figsize=(11, 5.6))
draw_grid(left, DEM, "① Elevation → flow direction", np.zeros((4, 4)))
draw_grid(right, accumulation, "② Count the cells that drain here", np.log(accumulation))
fig.tight_layout()
fig.savefig(FIG, bbox_inches="tight", pad_inches=0.15, facecolor="white")
print(accumulation)
