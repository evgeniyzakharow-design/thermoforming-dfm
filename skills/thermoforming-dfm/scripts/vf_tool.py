#!/usr/bin/env python3
"""Mesh facts for vacuum forming / thermoforming. Measurements only, no verdicts —
the rules to compare against live in SKILL.md and references/rules.md.

  vf_tool.py measure part.stl [--pull z] [--t 3] [--clamp 25] [--trim auto|<mm>]
                              [--blank 500x500] [--bar 25] [--dome <mm> | --blow-time <s>]
  vf_tool.py selftest

Dependencies: trimesh, numpy, scipy (+ lxml for .3mf).
Geometry facts (draft, undercuts, projected area) are delegated to `mold_tool.py`
from the `dfm` skill of earthtojake/text-to-cad when it is installed next to this
skill; without it those fields are reported as not measured.
"""
import argparse
import pathlib
import subprocess, json, math, os, sys, tempfile
import numpy as np
import trimesh

AXES = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}
# Depth limit is set by the method, not by the material (Sheryshev's ladder)
METHOD_DEPTH = {"male": 0.25, "male-bubble": 0.5, "plug": 1.0, "plug-bubble": 1.5}

VACUUM_KGF_PER_M2 = 9000.0   # practical pull of a working vacuum: ~0.9 bar over the footprint


def axis(s):
    sign = -1.0 if s.startswith("-") else 1.0
    return np.array(AXES[s.lstrip("+-")], float) * sign


def blank_size(s):
    w, _, h = s.lower().partition("x")
    return (float(w), float(h))


