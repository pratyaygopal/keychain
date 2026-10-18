#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
KICAD_PYTHON=${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3}
BOARD=kicad/uiuc-keychain.kicad_pcb
mkdir -p kicad/gerber preview reports
"$KICAD_PYTHON" scripts/build.py
"$KICAD_CLI" pcb drc --exit-code-violations -o reports/drc.rpt "$BOARD"
"$KICAD_CLI" pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts --no-netlist -o kicad/gerber/ "$BOARD"
"$KICAD_CLI" pcb export drill --excellon-separate-th --excellon-units mm -o kicad/gerber/ "$BOARD"
"$KICAD_PYTHON" - <<'PY'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
files = sorted(Path('kicad/gerber').glob('uiuc-keychain*'))
assert any(f.name.endswith('-NPTH.drl') for f in files), 'Missing NPTH drill'
assert any(f.name.endswith('-Edge_Cuts.gm1') for f in files), 'Missing outline'
with ZipFile('kicad/gerber.zip', 'w', ZIP_DEFLATED) as z:
    for f in files:
        z.write(f, f.name)
print('Packaged', len(files), 'fabrication files')
PY
"$KICAD_CLI" pcb render --width 1200 --height 1400 --side top --background opaque --quality high --use-board-stackup-colors -o preview/front.png "$BOARD"
"$KICAD_CLI" pcb render --width 1200 --height 1400 --side bottom --background opaque --quality high --use-board-stackup-colors -o preview/back.png "$BOARD"
