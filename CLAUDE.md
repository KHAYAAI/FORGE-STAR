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
- `tests/`: pytest suite. `.github/workflows/ci.yml` runs the tests, a quick simulation, the model, the PDF build and the image builds on every push.
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
- **heypcb.ai:** payload processor, radio carriers, bus interface, ground and test boards. It doesn't cover structure, thermal, high-performance RF/antennas, radiation qualification or bus integration.

## FORGE ecosystem links
FORGE STAR provides connectivity for the other FORGE ventures:
- **FORGE Freight:** tracking
- **Maritime USV venture:** over-the-horizon link and AIS
- **FORGE VOCAL:** satellite USSD/messaging fallback
- **ForgePay:** offline settlement
- **FORGE EYE:** sovereign data feed
- **Autonomy/robotics:** telemetry

## Good next engineering tasks for Claude Code
Done (Nov 2026): coverage sim with J2 and link budget, store-and-forward service, ThingsBoard provisioning + dashboard, ownership and monthly cash in the model, CI, PDF rendered from markdown.
1. Run ThingsBoard for real (`--profile full`) and check the dashboard renders. Docker Hub rate-limited the image in the build session, so it was only tested against a fake API.
2. Payload antenna trade study: isoflux vs patch vs small phased array, to close the NB-IoT downlink at 20–25°.
3. Orekit cross-check of `forgestar/orbits.py` (drag, full gravity) and an OpenSN network emulation.
4. Gateway downlink handler for real passes: SatNOGS observation → decoder → Kafka `iot.uplink` (replaces `sandf` in production).
5. Regulatory tracker (ICASA/ITU filing milestones, spectrum counsel actions) and a grant pipeline tracker.

## Conventions
- Write in plain English with short sentences. Use tables for comparisons.
- Mark figures as illustrative. Flag anything about the market or regulation for re-verification (Starlink/ICASA status changes).
- Company entity on documents: currently "MYFORGE PTY LTD". Confirm with Tebogo before external use.
