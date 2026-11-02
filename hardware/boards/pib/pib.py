"""FORGE STAR payload interface board (PIB), rev A: circuit as code (SKiDL).

What it does
  * STM32L432KC runs flight/libforge (store-and-forward, frames, FEC encode)
  * CAN to the satellite bus (SN65HVD230, 3.3 V)
  * high-side switch for the payload radio (AO3401A P-FET driven by a 2N7002)
  * radio current/voltage telemetry (INA219, 50 mΩ shunt) and board temperature (TMP117)
  * UART to the radio/SDR module, SWD for programming

Interfaces
  J1 bus:   1 VIN (5 V)  2 GND  3 CANH  4 CANL  5 GND
  J2 radio: 1 RADIO_PWR  2 GND  3 UART_TX  4 UART_RX  5 GND
  J3 SWD:   1 +3V3  2 SWDIO  3 SWCLK  4 NRST  5 GND

Run: python3 hardware/boards/pib/pib.py   -> pib.net + ERC report (hardware/build/pib/)
Parts come from KiCad's standard libraries. Values are a first design: review before fab.
"""
from __future__ import annotations

import sys
from pathlib import Path

import builtins

from skidl import ERC, KICAD7, Net, Part, generate_netlist, lib_search_paths, set_default_tool

set_default_tool(KICAD7)
lib_search_paths[KICAD7].append("/usr/share/kicad/symbols")

NC = builtins.NC  # SKiDL installs its no-connect net as a builtin
OUT = Path(__file__).resolve().parents[2] / "build" / "pib"
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"


def R(value, fp=R0603):
    return Part("Device", "R", value=value, footprint=fp)


def C(value, fp=C0603):
    return Part("Device", "C", value=value, footprint=fp)


def build():
    vin, gnd, v33 = Net("VIN"), Net("GND"), Net("+3V3")
    vin_s, radio_pwr = Net("VIN_SENSE"), Net("RADIO_PWR")
    canh, canl, can_tx, can_rx = Net("CANH"), Net("CANL"), Net("CAN_TX"), Net("CAN_RX")
    scl, sda = Net("I2C_SCL"), Net("I2C_SDA")
    tx, rx, en = Net("UART_TX"), Net("UART_RX"), Net("RADIO_EN")
    swdio, swclk, nrst = Net("SWDIO"), Net("SWCLK"), Net("NRST")
    for n in (vin, gnd, v33):
        n.drive = 3  # POWER drive so ERC accepts connector-fed rails

    # --- 3.3 V regulator ---
    u_reg = Part("Regulator_Linear", "AP2112K-3.3")
    u_reg["VIN"] += vin; u_reg["EN"] += vin; u_reg["GND"] += gnd; u_reg["VOUT"] += v33; u_reg["NC"] += NC
    C("1u")[1, 2] += vin, gnd
    C("1u")[1, 2] += v33, gnd

    # --- MCU ---
    mcu = Part("MCU_ST_STM32L4", "STM32L432KCUx")
    mcu["VDD"] += v33; mcu["VDDA"] += v33; mcu["VSS"] += gnd
    for v in ("100n", "100n", "4u7"):
        C(v)[1, 2] += v33, gnd
    mcu["NRST"] += nrst
    C("100n")[1, 2] += nrst, gnd
    R("10k")[1, 2] += mcu["PH3"], gnd                 # BOOT0 low: boot from flash
    mcu["PA11"] += can_rx; mcu["PA12"] += can_tx      # CAN1
    mcu["PB6"] += scl; mcu["PB7"] += sda              # I2C1
    mcu["PA2"] += tx; mcu["PA3"] += rx                # USART2 to radio
    mcu["PA0"] += en                                  # radio power enable
    mcu["PA13"] += swdio; mcu["PA14"] += swclk
    for p in ("PA1", "PA4", "PA5", "PA6", "PA7", "PA8", "PA9", "PA10", "PA15",
              "PB0", "PB1", "PB3", "PB4", "PB5", "PC14", "PC15"):
        mcu[p] += NC
    R("4k7")[1, 2] += scl, v33
    R("4k7")[1, 2] += sda, v33

    # --- CAN transceiver ---
    u_can = Part("Interface_CAN_LIN", "SN65HVD230")
    u_can["VCC"] += v33; u_can["GND"] += gnd; u_can["Rs"] += gnd   # Rs low: high-speed mode
    u_can["D"] += can_tx; u_can["R"] += can_rx; u_can["CANH"] += canh; u_can["CANL"] += canl
    u_can["Vref"] += NC
    C("100n")[1, 2] += v33, gnd
    R("120")[1, 2] += canh, canl                      # termination (DNP if not a bus end)

    # --- radio power: shunt -> high-side P-FET switch ---
    R("0R05", "Resistor_SMD:R_1206_3216Metric")[1, 2] += vin, vin_s
    q_sw = Part("Transistor_FET", "AO3401A")
    q_sw["S"] += vin_s; q_sw["D"] += radio_pwr
    gate = Net("SW_GATE")
    q_sw["G"] += gate
    R("100k")[1, 2] += gate, vin_s                    # off by default
    q_drv = Part("Transistor_FET", "2N7002")
    q_drv["D"] += gate; q_drv["S"] += gnd
    drv_g = Net("DRV_GATE")
    q_drv["G"] += drv_g
    R("100")[1, 2] += en, drv_g
    R("100k")[1, 2] += drv_g, gnd                     # radio stays off while the MCU boots
    C("10u", "Capacitor_SMD:C_1206_3216Metric")[1, 2] += radio_pwr, gnd

    # --- telemetry ---
    u_ina = Part("Sensor_Energy", "INA219AxD")
    u_ina["VS"] += v33; u_ina["GND"] += gnd; u_ina["A0"] += gnd; u_ina["A1"] += gnd   # I2C 0x40
    u_ina["IN+"] += vin; u_ina["IN-"] += vin_s; u_ina["SCL"] += scl; u_ina["SDA"] += sda
    C("100n")[1, 2] += v33, gnd
    u_tmp = Part("Sensor_Temperature", "TMP117xxDRV")
    u_tmp["V+"] += v33; u_tmp["GND"] += gnd; u_tmp["ADD0"] += gnd                     # I2C 0x48
    u_tmp["SCL"] += scl; u_tmp["SDA"] += sda; u_tmp["ALERT"] += NC
    C("100n")[1, 2] += v33, gnd

    # --- connectors ---
    hdr = "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
    j1 = Part("Connector_Generic", "Conn_01x05", ref="J1", value="BUS", footprint=hdr)
    j1[1, 2, 3, 4, 5] += vin, gnd, canh, canl, gnd
    j2 = Part("Connector_Generic", "Conn_01x05", ref="J2", value="RADIO", footprint=hdr)
    j2[1, 2, 3, 4, 5] += radio_pwr, gnd, tx, rx, gnd
    j3 = Part("Connector_Generic", "Conn_01x05", ref="J3", value="SWD", footprint=hdr)
    j3[1, 2, 3, 4, 5] += v33, swdio, swclk, nrst, gnd


