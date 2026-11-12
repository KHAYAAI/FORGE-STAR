# FORGE STAR boards in Zener (trial)

A trial of [Diode's Zener language and `pcb` tool](https://github.com/diodeinc/pcb) (MIT licence) next to the
existing SKiDL pipeline in `hardware/boards/`. Boards are written as code; `pcb` checks them and produces KiCad files.

All designs here are first drafts with illustrative values. An electrical engineer must review them before fabrication.

| Board | File | What it is | Status |
|---|---|---|---|
| Payload interface board (PIB) | `boards/pib/pib.zen` | Port of the SKiDL board: MCU, CAN to the bus, radio power switch, telemetry | Builds, 35 components |
| IoT test device | `boards/iot_node/iot_node.zen` | Battery NB-IoT node with GNSS for the lab test-bed and field trials | Builds, 71 components |

## Use

```bash
curl -fsSL https://raw.githubusercontent.com/diodeinc/pcb/main/install.sh | bash   # installs pcb
cd hardware/zener
pcb build boards/pib/pib.zen                  # check the design
pcb build boards/iot_node/iot_node.zen
pcb bom --offline boards/iot_node/iot_node.zen   # parts list, nothing sent to Diode
pcb layout --no-open boards/pib/pib.zen       # KiCad board file (needs KiCad 10)
```

`pcb bom` without `--offline`, `pcb quote` and `pcb auth` send design data to Diode's servers. Do not use them
until an NDA and an export-control check are in place.

## Parts

Each board keeps its own symbols and footprints in `parts/`. Add one from the installed KiCad libraries with:

```bash
python3 tools/import_kicad_part.py boards/iot_node RF_GSM:BC66
```

## Layout

```bash
pcb layout --no-open boards/iot_node/iot_node.zen   # creates or updates the KiCad board (needs KiCad 10)
python3 tools/place.py boards/iot_node              # positions from placement.json, outline, ground pours
FREEROUTING_JAR=... python3 tools/route.py boards/iot_node   # autoroute (not yet run)
```

| Board | Size | Placement | Routing |
|---|---|---|---|
| Payload interface board | 58 x 40 mm, 4 layers | Done, no placement errors in KiCad DRC | Not done: 51 connections open |
| IoT test device | 84 x 45 mm, 4 layers | Done, no placement errors in KiCad DRC | Not done: 101 connections open |

Both boards have four grounded M2.5 mounting holes and three fiducials.

3D pictures are in `docs/img/` (`pib-3d.png`, `iot_node-3d.png`) and 3D STEP files sit next to each board.
Several chips show as bare pads because KiCad's 3D model library is not installed here.

## Datasheet checks done (from public sources, November 2026)

| Item | Finding | Result in the design |
|---|---|---|
| MAX-M10S `VIO_SEL` | u-blox: connect to GND for 1.8 V, leave open for 3.3 V | Tied to GND. Correct for 1.8 V. |
| MAX-M10S supply | 1.76 V to 1.98 V in 1.8 V mode | The 1.8 V regulator's tolerance leaves little margin at the low end. Consider a tighter regulator. |
| BC66 `PWRKEY` | Thresholds are relative to VBAT; Quectel recommends an open-drain or open-collector driver | Driven by an open-collector transistor. Matches. |
| BC66 `RESET`, `PSM_EINT` | Active low | Driven the same way. The voltage domain of `PSM_EINT` was not found; the transistor makes it safe either way. |
| BC66 pin numbers | PWRKEY 7, RESET 15, PSM_EINT 19 | Match the KiCad symbol. |
| CC660D-LS (satellite module) | Same 17.7 x 15.8 x 2.0 mm LCC+LGA outline as BC66; has PWRKEY, PSM_EINT, UART, USIM, ADC; needs an external GNSS module | Outline and interfaces fit, and the board already has GNSS. **The pin-by-pin map is still unconfirmed**: Quectel's CC660D-LS hardware design manual is needed. |
| BC660K-GL (same footprint family) | No PWRKEY; adds BOOT and VIO_SEL; do not pull MAIN_RXD up to VDD_EXT | Not a drop-in for this board without changes. |

## Open items before fabrication

- **Routing:** neither board is routed. Run `tools/route.py` with Freerouting, or route by hand in KiCad.
- **CC660D-LS pin map:** get the hardware design manual from Quectel and compare every pin.
- **RF:** antenna traces need 50 ohm controlled impedance; the matching network values are placeholders that need
  measurement on a network analyser.
- **Engineer review:** an electrical engineer must review schematic, placement and routing. The checks above are
  from public datasheet summaries, not a substitute for that review.
