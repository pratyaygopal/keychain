# UIUC PCB Keychain

A 30 × 40 mm PCB keychain shaped like the University of Illinois Block I.
The front features a gold birb outline, and the back has gold circuit artwork,
both on green solder mask. Made from 1.6 mm FR4 with a 3.2 mm keyring hole,
it needs no components or assembly—just add a split ring.

Inspired by the `uiuc-pcb-ruler` project. Editable KiCad files, fabrication
Gerbers, and scripts to rebuild the design are included.

## Front and back

KiCad 3D renders of the current design:

| Front | Back |
| --- | --- |
| ![Gold bird on green Block I front](preview/front.png) | ![Green and gold circuit artwork](preview/back.png) |

## Ordering

Upload [`kicad/uiuc-keychain-jlcpcb.zip`](kicad/uiuc-keychain-jlcpcb.zip)
for fabrication. Select 2-layer FR4, 1.6 mm thickness, green solder mask,
and ENIG finish. The archive contains seven Gerber layers and one populated
Excellon drill file, all at the archive root. No assembly is required.

The only drill is the **3.2 mm non-plated keyring hole**, centered 5.2 mm
from the top and right board bounds. There are no plated holes; the empty
PTH export is intentionally excluded from the upload ZIP. The drill program
is `uiuc-keychain-NPTH.drl`. See the [drill map](reports/drill-map.svg) and
[verification report](reports/drill-verification.txt).

If JLCPCB reports missing drills, use **Replace file** to upload the named
fabrication ZIP above, rather than the repository's source-code ZIP. Ask
their engineer to check `uiuc-keychain-NPTH.drl` for the single 3.2 mm hole.

`scripts/rebuild.sh` regenerates the design and manufacturing files with
KiCad installed. Its packaging step verifies the drill's diameter, count,
and coordinates against the board before writing either upload ZIP.
