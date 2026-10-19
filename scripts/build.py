#!/usr/bin/env python3
"""Generate the component-free keychain with KiCad's bundled pcbnew Python."""
import math
from pathlib import Path
import pcbnew as p
from trace_birb import bird_mask

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'kicad/uiuc-keychain.kicad_pcb'
b = p.BOARD()
b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
b.GetDesignSettings().m_CopperEdgeClearance = p.FromMM(0.5)
b.GetDesignSettings().m_HoleClearance = p.FromMM(0.5)
title = b.GetTitleBlock()
title.SetTitle('UIUC Block I PCB Keychain')
title.SetRevision('2.0')
title.SetComment(0, 'Decorative PCB; green mask, ENIG bird and circuit artwork; no assembly')
b.SetTitleBlock(title)

# Widen the original Block I horizontally to the requested 30 x 40 mm.
# Keep its bar-height and shoulder-width proportions within those bounds.
H = 40.0
SCALE = H / 13.758333
W = 30.0
BAR = 3.725667 * SCALE
SHOULDER = W * 2.116667 / 9.52589
HOLE = (W - 5.2, 5.2)

def v(pt):
    return p.VECTOR2I(p.FromMM(100 + pt[0]), p.FromMM(80 + pt[1]))

def outline(inset=0):
    d = inset
    return [(d,d),(W-d,d),(W-d,BAR-d),(W-SHOULDER-d,BAR-d),
            (W-SHOULDER-d,H-BAR+d),(W-d,H-BAR+d),(W-d,H-d),
            (d,H-d),(d,H-BAR+d),(SHOULDER+d,H-BAR+d),
            (SHOULDER+d,BAR-d),(d,BAR-d)]

def line(a, c, layer, width):
    s = p.PCB_SHAPE()
    s.SetShape(p.SHAPE_T_SEGMENT)
    s.SetStart(v(a)); s.SetEnd(v(c))
    s.SetLayer(layer); s.SetWidth(p.FromMM(width)); b.Add(s)

def rounded_edges(points, radius=0.8):
    # Tangent quarter-circle fillets on convex and reentrant corners.
    corners = []
    for i, q in enumerate(points):
        prev, nxt = points[i-1], points[(i+1) % len(points)]
        u = ((prev[0]-q[0]), (prev[1]-q[1]))
        t = ((nxt[0]-q[0]), (nxt[1]-q[1]))
        lu, lt = math.hypot(*u), math.hypot(*t)
        u = (u[0]/lu, u[1]/lu); t = (t[0]/lt, t[1]/lt)
        start = (q[0]+u[0]*radius, q[1]+u[1]*radius)
        end = (q[0]+t[0]*radius, q[1]+t[1]*radius)
        center = (q[0]+(u[0]+t[0])*radius, q[1]+(u[1]+t[1])*radius)
        mid = (center[0]-(u[0]+t[0])*radius/math.sqrt(2),
               center[1]-(u[1]+t[1])*radius/math.sqrt(2))
        arc = p.PCB_SHAPE(); arc.SetShape(p.SHAPE_T_ARC)
        arc.SetArcGeometry(v(start), v(mid), v(end))
        arc.SetLayer(p.Edge_Cuts); arc.SetWidth(p.FromMM(0.05)); b.Add(arc)
        corners.append((start,end))
    for i, (_, end) in enumerate(corners):
        line(end, corners[(i+1) % len(corners)][0], p.Edge_Cuts, 0.05)

def polygon(poly, layer):
    # Convert holes into linked contours, preserving the bird's open interior.
    poly.Fracture()
    # Each PCB graphic stores one outline; emit the eye as its own polygon.
    for i in range(poly.OutlineCount()):
        part = p.SHAPE_POLY_SET(); part.AddOutline(poly.COutline(i))
        shape = p.PCB_SHAPE(); shape.SetShape(p.SHAPE_T_POLY)
        shape.SetPolyShape(part); shape.SetFilled(True); shape.SetWidth(0)
        shape.SetLayer(layer); b.Add(shape)

rounded_edges(outline())

