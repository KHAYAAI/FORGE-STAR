module ForgeSat {

  @ Command authentication: sits between the uplink deframer and the command dispatcher.
  @ Each uplinked command is ChaCha20-encrypted and ends with a u32 counter and an HMAC-SHA256 tag
  @ over the ciphertext (flight/libforge forge_auth.c). Sign-only mode: FORGE_CMD_ENCRYPT=0.
  @ Forged, corrupted or replayed commands are dropped before anything executes.
  passive component CmdAuth {

    @ Commands from the deframer (signed)
    sync input port comIn: Fw.Com

    @ Verified commands to the command dispatcher (trailer removed)
    output port comOut: Fw.Com

    @ Command responses from the dispatcher
    sync input port cmdResponseIn: Fw.CmdResponse

    @ Command responses back to the deframer
    output port cmdResponseOut: Fw.CmdResponse

    @ Commands accepted
    telemetry Accepted: U32

    @ Commands rejected
    telemetry Rejected: U32

    @ Highest command counter accepted (replay protection)
    telemetry LastCounter: U32

    @ Reasons a command can be rejected
    enum RejectReason { TOO_SHORT, BAD_SIGNATURE, REPLAY, NO_KEY }

    @ An uplinked command was rejected
    event Rejected(reason: RejectReason) severity warning high format "Uplinked command rejected: {}" throttle 20

    @ Authentication key loaded
    event KeyLoaded(keyBytes: U32) severity activity high format "Command authentication on ({} byte key)"

    # ---------------- standard ports ----------------
    event port logOut
    text event port logTextOut
    time get port timeCaller
    telemetry port tlmOut
  }
}
