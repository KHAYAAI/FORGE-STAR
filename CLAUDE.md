# FORGE STAR — project context for Claude Code

FORGE STAR is a South African sovereign LEO satellite data company in the FORGE ecosystem, founded by Tebogo (Tebza) Mvelase.
Positioning: **Africa's sovereign satellite data network**, a compliant, locally owned LEO infrastructure for the assets, vessels and people that terrestrial networks will never reach.
It's inspired by Exosat (Singapore), but it's Africa-first and starts with IoT, not broadband.

## Source of truth
- `docs/strategy.md`: the full strategy (business model, stack, stages, capital, valuation, risks). Edit this first; it's the canonical text.
- `scripts/build_pdf.py`: builds the FORGE-style PDF into `output/FORGE_STAR_Strategy.pdf` (ReportLab with DejaVu fonts). Run `python3 scripts/build_pdf.py`.
  It renders `docs/strategy.md` directly. Keep to the markdown subset documented at the top of its parser. Don't hard-code content in the script.
- `forgestar/`: shared Python package: `orbits.py` (circular orbits with J2, passes), `linkbudget.py` (per-elevation margins), `logic.py` (store-and-forward core).
- `sim/coverage_sim.py`: coverage, revisit and gateway passes → `sim/results/` (plus `link_budget.md`). The mask comes from the link budget; `MIN_ELEV_DEG` overrides it.
- `model/financial_model.py` + `model/assumptions.yaml`: Stages 0–3 model → `model/results/` (CSV, xlsx with monthly cash and ownership sheets, summary with consistency checks including the 30% HDG rule).
- `ground/docker-compose.yml`: Stage 0 platform (TimescaleDB, Kafka, ingest, `sandf` simulated satellites, device simulator; `--profile full` adds ThingsBoard; `--profile radio` adds SatNOGS). `ground/thingsboard/provision.py` creates the devices and dashboard.
- `forgestar/frames.py`: the store-and-forward downlink frame format (v1) shared by payload firmware and gateway. `ground/gateway/` decodes frames (Kafka `ground.frames`, a frames folder, or SatNOGS Network) into `iot.uplink`.
- `sim/latency_sim.py`: end-to-end delivery time (satellite wait + gateway wait), constellations × gateway networks × mask; `POLICY=single|resend`.
- `sim/antenna_trade.py`: payload antenna options vs usable elevation and service. `sim/sgp4_crosscheck.py`: validates `forgestar/orbits.py` against SGP4.
- `readiness/readiness.yaml` + `readiness/tracker.py`: the outside work (ICASA/ITU, ownership, funding, lab, orbit, customers) with dependencies → `readiness/STATUS.md` (critical path, late items, Gantt, plan options). Update statuses there.
- `forgestar/fec.py`: radio link layer: RS(255,223) with CCSDS parameters **in the CCSDS dual basis by default** (libfec-compatible), own encoder/decoder, CCSDS randomiser, ASM. `basis="conventional"` keeps the old form.
- `flight/libforge/`: C99 core: frames + ACKs, RS encode, store-and-forward ring buffer (per-record CRC, scrubbing, save/load), `forge_auth` (SHA-256/HMAC command auth), `forge_orbit` (onboard pass predictor), `forge_device` (device SDK). 4 ctest suites. Vectors: `test/make_vectors.py`, `test/make_orbit_vectors.py`.
- `flight/fprime/`: F´ v3.5.1 project (submodule `flight/fprime/fprime`). Components: `StoreForward` (6 UTs; acks, safe mode, persistence `FORGE_STORE`), `CmdAuth` (HMAC command authentication between deframer and dispatcher; key `FORGE_CMD_KEY`), `ModeManager` (safe mode on low bus voltage / lost bus link / command), `PassPredictor` (onboard passes; `FORGE_ELEMENTS`, `FORGE_SIM_S_PER_TICK`), `PayloadSim` (hardware stand-in). Deployment `Payload/`. Build: `fprime-util generate && fprime-util build`; ARM: `fprime-util generate aarch64-linux && fprime-util build aarch64-linux`. Run and verify: `python3 flight/run_payload.py [--arch aarch64]` (QEMU for ARM). `FORGE_CYCLE_MS` speeds up the 1 Hz loop.
- `ground/ops/`: mission ops (`forge_ops.py`: F´ framing, dictionary decode, signed commands; `cmd_auth.py`). Procedures in `docs/operations/`.
- `forgestar/modem.py`: software BPSK modem (RRC, Doppler, timing, PLL); gateway reads `*.cf32` IQ files.
- `ground/deploy/`: production overlay (TLS via Caddy, backups, no exposed data ports, required secrets).
- `ground/api/`: customer REST API (FastAPI): devices, messages, SLA, monthly usage; rate limit, audit log, `/metrics`, key revocation. Keys: `docker compose exec api python app.py create-key "<customer>"`.
- `forgestar/params/rf.yaml`: radio parameters with source/status. `docs/verification/register.yaml` → `scripts/verify_register.py` → `docs/verification/VERIFY.md`: everything still to confirm.
- `hardware/`: in-house PCB pipeline (SKiDL → KiCad pcbnew placement → Freerouting → DRC → fab zip). Board 1: payload interface board (`hardware/boards/pib/pib.py`).
- `tests/`: pytest suite (`pytest.ini` limits collection to `tests/`). `.github/workflows/ci.yml` runs the tests, a quick simulation, the model, the PDF build and the image builds on every push.
- `docs/ntn-testbed-plan.md`: NB-IoT NTN lab plan.
- `research/`: original inputs (the Exosat analysis, the open-source stack map, the first FORGE STAR plan, the v1 strategy summary). Read-only reference.

