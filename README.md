# UIUC PCB Keychain

A Block I shaped PCB keychain inspired by the neighboring
[`uiuc-pcb-ruler`](../uiuc-pcb-ruler) project. It carries over the ruler's
exposed gold artwork and 1.6 mm FR4, with green solder mask on both faces.

| Front | Back |
| --- | --- |
| ![Gold bird on green Block I front](preview/front.png) | ![Green and gold circuit artwork](preview/back.png) |

## Files

- Open `kicad/uiuc-keychain.kicad_pro` in **KiCad 10**; the editable layout is
  `kicad/uiuc-keychain.kicad_pcb`. All geometry is embedded; no external footprint
  libraries, components, schematic, or assembly are required.
- `kicad/gerber.zip` is the fabrication upload package, including the board
  outline and a separate non-plated drill file.
- `preview/front.png` and `preview/back.png` are KiCad 3D renders.
- `reports/drc.rpt` records the design check.
- `scripts/build.py` defines dimensions, artwork, copper, and hole placement.
- `scripts/trace_birb.py` converts the bundled original PNG into native PCB
  polygons without external imaging packages.

## Fabrication

| Setting | Value |
| --- | --- |
| Overall size | 30.000 × 40.000 mm |
| Material / layers | FR4 / 2 copper layers, 1 oz |
| Board thickness | 1.6 mm |
| Solder mask / silkscreen | Green on both sides / none |
| Surface finish | ENIG (exposed copper artwork becomes gold) |
| Outline corner radius | 0.8 mm, including inside corners |
| Keyring hole | One 3.2 mm non-plated hole |
| Hole center | 5.2 mm from top and right board bounds |
| Hole edge to board edge | 3.6 mm minimum |
| Copper to board edge / hole | 0.5 mm minimum |
| Assembly | None; decorative, unpowered PCB |

Upload `kicad/gerber.zip` to a PCB manufacturer and select the settings above.
Select **green solder mask** in the order form; Gerbers specify mask openings,
while the mask color is a manufacturing option.
The outline needs routed internal corners; request individual routed boards,
with no mouse bites on the finished outline. Review the manufacturer's CAM
preview for the I outline, single hole, green face with gold bird outline and inset back circuit
artwork. A split ring is separate hardware. No solder paste files are needed.

## Validation and design details

KiCad 10.0.7 DRC reports **zero violations and zero unconnected items** with
the included project settings. The isolated-copper warning is disabled because
the front zone is intentional decorative artwork with no electrical net;
clearance and outline checks remain enabled. The front copper clears the hole
by 0.5 mm, leaving a green surround. The back has a central chip motif, angled traces, and ring-shaped terminal
nodes, all in exposed gold with at least 2 mm of green margin to the board
outline. There is no back perimeter border. These nodes are artwork, not drilled holes or
electrical components. The front has an exposed gold bird outline traced directly from
`assets/birb.png`, copied from `../website/pics/birb.png`. Its outline and eye
are preserved at 12 mm wide, centered on the green I with the original aspect
ratio. The red artwork is rendered in exposed gold through openings in the green
solder mask; its dark background
and glow are omitted. Both faces are text-free.

The renders were inspected for the outline, hole, bird outline, and circuit artwork.
This is a digital design; no physical sample or keyring wear test has been made.

## Rebuild

With KiCad installed on macOS:

```sh
./scripts/rebuild.sh
```

The script rebuilds the board, runs DRC, exports Gerbers and Excellon drills,
packages the upload ZIP, and renders both sides. For another installation,
set `KICAD_CLI` and `KICAD_PYTHON` to the CLI executable and a Python interpreter
with KiCad's `pcbnew` module. Edit `scripts/build.py` to change the design.

## Sources

The Block I proportions come from the existing exposed-copper Block I in
`../uiuc-pcb-ruler/kicad/Footprints.pretty/Logo.kicad_mod` (the final two
polygons). Tiny deviations introduced by the original bitmap tracing are
normalized into straight, symmetric edges. The outline is widened horizontally
to the requested 30 × 40 mm dimensions while retaining the relative shoulder
widths and bar heights. Physical outline corners are
rounded for handling and routing.

University reference: [Illinois Block I logos](https://web.brand.illinois.edu/logos/)
and [brand guidelines](https://brand.illinois.edu/visual-identity/logo).
The university mark remains its owner's trademark; this project does not
claim university endorsement or grant trademark rights. This is a gold/green
PCB interpretation of the ruler artwork, rather than official orange/blue
color reproduction.
