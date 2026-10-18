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
title.SetRevision('1.9')
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

# Reverse: floating circuit artwork and hole surround, with no perimeter border.
for layer, width in [(p.B_Cu,0.65),(p.B_Mask,0.5)]:
    s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_CIRCLE)
    s.SetCenter(v(HOLE)); s.SetEnd(v((HOLE[0]+2.55,HOLE[1])))
    s.SetLayer(layer); s.SetWidth(p.FromMM(width)); b.Add(s)

# Text-free circuit artwork: a chamfered chip with radiating 45-degree traces.
# These are copper graphics, not a functional circuit or actual drilled vias.
def gold_path(points, width=0.34):
    for a, c in zip(points, points[1:]):
        line(a,c,p.B_Cu,width+0.14)
        line(a,c,p.B_Mask,width)

def terminal(pt, radius=0.58):
    for layer, width in [(p.B_Cu,0.38),(p.B_Mask,0.24)]:
        s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_CIRCLE)
        s.SetCenter(v(pt)); s.SetEnd(v((pt[0]+radius,pt[1])))
        s.SetLayer(layer); s.SetWidth(p.FromMM(width)); b.Add(s)

cx = W/2
chip = [(cx-2.1,17.2),(cx+2.1,17.2),(cx+2.8,17.9),
        (cx+2.8,22.1),(cx+2.1,22.8),(cx-2.1,22.8),
        (cx-2.8,22.1),(cx-2.8,17.9),(cx-2.1,17.2)]
gold_path(chip,0.42)
gold_path([(cx,18.5),(cx+1.5,20),(cx,21.5),(cx-1.5,20),(cx,18.5)],0.28)
terminal((cx,20),0.36)

top_paths = [
    [(cx-1.8,17.2),(cx-1.8,14.0),(9.25,11.25),(9.25,7.0),(6.25,4.0),(3.8,4.0)],
    [(cx-0.6,17.2),(cx-0.6,12.5),(11.65,10.9),(11.65,5.6),(10.05,4.0)],
    [(cx+0.6,17.2),(cx+0.6,11.0),(13.65,10.2),(13.65,3.8),(14.15,3.3)],
    [(cx+1.8,17.2),(cx+1.8,14.0),(18.45,11.2),(18.45,8.7),(16.75,7.0),(16.75,4.7)],
]
for path in top_paths:
    gold_path(path); terminal(path[-1])
    reflected = [(x,H-y) for x,y in path]
    gold_path(reflected); terminal(reflected[-1])

side_paths = [
    [(cx-2.8,18.2),(9.7,18.2),(8.8,17.3),(8.8,15.5)],
    [(cx-2.8,19.4),(9.6,19.4),(8.85,20.15)],
    [(cx-2.8,20.6),(10.1,20.6),(8.8,21.9)],
    [(cx-2.8,21.8),(10.1,21.8),(8.8,23.1),(8.8,25.0)],
]
for path in side_paths:
    # Follow the wider shoulders while retaining the circuit's masked margin.
    shoulder_shift = SHOULDER - 2.116667*SCALE
    path = [path[0]] + [(x+shoulder_shift,y) for x,y in path[1:]]
    gold_path(path,0.28); terminal(path[-1],0.43)
    reflected = [(W-x,y) for x,y in path]
    gold_path(reflected,0.28); terminal(reflected[-1],0.43)

# Short satellite traces occupy the wide end bars without approaching the hole.
for path in [
    [(3.8,7.2),(6.4,7.2),(7.5,8.3)],
    [(W-3.8,32.6),(W-6.4,32.6),(W-7.6,33.8)],
    [(W-3.8,35.6),(W-5.6,35.6),(W-7.2,37.2),(W-9.2,37.2)],
]:
    gold_path(path,0.28); terminal(path[0],0.45); terminal(path[-1],0.45)

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
