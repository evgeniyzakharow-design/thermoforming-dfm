# Measuring wall thickness on a formed part

For whoever runs the machine. Five minutes, three numbers, on the first two parts of a
new job and after any change of sheet thickness, bubble time or tool.

## Why

The wall thickness is predicted from geometry and from conservation of sheet material.
Two quantities in that prediction are **not measured**: how hard the sheet grips the tool
(friction plus thermal freezing) and how big the bubble actually gets. Until a real part
is measured, the calculation shows the right shape of the answer but not the exact
numbers.

Three measurements turn the estimate into a calibrated calculation, and every job after
that starts closer.

## What to measure

Three points, top to bottom. Expected values come with the job's calculation.

| # | Where | How to reach it |
|---|---|---|
| 1 | **Top of the part** — where the sheet landed first | at the edge of any machined opening or hole on top |
| 2 | **Middle of a side wall** | at the edge of a side slot; failing that, on the offcut from that wall |
| 3 | **The thinnest spot the calculation names** — usually an outer corner near the base, but with a pre-blown bubble it moves up the wall; take the coordinates from the report | at the trim line, or at the nearest edge |

Any other accessible edge is a bonus — note where it was.

## How

Callipers on a trimmed edge (0.05 mm resolution) or a thickness gauge. Measure at the
**edge**; do not try to clamp the whole part. Three readings per point, record the mean.

## What to report

Part and revision; sheet material and thickness; bubble time; which part of the run it
was and the date; the three numbers; any extra points with their location. Then one line
on what the part looked like:

- **bubbles on the surface** — the sheet was not dry enough;
- **webs or folds** — too much sheet in that area;
- **vent dimples** — vent holes too large, or vacuum applied too early;
- **all clean** — say so, that is data too.

That last line is worth as much as the numbers.