# A true NPTH, rather than a drawn circle, generates an Excellon drill hit.
fp = p.FOOTPRINT(b); fp.SetReference('H1'); fp.SetValue('Keyring 3.2mm NPTH')
fp.SetPosition(v(HOLE)); fp.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
pad = p.PAD(fp); pad.SetAttribute(p.PAD_ATTRIB_NPTH)
pad.SetShape(p.PAD_SHAPE_CIRCLE); pad.SetSize(p.VECTOR2I(p.FromMM(3.2),p.FromMM(3.2)))
pad.SetDrillSize(p.VECTOR2I(p.FromMM(3.2),p.FromMM(3.2)))
pad.SetLayerSet(p.LSET.AllCuMask()); pad.SetPosition(v(HOLE))
fp.Add(pad); b.Add(fp)

# Filled, unconnected decorative copper retains islands and clears the hole.
z = p.ZONE(b); z.SetLayer(p.F_Cu); z.SetNetCode(0)
z.SetLocalClearance(p.FromMM(0.5)); z.SetMinThickness(p.FromMM(0.2))
z.SetIslandRemovalMode(0)
poly = z.Outline(); poly.NewOutline()
for pt in outline(0.8):
    pt = v(pt); poly.Append(pt.x,pt.y)
b.Add(z)
# Open solder mask only over the original bird outline and eye: gold on green.
bird = bird_mask(ROOT / 'assets/birb.png',p,v,(W/2,H/2),width=12.0)
polygon(bird,p.F_Mask)

# Regular back artwork: solid chip and terminals with generous mask overlap.
# Trace copper is 0.80 mm wide; exposed gold is 0.40 mm wide. Terminal
# diameters are 1.60 mm copper / 1.20 mm mask. Nothing here is a drill or via.
TRACE_COPPER = 0.80
TRACE_GOLD = 0.40

def gold_path(points):
    for a, c in zip(points,points[1:]):
        dx,dy = abs(c[0]-a[0]),abs(c[1]-a[1])
        assert dx < 1e-8 or dy < 1e-8 or abs(dx-dy) < 1e-8, 'Use 45-degree routing'
        line(a,c,p.B_Cu,TRACE_COPPER)
        line(a,c,p.B_Mask,TRACE_GOLD)

def terminal(pt):
    for layer,radius in [(p.B_Cu,0.80),(p.B_Mask,0.60)]:
        s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_CIRCLE)
        s.SetCenter(v(pt)); s.SetEnd(v((pt[0]+radius,pt[1])))
        s.SetFilled(True); s.SetWidth(0); s.SetLayer(layer); b.Add(s)

def chip(inset):
    left,right,top,bottom = 12+inset,18-inset,17+inset,23-inset
    bevel=0.8
    poly=p.SHAPE_POLY_SET(); poly.NewOutline()
    for pt in [(left+bevel,top),(right-bevel,top),(right,top+bevel),
               (right,bottom-bevel),(right-bevel,bottom),(left+bevel,bottom),
               (left,bottom-bevel),(left,top+bevel)]:
        q=v(pt); poly.Append(q.x,q.y)
    return poly

# A filled chamfered square replaces the hollow chip frame and inner rings.
polygon(chip(0.0),p.B_Cu)
polygon(chip(0.25),p.B_Mask)

# Three evenly spaced top/bottom leads; two evenly spaced side leads.
# The gold hole-surround and small disconnected satellite traces are omitted.
top_paths = [
    [(13,17.5),(13,13),(10,10),(10,7),(7,4),(4,4)],
    [(15,17.5),(15,4)],
    [(17,17.5),(17,13),(20,10),(20,7)],
]
for path in top_paths:
    gold_path(path); terminal(path[-1])
    reflected=[(x,H-y) for x,y in path]
    if path is top_paths[-1]:
        reflected += [(23,36),(26,36)]
    gold_path(reflected); terminal(reflected[-1])

side_paths = [
    [(12.5,19),(10,19),(9.5,18.5),(9.5,16)],
    [(12.5,21),(10,21),(9.5,21.5),(9.5,24)],
]
for path in side_paths:
    gold_path(path); terminal(path[-1])
    reflected=[(W-x,y) for x,y in path]
    gold_path(reflected); terminal(reflected[-1])

p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(BOARD), b)

# Store fabrication materials/colors in the board so the 3D preview is faithful.
data = BOARD.read_text()
stackup = '''(stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG") (dielectric_constraints no)
    )'''
data = data.replace('(setup', '(setup\n    ' + stackup, 1)
BOARD.write_text(data)
print(f'Generated {BOARD}: {W:.3f} x {H:.3f} mm; keyring at {HOLE}, drill 3.2 mm')