def fits(win, dim, edge, gap):
    """How many moulds of size `dim` fit across a window `win`, keeping `edge` to the
    clamp frame and `gap` between neighbours."""
    free = win - 2 * edge
    return 0 if free < dim else int((free + gap) // (dim + gap))


def cells(win, dim, edge, bar):
    """Same, but with divider bars of width `bar` between moulds: each cell behaves as
    a single mould with `edge` to the frame or to the bar on each side."""
    n = 0
    while (win - n * bar) / (n + 1) >= dim + 2 * edge:
        n += 1
    return n


def wall_illig(win, parts, one_side, foot, t):
    """Average wall by Illig's law: s = t * F1/F2.

    F1 is the *free sheet* — the blank minus the clamped rim, divided by the number of
    moulds on it. F2 is everything the sheet ends up covering: the part plus the apron
    from the base of the mould out to the frame. Spread is +-30 %: thin spots 0.7*s,
    thick 1.3*s.

    The common alternative — part surface / part footprint — silently assumes the sheet
    is fed only by the area directly above the mould. On a male tool the whole free
    sheet feeds the draw, and the two answers differ by a factor of two on real parts.
    """
    if parts < 1:
        return None
    f1 = win[0] * win[1] / parts
    f2 = one_side + max(f1 - foot, 0.0)
    if f2 <= 0 or f1 <= 0:
        return None
    s = t * f1 / f2
    return {"avg_mm": round(s, 2), "band_mm": [round(0.7 * s, 2), round(1.3 * s, 2)],
            "F1_mm2": round(f1), "F2_mm2": round(f2)}


def layout(w, l, hm, clamp, bar, blanks, one_side=None, t=3.0, window=None):
    """How many moulds fit per blank, and the wall that follows from that layout.

    Spacing rule: gap between moulds 1.75 * mould height (1.3 * H as a hard minimum,
    never below 25 mm), distance to the frame 0.5 * H (0.3 * H minimum). Crowding the
    frame pulls the sheet out of the clamp; leaving too much sheet webs it.
    """
    out = []
    foot = w * l
    for bw, bl in blanks:
        win = tuple(window) if window else (bw - 2 * clamp, bl - 2 * clamp)
        row = {"blank_mm": [bw, bl], "window_mm": list(win),
               "window_source": "given" if window else "blank minus clamped rim"}
        for name, gap, edge in (("recommended", max(1.75 * hm, 25), 0.5 * hm),
                                ("minimum", max(1.3 * hm, 25), 0.3 * hm)):
            n = max(fits(win[0], a, edge, gap) * fits(win[1], b, edge, gap) for a, b in ((w, l), (l, w)))
            # how much spare sheet is actually left round the moulds: too much webs (rules 6, 11)
            spare = min((win[i] - (max(fits(win[i], d, edge, gap), 1) * d +
                                   (max(fits(win[i], d, edge, gap), 1) - 1) * gap)) / 2.0
                        for i, d in ((0, w), (1, l)))
            row[name] = {"parts": n, "gap_mm": round(gap, 1), "edge_mm": round(edge, 1),
                         "actual_edge_mm": round(spare, 1),
                         "actual_edge_in_H": round(spare / hm, 2) if hm else None}
            if hm and spare > hm:
                row[name]["webbing_risk"] = (
                    "mould sits %.1f H from the frame, outside the 0.3-1.0 H band: too much spare "
                    "sheet is the first cause of webbing. Use a reducing window about %d x %d mm "
                    "(--window), or take up the excess with a 45 deg apron round the base"
                    % (spare / hm, round(w + hm), round(l + hm)))
            if one_side:
                row[name]["wall_illig"] = wall_illig(win, n, one_side, foot, t)
            grid = max(((cells(win[0], a, edge, bar), cells(win[1], b, edge, bar)) for a, b in ((w, l), (l, w))),
                       key=lambda c: c[0] * c[1])
            row[name]["with_divider"] = {"parts": grid[0] * grid[1], "cells": list(grid), "bar_mm": bar}
            if one_side:
                row[name]["with_divider"]["wall_illig"] = wall_illig(win, grid[0] * grid[1], one_side, foot, t)
        out.append(row)
    return out


def local_draw(mesh, p, patch=12.0):
    """Local areal draw per face: neighbourhood area divided by its projection.

    A flat patch gives 1, a leaning wall 1/cos, a vertical one runs away. This is the
    geometric estimate (GEA): a trend, not a thickness measurement.
    """
    from scipy.spatial import cKDTree
    c, a = mesh.triangles_center, mesh.area_faces
    proj = a * np.abs(mesh.face_normals @ p)
    tree = cKDTree(c)
    ratio = np.ones(len(a))
    for i, nb in enumerate(tree.query_ball_point(c, patch)):
        sp_ = proj[nb].sum()
        if sp_ <= 1e-9:                      # neighbourhood held vertical faces only
            nb = tree.query_ball_point(c[i], patch * 3)
            sp_ = proj[nb].sum()
        ratio[i] = min(a[nb].sum() / sp_, 10.0) if sp_ > 1e-9 else 10.0
    return ratio                             # 10 is a ceiling: "draw is well above 3:1"


def required_radius(ratio, t):
    """Radius ladder by local draw (Illig), with a hard floor.

    draw below 1.2  -> 0.5 * t   (almost no stretching there)
    1.2 .. 3        -> 1.0 * t   (floor: never below sheet thickness where it stretches)
    above 3         -> 1.5 * t
    """
    return np.where(ratio < 1.2, 0.5 * t, np.where(ratio <= 3.0, 1.0 * t, 1.5 * t))


def local_radius(mesh):
    """Rough fillet radius at a face, from its neighbours: for two adjacent faces with
    dihedral angle a and centre distance d, the arc radius is about d / a."""
    fa, ang = mesh.face_adjacency, mesh.face_adjacency_angles
    c = mesh.triangles_center
    d = np.linalg.norm(c[fa[:, 0]] - c[fa[:, 1]], axis=1)
    ok = (ang > 1e-3) & (d > 0.05)           # coincident centres are tessellation noise
    r = np.where(ok, d / np.maximum(ang, 1e-9), np.inf)
    out = np.full(len(mesh.faces), np.inf)
    np.minimum.at(out, fa[:, 0], r)
    np.minimum.at(out, fa[:, 1], r)
    return out


def zones(mesh, p, t, patch=12.0):
    """Required radius by zone, and places where the modelled radius is smaller.

    Faces steeper than 70 deg to the pull are excluded: their projection is nearly zero,
    so the geometric draw ratio explodes, while the material actually arrived sideways
    from the apron. For those the default radius applies, not the ladder.
    """
    ratio = local_draw(mesh, p, patch)
    need = required_radius(ratio, t)
    have = local_radius(mesh)
    a = mesh.area_faces
    cosp = np.abs(mesh.face_normals @ p)
    shallow = cosp > math.sin(math.radians(20))
    by_need = {}
    for v in sorted(set(np.round(need[shallow], 2))):
        by_need["%.1f" % v] = round(float(a[shallow & np.isclose(need, v)].sum()))
    tight = shallow & (have < need * 0.9) & np.isfinite(have)
    worst = None
    if tight.any():
        i = int(np.argmin(np.where(tight, have / need, np.inf)))
        worst = {"at_mm": [round(float(x), 1) for x in mesh.triangles_center[i]],
                 "local_draw": round(float(ratio[i]), 2),
                 "required_mm": round(float(need[i]), 2),
                 "estimated_mm": round(float(have[i]), 2)}
    return {
        "patch_mm": patch,
        "shallow_area_mm2": round(float(a[shallow].sum())),
        "wall_area_mm2": round(float(a[~shallow].sum())),
        "max_local_draw_shallow": round(float(ratio[shallow].max()), 2) if shallow.any() else None,
        "area_by_required_radius_mm2": by_need,
        "tight_area_mm2": round(float(a[tight].sum())),
        "worst_spot": worst,
        "note": ("Shallow faces only (up to 70 deg to the pull). Modelled radius is estimated from "
                 "mesh dihedral angles and is coarse — confirm on a section or in CAD."),
    }


def blow_fraction(dome_mm, span_mm, f2_over_f1):
    """Share of the total draw taken by the pre-blown bubble.

    The free sheet blown up over the window is a spherical cap: for height h over a
    window of radius R its area is pi*(R^2 + h^2), so the areal pre-stretch is
    1 + (h/R)^2. That stretch happens before the sheet touches anything and spreads
    evenly, so its share of the total draw is ln(pre) / ln(F2/F1).
    """
    if not dome_mm or dome_mm <= 0 or span_mm <= 0 or not f2_over_f1 or f2_over_f1 <= 1:
        return 0.0, 1.0
    R = span_mm / 2.0
    pre = 1.0 + (dome_mm / R) ** 2
    # pre > total draw means the bubble alone stretches the sheet more than the part
    # needs: the share clamps at 1 and the caller is told the bubble is oversized
    return max(0.0, min(1.0, math.log(pre) / math.log(f2_over_f1))), pre


def geodesic_from_contact(mesh, p, tol=None, dome=0.0):
    """Distance ALONG THE SURFACE from the first-contact zone to every face.

    Borrowed from kinematic draping of composites: material does not drop straight down,
    it travels over the tool from wherever contact started. Hence a geodesic distance
    (Dijkstra over mesh edges) rather than height.

    Where contact starts depends on pre-blow:
      * no bubble — the flat sheet lands on the whole top plateau at once;
      * with a bubble — the tool enters the stretched dome from below and contact starts
        at a point, then rolls outwards. So the seed is a small spot at the apex.
    """
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    v = mesh.vertices
    along = v @ p
    h = float(along.max() - along.min())
    tol = tol if tol else max(0.5, 0.005 * h)
    if dome > 0:
        apex = v[int(np.argmax(along))]
        spot = max(3.0, 0.02 * h)
        seeds = np.where(np.linalg.norm(v - apex, axis=1) <= spot)[0]
    else:
        seeds = np.where(along >= along.max() - tol)[0]
    if not len(seeds):
        seeds = np.array([int(np.argmax(along))])
    e = mesh.edges_unique
    w = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1)
    rows = np.concatenate([e[:, 0], e[:, 1]])
    cols = np.concatenate([e[:, 1], e[:, 0]])
    g = csr_matrix((np.concatenate([w, w]), (rows, cols)), shape=(len(v), len(v)))
    d = dijkstra(g, indices=seeds, min_only=True)
    if not np.isfinite(d).all():             # disconnected mesh pieces
        d[~np.isfinite(d)] = np.nanmax(d[np.isfinite(d)]) if np.isfinite(d).any() else 0.0
    return d[mesh.faces].mean(axis=1)


