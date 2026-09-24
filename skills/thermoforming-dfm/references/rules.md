# Thermoforming design rules

Rules for designing a part and a mould for vacuum forming, with the reasoning and the
source behind each number. Where sources disagree, the disagreement is stated rather
than averaged away.

`t` is sheet thickness, `H` is mould height (or cavity depth).

## 1. Male tool or female tool

| | Male (positive, "plug") | Female (negative, cavity) |
|---|---|---|
| Accurate side | inner | outer |
| Thick spot | top face, where the sheet lands first (stays close to `t`) | rim |
| Thin spot | outer corners at the base | cavity bottom and its corners |
| Sheet texture | faces away from the tool, survives | pressed against the tool, can flatten; vent marks land on the visible face |
| Pre-blown bubble | helps a lot — evens out the walls | barely helps |
| Depth limit | see §4 | stricter without a plug assist |

A male tool is cheaper to make and hides tool marks under the sheet's own surface. If
the part's visible face must be dimensionally exact, that argues for a female tool —
then plan for vent marks on it.

## 2. Draft

- **Male tool: 5 deg or more. Female tool: 3 deg or more.** Textured faces that press
  against the tool: 5 deg minimum.
- **On short features check the gap, not the angle.** 5 deg over a 5 mm rib is only
  0.44 mm of clearance per side. The foundry pattern standard (GOST 3212-92) asks for
  0.50 mm at that height and specifies draft *by feature height*, with the absolute
  offset roughly constant at 0.4-1.2 mm. Below ~10 mm, design to the offset.
- **Wooden or MDF tooling needs more draft than metal** — the same standard adds
  20-25 % for wooden patterns.
- Zero draft is not automatically a refusal: the part will release if demoulding is
  mechanised and the surface is smooth, but the force grows. In injection moulding the
  ejection force is friction plus the shrinkage grip resolved through the angle; with a
  small angle it is essentially all friction.
- Shrinkage grips a male tool: an ABS part shrinking 0.6-0.7 % onto a 230 mm former
  closes about 0.75 mm per side. Draft has to beat that before it does anything else.

## 3. Radii

- **Default outside radius 1.5 t.** Never below `t` anywhere the sheet stretches.
- **Ladder by local draw** (the draw *at that spot*, not of the whole part). Illig gives
  below 2:1 -> 0.5 t; 2:1 to 3:1 -> 0.5 to 1 t; above 3:1 -> 1.5 t. The tool implements a
  stricter reading — below 1.2 -> 0.5 t; 1.2 to 3 -> 1 t; above 3 -> 1.5 t — taking the
  upper end of the middle band and applying the floor, because a sheet that stretches at
  all will not lay into half its own thickness.
- **Bottom corners and three-way corners: 3 t**, because the sheet arrives there last
  and is thinnest. The ladder above tops out at 1.5 t, so this one is a hand check — the
  tool will not raise it.
- A corner that will not form is usually not a radius problem first. Check venting at
  the corner before enlarging the radius: trapped air is the more common cause.
- Cross-industry agreement on the same numbers: injection moulding specifies an inside
  radius of at least 0.5 of wall thickness and an outside radius of 1.5 of wall
  thickness, with stress concentration rising sharply below a radius-to-thickness ratio
  of 0.5; composite tooling forbids a corner radius smaller than the laminate thickness
  and aims for twice it.
- Inside and outside radii are struck from the same centre, so `R_outside = R_inside + t`.

## 4. Depth

- **Depth of a cavity or a pocket: no more than 0.5 of its smallest width.**
- The limit is set by the *method*, not by the material (Sheryshev): male tool with no
  pre-stretch 0.25; **male tool with a pre-blown bubble 0.5**; with a plug assist 1;
  with both 1.5 to 2.
- Guides that quote 0.75 are usually quoting a female tool with a plug assist.
- The same wall shows up in neighbouring processes: in deep drawing of sheet metal the
  limiting first-draw coefficient is about 0.55. Every drawing process has a ceiling per
  pass; past it you need a second tool, not a better radius.

## 5. Wall thickness

**The law is conservation of sheet material, and the correct form is Illig's:**

