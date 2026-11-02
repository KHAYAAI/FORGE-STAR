module ForgeSat {

  @ One device message received over the NB-IoT NTN uplink
  port DeviceMsg(
    shortId: U32 @< crc32 of the device name
    tCreated: U32 @< device timestamp, unix seconds
    latE5: I32 @< latitude x 1e5
    lonE5: I32 @< longitude x 1e5
    payload: string size 200 @< compact JSON
  )

  @ Gateway pass state from the onboard pass predictor (true = gateway in view)
  port PassState(inView: bool)

  @ Store-and-forward payload: buffers device messages on board and, during a
  @ gateway pass, sends them down as forgestar frames v1 wrapped in RS(255,223) link blocks.
  @ The core is flight/libforge (C99), shared byte-for-byte with the Python ground segment.
  active component StoreForward {

    @ Device messages from the NB-IoT receiver
    async input port deviceIn: DeviceMsg

    @ Link blocks out to the downlink radio (buffer valid for the duration of the call)
    output port linkOut: Fw.BufferSend

    @ Rate group tick: while a pass is active, send one link block per tick
    async input port schedIn: Svc.Sched

    @ Pass state from the onboard pass predictor (same effect as SF_PASS_START / SF_PASS_END)
    async input port passIn: PassState

    @ Start a downlink pass (gateway in view)
    async command SF_PASS_START opcode 0x00

    @ End the downlink pass
    async command SF_PASS_END opcode 0x01

    @ Discard everything stored on board
    async command SF_CLEAR opcode 0x02

    @ Messages currently stored on board
    telemetry Stored: U32

    @ Messages dropped because the buffer was full
    telemetry Dropped: U32

    @ Link blocks sent since boot
    telemetry BlocksSent: U32

    @ A downlink pass started
    event PassStarted(stored: U32) severity activity high format "Downlink pass started, {} messages on board"

    @ A downlink pass ended
    event PassEnded(blocks: U32, records: U32) severity activity high format "Downlink pass ended: {} link blocks, {} messages sent"

    @ Store-and-forward buffer full
    event BufferFull severity warning high format "Store-and-forward buffer full, message dropped" throttle 5

    @ Buffer cleared by command
    event Cleared(discarded: U32) severity activity high format "Store-and-forward buffer cleared, {} messages discarded"

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
