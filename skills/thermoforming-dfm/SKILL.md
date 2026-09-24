---
name: thermoforming-dfm
description: Design-for-manufacturing review of a part or a mould for vacuum forming / thermoforming — draft, radii by local draw, depth limit by method, wall thickness by Illig's law, undercuts, webbing, venting, how many parts fit a blank, and what to measure on the first formed part. Use when asked whether a part (.stl/.3mf/.step) can be vacuum formed or thermoformed, how thin the wall will get, how many parts fit a sheet, how to turn a 3D-printed design into a formable one, or for a thermoforming DFM review.
---

# Thermoforming DFM review

Produce a process-specific review of a part or a mould for vacuum forming. This is a
guided review, not a certification: report what was measured, what was assumed, and what
could not be checked.

Read `references/rules.md` before comparing anything — the numbers, and the reasons
behind them, live there. For a design drawn for 3D printing, start from
`references/print-to-forming.md` instead of listing violations one by one.

## Measure, do not eyeball

```bash
python scripts/vf_tool.py measure part.stl --pull z --t 3 [--blank 500x500] [--blow-time 0.4]
```

The tool reports facts only: height and footprint, depth-to-width against the method
limit, required radius by zone with the tightest spot, layout on the blank, average wall
by Illig's law with its +-30 % band, the thickness profile along the height, the bubble's
share of the draw, and three points to measure on the first formed part.

**Geometry facts — draft, undercuts, projected area — come from `mold_tool.py` of the
`dfm` skill** ([earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad)),
which this tool calls when that skill is installed alongside, or when `MOLD_TOOL` points
at it. There is no second implementation of those numbers here: two of them would drift
apart silently. Without it the report says `NOT MEASURED` for those fields and the
forming maths still runs.

If the pull direction is not obvious, settle it with `mold_tool.py pulls <mesh>` before
anything else.

A screenshot supports a suspicion; it is not a measurement. Script parameters describe
intent — verify the exported mesh matches them before treating a number as evidence.

## Before measuring

**Strip post-forming features.** Slots, holes and windows are machined after forming but
exist in the model, and their vertical faces read as zero draft and as undercuts. Measure
the shape that will actually be formed, or subtract those areas explicitly.

## What the tool cannot tell you

- **The wall profile is a geometric estimate.** Material stops flowing where it touches,
  and how much it stops depends on friction and thermal freezing, which are not modelled
  — they sit in one calibration knob (`grip`, default 1.0). Until a formed part is
  measured, trust the shape of the profile and the location of the thin spot, not the
  second decimal.
- **Bubble height** is `rate x time` with a machine-specific rate; calibrate it.
- **Modelled radii** are estimated from mesh dihedral angles — coarse. Confirm on a
  section or in CAD.
- Measured thickness at the last point of contact can come out thicker than the starting
  sheet; geometry will not predict that.

## Report

1. How the part was read: male or female tool, pull direction, which side is accurate.
2. Failures in order of severity: will not release (zero draft, undercut) -> will not
   form (depth, radii, venting) -> wall too thin -> layout.
3. For each failure, a concrete fix with numbers ("step draft 0 deg -> 3 deg"), not a
   restatement of the rule.
4. Layout: parts per blank, with and without a divider bar.
5. Assumptions and unmeasured items, stated plainly.
6. The three measurement points for the first formed part, with expected values.
