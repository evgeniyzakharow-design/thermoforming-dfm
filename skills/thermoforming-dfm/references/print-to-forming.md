# Turning a 3D-printed prototype into a formable part

Printing puts material wherever it is needed: any wall thickness anywhere, ribs inward,
closed volumes, zero draft. **Forming stretches one shell out of a sheet of constant
starting thickness**: you get exactly one surface, always open on one side, always
thinner than the sheet and thinner unevenly. So the conversion is not "fix the draft
angles" — it is splitting the part into what a sheet can give and what has to move to a
neighbouring part or to a machining operation.

## Typical substitutions

| In the printed model | Why a sheet will not give it | What to do |
|---|---|---|
| Solid mass (a 10 mm thick rim, bosses, pads) | a sheet gives a shell, not a body | move the function to a separate part or to machining; keep the outline as a step or an S-transition |
| Narrow deep groove, a 3 mm wall standing 12 mm tall | the sheet cannot reach the bottom: the groove is deeper than it is wide | widen it, add draft and radii, or make it a separate part |
| Double walls, closed volume | one surface, one open side | second part, joined after forming |
| Holes, slots, windows | vacuum does not make holes; the sheet just spans them | machine after forming; check there is flat land around the hole for a nut, and that the fixture can reach the side |
| Zero draft | the part shrinks onto a male tool and grips | 5 deg on a male tool, 3 deg on a female one; below 10 mm of height work to a clearance of 0.5 mm per side |
| Sharp edge, decorative R1 | the sheet will not lay into it, and the corner becomes a stress raiser | radius by local draw, 1.5 t by default, never below t |
| Undercuts | the tool will not come out | remove, split into two parts, or change the pull direction |
| Ribs inward | on a male tool the inner surface is the tool face | ribs outward, preferably along the walls |
| Constant 3 mm wall | formed wall varies: ~0.77 t at the top, down to 0.5 t in the bottom corner | anything needing thickness (threads, magnet pockets, press fits) goes to a separate part or is machined to the measured thickness |
| Closed bottom | forming is always open on one side | separate bottom part; plan the trim line |
| Nominal dimensions | shrinkage 0.6-0.7 % | the tool is made oversize, not the part |

## Order of work

1. **Decide male or female.** Everything else follows: where the accurate side is, which
   way ribs point, where it will be thin.
2. **Check the two ceilings before drawing anything.** Depth to smallest width no more
   than 0.5, and the layout on the blank — how many parts fit and what share of the free
   sheet feeds one mould. A part that fails here cannot be rescued by detailing.
3. **Delete what a sheet cannot give** — masses, narrow grooves, undercuts, closed
   volumes, holes — using the table above.
4. **Redistribute the functions.** Load paths, threads, accurate thicknesses usually
   belong to the neighbouring part, and that assembly is designed here, not afterwards.
5. **Draft and radii**, by feature height and by local draw — not one value for the part.
6. **Wall and shrinkage**: compute the wall from the layout, look at the profile and the
   thinnest spot, put the shrinkage into the tool.
7. **Measure the formed shape, not the finished part.** Slots and holes are machined
   after forming but exist in the model, and their vertical faces read as zero draft and
   undercuts. Strip them before measuring, or subtract them explicitly from the report.
8. **Run the tool and hand over a measurement sheet** so the first formed part comes back
   with three numbers (`references/measurement-sheet.md`).
