---
name: thermoforming-dfm
description: Design-for-manufacturing review of a part or a mould for vacuum forming / thermoforming — draft, radii by local draw, depth limit by method, wall thickness by Illig's law, undercuts, webbing, venting, how many parts fit a blank, and what to measure on the first formed part. Use when asked whether a part (.stl/.3mf/.step) can be vacuum formed or thermoformed, how thin the wall will get, how many parts fit a sheet, how to turn a 3D-printed design into a formable one, or for a thermoforming DFM review. Also matches the same questions in Russian: «годится ли деталь под вакуумную формовку», «какая будет толщина стенки», «сколько деталей выйдет с листа», «какой нужен уклон и радиус», «как перевести печатную модель в формуемую».
license: MIT
---

# Thermoforming DFM review

Provenance: maintained in [evgeniyzakharow-design/thermoforming-dfm](https://github.com/evgeniyzakharow-design/thermoforming-dfm).

Produce a process-specific review of a part or a mould for vacuum forming. This is a
guided review, not a certification: report what was measured, what was assumed, and what
could not be checked.

Read `references/rules.md` before comparing anything — the numbers, and the reasons
behind them, live there. For a design drawn for 3D printing, start from
`references/print-to-forming.md` instead of listing violations one by one.

## Measure, do not eyeball

Paths below are relative to this skill's directory. Use `python3` if `python` is not on
PATH, and check the environment once before trusting any number:

```bash
pip install -r requirements.txt          # trimesh, numpy, scipy
python3 scripts/vf_tool.py selftest      # must print: selftest ok
python3 scripts/vf_tool.py measure part.stl --pull z --t 3 \
        [--method male|male-bubble|plug|plug-bubble] [--blank 500x500] [--window 270x230] \
        [--blow-share 0.5 | --blow-time 0.2 | --dome 50]
```

`--clamp` is the clamped rim per side, `--bar` the width of a divider bar on the frame,
`--trim` the height added above the part for the trim line (`auto` = 12 + t). All three
default and all three are declared in the report's `assumptions`.

**Sheet thickness is required** — every wall number scales with it, so the tool will not
guess. **The method defaults to the strictest** (bare male tool, limit 0.25); giving a
bubble promotes it to 0.5, a plug assist has to be stated. Limits: male 0.25, male with a
pre-blown bubble 0.5, plug assist 1.0, plug plus bubble 1.5. The ratio is taken over the *mould* height — part plus trim allowance — because the
sheet is drawn over all of it; the part-only figure is reported beside it.

**If the user has no bubble figure, start from 60-80 % of the deepest part on the tool**
(`references/rules.md`, section 15) and give that as `--dome`. Then correct it on the
first two parts: a thin top means the bubble was too big, thin bottom corners mean it was
too small.

**The bubble is given as a height, not as a time.** `--dome` in millimetres, or
`--blow-share 0..1` to let the part's own draw pick it. Seconds are machine-specific —
the same second grows a different bubble on a different blower — so `--blow-time` only
works together with `--blow-rate` measured on that machine, and the tool refuses the
combination otherwise rather than inventing a rate. The procedure for measuring the rate
once is in `references/rules.md`.

**Two guards worth reading before the numbers.** `scale_check.units_suspect` fires when
the part is under 20 mm or over 2.5 m across — usually a file exported in centimetres or
inches, and every number downstream would be wrong by that factor. `layout[].*.fits` is
false with a `does_not_fit` line when the part plus its clearance does not go into the
window at all; the wall figures are then absent rather than optimistic.

**`sheet.draped_area_mm2` is the surface the sheet is taken to cover** — the faces a ray
along the pull can leave without hitting the part again. That is the top and the walls,
and not the base a solid stands on or the inner skin of a shell, so the same part gives
the same answer whether the file is a closed solid or a double-skinned model. It feeds F2
directly, so if it looks wrong, every wall number is wrong with it.

**Read the `assumptions` block out loud in the review.** Everything the user did not
state — blank size, clamped rim, divider bar, method, trim allowance — is listed there
with what it scales. Blank and clamp set the free sheet F1, so they move every wall
number; an unstated blank is the most common way a confident answer turns out to be for
somebody else's machine.

**Ask whether the mesh is the part or the tool.** The tool is made oversize by the
shrinkage; if the mesh already is the tool, do not add it twice. And ask what the tool is
made of: wood or MDF needs 20-25 % more draft than metal.

The tool reports facts only: height and footprint, depth-to-width against the method
limit, draft split into wall that opens and wall that **overhangs** (reverse draft locks
the part onto a male tool — that is a release failure, not a finish problem), undercuts,
projected area and the vacuum force from it, required radius by zone with the tightest
spot, layout on the blank including a webbing warning when the mould sits further than
1 H from the frame, average wall by Illig's law with its +-30 % band, the thickness
profile along the height, the bubble's share of the draw, and three points to measure on
the first formed part.

Two rules from `references/rules.md` the tool does **not** enforce — check them by hand:
bottom and three-way corners want **3 t**, where the ladder tops out at 1.5 t; and the
vent count, where the total hole area must exceed the vacuum port (count = port area
divided by 1.77 mm2 for 1.5 mm holes).

**The skill stands alone.** Draft, undercuts and projected area are measured here:
draft per face with facets on fillets tangent to the pull reported separately (they are
tessellation, not vertical walls); undercuts by counting how often a line along the pull
crosses the solid — more than twice means material overhangs material and no draft or
radius will fix it; projected area, and from it the vacuum force on the mould base.
Undercuts need a watertight mesh; if it is not watertight the field is null and says so.

**The built-in numbers are always the primary answer**, so the same part measures the
same on every machine. If the `dfm` skill of
[text-to-cad](https://github.com/earthtojake/text-to-cad) is installed alongside (or
`MOLD_TOOL` points at its `mold_tool.py`), it is run as a **silent cross-check**:
`geometry.cross_check` says `agrees: true` and nothing more, or lists the numbers that
differ. A disagreement is a signal to look at the mesh, not to average — mold_tool pools
facets by the surface they lie on, which usually makes it right about fillets tangent to
the pull. Its `pulls` command also remains the fastest way to settle a pull direction
when the obvious one is not obvious.

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
