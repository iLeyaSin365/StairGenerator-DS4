import bmesh
from mathutils import Vector
from math import pi, sin, cos, atan2, radians

from ..utils import VEC_UP, popup_message


def compute_and_build_stairs(bm, face1, face2, prop):
    c1 = face1.calc_center_bounds()
    c2 = face2.calc_center_bounds()
    delta = c2 - c1
    horizontal_dist = Vector((delta.x, delta.y, 0)).length
    height_diff = delta.z

    if horizontal_dist < 0.001 and abs(height_diff) < 0.001:
        popup_message("Selected faces are too close / at the same position")
        return False

    stair_type = getattr(prop, "stair_type", "STRAIGHT")

    if stair_type == "U":
        return build_u(bm, c1, c2, prop)
    elif stair_type == "L":
        return build_l(bm, c1, c2, prop)
    elif stair_type == "CURVED":
        return build_curved(bm, c1, c2, prop, face1, face2)
    else:
        return build_straight(bm, c1, c2, prop)


def _endpoints(c1, c2):
    lower, upper = (c1, c2) if c1.z <= c2.z else (c2, c1)
    return lower, upper


def _axis(forward, up=VEC_UP):
    forward = Vector((forward.x, forward.y, 0))
    if forward.length < 0.001:
        forward = Vector((1, 0, 0))
    forward.normalize()
    side = forward.cross(up).normalized()
    return forward, side


def _rot_z(forward, side, degrees):
    angle = radians(degrees)
    c, s = cos(angle), sin(angle)
    f = Vector((forward.x * c - forward.y * s, forward.x * s + forward.y * c, 0))
    sd = Vector((side.x * c - side.y * s, side.x * s + side.y * c, 0))
    return f.normalized(), sd.normalized()


def _rot_halves(axis, angle):
    """Rotate a horizontal unit vector by `angle` (radians) around Z and return
    (forward, side) where side = forward.cross(VEC_UP)."""
    c, s = cos(angle), sin(angle)
    f = Vector((axis.x * c - axis.y * s, axis.x * s + axis.y * c, 0))
    if f.length < 1e-5:
        f = Vector((1, 0, 0))
    f.normalize()
    sd = Vector((-f.y, f.x, 0.0))
    return f, sd


def build_straight(bm, c1, c2, prop):
    lower, upper = _endpoints(c1, c2)
    delta = upper - lower
    forward, side = _axis(delta)
    run = Vector((delta.x, delta.y, 0)).length
    rise = abs(delta.z)
    sc = prop.step_count
    riser = rise / sc
    tread = run / sc
    width = prop.step_width

    collected = [] if prop.has_railing else None
    for i in range(sc):
        t = (i + 0.5) / sc
        center = lower + delta * t
        nosing = create_step_box(bm, center, forward, side, width, tread, riser)
        if prop.has_railing:
            collected.append(nosing)

    if prop.has_railing:
        build_railing(bm, lower, upper, forward, side, prop, collected)

    return True


