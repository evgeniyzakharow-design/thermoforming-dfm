# thermoforming-dfm

An agent skill for **vacuum forming / thermoforming design review**: draft, radii, depth
limits, wall thickness, venting, nesting on the blank — measured from a mesh, compared
against rules that carry their sources with them.

Open DFM skills cover sheet metal, CNC machining, injection moulding and 3D printing.
Thermoforming is missing from all of them, even though it is how most large, thin,
low-volume plastic housings are actually made. This fills that gap.

## What it does

```bash
python3 skills/thermoforming-dfm/scripts/vf_tool.py measure part.stl --pull z --t 3 --blow-share 0.5
```

- **Wall thickness by Illig's law** `s = t * F1/F2` — fed by the free sheet, not by the
  part's footprint, so the answer depends on how the blank is laid out. The widespread
  "part area / footprint" shortcut is off by a factor of two on real parts.
- **Thickness profile along the height**, with the thinnest spot located: material is
  laid out along the sheet's geodesic path from the first point of contact, an idea
  borrowed from kinematic draping of composites.
- **Pre-blown bubble as a number**: areal pre-stretch `1 + (h/R)^2` and its share of the
  total draw. With a bubble, contact starts at a point and rolls outward, which is why
  the profile flattens.
- **Required radius by local draw**, not one radius for the whole part, with the tightest
  spot reported.
- **Depth limit set by the method**: 0.25 for a bare male tool, 0.5 with a bubble, 1 with
  a plug assist.
- **Nesting on the blank**: parts per sheet with and without divider bars, the wall that
  follows from each layout, and a warning when the mould sits more than 1 H from the
  frame — too much spare sheet is the first cause of webbing. `--window` models a
  reducing window and shows what it costs in wall thickness.
- **Depth limit by method**: bare male tool 0.25, with a pre-blown bubble 0.5, plug assist
  1.0, taken over the mould height rather than the part's.
- **Three points to measure on the first formed part**, with expected values — the loop
  that turns the estimate into a calibrated calculation.

- **Draft split by which way the wall leans.** Wall that overhangs locks the part onto a
  male tool no matter how smooth it is — a release failure, and the one a magnitude-only
  draft check misses. Plus undercuts and projected area measured in the same pass: facets on fillets
  tangent to the pull are reported apart from real vertical walls, undercuts come from
  counting how often a line along the pull crosses the solid, and the vacuum force on the
  mould base follows from the projected area.

Nothing else is required to run it, and the built-in numbers are always the primary
answer — the same part measures the same on every machine. If the
[`dfm`](https://github.com/earthtojake/text-to-cad) skill happens to be installed
alongside, it runs as a silent cross-check that speaks only when the two disagree. On a
test part they agree to within 3 mm2 of projected area.

## Example

A 200 x 200 x 60 box, 3 mm ABS, 500 x 500 blank, 0.15 s of pre-blow:

```
depth_to_width   0.30            limit for this method 0.5 — ok
parts per blank  1               F1 202 500 mm2, F2 226 500 mm2
average wall     2.68 mm         band 1.88 … 3.49
bubble           37.5 mm         pre-stretch 1.03, 24 % of the total draw
profile          2.81 mm on top  →  2.54 mm at the base
thinnest         2.26 mm         at a bottom corner
vacuum force     360 kgf         projected area x 9000 kgf/m2
zero draft       48 000 mm2      the box has vertical walls — draft them
```

Then measure three points on the first formed part and the estimate stops being an
estimate.

## Install

This repository is an **agent skill** (`skills/thermoforming-dfm/`) wrapped in a plugin
manifest so it can be installed in one line.

As a Claude Code plugin:

```
/plugin marketplace add evgeniyzakharow-design/thermoforming-dfm
/plugin install thermoforming-dfm
```

Or as a plain skill — copy `skills/thermoforming-dfm/` into `.claude/skills/` of your
project. Nothing in the skill depends on the plugin wrapper.

```bash
pip install -r skills/thermoforming-dfm/requirements.txt
python3 skills/thermoforming-dfm/scripts/vf_tool.py selftest
```

Python 3.11+, `trimesh`, `numpy`, `scipy` (`lxml` for .3mf). Export STEP to STL first.

## What is here

| File | What |
|---|---|
| `skills/thermoforming-dfm/SKILL.md` | the review procedure the agent follows |
| `skills/thermoforming-dfm/references/rules.md` | the rules, with the reasoning and the source behind every number |
| `skills/thermoforming-dfm/references/print-to-forming.md` | turning a 3D-printed design into a formable one: substitutions table and order of work |
| `skills/thermoforming-dfm/references/measurement-sheet.md` | one page for the shop floor: what to measure on a formed part and what to report |
| `skills/thermoforming-dfm/scripts/vf_tool.py` | the measurement tool, with a self-test |

## Honesty about limits

The thickness profile is **geometric**. Material stops flowing where it touches, and how
much depends on friction and thermal freezing — one calibration knob stands in for both,
because instrumented experiments could not separate them either. Bubble height is
`rate x time` with a machine-specific rate. Both are calibrated by measuring a real part;
that is what the measurement sheet is for. Until then: trust the shape of the profile and
where the thin spot is, not the second decimal.

## Sources

Rules are compiled from Illig/Schwarzmann, Formech's guide and technical newsletters,
Sheryshev, Arla Plast, SPE Thermoforming Quarterly, published measurements
(Karabeyoglu et al. 2017), a doctoral study of plug-assisted forming (Erner, Ecole des
Mines de Paris, 2005), the foundry pattern standard GOST 3212-92, and design guides from
injection moulding and composite tooling for cross-checks. Numbers are cited; no source
text is reproduced.

## Licence

MIT.
