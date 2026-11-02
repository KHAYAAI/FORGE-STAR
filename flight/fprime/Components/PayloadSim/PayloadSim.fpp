module ForgeSat {

  @ Stands in for payload hardware when the flight software runs without it:
  @ an NB-IoT receiver (device messages), the onboard pass predictor (gateway passes)
  @ and the X-band downlink radio (writes link blocks to a file).
  @ On the satellite each output is replaced by the real driver; StoreForward is unchanged.
  passive component PayloadSim {

    @ 1 Hz tick from a rate group
    sync input port schedIn: Svc.Sched

    @ Device messages to StoreForward
    output port deviceOut: DeviceMsg

    @ Gateway pass state to StoreForward
    output port passOut: PassState

    @ Link blocks from StoreForward (what the downlink radio would transmit)
    sync input port linkIn: Fw.BufferSend

    @ Messages generated
    telemetry MessagesGenerated: U32

    @ Bytes "transmitted" to the ground
    telemetry BytesDownlinked: U32

    @ Gateway pass in progress
    telemetry PassActive: bool

    @ Downlink file opened
    event DownlinkFile(path: string size 80) severity activity high format "Downlink recording to {}"

    # ---------------- standard ports ----------------
    event port logOut
    text event port logTextOut
    time get port timeCaller
    telemetry port tlmOut
  }
}