def build_l(bm, c1, c2, prop):
    nosing_list = [] if prop.has_railing else None
    lower, upper = _endpoints(c1, c2)
    delta = upper - lower
    run = Vector((delta.x, delta.y, 0)).length
    rise = abs(delta.z)
    sc = prop.step_count
    width = prop.step_width
    riser = rise / sc

    turn = radians(getattr(prop, "landing_rotation", 90.0))
    # clamp so the two flights don't become parallel/degenerate
    turn = max(radians(15.0), min(radians(165.0), abs(turn)))
    if turn > pi / 2:
        turn = pi - turn

    run_axis = Vector((delta.x, delta.y, 0))
    if run_axis.length < 1e-4:
        run_axis = Vector((1, 0, 0))
    run_axis.normalize()

    half = turn / 2
    fwd1, side1 = _rot_halves(run_axis, half)
    fwd2, side2 = _rot_halves(run_axis, -half)

    # Each flight climbs half the rise; split the horizontal run so the two
    # flight axes place the landing exactly at the corner: solve the 2x2 system
    #   fwd1*d1 + fwd2*d2 = run_axis * run
    a11, a12 = fwd1.x, fwd2.x
    a21, a22 = fwd1.y, fwd2.y
    det = a11 * a22 - a12 * a21
    if abs(det) < 1e-6:
        return build_straight(bm, c1, c2, prop)
    bx, by = run_axis.x * run, run_axis.y * run
    d1 = (bx * a22 - by * a12) / det
    d2 = (a11 * by - a21 * bx) / det

    if d1 <= 1e-4 or d2 <= 1e-4:
        return build_straight(bm, c1, c2, prop)

    landing_z = lower.z + rise * 0.5
    landing_center = Vector((lower.x, lower.y, 0)) + fwd1 * d1
    landing_center = Vector((landing_center.x, landing_center.y, landing_z))

    split = max(sc // 2, 1)

    # Flight 1: lower -> landing along fwd1, up half rise
    riser1 = (landing_z - lower.z) / split
    tread1 = d1 / split
    for i in range(split):
        t = (i + 0.5) / split
        center = lower + (landing_center - lower) * t
        nosing = create_step_box(bm, center, fwd1, side1, width, tread1, riser1)
        if prop.has_railing:
            nosing_list.append(nosing)

    # Landing slab oriented along the second flight (turn direction)
    land_fwd, land_side = fwd2, side2
    landing_box = create_step_box(bm, landing_center, land_fwd, land_side, prop.landing_width, prop.landing_length, prop.landing_thickness)

    # Flight 2: landing -> upper along fwd2, up half rise
    riser2 = (upper.z - landing_z) / (sc - split)
    tread2 = d2 / (sc - split)
    for i in range(sc - split):
        t = (i + 0.5) / (sc - split)
        center = landing_center + (upper - landing_center) * t
        nosing = create_step_box(bm, center, fwd2, side2, width, tread2, riser2)
        if prop.has_railing:
            nosing_list.append(nosing)

    if prop.has_railing:
        build_railing(bm, lower, upper, fwd1, side1, prop, nosing_list)

    return True


def build_u(bm, c1, c2, prop):
    lower, upper = _endpoints(c1, c2)
    forward, side = _axis(upper - lower)
    delta = upper - lower
    run = Vector((delta.x, delta.y, 0)).length
    rise = abs(delta.z)
    sc = prop.step_count
    width = prop.step_width
    nosing_list = [] if prop.has_railing else None

    landing_len = prop.landing_length
    landing_wdt = prop.landing_width
    landing_thk = prop.landing_thickness

    mid = (lower + upper) / 2
    # Two landings: one on each side of the run line so the flights run parallel
    offset = side * (landing_len * 0.5)
    mid_low = Vector((mid.x, mid.y, lower.z + rise * 0.25)) + offset * 0
    corner = Vector((mid.x, mid.y, 0)) + offset
    landing_center = Vector((corner.x, corner.y, lower.z + rise * 0.5))

    split = max(sc // 2, 1)

    # Flight 1: lower -> landing forward
    run1 = Vector((landing_center.x - lower.x, landing_center.y - lower.y, 0)).length
    fwd1, side1 = _axis(landing_center - lower, VEC_UP)
    riser1 = abs(landing_center.z - lower.z) / split
    tread1 = run1 / split
    for i in range(split):
        t = (i + 0.5) / split
        center = lower + (landing_center - lower) * t
        nosing = create_step_box(bm, center, fwd1, side1, width, tread1, riser1)
        if prop.has_railing:
            nosing_list.append(nosing)

    land_fwd, land_side = _rot_z(fwd1, side1, getattr(prop, "landing_slab_rotation", 0.0))
    create_step_box(bm, landing_center, land_fwd, land_side, landing_wdt, landing_len, landing_thk)

    # Flight 2: landing -> upper turned 180 (switchback)
    run2 = Vector((upper.x - landing_center.x, upper.y - landing_center.y, 0)).length
    fwd2, side2 = _axis(upper - landing_center, VEC_UP)
    riser2 = abs(upper.z - landing_center.z) / (sc - split)
    tread2 = run2 / (sc - split)
    for i in range(sc - split):
        t = (i + 0.5) / (sc - split)
        center = landing_center + (upper - landing_center) * t
        nosing = create_step_box(bm, center, fwd2, side2, width, tread2, riser2)
        if prop.has_railing:
            nosing_list.append(nosing)

    if prop.has_railing:
        build_railing(bm, lower, upper, forward, side, prop, nosing_list)

    return True


def build_curved(bm, c1, c2, prop, face1, face2):
    lower, upper = _endpoints(c1, c2)
    delta = upper - lower
    run = Vector((delta.x, delta.y, 0)).length
    rise = abs(delta.z)
    sc = prop.step_count
    width = prop.step_width

    # Key the arc off the faces in height order so the climbing direction matches.
    # face1 is lower when c1 is lower; otherwise swap so a_start = lower face angle.
    if c1.z <= c2.z:
        low_n, high_n = face1.normal, face2.normal
    else:
        low_n, high_n = face2.normal, face1.normal
    a_start = atan2(low_n.y, low_n.x)
    a_end = atan2(high_n.y, high_n.x)
    # shortest signed sweep between the lower and upper face normals
    sweep = a_end - a_start
    while sweep > pi:
        sweep -= 2 * pi
    while sweep < -pi:
        sweep += 2 * pi
    sgn = 1.0 if sweep >= 0 else -1.0

    mid = (lower + upper) / 2
    radius = max(run / 2, 0.1)
    nosing_list = [] if prop.has_railing else None

    def arc_step(t, a):
        pos = Vector((mid.x + radius * cos(a), mid.y + radius * sin(a), lower.z + rise * t))
        forward = Vector((-sin(a) * sgn, cos(a) * sgn, 0))
        side = Vector((cos(a) * sgn, sin(a) * sgn, 0))
        nosing = create_step_box(bm, pos, forward, side, width, run / sc, rise / sc)
        if prop.has_railing:
            nosing_list.append(nosing)

    if prop.has_landing and sc >= 4:
        split = sc // 2
        land_z = lower.z + rise * 0.5
        land_angle = a_start + sweep * 0.5
        land_pos = Vector((mid.x + radius * cos(land_angle), mid.y + radius * sin(land_angle), land_z))
        # arc flight 1
        for i in range(split):
            t = (i + 0.5) / split
            arc_step(t, a_start + sweep * t)
        create_step_box(bm, land_pos, Vector((-sin(land_angle) * sgn, cos(land_angle) * sgn, 0)), Vector((cos(land_angle) * sgn, sin(land_angle) * sgn, 0)), prop.landing_width, prop.landing_length, prop.landing_thickness)
        for i in range(sc - split):
            t = 0.5 + (i + 0.5) / (sc - split) * 0.5
            arc_step(t, a_start + sweep * t)
    else:
        for i in range(sc):
            t = (i + 0.5) / sc
            arc_step(t, a_start + sweep * t)

    if prop.has_railing:
        forward0 = Vector((-sin(a_start) * sgn, cos(a_start) * sgn, 0))
        side0 = Vector((cos(a_start) * sgn, sin(a_start) * sgn, 0))
        build_railing(bm, lower, upper, Vector((cos(a_start), sin(a_start), 0)), side0, prop, nosing_list)

    return True


def create_step_box(bm, center, forward, side, width, depth, height):
    half_w = width / 2
    half_d = max(depth, 0.01) / 2
    half_h = max(height, 0.01) / 2

    ay = side * half_w
    ax = forward * half_d
    az = VEC_UP * half_h

    corners = (
        center - ax - ay - az, center - ax + ay - az,
        center + ax - ay - az, center + ax + ay - az,
        center - ax - ay + az, center - ax + ay + az,
        center + ax - ay + az, center + ax + ay + az,
    )
    vs = [bmesh.ops.create_vert(bm, co=c)["vert"][0] for c in corners]
    for quad in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6)):
        bmesh.ops.contextual_create(bm, geom=[vs[i] for i in quad])

    nosing_center = center + forward * half_d + VEC_UP * half_h
    nosing_left = nosing_center - side * half_w
    nosing_right = nosing_center + side * half_w
    return nosing_left, nosing_right