def thickness_profile(mesh, p, t, s_avg, bands=8, grip=1.0, blow=0.0):
    """Where the material ends up: laid out along the sheet's path, not by height.

    Illig's law gives one average and a +-30 % band; it does not say where the thin spot
    is. Here the part's material budget (s_avg * area) is distributed over faces with a
    weight 1 / (1 + grip * (1 - blow) * g), where g is the geodesic path from first
    contact, normalised to its maximum.

    `grip` is the calibration knob. It holds two effects at once: friction of the sheet
    on the tool and thermal freezing on contact. They do not need separating — Erner
    (Ecole des Mines de Paris, 2005) showed experimentally that both localise the
    deformation the same way and could not be told apart; the same work gives a hot-sheet
    friction coefficient of 0.6 to 1.5, rising with interface temperature, which is why a
    warm tool draws differently from a cold one. Calibrate against a formed part.

    `blow` (0..1) is the share of the draw already taken by the bubble.

    The physical alternative is to simulate the process: a mass-spring sheet, vacuum as a
    force along the normal proportional to triangle area, collision against the tool, and
    thickness as the local area ratio. What such a model still needs is friction and
    thermal freezing — without them it predicts a more even wall than reality gives.

    Geometry gives a trend, not truth: at the last point of contact a real measurement can
    read thicker than the starting sheet (Karabeyoglu et al., 2017).
    """
    a = mesh.area_faces
    c = mesh.triangles_center @ p
    top, bot = float(c.max()), float(c.min())
    h = top - bot
    if h <= 0 or not s_avg or s_avg <= 0:
        return None
    path = geodesic_from_contact(mesh, p, dome=(1.0 if blow > 0 else 0.0))
    gmax = float(path.max()) or 1.0
    w = 1.0 / (1.0 + grip * (1.0 - blow) * (path / gmax))
    budget = s_avg * float(a.sum())
    denom = float((a * w).sum())
    if denom <= 0:
        return None
    s_face = np.minimum(budget / denom * w, t)
    edges = np.linspace(bot, top, bands + 1)
    rows = []
    for i in range(bands):
        lo, hi = edges[i], edges[i + 1]
        m = (c >= lo) & (c < hi) if i < bands - 1 else (c >= lo)
        ai = float(a[m].sum())
        if ai <= 0:
            continue
        si = float((s_face[m] * a[m]).sum() / ai)
        rows.append({"from_mm": round(lo - bot, 1), "to_mm": round(hi - bot, 1),
                     "area_mm2": round(ai), "path_mm": round(float(path[m].mean()), 1),
                     "wall_mm": round(si, 2), "worst_in_band_mm": round(si * 0.7, 2)})
    rows.reverse()                           # read top-down, from first contact to the base
    i_thin = int(np.argmin(s_face))
    return {"grip": grip, "blow": round(blow, 2), "bands": rows, "max_path_mm": round(gmax, 1),
            "thinnest": {"at_mm": [round(float(x), 1) for x in mesh.triangles_center[i_thin]],
                         "wall_mm": round(float(s_face[i_thin]), 2),
                         "path_mm": round(float(path[i_thin]), 1)},
            "note": ("worst_in_band is 0.7 of the band average (Illig's +-30 % band). "
                     "grip is not calibrated until a formed part is measured.")}


