# Mission operations procedures (draft)

How operators run the FORGE STAR payload. Commands are sent with `ground/ops/forge_ops.py`
(or fprime-gds) and **must be signed**: the payload drops unsigned, forged and replayed commands.

## Tools

```bash
# per-satellite command key: generate once, store in the operator secret store, load onto the satellite pre-launch
python3 ground/ops/cmd_auth.py new-key

# command + monitor (the satellite's ground link connects to this port)
python3 ground/ops/forge_ops.py --dict <PayloadTopologyDictionary.json> --port 50000 --key <hex key> \
    --cmd "Payload.cmdDisp.CMD_NO_OP" --listen 30
```

## Routine

| When | Do | Check |
|---|---|---|
| **Each gateway pass** | Nothing: the onboard pass predictor starts and ends the downlink | `PassStarted` / `PassEnded` events; `storeForward.BlocksSent` rising |
| **Weekly, or after a manoeuvre** | Upload fresh orbit elements: `Payload.passPredictor.PP_SET_ELEMENTS <epoch> <alt_km> <inc> <raan> <u> <gmst>` (from the latest TLE) | `ElementsLoaded`; `passPredictor.NextPassS` sensible |
| **New gateway** | `Payload.passPredictor.PP_SET_GATEWAY <slot> <lat> <lon> <mask_deg>` | `GatewaySet` |
| **Daily** | Review `storeForward.Stored`, `Dropped`, `Corrupted`, `cmdAuth.Rejected` | Dropped/Corrupted rising → investigate (buffer sizing, radiation) |

## Off-nominal

| Symptom | Action |
|---|---|
| **`EnteredSafe: low bus voltage`** | Leave in SAFE. Ask the bus operator for power status. When `modeManager.BusVolts` > 7.0 V: `Payload.modeManager.MM_NOMINAL` |
| **`EnteredSafe: no bus power report`** | Bus link lost: check bus health with the bus partner before returning to NOMINAL |
| **`cmdAuth.Rejected`** you did not cause | Possible spoofing attempt: log it, check ground key handling, consider key rotation |
| **`Scrubbed` events frequent** | Radiation upsets in payload memory: check orbit position (South Atlantic Anomaly), raise scrub rate |
| **Before a planned reset** | `Payload.storeForward.SF_SAVE`, wait for `Saved`; after boot expect `Restored` |
| **Ground queue of old messages** | `Payload.storeForward.SF_CLEAR` only if instructed: discarded messages are lost to customers |

## Key rotation

1. Generate a new key (`cmd_auth.py new-key`).
2. Uplink it through the bus partner's secure channel (key upload command: to be defined with the bus/ADCS partner).
3. Switch the ground signer to the new key and confirm with `CMD_NO_OP`.
4. Revoke and destroy the old key.

*Draft: to be reviewed against the bus partner's operations manual and turned into signed-off procedures before launch.*
