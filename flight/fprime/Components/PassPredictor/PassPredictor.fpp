module ForgeSat {

  @ Onboard gateway pass predictor (flight/libforge forge_orbit.c: circular orbit + J2 + Earth rotation).
  @ Operators uplink orbit elements and gateway locations; the predictor raises and lowers the
  @ pass state that drives StoreForward's downlink.
  passive component PassPredictor {

    @ 1 Hz tick
    sync input port schedIn: Svc.Sched

    @ Pass state to StoreForward
    output port passOut: PassState

    @ Load orbit elements (epoch unix seconds; angles in degrees)
    sync command PP_SET_ELEMENTS(epoch: U32, altKm: F32, incDeg: F32, raanDeg: F32, uDeg: F32, gmstDeg: F32) opcode 0x00

    @ Set a gateway slot (0-7); a mask of zero or less disables the slot
    sync command PP_SET_GATEWAY(slot: U8, latDeg: F32, lonDeg: F32, maskDeg: F32) opcode 0x01

    @ Gateway in view now
    telemetry InView: bool

    @ Seconds until the next gateway pass (-1 = none within 2 days)
    telemetry NextPassS: F32

    @ Elements loaded
    event ElementsLoaded(epoch: U32, altKm: F32, incDeg: F32) severity activity high format "Orbit elements loaded: epoch {}, {.1f} km, {.1f} deg"

    @ Gateway slot set
    event GatewaySet(slot: U8, latDeg: F32, lonDeg: F32) severity activity low format "Gateway {} at {.2f}, {.2f}"

    @ Pass state changed
    event PassPredicted(inView: bool) severity activity low format "Gateway in view: {}"

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