```
s = t * F1 / F2
```

- `F1` — the free sheet: the blank minus the clamped rim. With several moulds on one
  blank, the share of the field feeding this mould.
- `F2` — everything the sheet covers when formed: the part plus the apron from the base
  of the mould out to the frame.
- Spread about the average: **+-30 %** (thin 0.7 s, thick 1.3 s).

**The common shortcut "part surface / part footprint" is not the same law.** It feeds
the draw only from the area directly above the mould, while on a male tool the whole
free sheet feeds it. On a real part the two differ by a factor of two, and the shortcut
demands a thicker sheet than the process actually needs.

**Where the material ends up:** the top lands first and stays near `t`; the wall thins
with distance travelled over the tool; outer corners at the base hold 25-40 % of `t`.
The average and the minimum are different numbers — put both on the drawing, and never
write a single "wall 3 mm".

**Multi-up layouts cut F1.** If the share of the field is smaller than the part's
surface, the part cannot be formed from that blank at all.

**A warm tool draws differently from a cold one.** The sheet stops flowing where it
touches, for two reasons at once — friction and thermal freezing — and experiments could
not separate them (Erner, Ecole des Mines de Paris, 2005). As the tool warms through a
run, freezing weakens and friction grows. If two trial parts disagree, ask about tool
temperature before touching geometry.

## 6. Spacing on the blank

| | |
|---|---|
| Between moulds (wall to wall at the base) | **1.75 H** of the taller neighbour; 1.3 H acceptable for low moulds; never below 25 mm |
| Mould to the frame | **0.5 H**, 0.3 to 1.0 H acceptable |
| With a divider bar on the frame | each cell behaves as a single mould: 0.5 H to the bar, plus the bar width |

Too close to the frame and the sheet is dragged out of the clamp; too much spare sheet
and it webs between the moulds. A reducing window is the standard cure for too much
sheet.

**Match the window shape to the part**: round windows for round and conical parts,
rectangular for rectangular ones — the thickness distribution comes out more even.

## 7. Undercuts

No undercuts, or the part must release along a tilted pull. Split tools and moving
sections exist but belong to a different class of machine.

## 8. Venting

- **Hole diameter 1 mm for sheet up to 2 mm, 1.5 mm above that.** Industrial practice on
  metal tools goes finer (0.5-0.8 mm); hole size is a compromise between evacuation speed
  and the dimple the hole leaves.
- **Spacing about 25 mm**, closer in corners, grooves, and anywhere the sheet arrives
  last. Holes belong at the deepest points and in every corner.
