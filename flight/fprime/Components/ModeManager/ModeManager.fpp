module ForgeSat {

  @ Payload mode manager: puts the payload in SAFE mode (transmitter off, storing continues) on
  @ low bus voltage, loss of bus power reports, or operator command. Leaving SAFE needs an operator
  @ command and healthy power (spacecraft convention: no automatic recovery).
  passive component ModeManager {

    @ 1 Hz tick
    sync input port schedIn: Svc.Sched

    @ Bus power reports
    sync input port busPowerIn: BusPower

    @ Mode out to the payload
    output port modeOut: Mode

    @ Enter safe mode
    sync command MM_SAFE opcode 0x00

    @ Return to nominal (refused while power is low)
    sync command MM_NOMINAL opcode 0x01

    @ Current mode
    telemetry Safe: bool

    @ Last reported bus voltage
    telemetry BusVolts: F32

    @ Entered safe mode
    event EnteredSafe(reason: string size 40) severity warning high format "Payload SAFE mode: {}"

    @ Back to nominal
    event ExitedSafe severity activity high format "Payload back to NOMINAL"

    @ Nominal refused
    event NominalRefused(volts: F32) severity warning low format "NOMINAL refused: bus at {.2f} V"

    # ---------------- standard ports ----------------
    command recv port cmdIn
    command reg port cmdRegOut
    command resp port cmdResponseOut
    event port logOut
    text event port logTextOut
    time get port timeCaller
    telemetry port tlmOut
  }
}