def _bar(bm, p1, p2, up, thickness):
    vec = p2 - p1
    if vec.length < 1e-5:
        return
    axis = vec.normalized()
    side = axis.cross(up) if up else Vector((1, 0, 0))
    if side.length < 1e-5:
        side = Vector((1, 0, 0))
    side.normalize()
    up2 = axis.cross(side).normalized()
    hw = thickness / 2

    def C(p, a, b):
        return p + side * hw * a + up2 * hw * b

    corners = (C(p1, 1, 1), C(p1, -1, 1), C(p1, -1, -1), C(p1, 1, -1),
               C(p2, 1, 1), C(p2, -1, 1), C(p2, -1, -1), C(p2, 1, -1))
    vs = [bmesh.ops.create_vert(bm, co=c)["vert"][0] for c in corners]
    for quad in ((0, 1, 2, 3), (5, 6, 7, 4), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bmesh.ops.contextual_create(bm, geom=[vs[i] for i in quad])


def _baluster_profile(prop):
    bulb = max(getattr(prop, "baluster_bulb", 1.0), 0.1)
    waist = max(getattr(prop, "baluster_waist", 0.55), 0.05)
    top = max(getattr(prop, "baluster_top", 0.65), 0.05)
    return [
        (0.00, waist * 0.7),
        (0.12, waist),
        (0.30, bulb * 0.8),
        (0.50, bulb),
        (0.72, waist),
        (0.85, top * 0.8),
        (1.00, top),
    ]


def _turned_baluster(bm, base, top, radius, prop, seg=8):
    """Lathe a classical turned (bulbed) baluster along a vertical axis."""
    vec = top - base
    length = max(vec.length, 1e-4)
    cx, cy = (base.x + top.x) / 2, (base.y + top.y) / 2

    profile = _baluster_profile(prop)
    rings = []
    for (h, rf) in profile:
        r = max(radius * rf, 0.001)
        z = base.z + h * length
        ring = [
            bmesh.ops.create_vert(bm, co=Vector((cx + cos(2 * pi * k / seg) * r, cy + sin(2 * pi * k / seg) * r, z)))["vert"][0]
            for k in range(seg)
        ]
        rings.append(ring)

    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            k2 = (k + 1) % seg
            bmesh.ops.contextual_create(bm, geom=[a[k], a[k2], b[k2], b[k]])

    # cap both ends
    bmesh.ops.contextual_create(bm, geom=rings[0])
    bmesh.ops.contextual_create(bm, geom=rings[-1])


def build_railing(bm, lower, upper, forward, side, prop, nosings=None):
    if getattr(prop, "rail_style", "SLOPE") == "STEPPED" and nosings:
        return build_railing_stepped(bm, nosings, prop)

    width = prop.step_width
    rail_h = prop.rail_height
    rail_t = prop.rail_thickness
    bal_t = prop.baluster_thickness
    fill = prop.rail_fill
    n = prop.post_count
    if fill == "NONE":
        rail_t = max(rail_t, 0.05)

    for s in (1, -1):
        low = Vector((lower.x, lower.y, lower.z)) + side * (width / 2) * s
        high = Vector((upper.x, upper.y, upper.z)) + side * (width / 2) * s

        # Handrail (top) along the slope
        _bar(bm, low + VEC_UP * rail_h, high + VEC_UP * rail_h, VEC_UP, rail_t)

        if fill == "WALL":
            # Continuous wall panel between the running line and the handrail
            _bar(bm, low, high, VEC_UP, rail_t)
            low_mid = low + VEC_UP * rail_h * 0.5
            high_mid = high + VEC_UP * rail_h * 0.5
            _bar(bm, low_mid, high_mid, VEC_UP, rail_t)
            continue

        if fill == "BALUSTERS":
            pos_count = n + 2
            turned = getattr(prop, "baluster_type", "PLAIN") == "TURNED"
            for i in range(pos_count):
                t = i / (pos_count - 1)
                base = low.lerp(high, t)
                top = base + VEC_UP * rail_h
                # Thick newels at both ends + every few, thin balusters between
                is_newel = (i == 0) or (i == pos_count - 1) or (i % 3 == 0)
                if is_newel:
                    _bar(bm, base, top, VEC_UP, rail_t)
                elif turned:
                    _turned_baluster(bm, base, top, bal_t * 0.5, prop)
                else:
                    _bar(bm, base, top, VEC_UP, bal_t)
            if prop.bottom_rail:
                _bar(bm, low, high, VEC_UP, bal_t)


def build_railing_stepped(bm, nosings, prop):
    """Railing that follows every step, giving a turning point at each nosing.

    `nosings` is an ordered list of (nosing_left, nosing_right) Vectors, one
    entry per step, positioned at the top/leading edge of each tread.
    """
    rail_h = prop.rail_height
    rail_t = prop.rail_thickness
    bal_t = prop.baluster_thickness
    fill = prop.rail_fill

    for s, idx in ((1, 1), (-1, 0)):
        pts = [n[idx] for n in nosings]
        rail_pts = [p + VEC_UP * rail_h for p in pts]

        # sloped handrail: connect every consecutive nosing -> a flex point per step
        for a, b in zip(rail_pts, rail_pts[1:]):
            _bar(bm, a, b, VEC_UP, rail_t)

        if fill == "NONE":
            continue

        if fill == "WALL":
            for a, b in zip(pts, pts[1:]):
                am, bm_ = a + VEC_UP * rail_h, b + VEC_UP * rail_h
                _bar(bm, a, b, VEC_UP, rail_t)
                _bar(bm, am, bm_, VEC_UP, rail_t)
            continue

        if fill == "BALUSTERS":
            turned = getattr(prop, "baluster_type", "PLAIN") == "TURNED"
            for p, rp in zip(pts, rail_pts):
                is_newel = p.z <= pts[0].z + 0.001 or p.z >= pts[-1].z - 0.001
                if is_newel:
                    _bar(bm, p, rp, VEC_UP, rail_t)
                elif turned:
                    _turned_baluster(bm, p, rp, bal_t * 0.5, prop)
                else:
                    _bar(bm, p, rp, VEC_UP, bal_t)
            if prop.bottom_rail:
                for a, b in zip(pts, pts[1:]):
                    _bar(bm, a, b, VEC_UP, bal_t)