def measure_request(prof):
    """Three points to measure on the first formed part — the ones that calibrate the model."""
    if not prof or not prof.get("bands"):
        return None
    b = prof["bands"]
    mid = b[len(b) // 2]
    thin = prof["thinnest"]
    return {
        "why": "calibrates grip and bubble height; until then the profile is a geometric estimate",
        "how": "callipers on a trimmed edge or a thickness gauge, 0.05 mm resolution",
        "points": [
            {"where": "top of the part — the first-contact zone", "expected_mm": b[0]["wall_mm"]},
            {"where": "wall at %s-%s mm above the base" % (mid["from_mm"], mid["to_mm"]),
             "expected_mm": mid["wall_mm"]},
            {"where": "thinnest bottom corner", "expected_mm": thin["wall_mm"],
             "at_mm": thin["at_mm"]},
        ],
    }


def curved_faces(mesh, smooth_deg=20.0):
    """Faces that lie on a curved surface rather than a flat one.

    A face on a plane meets its neighbours at ~0 deg; on a fillet or a cylinder at a few
    degrees; across a sharp edge at much more. Faces in between are the curved ones. This
    matters for draft: a curved surface is tangent to the pull along a *line*, so the
    facets near that line read as zero draft no matter how fine the mesh is — that is
    tessellation, not a vertical wall.
    """
    fa, ang = mesh.face_adjacency, np.degrees(mesh.face_adjacency_angles)
    worst = np.zeros(len(mesh.faces))
    np.maximum.at(worst, fa[:, 0], ang)
    np.maximum.at(worst, fa[:, 1], ang)
    return (worst > 0.5) & (worst < smooth_deg)


def undercut_grid(mesh, p, pitch=2.0):
    """Where the solid is re-entrant along the pull, by counting ray crossings.

    A shape can be drawn off the tool along `p` only if a line in that direction enters
    and leaves the solid once. More than one interval means material overhangs material —
    an undercut — and no radius or draft will fix it. Resolution is the grid pitch.
    """
    p = p / np.linalg.norm(p)
    u = np.cross(p, [1, 0, 0] if abs(p[0]) < 0.9 else [0, 1, 0]); u /= np.linalg.norm(u)
    w = np.cross(p, u)
    v = mesh.vertices
    a1, a2, ap = v @ u, v @ w, v @ p
    g1 = np.arange(a1.min() + pitch / 2, a1.max(), pitch)
    g2 = np.arange(a2.min() + pitch / 2, a2.max(), pitch)
    G1, G2 = np.meshgrid(g1, g2)
    origins = (G1.ravel()[:, None] * u + G2.ravel()[:, None] * w + (ap.min() - 10) * p)
    _, idx_ray, _ = mesh.ray.intersects_location(origins, np.tile(p, (len(origins), 1)),
                                                 multiple_hits=True)
    counts = np.bincount(idx_ray, minlength=len(origins))
    return {"pitch_mm": pitch,
            "footprint_mm2": round(float((counts > 0).sum() * pitch ** 2)),
            "undercut_area_mm2": round(float((counts > 2).sum() * pitch ** 2)),
            "note": "rays crossing the solid more than twice; resolution is the grid pitch"}


def builtin_facts(mesh, p, wall_limit=45.0, zero_tol=0.5, pitch=2.0):
    """Draft, projected area and undercuts computed here, with no outside tool."""
    n, a = mesh.face_normals, mesh.area_faces
    along = n @ p
    cosp = np.abs(along)
    draft = np.degrees(np.arcsin(np.clip(cosp, 0, 1)))
    wall = cosp < math.sin(math.radians(wall_limit))
    curved = curved_faces(mesh)
    zero = wall & (draft < zero_tol)
    # which way a wall leans. On a male tool pulled along +p a wall whose outward normal
    # tilts along +p opens as the part lifts; one tilting the other way overhangs, and the
    # part locks on however smooth the tool is.
    lean = np.degrees(np.arcsin(np.clip(along, -1, 1)))
    opening = wall & (lean > zero_tol)
    reverse = wall & (lean < -zero_tol)
    proj = float((a * cosp).sum()) / 2.0      # exact for a draw-able shape (no self-shadowing)
    uc = undercut_grid(mesh, p, pitch) if mesh.is_watertight else None
    return {
        "draft": {
            "wall_area_mm2": round(float(a[wall].sum())),
            "opening_area_mm2": round(float(a[opening].sum())),
            "reverse_draft_area_mm2": round(float(a[reverse].sum())),
            "worst_reverse_deg": round(float(-lean[reverse].min()), 2) if reverse.any() else 0.0,
            "zero_draft_wall_area_mm2": round(float(a[zero & ~curved].sum())),
            "zero_draft_on_curved_mm2": round(float(a[zero & curved].sum())),
            "min_wall_draft_deg": round(float(draft[wall].min()), 2) if wall.any() else None,
            "histogram_mm2": {k: round(float(a[wall & (draft >= lo) & (draft < hi)].sum()))
                              for k, lo, hi in (("0-1", 0, 1), ("1-2", 1, 2), ("2-3", 2, 3),
                                                ("3-5", 3, 5), ("5-10", 5, 10), ("10-45", 10, 45.01))},
            "note": ("reverse_draft_area is wall that overhangs: the part grows wider away from the "
                     "opening, so it locks onto a male tool — that is a release failure, not a "
                     "finish problem. zero_draft_on_curved is tessellation of a fillet tangent to "
                     "the pull, not a vertical wall: it scales with mesh density and is not a defect"),
        },
        "undercuts": uc,
        "projection": {"projected_area_mm2": round(proj),
                       "note": "sum of |n.p| * area / 2; exact unless the shape shadows itself"},
    }


def geom_facts(path, pull_spec):
    """Draft, undercuts and projected area — from `mold_tool.py` of the `dfm` skill.

    That tool separates facets lying on a curved surface merely tangent to the pull from
    genuine vertical walls, and checks units and watertightness. Keeping a second
    implementation of the same numbers here would only let the two drift apart silently.
    Set MOLD_TOOL to point at it, or install this skill next to `dfm`.
    """
    env = os.environ.get("MOLD_TOOL")
    here = pathlib.Path(__file__).resolve()
    cands = [pathlib.Path(env)] if env else []
    cands += [here.parents[2] / "dfm" / "scripts" / "mold_tool.py",
              here.parents[1] / "dfm" / "scripts" / "mold_tool.py"]
    tool = next((c for c in cands if c.exists()), None)
    if not (path and tool):
        return None
    try:
        out = subprocess.run([sys.executable, str(tool), "measure", str(path), "--pull", pull_spec],
                             capture_output=True, timeout=300)
        return json.loads(out.stdout)
    except Exception:
        return None


def measure(mesh, pull, t, clamp, trim, bar=25.0, dome=0.0, blow_rate=250.0,
            blanks=((500, 500),), path=None, pull_spec="z", method="male-bubble",
            window=None, blow_share=None):
    p = pull / np.linalg.norm(pull)
    v = mesh.vertices
    along = v @ p
    h = float(along.max() - along.min())
    u = np.cross(p, [1, 0, 0] if abs(p[0]) < 0.9 else [0, 1, 0]); u /= np.linalg.norm(u)
    w_ = np.cross(p, u)
    fw, fl = sorted([float(np.ptp(v @ u)), float(np.ptp(v @ w_))])
    a = mesh.area_faces
    bi = builtin_facts(mesh, p)
    gf = geom_facts(path, pull_spec) or {}
    trim_mm = (12 + t) if trim == "auto" else float(trim)
    hm = h + trim_mm
    one_side = float(a.sum() / 2)            # shell model: one side is about half the area
    lim = METHOD_DEPTH.get(method, 0.5)
    lay = layout(fw, fl, hm, clamp, bar, blanks, one_side, t, window)
    rec = lay[0]["recommended"]
    win = lay[0]["window_mm"]
    s_avg = (rec.get("wall_illig") or {}).get("avg_mm")
    wi = rec.get("wall_illig") or {}
    f2f1 = (wi.get("F2_mm2") / wi.get("F1_mm2")) if wi.get("F1_mm2") else None
    if blow_share and f2f1 and not dome:          # pick the bubble from the share it should take
        dome = (min(win) / 2.0) * math.sqrt(max(math.exp(blow_share * math.log(f2f1)) - 1.0, 0.0))
    bfrac, pre = blow_fraction(dome, min(win), f2f1)
    prof_nb = thickness_profile(mesh, p, t, s_avg)
    prof_dome = thickness_profile(mesh, p, t, s_avg, blow=bfrac) if dome else None
    proj = bi["projection"]["projected_area_mm2"]
    return {
        "pull_axis": p.round(3).tolist(),
        "height_along_pull_mm": round(h, 2),
        "footprint_mm": [round(fw, 2), round(fl, 2)],
        "depth_to_width": round(hm / fw, 3),
        "depth_limit": {"method": method, "max": lim,
                        "ok": hm / fw <= lim,
                        "part_only": round(h / fw, 3),
                        "note": ("ratio is taken over the MOULD height (part + trim allowance), because "
                                 "the sheet is drawn over all of it; part_only is the part alone. "
                                 "Limits by method: male 0.25, male with a pre-blown bubble 0.5, "
                                 "plug assist 1.0, plug plus bubble 1.5-2")},
        "watertight": bool(mesh.is_watertight),
        "geometry": {
            "source": "built-in" + (" + mold_tool cross-check" if gf else ""),
            "draft": bi["draft"],
            "undercuts": bi["undercuts"],
            "projection": bi["projection"],
            "vacuum_force_kgf": round(proj / 1e6 * VACUUM_KGF_PER_M2),
            "mold_tool": ({"draft": gf.get("draft"), "undercuts": gf.get("undercuts"),
                           "projection": gf.get("projection"),
                           "note": "from the dfm skill; prefer these draft numbers — it pools facets by "
                                   "the surface they lie on. A disagreement with the built-in figures "
                                   "above is worth looking into, not averaging"} if gf else None),
            "note": ("vacuum_force is the projected area times 9000 kgf/m2 — size the mould base and "
                     "its fixings for that. Measure the FORMED shape: slots and holes that are milled "
                     "after forming read as zero draft and undercuts."),
        },
        "sheet": {"t_mm": t, "one_side_area_mm2": round(one_side),
                  "note": "wall comes from layout[].wall_illig: s = t*F1/F2, so it depends on the layout"},
        "mold": {"trim_allowance_mm": trim_mm, "mold_height_mm": round(hm, 2)},
        "zones": zones(mesh, p, t),
        "layout": lay,
        "profile_no_blow": prof_nb,
        "profile_with_bubble": prof_dome,
        "measure_after_forming": (measure_request(prof_nb) if (f2f1 and pre > f2f1)
                                  else measure_request(prof_dome or prof_nb)),
        "bubble": {"height_mm": round(dome, 1), "rate_mm_s": blow_rate,
                   "pre_stretch": round(pre, 2), "share_of_draw": round(bfrac, 2),
                   "oversized": bool(f2f1 and pre > f2f1),
                   "note": ("pre_stretch above the total draw F2/F1 means the bubble alone stretches "
                            "the sheet more than this part needs: the top comes out thin and the profile "
                            "flattens artificially. Shorten the blow time." if (f2f1 and pre > f2f1)
                            else "bubble takes this share of the draw before the sheet touches the tool")}
        if dome else None,
    }


def selftest():
    box = trimesh.creation.box([100, 100, 50])
    tmp = pathlib.Path(tempfile.gettempdir()) / "vf_selftest_box.stl"
    box.export(tmp)
    r = measure(box, axis("z"), t=3, clamp=20, trim=0, bar=50, path=tmp, pull_spec="z")
    assert r["height_along_pull_mm"] == 50 and r["footprint_mm"] == [100, 100]
    assert r["depth_to_width"] == 0.5 and r["depth_limit"]["ok"]
    assert len(r["measure_after_forming"]["points"]) == 3
    wi = r["layout"][0]["recommended"]["wall_illig"]
    assert wi and 0 < wi["avg_mm"] <= r["sheet"]["t_mm"], wi
    assert wi["band_mm"][0] < wi["avg_mm"] < wi["band_mm"][1]
    g = r["geometry"]                        # box 100x100x50: four vertical walls, no undercut
    assert g["draft"]["zero_draft_wall_area_mm2"] == 20000, g["draft"]
    assert g["draft"]["zero_draft_on_curved_mm2"] == 0, g["draft"]
    assert g["projection"]["projected_area_mm2"] == 10000 and g["vacuum_force_kgf"] == 90, g
    assert g["undercuts"]["undercut_area_mm2"] == 0, g["undercuts"]
    if g["mold_tool"]:                       # both paths measured the same wall
        assert abs(g["mold_tool"]["draft"]["zero_draft_wall_area_mm2"] -
                   g["draft"]["zero_draft_wall_area_mm2"]) < 1, g
    assert g["draft"]["reverse_draft_area_mm2"] == 0, g["draft"]   # straight box: no overhang
    assert r["depth_limit"]["method"] == "male-bubble" and r["depth_limit"]["max"] == 0.5
    assert r["depth_limit"]["part_only"] == 0.5 and r["depth_to_width"] == 0.5  # trim=0 here
    strict = measure(box, axis("z"), t=3, clamp=20, trim=0, bar=50, path=tmp, method="male")
    assert not strict["depth_limit"]["ok"], "0.5 must fail the bare male-tool limit of 0.25"
    # a reducing window changes the free sheet, so it changes the wall
    red = measure(box, axis("z"), t=3, clamp=20, trim=0, bar=50, window=(200, 200))
    assert red["layout"][0]["window_mm"] == [200, 200]
    assert red["layout"][0]["recommended"]["wall_illig"]["avg_mm"] < wi["avg_mm"], "smaller window, thinner wall"
    assert r["layout"][0]["recommended"].get("webbing_risk"), "460 window round a 100 mm box is too much sheet"
    assert not red["layout"][0]["recommended"].get("webbing_risk"), red["layout"][0]["recommended"]
    # picking the bubble by share reproduces that share
    bs = measure(box, axis("z"), t=3, clamp=20, trim=0, bar=50, blow_share=0.5)
    assert abs(bs["bubble"]["share_of_draw"] - 0.5) < 0.02, bs["bubble"]
    # a mushroom cannot be drawn along z: the cap overhangs the stem by 100x100 - 40x40
    cap = trimesh.creation.box([100, 100, 20]); cap.apply_translation([0, 0, 40])
    stem = trimesh.creation.box([40, 40, 40]); stem.apply_translation([0, 0, 10])
    uc = undercut_grid(trimesh.util.concatenate([cap, stem]), axis("z"))
    assert uc["undercut_area_mm2"] == 1600, uc
    assert r["layout"][0]["recommended"]["parts"] == 4, r["layout"][0]
    assert fits(100, 200, 0, 10) == 0 and cells(300, 304, 0, 0) == 0
    assert r["layout"][0]["recommended"]["with_divider"]["cells"] == [2, 2]
    flat = trimesh.creation.box([100, 100, 1]).subdivide_to_size(6.0)
    zf = zones(flat, axis("z"), t=3)
    assert zf["max_local_draw_shallow"] < 1.6 and list(zf["area_by_required_radius_mm2"]) == ["1.5"], zf
    zb = zones(box.subdivide_to_size(6.0), axis("z"), t=3)
    assert zb["wall_area_mm2"] > 0 and zb["tight_area_mm2"] > 0 and zb["worst_spot"], zb
    pr = r["profile_no_blow"]
    assert pr and pr["bands"][0]["wall_mm"] >= pr["bands"][-1]["wall_mm"]
    assert all(b["wall_mm"] <= 3.0 for b in pr["bands"])
    got = sum(b["wall_mm"] * b["area_mm2"] for b in pr["bands"])
    want = wi["avg_mm"] * sum(b["area_mm2"] for b in pr["bands"])
    # a few per cent go missing where faces clip at sheet thickness; more than that
    # would mean the budget is not conserved
    assert abs(got - want) / want < 0.06, (got, want)
    # with a bubble the contact starts at a point, so the path to the rim is longer
    assert geodesic_from_contact(box, axis("z"), dome=1.0).max() > \
           geodesic_from_contact(box, axis("z")).max()
    f, pre = blow_fraction(100, 450, 1.31)
    assert 0.6 < f < 0.8 and 1.15 < pre < 1.25, (f, pre)
    assert blow_fraction(0, 450, 1.31) == (0.0, 1.0)
    # a bubble that out-stretches the draw clamps at 1 and is flagged oversized
    assert blow_fraction(100, 450, 1.05)[0] == 1.0
    big = measure(box, axis("z"), t=3, clamp=20, trim=0, bar=50, dome=150, path=tmp, pull_spec="z")
    assert big["bubble"]["oversized"] and big["bubble"]["share_of_draw"] == 1.0, big["bubble"]
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description="Thermoforming DFM measurements")
    sp = ap.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("measure")
    m.add_argument("mesh")
    m.add_argument("--pull", default="z", help="direction the part comes off the tool: z, -z, y...")
    m.add_argument("--t", type=float, default=3.0, help="sheet thickness, mm")
    m.add_argument("--clamp", type=float, default=25.0, help="clamped rim per side, mm")
    m.add_argument("--trim", default="auto", help="height added for trimming: auto = 12 + t")
    m.add_argument("--blank", action="append", default=None, help="blank size WxH in mm, repeatable (default 500x500)")
    m.add_argument("--bar", type=float, default=25.0, help="width of a divider bar on the frame, mm")
    m.add_argument("--dome", type=float, default=0.0, help="bubble height, mm (0 = no pre-blow)")
    m.add_argument("--blow-time", type=float, default=0.0, dest="blow_time",
                   help="blow time in seconds; converted to height with --blow-rate")
    m.add_argument("--blow-rate", type=float, default=250.0, dest="blow_rate",
                   help="bubble growth rate, mm/s — machine specific, calibrate it")
    m.add_argument("--blow-share", type=float, default=None, dest="blow_share",
                   help="pick the bubble so it takes this share (0..1) of the total draw")
    m.add_argument("--window", default=None, help="clamp window WxH in mm, e.g. a reducing window 270x230")
    m.add_argument("--method", default="male-bubble", choices=sorted(METHOD_DEPTH),
                   help="forming method — it sets the depth limit (default male-bubble, 0.5)")
    sp.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "selftest":
        return selftest()
    try:
        mesh = trimesh.load(a.mesh, force="mesh")
    except Exception as e:
        print(json.dumps({"error": f"could not load mesh: {e}"})); sys.exit(1)
    blanks = [blank_size(s) for s in (a.blank or ["500x500"])]
    dome = a.dome if a.dome else (a.blow_time * a.blow_rate if a.blow_time else 0.0)
    print(json.dumps(measure(mesh, axis(a.pull), a.t, a.clamp, a.trim, a.bar, dome, a.blow_rate,
                             blanks=blanks, path=a.mesh, pull_spec=a.pull, method=a.method,
                             window=blank_size(a.window) if a.window else None,
                             blow_share=a.blow_share), indent=1))


if __name__ == "__main__":
    main()
