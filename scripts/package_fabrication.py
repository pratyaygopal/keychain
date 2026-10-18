#!/usr/bin/env python3
"""Check the keyring drill against the board, then make an unambiguous CAM ZIP."""
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
GERBER = ROOT / 'kicad/gerber'
board = p.LoadBoard(str(ROOT / 'kicad/uiuc-keychain.kicad_pcb'))
holes = [pad for fp in board.GetFootprints() for pad in fp.Pads()
         if pad.GetDrillSize().x > 0]
assert len(holes) == 1, 'Revisit packaging: design no longer has exactly one hole'
pad = holes[0]
assert pad.GetAttribute() == p.PAD_ATTRIB_NPTH, 'Keyring hole must be non-plated'
assert pad.GetDrillSize().x == pad.GetDrillSize().y, 'Expected circular hole'
expected = (p.ToMM(pad.GetDrillSize().x),
            p.ToMM(pad.GetPosition().x), -p.ToMM(pad.GetPosition().y))

drill = GERBER / 'uiuc-keychain-NPTH.drl'
text = drill.read_text()
assert '\nMETRIC\n' in text and 'NonPlated' in text, 'Expected metric NPTH export'
tools = dict(re.findall(r'^T(\d+)C([\d.]+)$',text,re.M))
hits, tool = [], None
for line in text.splitlines():
    selection = re.fullmatch(r'T(\d+)',line)
    if selection:
        tool = selection[1]
    hit = re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
    if hit:
        assert tool in tools, 'Drill hit has no defined tool'
        hits.append((float(tools[tool]),float(hit[1]),float(hit[2])))
assert len(hits) == 1, f'Expected one drill hit, found {len(hits)}'
assert all(abs(a-b)<0.00001 for a,b in zip(hits[0],expected)), (hits,expected)
assert abs(expected[0]-3.2)<0.00001, 'Expected 3.2 mm keyring drill'

names = ['F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs',
         'F_Silkscreen.gto','B_Silkscreen.gbo','Edge_Cuts.gm1']
files = [GERBER / ('uiuc-keychain-'+name) for name in names] + [drill]
assert all(f.is_file() and f.stat().st_size for f in files), 'Missing CAM file'
outputs = [ROOT/'kicad/gerber.zip',ROOT/'kicad/uiuc-keychain-jlcpcb.zip']
for output in outputs:
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        for f in files:
            z.write(f,f.name)
    with ZipFile(output) as z:
        assert z.testzip() is None
        assert [n for n in z.namelist() if n.endswith('.drl')] == [drill.name]
        assert z.read(drill.name).decode() == text

outline = p.SHAPE_POLY_SET()
assert board.GetBoardPolygonOutlines(outline,False), 'Invalid board outline'
bounds = outline.BBox()
right = p.ToMM(bounds.GetRight()) - expected[1]
top = -expected[2] - p.ToMM(bounds.GetTop())
report = (f'Verified both fabrication ZIPs: {len(files)} files at archive root.\n'
          f'Exactly one populated drill file: {drill.name}\n'
          f'Exactly one non-plated circular hole, diameter {expected[0]:.3f} mm.\n'
          f'Excellon coordinate X{expected[1]:.3f} Y{expected[2]:.3f} mm.\n'
          f'Hole center: {right:.3f} mm from right bound; {top:.3f} mm from top bound.\n'
          'Drill coordinates and diameter match the editable KiCad board.\n'
          'Empty plated-hole drill file omitted from upload ZIPs.\n')
(ROOT/'reports').mkdir(exist_ok=True)
(ROOT/'reports/drill-verification.txt').write_text(report)
drill_map = GERBER/'uiuc-keychain-NPTH-drl_map.svg'
if drill_map.is_file():
    drill_map.replace(ROOT/'reports/drill-map.svg')
empty_map = GERBER/'uiuc-keychain-PTH-drl_map.svg'
if empty_map.is_file():
    empty_map.unlink()
print(report)