## Decisions already made (don't relitigate without reason)
- **Wedge:** NB-IoT NTN (3GPP Rel-17) and store-and-forward messaging, satellite AIS/VDES, and sovereign data relay. No consumer broadband early on.
- **D2C:** handled later through a partner, not on our own ~$300k small satellites (the antenna aperture doesn't close).
- **Buy, don't build, the bus:** from SA suppliers (Dragonfly Aerospace, CubeSpace). We own the payload, network, ground segment, data platform and sovereign operations.
- **Demonstrator:** hosted payload first, then a 6U–12U. No PocketQube.
- **Spectrum:** a modest NGSO filing (24–100 satellites) in IoT-appropriate bands via ICASA. Engage specialist counsel early.
- **Ownership:** design the cap table for ICASA's 30% historically-disadvantaged-group ownership rule from day one. It's both a moat against Starlink and a constraint on us.
- **Sequencing:** ground and services company first (revenue before orbit), then the satellite company.

## Key numbers (illustrative; keep consistent across docs)
| Stage | Sats | Timing | Capital | Valuation (illustr.) |
|---|---|---|---|---|
| 0 Ground first | 0 | 0–12 mo | $1–3M (bootstrap ~$0.2–0.5M) | $5–30M (0–1 combined) |
| 1 Demonstrator | 1–2 | 12–30 mo | $5–12M (lean $0.5–3M) | |
| 2 Early service | 6–12 | yr 2.5–3.5 | $15–30M | $50–150M |
| 3 Operational | 24–48 | yr 3.5–5 | $30–60M + prepayments | $200–500M |
| 4 Continuous narrowband | 80–150 | yr 5–7 | $100–250M co-financed | $1–3B |
| 5 Broadband | hundreds+ | yr 7+ | $0.5–2B+ gov/DFI | $3–10B+ |

- Cumulative to Stage 3: about $51–105M gross, or about $40–75M equity.
- Coverage of the path to full launch (24–48 sats): open source + heypcb.ai covers **~28%**. With Claude Code assist it reaches **~43%**.
- Bootstrapping covers about 10% of the work and about 1% of the capital to full launch, but ~80–100% of a hosted-payload first launch.
- Satellites needed for frequent IoT (20–40 min): SA 16–24, SADC 24–36, Africa 30–48 **on average**. Simulation shows that a worst-case gap under ~1 h needs ~36–48 (SA) and ~80 (Africa) at a 10° mask. Continuous narrowband: 80–150 for Africa.
- Financial model base case: Stage 3 (36 sats, yr 6) revenue ~$37M, equity ~$50M, gross need ~$38M. Monthly cash dips ~$0.5M negative at the start of year 2: close the seed round by the end of year 1. HDG share stays >50% only if each round has HDG-qualifying investors.
- Schedule: with dependencies chained, Stage 2 lands ~61 months from start if run in sequence; ~43 months on the fast track (own demonstrator in parallel with the hosted payload, Series A on the hosted-payload result).
- **Stage 3 design:** 42 sats @45° + 6 @10° (48) + 6 gateways (Hartebeesthoek, Cape Town, Walvis Bay, Mauritius, Malindi, Lagos) + isoflux antenna → 95% ≤ 26 min at all 7 customer sites (`sim/equatorial_study.py`). Re-send-until-acked is built (ACK frames, gateway dedupe); live run: 95% ≤ ~40 min on 24 sats, SA gateways.
- Stress tests: no sovereign contract → year-6 revenue ~$19.5M (biggest commercial risk); IoT at $1 → ~$31.6M. Seed must close by month 12 → raise on signed LOIs (tracker option `seed_on_lois`, earliest ~month 11).
- Launch readiness: `python3 scripts/launch_readiness.py` → `docs/LAUNCH_READINESS.md` (TRL in `readiness/trl.yaml`). First payload in orbit: ~Feb 2029 fast track; critical path runs through ICASA (counsel → pre-application → test licence → lab).
- IoT pricing: entrants at ~$1/device/month; at that price year-6 revenue ~$31.6M (vs $37.5M). The sovereign contract is the real dependency.
- Antenna: demo = patch + deeper NB-IoT repetition (mask ~26°); Stage 2 = shaped isoflux beam (mask 16–21°, needs ~25–40 W during passes).
- Link budget: NB-IoT uplink closes from ~22° (the coverage mask). The downlink only closes from ~37° with a 14 dBi patch: the payload antenna is the RF design driver.

## Open-source stack
- **Flight:** F´ (primary), cFS (alternative), libcsp, Zephyr/FreeRTOS
- **Reference hardware:** LibreCube, BIRDS
- **Design tools:** FreeCAD, KiCad
- **RF:** GNU Radio, SoapySDR, gr-satellites, SatDump, AIS-catcher/gr-ais
- **NTN:** OpenAirInterface NTN, Open5GS/free5GC
- **Ground:** SatNOGS, Gpredict+Hamlib, Yamcs or OpenC3 COSMOS, Open MCT, TinyGS
- **Flight dynamics:** Orekit, GMAT, Skyfield
- **Constellation emulation:** OpenSN
- **Platform:** ThingsBoard, Kafka, PostgreSQL+TimescaleDB (hosted in SA)
- **PCB design:** in house with SKiDL + KiCad + Freerouting + kicad-cli (`hardware/`), instead of heypcb.ai. Fork open CubeSat boards (LibreCube, OreSat, PyCubed). Neither covers structure, thermal, high-performance RF/antennas, radiation qualification or bus integration.

## FORGE ecosystem links
FORGE STAR provides connectivity for the other FORGE ventures:
- **FORGE Freight:** tracking
- **Maritime USV venture:** over-the-horizon link and AIS
- **FORGE VOCAL:** satellite USSD/messaging fallback
- **ForgePay:** offline settlement
- **FORGE EYE:** sovereign data feed
- **Autonomy/robotics:** telemetry

## Good next engineering tasks for Claude Code
Done (Nov 2026): signed commanding, safe mode, persistence + memory scrubbing, onboard pass predictor, device SDK, mission ops tool, software modem, production overlay, API hardening.
Hardware-dependent (blocked until lab kit / bus partner / board exist): NB-IoT NTN base station on the payload SDR (OpenAirInterface), real radio + bus drivers, payload computer port, HIL and qualification tests.
Still possible without hardware:
1. CCSDS convolutional inner code (K=7, r=1/2) + Viterbi in `forgestar/fec.py` and libforge (~3 dB link margin).
2. Command encryption (AES-GCM) on top of `CmdAuth`; key-upload command design with the bus partner.
3. sandf multi-shell (42+6) so the live stack runs the Stage 3 design; ITU filing parameter sheet.
4. Customer onboarding + billing service (from `/v1/report`); POPIA retention policies in TimescaleDB.
5. Autoroute the payload interface board once Freerouting is approved.

## Conventions
- Write in plain English with short sentences. Use tables for comparisons.
- Mark figures as illustrative. Flag anything about the market or regulation for re-verification (Starlink/ICASA status changes).
- Company entity on documents: currently "MYFORGE PTY LTD". Confirm with Tebogo before external use.