# Fixed positions (mm, rotation): ICs in the middle, connectors on the edges. Passives auto-place.
IC_POS = {"U2": (25, 17, 0), "U1": (10, 9, 0), "U3": (40, 9, 0), "U4": (39, 26, 0), "U5": (25, 29, 0),
          "Q1": (11, 26, 0), "Q2": (17, 31, 0)}
EDGE_POS = {"J1": (3.0, 14, 0), "J2": (47.0, 14, 0), "J3": (16, 3.0, 90)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build()
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        ERC()
    report = buf.getvalue()
    (OUT / "erc.txt").write_text(report)
    generate_netlist(file_=str(OUT / "pib.net"))
    errors = [l for l in report.splitlines() if "ERROR" in l]
    print(f"netlist: {OUT / 'pib.net'}; ERC errors: {len(errors)}")
    for e in errors[:20]:
        print(" ", e)
    if errors or "--netlist-only" in sys.argv:
        return 1 if errors else 0
    import json
    circuit = builtins.default_circuit
    spec = {"name": "pib", "width_mm": 50, "height_mm": 36, "ic_positions": IC_POS, "edge_positions": EDGE_POS,
            "parts": [{"ref": p.ref, "name": p.name, "value": str(p.value), "footprint": p.footprint,
                       "pins": {str(pin.num): pin.net.name for pin in p.pins
                                if pin.net is not None and pin.net.name and not pin.net.name.startswith("__NOCONNECT")}}
                      for p in circuit.parts]}
    (OUT / "pib.json").write_text(json.dumps(spec, indent=1))
    print(f"board spec: {OUT / 'pib.json'} ({len(spec['parts'])} parts)")
    # PCB stage runs in its own process (KiCad's pcbnew module): hardware/tools/forge_pcb.py
    import subprocess
    res = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "forge_pcb.py"),
                          str(OUT / "pib.json")])
    return res.returncode



if __name__ == "__main__":
    sys.exit(main())
