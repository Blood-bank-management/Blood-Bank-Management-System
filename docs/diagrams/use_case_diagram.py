import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 10.9), dpi=150)
ax.set_xlim(-0.2, 16.6)
ax.set_ylim(0, 10.9)
ax.axis("off")
FONT = "DejaVu Sans"

# System boundary
ax.add_patch(Rectangle((2.6, 0.35), 10.8, 10.05, fill=False, lw=1.6, ec="#222"))
ax.text(7.5, 10.05, "Blood Bank Management System (BBMS)", ha="center",
        va="center", fontsize=14, fontweight="bold", family=FONT)

W, H = 2.55, 0.72
UC = {
    # donor
    "UC-01": (4.75, 8.62, "UC-01 Register\nas a donor"),
    "UC-03": (5.48, 7.65, "UC-03 Update\nown profile"),
    "UC-04": (5.96, 6.53, "UC-04 View own\ndonation history"),
    # requester
    "UC-06": (4.70, 2.45, "UC-06 Submit a\nblood request"),
    "UC-07": (4.70, 1.30, "UC-07 Track a\nsubmitted request"),
    # shared
    "UC-02": (7.75, 5.00, "UC-02 Log in /\nlog out"),
    "UC-05": (7.75, 3.85, "UC-05 Search blood\navailability"),
    # staff
    "UC-08": (11.44, 9.21, "UC-08 Record\na donation"),
    "UC-09": (10.67, 8.41, "UC-09 Update\ndonor eligibility"),
    "UC-10": (10.09, 7.47, "UC-10 Approve /\nreject a request"),
    "UC-11": (9.71, 6.43, "UC-11 Issue\nblood"),
    "UC-13": (10.90, 2.75, "UC-13 View\naudit log"),
    # admin
    "UC-12": (10.90, 1.25, "UC-12 Manage\nuser accounts"),
    # included
    "INV": (7.60, 8.50, "Update blood\ninventory"),
    "AUD": (7.75, 1.80, "Record audit\nentry"),
}
for k, (x, y, label) in UC.items():
    inc = k in ("INV", "AUD")
    ax.add_patch(Ellipse((x, y), W if not inc else 2.4, H, fill=True,
                         fc="#f3f6fb" if not inc else "#fbf6ee",
                         ec="#1f3b63" if not inc else "#8a5a12", lw=1.3))
    ax.text(x, y, label, ha="center", va="center", fontsize=9.5, family=FONT)


def actor(x, y, name):
    ax.add_patch(plt.Circle((x, y + 0.55), 0.17, fill=False, lw=1.5))
    ax.plot([x, x], [y + 0.38, y - 0.15], c="k", lw=1.5)
    ax.plot([x - 0.3, x + 0.3], [y + 0.2, y + 0.2], c="k", lw=1.5)
    ax.plot([x, x - 0.25], [y - 0.15, y - 0.55], c="k", lw=1.5)
    ax.plot([x, x + 0.25], [y - 0.15, y - 0.55], c="k", lw=1.5)
    ax.text(x, y - 0.8, name, ha="center", va="top", fontsize=11,
            fontweight="bold", family=FONT)


ACT = {"Donor": (0.8, 5.0), "Requester": (0.8, 1.9),
       "Staff": (15.2, 5.0), "Administrator": (15.2, 1.1)}
for n, (x, y) in ACT.items():
    actor(x, y, n)


def edge_point(k, toward):
    import math
    x, y, _ = UC[k]
    w = (W if k not in ("INV", "AUD") else 2.4) / 2
    h = H / 2
    dx, dy = toward[0] - x, toward[1] - y
    t = 1 / math.sqrt((dx / w) ** 2 + (dy / h) ** 2)
    return x + dx * t, y + dy * t


def assoc(actor_name, k):
    ax_, ay = ACT[actor_name]
    start = (ax_ + (0.35 if ax_ < 8 else -0.35), ay + 0.15)
    ex, ey = edge_point(k, start)
    ax.plot([start[0], ex], [start[1], ey], c="#333", lw=1.1)


for k in ("UC-01", "UC-03", "UC-04", "UC-02", "UC-05"):
    assoc("Donor", k)
for k in ("UC-06", "UC-07"):
    assoc("Requester", k)
for k in ("UC-08", "UC-09", "UC-10", "UC-11", "UC-13", "UC-02", "UC-05"):
    assoc("Staff", k)
assoc("Administrator", "UC-12")

# Generalization: Administrator -> Staff (hollow triangle at Staff)
ax.add_patch(FancyArrowPatch((15.2, 2.2), (15.2, 3.7),
             arrowstyle="-|>,head_width=0.45,head_length=0.6",
             mutation_scale=18, fc="white", ec="#333", lw=1.3))
ax.text(15.32, 2.95, "generalization\n(admin is also staff)", fontsize=8.5,
        family=FONT, va="center", color="#444")


def include(src, dst, lx, ly):
    sx, sy, _ = UC[src]
    dx_, dy_, _ = UC[dst]
    a = edge_point(src, (dx_, dy_))
    b = edge_point(dst, (sx, sy))
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="->", mutation_scale=14,
                 ls=(0, (4, 3)), ec="#8a5a12", lw=1.1))
    ax.text(lx, ly, "«include»", fontsize=8.5, family=FONT, color="#8a5a12",
            ha="center")


include("UC-08", "INV", 9.35, 9.0)
include("UC-11", "INV", 8.1, 7.3)
include("UC-12", "AUD", 9.25, 1.15)
include("UC-06", "AUD", 6.4, 2.35)

ax.text(7.95, 0.08,
        "UC-08 to UC-11 also «include» Record audit entry (BBMS-SR-005); those "
        "links are omitted for readability.",
        ha="center", fontsize=8.5, family=FONT, color="#555", style="italic")
plt.savefig("use_case_diagram.png",
            bbox_inches="tight", facecolor="white")
print("ok")
