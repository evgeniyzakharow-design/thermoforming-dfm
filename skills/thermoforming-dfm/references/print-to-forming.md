# Turning a 3D-printed prototype into a formable part

Printing puts material wherever it is needed: any wall thickness anywhere, ribs inward,
closed volumes, zero draft. **Forming stretches one shell out of a sheet of constant
starting thickness**: you get exactly one surface, always open on one side, always
thinner than the sheet and thinner unevenly. So the conversion is not "fix the draft
angles" — it is splitting the part into what a sheet can give and what has to move to a
neighbouring part or to a machining operation.

## What survives the conversion

Fix these first, before deleting anything: they are why the part exists. Everything in
the table below is negotiable; this list is not.

- **Silhouette and overall size.** They move only where draft and radii force them, and
  that is a decision taken deliberately — draft changes an outline by design, not as a
  side effect.
- **Interfaces to neighbouring parts — yes. The fastening method — no.** What mates with
  what survives; how it is held moves: a 1 mm rebate becomes a seat plus magnets, a boss
  becomes a separate insert.
- **The stiffness requirement, not the section that delivered it.** Printing gave
  stiffness through thickness; forming gives it through ribs, steps and a slight crown.
  Carry over "this face must not oil-can", not "3 mm".
- **Functional areas and flow sections.** Geometry changes, area is held: inlet, filter
  face, outlet. Write the areas down before redrawing and check them after — a diameter
  that moves a millimetre for a tooling reason quietly changes the area it was chosen
  for, and the change is invisible in the model.
- **Hold the interface dimension, not the one you happened to draw.** Whatever meets the
  neighbouring part — an outside diameter entering a bore, a face that lands on a
  gasket — is the dimension that carries over unchanged; the wall then eats inward by
  whatever the technology gives. Compare like for like across the two revisions: a
  printed feature measured on its bore and a formed one measured on its outside are not
  the same number, and the comparison will invent a loss that is not there. At equal
  interface the thinner formed wall usually gives the *larger* free section.
- **The accurate side and the datums.** On a male tool the accurate side is the inner
  one, and every fitting dimension is re-referenced to it. Decide this before drawing, or
  half the dimensions end up on the face the process does not control.
- **Ergonomics and contact points.** What the hand grips, what the part stands on, which
  face is the visible one.
- **Brand lines and markings as intent, not as relief.** A sheet will not pull fine
  relief: logos and patterns move to an applied part or to another process — laser,
  print, a label.

**What does not survive, and is not worth defending:** the nominal wall thickness,
decorative radii below `t`, fasteners in the body of the part, tight dimensions on the
non-tool side, zero draft.

## Interfaces: ask which surface carries the function

A feature that meets a neighbouring part has two surfaces, and only one of them carries
the function: a spigot entering a bore works on its outside, a socket receiving a shaft
works on its inside, a lip sealing against a face works on the face. **Which one it is
cannot be read off the geometry.** It comes from what the neighbour does, and a printed
model carries no answer either — there both surfaces were simply drawn to nominal.

So at every interface, ask before redrawing, and do not pick one to keep moving:

1. **Which dimension has to stay the same — the outside or the inside?** That one is the
   interface and it transfers unchanged. The other is a consequence of wall thickness and
   will move.
2. **What is the clearance to the mating part?** The formed wall varies by about +-30 %,
   and if the interface is not the surface lying on the tool, that variation lands inside
   the clearance.
3. **Does the interface surface lie on the tool?** On a male tool the tool face is the
   inner surface of the part — except inside a pocket or a hole drawn into the tool,
   where it is the outer one. If the functional surface is not the tool side, either move
   the interface to the tool side or widen the clearance to swallow two wall thicknesses.

Record the answer as a named constant on that surface in the model, and add a check that
the constant still sits there. A constant that migrates to the other surface reproduces
the printed geometry under a formed name: the model reads correctly and the part does not
fit.

## Typical substitutions

| In the printed model | Why a sheet will not give it | What to do |
|---|---|---|
| Solid mass (a 10 mm thick rim, bosses, pads) | a sheet gives a shell, not a body | move the function to a separate part or to machining; keep the outline as a step or an S-transition |
| Narrow deep groove, a 3 mm wall standing 12 mm tall | the sheet cannot reach the bottom: the groove is deeper than it is wide | widen it, add draft and radii, or make it a separate part |
| Double walls, closed volume | one surface, one open side | second part, joined after forming |
| Holes, slots, windows | vacuum does not make holes; the sheet just spans them | machine after forming; check there is flat land around the hole for a nut, and that the fixture can reach the side |
| Zero draft | the part shrinks onto a male tool and grips | 5 deg on a male tool, 3 deg on a female one |
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
   For every feature that meets a neighbour, settle the interface question above before
   drawing it — one question asked beats a diameter chosen by accident.
5. **Draft and radii**, by feature height and by local draw — not one value for the part.
6. **Wall and shrinkage**: compute the wall from the layout, look at the profile and the
   thinnest spot, put the shrinkage into the tool.
7. **Measure the formed shape, not the finished part.** Slots and holes are machined
   after forming but exist in the model, and their vertical faces read as zero draft and
   undercuts. Strip them before measuring, or subtract them explicitly from the report.
8. **The first tool can be printed too.** If the prototype came off a printer, the trial
   tool can as well: 20-50 parts is enough to settle the bubble, the cycle and the wall
   before anyone mills anything (section 16 of `rules.md`). Print it hollow with vented
   ribs, and not in PLA.
9. **Run the tool and hand over a measurement sheet** so the first formed part comes back
   with three numbers (`references/measurement-sheet.md`).
