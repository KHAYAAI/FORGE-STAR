# FORGE STAR boards in Zener (trial)

A trial of [Diode's Zener language and `pcb` tool](https://github.com/diodeinc/pcb) (MIT licence) next to the
existing SKiDL pipeline in `hardware/boards/`. Boards are written as code; `pcb` checks them and produces KiCad files.

All designs here are first drafts with illustrative values. An electrical engineer must review them before fabrication.

| Board | File | What it is | Status |
|---|---|---|---|
| Payload interface board (PIB) | `boards/pib/pib.zen` | Port of the SKiDL board: MCU, CAN to the bus, radio power switch, telemetry | Builds, 28 components |
| IoT test device | `boards/iot_node/iot_node.zen` | Battery NB-IoT node with GNSS for the lab test-bed and field trials | Builds, 61 components |

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

## Open items before fabrication

- **Layout:** `pcb layout` needs KiCad 10. Placement and routing are not done for either board.
- **NTN module:** the IoT device uses the Quectel BC66 footprint. BC66 is terrestrial NB-IoT. The plan is to fit an
  NTN module in the same footprint (candidate: Quectel CC660D-LS). Pin compatibility is not yet verified.
- **1.8 V logic:** check MAX-M10S `VIO_SEL`, TMP117 minimum supply and BC66 `PWRKEY`/`RESET`/`PSM_EINT` levels
  against the data sheets.
- **Protection:** no SIM ESD protection, battery reverse-polarity protection or power switch on the IoT device.
- **TMP117 thermal pad** (pad 7) is left unconnected on both boards. `pcb build` warns about it.
- **RF:** antenna traces need 50 ohm controlled impedance; the matching network values are placeholders.