- **The total vent area at the tool surface must exceed the cross-section of the central
  vacuum port** (Illig's rule of thumb). It is easy to violate: a hundred 1.5 mm holes
  add up to 177 mm2, less than a single 1/2" port.
- Drill the hole shallow and relieve it from the back: 80 % of the depth with a 5-10 mm
  drill, then the small diameter through the surface. A long thin channel strangles the
  flow.
- **Raise the tool about 1 mm off the base board** (washers, strips, mesh) so air moves
  under the whole base — this beats drilling more holes around the perimeter. The
  alternative is channels milled into the underside, with the tool bolted down flat.
- Porous tooling materials (sintered aluminium, porous resins) need no holes at all.
- During a pre-blow, air speed at a vent can chill-mark the sheet; those vents are then
  piped separately and used only for evacuation.

## 9. Trim allowance and mould height

Add 12 mm plus one sheet thickness above the part for the trim line, and design the
mould so the trim line is accessible. Composite tooling uses 5-10 mm for prepreg; the
principle is the same — the formed part is always open on one side and always needs
trimming.

## 10. Shrinkage and tolerances

- ABS shrinks 0.6-0.7 % after forming; the mould is made larger by that amount.
- Most of it happens during cooling on the tool, the rest over the next hours; parts
  measured straight off the machine will not match parts measured the next day.
- Thermoforming is not a precision process: simple parts hold roughly IT17. Design the
  part so critical fits are machined after forming, not formed.

## 11. Webbing

Webs come from too much sheet in one place — a tall mould next to another, sharp vertical
corners, moulds too close together. Cures, cheapest first: a reducing window; more spacing;
draft and radii; angled fillets or an apron at 45 deg around the base to take up the excess;
a slower vacuum; and deliberately placing a rib where the fold would otherwise land.

## 12. Drying

**ABS: 80 C, one hour per millimetre of thickness.** A 3 mm sheet needs 3 hours.
Sources range from 1 to 2 hours per millimetre; one hour is the newer figure and the
feedback signal is unambiguous — **bubbles on the surface during heating mean the sheet
was not dry enough.** Above 80 C is pointless; the glass transition of ABS is 100 C.

## 13. Tool surface

- **Not a mirror.** An even light roughness over the body, gloss only on the top edges
  the sheet slides across. Too little friction thins the base of the part, because the
  sheet slips instead of gripping where it lands.
- Injection moulding's SPI scale gives a language for this: body around C-3 to D-1
  (Ra 0.63-1.0 um, stone-finished or bead blasted), sliding edges B-1 to B-3
  (Ra 0.05-0.32 um).
- A competing view exists: reducing roughness improves contact and shortens the cycle by
  5-9 % (Sheryshev). That optimises the cycle; the roughness advice above optimises the
  draw. Pick knowingly.

## 14. Cooling

- Contact is one-sided, so cooling takes about **four times longer** than a part cooled
  from both sides. That is the method, not a fault of the tool.
- Demould an amorphous sheet at about `Tg - 20`, so roughly 80 C for ABS.
- Tool temperature is the main lever on cycle time: warming the tool from 20 to 70 C
  roughly doubles the cooling time of a 3 mm ABS sheet.
- Contact conductance is not perfect but is high enough not to dominate: at about
  2000 W/(m2K) the Biot number of a 3 mm sheet is ~35 and the contact adds only a few
  per cent to the cooling time; with poor contact (~230 W/(m2K)) it adds half again.

## 15. Pre-blown bubble

- The bubble does not change the average wall — it redistributes it, and it flattens the
  profile along the height dramatically.
- Areal pre-stretch of a spherical cap of height `h` over a window of radius `R` is
  `1 + (h/R)^2`; its share of the total draw is `ln(pre) / ln(F2/F1)`.
- With a bubble, first contact happens at a *point* inside the dome and rolls outward,
  much later than a flat sheet landing on the whole top face.
- **Height is the physical quantity; seconds are not.** The calculation needs a bubble
  height. Machines are set in seconds, and the same second gives a different height on
  every machine — blower, window size, sheet thickness and sheet temperature all change
  it, and the growth is not linear. So work in millimetres and convert only for your own
  machine.
- **Measuring your machine's growth rate, once.** Heat a sheet as you would for forming,
  blow with the table down, cut the blow at a known time, and measure the apex height
  above the frame with a rule or a rod across the frame. Two or three points across your
  working range (say 0.2 / 0.4 / 0.6 s) give the rate in mm/s near that range. Machines
  with a photocell skip this entirely — they limit the bubble by measured height, and
  manufacturers themselves call manual time settings sloppy.
- Whatever the rate says, it is a starting value: correct it in 0.1 s steps over two
  trial parts — thin top means the bubble was too big, thin bottom corners mean it was
  too small.

## Sources

Rules are compiled from: Illig/Schwarzmann, *Thermoforming* (radius ladder, the wall
law, venting, wrinkle control); Formech's vacuum forming guide and technical newsletters
(spacing, reducing windows, tooling materials, mounting, cast resin tools); Sheryshev,
*Thermoforming of polymer sheets and films* and *Modern features of thermoforming*
(method-dependent depth limits, one-sided cooling, thickness distribution along the
profile); Arla Plast and SPE Thermoforming Quarterly (materials and defects);
Karabeyoglu et al., 2017 (measured wall thickness against geometric prediction);
Erner, Ecole des Mines de Paris, 2005 (friction and thermal freezing, contact
conductance); GOST 3212-92 (draft by feature height and pattern material); injection
moulding and composite tooling design guides for the cross-industry checks.

Numbers are cited; no source text is reproduced here.
