# FORGE STAR — Technical and Investor Brief

> Africa's sovereign satellite data network

All figures are illustrative. Regulatory, market and vendor facts need confirming before external commitments.

---

## 00 · How to read this
### One document, several readers

@reader Everyone

FORGE STAR is a South African company building a locally owned low-Earth-orbit network for IoT, maritime AIS and sovereign data relay. It runs as a ground and services company first (revenue before orbit), then becomes a satellite operator. Each section below is written for a specific reader, and you can read any of them on its own.

| Section | Written for | What you get |
|---|---|---|
| **01 Executive summary** | Investors, board | The case in one page |
| **02 Market and business model** | Investors | Customers, revenue lines, why now |
| **03 Financials and stress tests** | Investors, CFO | Capital need, revenue path, downside cases |
| **04 Regulation and ownership** | Counsel, investors | ICASA, ITU, the 30% HDG rule |
| **05 System architecture** | Everyone | How the network works end to end |
| **06 Constellation and RF design** | Systems and RF engineers | Orbits, coverage, delivery time, link budget, coding |
| **07 Flight software** | Software and flight engineers | F´ deployment, security, safe mode |
| **08 Ground segment and platform** | Software, operations, customers' IT | Gateway, data platform, API, billing |
| **09 Hardware: build, buy, bridge** | Hardware and RF engineers, partners | What we build, what we buy, who covers the gaps |
| **10 Evidence and maturity** | Technical due diligence | Tests, CI, TRL, what is verified |
| **11 Path to launch** | Everyone | Timeline, critical path, next 90 days |
| **12 Risks** | Investors, board | What could break the plan |
| **13 Where FORGE STAR reaches** | Investors, partners, business development | Global coverage map, service by region, first export markets |
| **14 Sources and caveats** | Everyone | What was checked, and what still needs confirming |

---

## 01 · Executive summary
### FORGE STAR in one page

@reader Investors and board

> **FORGE STAR is Africa's sovereign satellite data network:** locally owned LEO infrastructure that connects the assets, vessels and people that terrestrial networks will never reach, with the data landed and hosted in South Africa.

| Question | Answer |
|---|---|
| **What we sell** | Satellite IoT connectivity, maritime AIS data, sovereign data relay; later wholesale capacity to mobile operators and constellation-in-a-box for African states |
| **Who buys** | Mining, agriculture, water, conservation, fisheries and Navy, logistics corridors, the SA government, FORGE ecosystem ventures |
| **Why us** | Compliant with ICASA's local-ownership rules where Starlink is not licensed; sovereign data hosting; Africa-first design |
| **Stage 3 design** | 48 satellites (42 at 45° + 6 at 10°) and 6 gateways: 95% of messages delivered within 26 minutes at every modelled customer site |
| **Measured, not just modelled** | The full platform runs end to end on a simulated constellation: 95% of satellite messages delivered within 9 minutes in a live run |
| **Capital** | ~$50M equity to an operational network (Stage 3); gross need ~$47M (base case) |
| **Revenue** | ~$37.5M a year at Stage 3 (year 6, base case) |
| **First payload in orbit** | ~April 2029 on the fast track (hosted payload); own satellite ~June 2029 |
| **What it waits on** | Spectrum counsel and ICASA, the bus partner, the lab grant, signed LOIs — not software |

**What already exists.** The flight software (NASA F´), the store-and-forward core in C, the radio link layer, the gateway, the data platform, dashboards, customer API, billing, the constellation and financial models, an in-house PCB pipeline and a readiness tracker. All of it is in one repository and tested on every change.

---

## 02 · Market and business model
### Who pays, for what, and why now

@reader Investors

#### Why now

- **Starlink is not licensed in South Africa.** ICASA's 30% historically-disadvantaged-group (HDG) ownership rule applies; FORGE STAR is designed to comply.
- **The equity-equivalent route is contested.** ICASA says it needs a change to the Electronic Communications Act. This is the main threat to the moat, and the plan does not depend on Starlink staying out.
- **Chinese constellations are behind target and carry alignment risk.** Other operators do not serve African sovereign demand or mass IoT.
- **Early costs have collapsed.** Open-source flight and ground software and AI-assisted design make a demonstrator affordable.

#### Customers and pricing

| Segment | Buyers | Offer | Pricing |
|---|---|---|---|
| **Maritime and security** | SA Navy, DFFE, SAMSA, ports, insurers | AIS vessel tracking, illegal-fishing detection | Annual subscription or contract |
| **Mining and energy** | Mining houses, Eskom, IPPs | Remote asset monitoring | Per device per month + platform fee |
| **Agriculture and water** | Farms, co-ops, water boards | Sensors beyond cell coverage | Per device per month |
| **Conservation** | SANParks, reserves | Collars, fence sensors, ranger messaging | Per device or per reserve |
| **FORGE ecosystem** | Freight, USV, VOCAL, ForgePay, EYE | Tracking, links, offline messaging | Internal contracts, first references |
| **SA government** | DCDT / SA Connect, provinces | Sovereign capacity, rural sites | Multi-year contract, part prepaid |
| **Mobile operators (later)** | MTN, Vodacom, others | Wholesale NB-IoT satellite capacity | Wholesale + revenue share |

**Pricing reality check.** New LEO IoT entrants now price at about $1 per device per month (Myriota from $0.99; Sateliot targets about €1). FORGE STAR competes on sovereignty, local support and data landing in SA, not on undercutting. IoT is a minority of Stage 3 revenue; the **SA government capacity contract** is the line the plan depends on most.

---

## 03 · Financials and stress tests
### Capital, revenue path and downside cases

@reader Investors and CFO

Generated from `model/` (years 1–6, Stage 0 to Stage 3). Illustrative; not financial advice.

| Year | Satellites | Revenue (base) | Revenue (low) | Revenue (high) |
|---|---|---|---|---|
| **1** | 0 | $0.3M | $0.2M | $0.4M |
| **2** | 1 | $1.4M | $0.8M | $1.8M |
| **3** | 2 | $3.9M | $2.3M | $5.1M |
| **4** | 10 | $16.5M | $9.9M | $21.5M |
| **5** | 30 | $29.4M | $17.6M | $38.2M |
| **6** | 48 | $37.5M | $22.5M | $48.8M |

| Stress test | Year-6 revenue | Year-6 EBITDA | Read |
|---|---|---|---|
| **Base** | $37.5M | $12.6M | No month below zero cash |
| **IoT at ~$1/device** | $31.6M | $9.2M | Still in the Stage 3 range |
| **No SA government contract** | $19.5M | $2.2M | Below the Stage 3 range: the biggest commercial risk |
| **Low case (slow sales, higher costs)** | $22.5M | $3.0M | Cash short ~$1.5M in year 3: needs a larger seed or earlier Series A |

#### Funding plan

| Round | When | Amount | Purpose |
|---|---|---|---|
| **Founder, bootstrap, grants** | Year 1 | ~$0.55M | Stage 0 platform, lab, licences |
| **Seed (on signed LOIs)** | By month 12 | ~$2.5M | Hosted payload, own demonstrator start |
| **Series A** | Year 3 | ~$22M | Early service (6–12 satellites) |
| **Series B + government prepayment** | Year 5 | ~$25M + prepayments | Operational network (48 satellites) |

**Equity to Stage 3:** ~$50M. **Gross capital to Stage 3:** ~$47M base, ~$60M in the low case. The seed must close by month 12; the readiness plan shows that is only reachable by raising on signed LOIs rather than waiting for paying customers.

---

## 04 · Regulation and ownership
### Permission to transmit and the 30% rule

@reader Counsel and investors

| Item | Position | Status |
|---|---|---|
| **ICASA licensing** | ECNS/ECS + radio frequency spectrum licence; test licence for the lab | Not started: counsel to be briefed |
| **ITU filing** | Modest NGSO filing through ICASA; draft parameters generated (`docs/itu/FILING_PARAMETERS.md`) | Draft ready for counsel |
| **Bands (draft)** | NB-IoT NTN n256 (1980–2010 / 2170–2200 MHz), AIS receive (VHF), X-band feeder (8025–8400 MHz) | To confirm against RR and ICASA band plan |
| **Deployment milestones** | Res. 35: 10% / 50% / 100% within 2 / 5 / 7 years of the bring-into-use deadline | Filing 96 satellites means 95 needed by the final milestone; file closer to 48 if growth is uncertain |
| **30% HDG ownership** | Cap table keeps HDG ownership above 50% through Series B, if each round includes HDG-qualifying investors | Founder flags are placeholders: confirm with counsel |
| **POPIA** | Data hosted in SA; 24-month default retention; audit log; Information Officer to appoint | Checklist drafted |

| After round | Post-money | HDG share |
|---|---|---|
| **Founding** | — | 75.0% |
| **Seed** | $12.5M | 66.0% |
| **Series A** | $82M | 54.8% |
| **Series B** | $245M | 52.2% |

---

## 05 · System architecture
### How the network works end to end

@reader Everyone

<!-- diagram:architecture -->

**How a message travels.**
- A device sends a reading over NB-IoT NTN. Every FORGE STAR satellite overhead takes a copy and holds it on board.
- When a satellite passes a gateway, it downlinks its stored messages in error-corrected link blocks.
- The gateway decodes them, removes duplicate copies, stores each message once and sends acknowledgements back up.
- Satellites relay the acknowledgements: devices stop re-sending, satellites drop copies they no longer need.
- Messages flow through Kafka into TimescaleDB in South Africa; customers see them in dashboards and through the API, and are billed monthly.

**Stage 0** uses the same platform with traffic from a resale partner, so customers sign up and pay before our satellites fly and move across with no change on their side.

| Layer | What it is | Status |
|---|---|---|
| **Devices** | NB-IoT NTN modules + FORGE STAR device SDK (C) | SDK built and tested; module integration needs hardware |
| **Space segment** | 6U–12U satellites on a bought bus; our payload and flight software | Software built; payload hardware to build |
| **Gateways** | SA-owned + leased partner stations; modem, FEC, dedupe, acks | Software built and tested |
| **Data platform** | Kafka, TimescaleDB, ThingsBoard, API, billing | Built; runs end to end; production overlay ready |
| **Operations** | Mission ops tool, procedures, readiness and verification tracking | Built |

---

## 06 · Constellation and RF design
### Orbits, delivery time, link budget and coding

@reader Systems and RF engineers

#### Stage 3 constellation

| Shell | Satellites | Planes | Inclination | Altitude |
|---|---|---|---|---|
| **A (main)** | 42 | 7 | 45° | 550 km |
| **B (equatorial)** | 6 | 1 | 10° | 550 km |

Gateways: Hartebeesthoek, Cape Town (owned), Walvis Bay, Mauritius, Malindi, Lagos (leased, data relayed to SA). Orbit model: circular + J2 secular drift, checked against SGP4 (planes agree within 3 km over 3 days).

#### Delivery time (95th percentile)

| Configuration | Johannesburg | Maputo corridor | Lusaka | Dar es Salaam | Nairobi | Lagos |
|---|---|---|---|---|---|---|
| **24 sats, SA gateways, 22° mask** | 1.6 h | 81 min | 1.8 h | 3.4 h | 5.8 h | 4.3 h |
| **36 sats, 4 gateways, 16° mask** | 44 min | 71 min | 12 min | 44 min | 1.8 h | 1.9 h |
| **Stage 3 design (42+6, 6 gateways)** | 8 min | 8 min | 26 min | 11 min | 9 min | 11 min |

Live platform run on the Stage 3 design: **95% of satellite messages within 9 minutes** (maximum 14 minutes). Two design rules came out of this work: devices must **re-send until acknowledged** (single-copy hand-off left messages stranded on satellites heading away from gateways), and **gateways are the cheap lever** for sites far from SA.

#### Link budget (illustrative parameters, `forgestar/params/rf.yaml`)

| Link | Closes (3 dB margin) from | Note |
|---|---|---|
| **NB-IoT uplink** (23 dBm device → 14 dBi patch) | ~22° | Sets the baseline mask |
| **NB-IoT downlink** (2 W, ±30° patch) | ~37° | The payload design driver |
| **AIS receive** (VHF monopole) | horizon | Collision-limited, not budget-limited |
| **Feeder downlink** (X-band → 3.7 m dish) | ~4° | Comfortable |

#### Antenna trade

| Option | Usable mask | DC power | Est. cost |
|---|---|---|---|
| **Patch 14 dBi, 2 W (baseline)** | 37° | 12 W | ~$15k |
| **Patch + deeper NB-IoT repetition** | 26° | 12 W | ~$15k |
| **Isoflux 7 dBi, 5 W** | 21° | 25 W | ~$45k |
| **Isoflux 5 dBi, 8 W** | 16° | 38 W | ~$55k |
| **4×4 phased array** | 20° | 30 W | ~$150k |

Demonstrator: patch + deeper repetition. Stage 2 onward: shaped isoflux antenna, provided the bus supplies ~25–40 W during passes.

#### Link layer

| Element | Choice | Verified |
|---|---|---|
| **Outer code** | Reed–Solomon (255,223), CCSDS parameters, dual basis (libfec table) | Own encoder and decoder; corrects up to 16 bytes per codeword |
| **Inner code** | CCSDS convolutional K=7 r=1/2, soft-decision Viterbi | Decodes at Eb/N0 ≈ 2.5 dB (RS alone needs ~6 dB) |
| **Randomiser, sync** | CCSDS pseudo-random sequence; 0x1ACFFC1D marker | Matches CCSDS 131.0-B sequence |
| **Modulation** | BPSK, root-raised-cosine; receiver handles Doppler, timing, phase | Software modem tested with offsets and noise |

---

## 07 · Flight software
### F´ deployment, security and fault handling

@reader Software and flight engineers

The payload software is a NASA F´ (v3.5.1) deployment with a portable C99 core (`flight/libforge`, no dynamic memory) that is byte-identical to the ground implementation (shared test vectors).

| Component | Responsibility |
|---|---|
| **StoreForward** | Onboard store (16,384 messages), frame building, link blocks; ACK handling; safe-mode inhibit; persistence across reboots; memory scrubbing |
| **CmdAuth** | Every uplinked command ChaCha20-encrypted and HMAC-SHA256-authenticated with a monotonic counter; forged, corrupted or replayed commands are dropped before the dispatcher |
| **ModeManager** | SAFE mode on low bus voltage, lost bus reports or operator command; return to NOMINAL needs a command and healthy power |
| **PassPredictor** | Onboard gateway pass prediction from uplinked orbit elements (matches the ground model to 1e-9 km) |
| **PayloadSim** | Hardware stand-in (NB-IoT messages, bus power, downlink radio) for running without hardware; replaced by real drivers |
| **Standard F´** | Rate groups, command dispatcher, event logger, telemetry, parameters, buffer manager, framer, TCP ground link |

| Property | Evidence |
|---|---|
| **Runs on target-class hardware** | Cross-compiled for 64-bit ARM and run under QEMU on every CI build |
| **Nothing lost or reordered** | Downlink decoded on the ground: 720 messages, in order, every block decoded |
| **Survives reboot** | Store restored after restart (integration test on the real binary) |
| **Security** | Unsigned, replayed and tampered commands rejected; opcode not visible on the wire |
| **Radiation upsets** | Corrupted stored records detected by per-record CRC and discarded, never downlinked |

**Still to build (needs hardware):** the NB-IoT NTN base station on the payload SDR (OpenAirInterface NTN), real radio and bus drivers, the payload computer port, hardware-in-the-loop tests.

---

## 08 · Ground segment and platform
### Gateway, data platform, API and billing

@reader Software, operations and customers' IT

| Service | What it does |
|---|---|
| **Gateway** | Reads IQ recordings, demodulated bytes or frames (Kafka, files, SatNOGS Network); RS + Viterbi decoding; duplicate removal; ACK uplink |
| **Ingest** | Kafka → TimescaleDB; ThingsBoard forwarding |
| **Customer API** | Per-customer keys; devices, messages, latest reading, SLA, usage, invoices; rate limits, audit log, metrics, key revocation |
| **Billing** | Monthly invoices per active device, minimum charge, SLA credit when the 95% delivery target is missed |
| **Dashboards** | ThingsBoard: devices, map, delivery-time chart (provisioned by script) |
| **Mission operations** | Signed, encrypted commanding and telemetry decoding for the flight software; procedures for passes, safe mode, key rotation |
| **Production overlay** | TLS (Caddy), nightly backups, no database or Kafka ports on the host, required secrets, 24-month retention |

![ThingsBoard operations dashboard from a live run: device table, map and delivery times](docs/img/thingsboard-operations.png)

---

## 09 · Hardware: build, buy, bridge
### What we design, what we buy, and who covers the gaps

@reader Hardware and RF engineers, partners

#### Boards: heypcb.ai plus our pipeline

heypcb.ai designs the circuit boards (schematics, routing, Gerbers, BOMs, KiCad projects), starting from its library of open-hardware boards. Every board comes back as a KiCad project, so our in-house pipeline (SKiDL → KiCad → design rule checks → fab files) checks and packages it on every change.

| Board | Designed by | Status |
|---|---|---|
| **Payload interface board** (STM32, CAN, radio power switch, current and temperature) | heypcb.ai from our netlist; checked by our pipeline | Schematic and placement done; routing next |
| **Payload processor carrier** | heypcb.ai (module bought) | Module to choose |
| **S-band radio carrier** (digital, power, clock) | heypcb.ai; RF layout by the RF engineer | Not started |
| **Lab test boards** | heypcb.ai | Not started |

![Payload interface board rev A, placed by the in-house pipeline (not yet routed)](docs/img/pib-revA-placement.png)

#### The gaps heypcb.ai does not cover, and how we bridge them

| Gap | Bridge | Notes from the research (to confirm) |
|---|---|---|
| **Bus integration, structure, thermal** | Hosted-payload platform (e.g. Loft Orbital Payload Hub) or the bus partner's integration service (Dragonfly, CubeSpace) | Loft integrates payloads on a standard hub (reported ~2 days); no public pricing. Dragonfly offers 50–150 kg-class buses; no public hosted-payload offer |
| **High-performance RF** | Flight-heritage radios: EnduroSat, Alén Space, IQ Spacecom, Syrlinks | EnduroSat list prices: S-band transceiver ~$13–14k; X-band transmitter ~$32k. A TT&C transceiver is not an NB-IoT base station: the payload still needs an SDR |
| **Antennas** | Antenna Magus (design library), openEMS / CST / HFSS (simulation), range test | Antenna Magus Learning Edition is free (12 antenna types); commercial licence quote-only |
| **Radiation** | SPENVIS analysis, heritage parts, proton testing at iThemba LABS (Cape Town) | SPENVIS is free. iThemba LABS has a proton single-event-effect facility (first in Africa); external access terms to confirm |
| **Structural and thermal analysis** | SimScale, FreeCAD + CalculiX; bus partner's thermal model; vibration and thermal-vacuum tests | SimScale has a free tier (public projects only) |
| **Systems engineering** | Capella (open source) for interfaces and budgets | Valispace: no startup programme found; reported acquired by Altium |

#### Bought in

| Item | From | Illustrative cost |
|---|---|---|
| **Satellite bus** | Dragonfly Aerospace or CubeSpace | Part of ~$1.8M for the first own satellite |
| **Hosted-payload slot** | Bus partner or a hosting platform | ~$350k |
| **Launch** | Rideshare broker | ~$250k + ~8% insurance |
| **NB-IoT NTN device kits** | Module vendors | $100–300 each |
| **Lab kit** | SDRs, GPS clock, attenuators, shielded box, analyser | ~$12–25k (TIA/DSI grant) |

**People still needed:** an RF engineer, and a part-time systems or mechanical engineer to own interfaces and tests.

---

## 10 · Evidence and maturity
### What is tested, and how mature each part is

@reader Technical due diligence

| Evidence | Count |
|---|---|
| **Python tests** | 66 (includes live tests against the flight binary) |
| **C test suites** | 4 (core, command security, orbit, device SDK) |
| **F´ unit tests** | 6 |
| **CI jobs on every push** | 4: Python and analysis, platform images and production overlay, flight software (native and ARM), hardware pipeline |
| **Cross-language checks** | C and Python produce identical frames, link blocks, convolutional code, ACKs and orbits |

| Subsystem | TRL now | Needed for launch |
|---|---|---|
| **Store-and-forward core (C)** | 4 | 6 |
| **Flight software (F´)** | 4 | 6 |
| **Radio link layer** | 4 | 6 |
| **Device SDK** | 4 | 5 |
| **Ground gateway** | 4 | 6 |
| **Data platform** | 5 | 7 |
| **Constellation design** | 4 | 5 |
| **Payload interface board** | 3 | 6 |
| **NB-IoT NTN payload radio** | 2 | 6 |
| **Payload antenna** | 2 | 6 |
| **Satellite bus** | bought | flight-proven |

**Verification register** (`docs/verification/VERIFY.md`): 16 claims tracked, 12 web-checked, 0 yet confirmed by counsel or quotes; 34 of 36 radio parameters still illustrative pending datasheets.

---

## 11 · Path to launch
### Timeline, critical path and the next 90 days

@reader Everyone

| Milestone | Fast track | Current plan |
|---|---|---|
| **ICASA pre-application meeting** | Apr 2027 | Apr 2027 |
| **Lab grant awarded** | May 2027 | May 2027 |
| **ICASA test licence** | Aug 2027 | Aug 2027 |
| **Seed round closed** | Nov 2027 | Apr 2028 |
| **Lab proves NB-IoT through the satellite channel** | Nov 2027 | Nov 2027 |
| **Payload frozen against the bus/host interface** | Mar 2028 | Mar 2028 |
| **ICASA spectrum licence** | Jun 2028 | Jun 2028 |
| **Hosted payload in orbit** | **Apr 2029** | Jul 2029 |
| **Own 6U–12U satellite in orbit** | **Jun 2029** | Jul 2030 |
| **Early service (6–12 satellites)** | Jul 2030 | Jan 2032 |

**Fast track** = seed raised on signed LOIs, own demonstrator built in parallel with the hosted payload, Series A on the hosted-payload result.

**The critical path runs through spectrum:** counsel → ICASA pre-application meeting → test licence → lab → antenna decision → payload freeze → hosted-payload slot → launch.

#### Next 90 days

- **Spectrum counsel:** brief with the ITU parameter sheet; request the ICASA meeting and a lab test licence; decide the filing size.
- **Bus partner and host RFQs:** Dragonfly and CubeSpace, plus one hosting platform; ask for 25–40 W payload power during passes and the interface control document.
- **Lab grant:** TIA/DSI application with the 12-week test plan and bill of materials.
- **Payload interface board:** route with heypcb.ai, fab 5 boards, bring up with the flight core.
- **RF quotes:** S-band SDR and power amplifier, X-band transmitter, S-band patch.
- **Radiation:** SPENVIS analysis for our orbits; contact iThemba LABS about access.
- **Revenue:** signed LOIs from FORGE Freight, the maritime venture and one mining group; first SatNOGS station live.

#### What we are asking for

| From | Ask |
|---|---|
| **Investors** | Seed of ~$2.5M by month 12, with an HDG-qualifying anchor |
| **Grant bodies** | Lab funding for the NB-IoT NTN test-bed |
| **Partners** | Bus or hosting quotes and interface documents |
| **Customers** | Letters of intent and pilots on the Stage 0 platform |

---

## 12 · Risks
### What could break the plan

@reader Investors and board

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Spectrum (ICASA/ITU)** | No licence, no service; milestones can truncate a filing | Early counsel; modest filing; draft parameters ready |
| **Ownership rules change** | Equity equivalents could let Starlink in | Sell sovereignty and IoT, not broadband |
| **Sovereign contract** | Without it, year-6 revenue falls to ~$19.5M | Start the government conversation early; prepayment terms |
| **IoT price pressure** | Entrants at ~$1/device | Compete on sovereignty, local service, SLA |
| **Payload RF** | Downlink closes only from ~37° on a simple patch | Isoflux antenna; deeper repetition for the demo; RF hire |
| **NB-IoT NTN software maturity** | Open-source base station is the biggest unknown | Lab test-bed first; vendor fallback |
| **Capital timing** | Seed needed by month 12 | Raise on signed LOIs; grants as bridge |
| **Launch slippage** | Rideshare dates move | Hosted payload first; schedule buffers |

---

## 13 · Where FORGE STAR reaches
### The African network is a near-global network

@reader Investors, partners and business development

The Earth rotates under every orbit, so the 45° and 10° shells pass over every longitude, and a satellite at 550 km is visible from beyond its inclination. The same 48 satellites designed for Africa therefore fly over a band from about **55°S to 55°N**: about **81% of the Earth's surface** sees a satellite at least a quarter of the time. Where a satellite can also see one of the African gateways at the same moment, service is **real time**; everywhere else it is **store-and-forward** until more gateways are added.

![Stage 3 coverage: real time across Africa and Madagascar (orange), store-and-forward across the 55°S–55°N band (blue)](docs/img/coverage-stage3.png)

![Stage 4 (150 satellites): satellites overhead 85–100% of the time across most of the band](docs/img/coverage-stage4.png)

#### Coverage by latitude band (share of time a satellite is overhead)

| Latitude | Stage 3 (48) | Stage 4 (150) | Examples |
|---|---|---|---|
| **35–45° N and S** | 63–65% | 100% | Cape Town, Buenos Aires, Sydney, Auckland, Madrid, Rome, Tokyo, Casablanca |
| **15–25°** | 44–46% | 86–94% | Johannesburg, São Paulo, Madagascar, Riyadh, Dubai, Mumbai, Mexico City |
| **0–15°** | 44–47% | 94–100% | Lagos, Nairobi, Kinshasa, Jakarta, Manila, Lima |
| **About 55°** | 14% | 40% | Southern Argentina, northern UK |
| **Above about 60°** | 0% | 0% | Moscow and north, Arctic, Antarctica |

#### Service by region (Stage 3)

| Region | Satellite overhead | Real time (African gateways) | 95% delivery, African gateways only | With 5 more gateways |
|---|---|---|---|---|
| **Southern, East, Central, West Africa** | 42–67% | Almost all of it | 8–26 min | — |
| **Madagascar** | 46% | 46% | Minutes | — |
| **Sudan, Senegal** | 42–44% | 18–33% | Under ~1 h | — |
| **Gulf and Middle East** (Riyadh, Dubai, Cairo) | 45–57% | 4–13% | ~1–2 h | Regional gateway needed |
| **South America** (São Paulo, Buenos Aires, Lima) | 42–65% | 0% | ~40+ min | São Paulo ~10 min (Brazil gateway) |
| **South Asia** (Mumbai, Dhaka) | 45–46% | 0% | ~2 h | Mumbai ~19 min (India gateway) |
| **South-East Asia** (Jakarta, Manila, Malacca Strait) | 41–45% | 0% | ~1.5–2 h | Jakarta ~12 min, Malacca ~10 min (Singapore gateway) |
| **Australia, New Zealand** | 61–66% | 0% | ~75–85 min | Perth ~6 min; Sydney 63 min (needs an east-coast gateway) |
| **Mexico, Caribbean, Panama** | 47% | 0% | ~45–75 min | Panama ~29 min (Panama gateway) |

"5 more gateways" = Brazil, Panama, Singapore, Western Australia and India (leased passes, roughly $60k a year each, illustrative). Coverage is not permission: each country needs landing rights, gateway licences and spectrum coordination.

#### First export markets

| # | Market | Why first | What it needs |
|---|---|---|---|
| **1** | **SADC states** (Namibia, Botswana, Zambia, Mozambique, Tanzania) | Real-time coverage already; regional regulatory ties; logistics corridors and mining; "constellation-in-a-box" co-financing partners | Landing rights per state; Walvis Bay, Lusaka, Maputo, Dar gateways |
| **2** | **Indian Ocean maritime** (Mauritius, Madagascar, Seychelles, Mozambique Channel) | Real time over Madagascar and Mauritius; fisheries enforcement and shipping on the Cape route; sells AIS data, not consumer service | Mauritius gateway; fisheries and port-authority contracts |
| **3** | **East and West Africa** (Kenya, Nigeria, Senegal, Ghana) | Real time via Malindi and Lagos gateways; large agriculture, energy and logistics IoT markets | Landing rights; partner gateways in country |
| **4** | **Global maritime AIS data** (shipping insurers, flag states, port operators) | The Indian Ocean, Malacca, Suez approaches, South Atlantic and Panama lie inside the band on Stage 3 satellites; data products sold from SA | AIS data licensing; Singapore and Panama gateways for low latency |
| **5** | **Brazil and the Southern Cone** (agriculture and mining IoT) | Strong coverage at 23–35°S; large farm and mining IoT demand; a neutral, non-aligned alternative | ANATEL authorisation; Brazil gateway; in-country data landing |

Outside Africa the pitch changes from "sovereign for South Africa" to **neutral, non-aligned and landed in country**: each regional gateway lands customers' data in their own jurisdiction.

*Maps and figures from `sim/coverage_map.py`, `sim/latency_sim.py` and the global gateway study (first-order: circular orbits, 16° user mask, 2-day averages). Regulatory steps per market to confirm with counsel.*

---

## 14 · Sources and caveats
### What was checked, and what still needs confirming

@reader Everyone

> **Product names, programmes and facility details come partly from general knowledge and partly from a web check on 2–3 November 2026, not from vendor quotes.** Vendors' offers, pricing and availability change, so every figure in sections 02, 04 and 09 needs confirming directly before commitments. Each item is tracked in the verification register (`docs/verification/VERIFY.md`, items R1–R4, M1–M2, C1–C2, O1, V1–V7) and the readiness plan (items H1–H7).

| Item | Checked | Still to confirm | Owner |
|---|---|---|---|
| **Starlink / ICASA status** | Web-checked | Counsel opinion | Spectrum counsel |
| **ITU Resolution 35 milestones** | Web-checked | Consolidated Radio Regulations text | Spectrum counsel |
| **IoT pricing** | Web-checked (vendor marketing) | Competitor quotes | Sales lead |
| **Starlink scale** | Web-checked (S-1 via secondary sources) | Primary filing | Founder |
| **Hosting platforms** | Web-checked; no public prices | Quotes from Loft and one other | Founder |
| **Bus partners** | Web-checked; no public hosted offer | RFQ responses | Founder |
| **RF hardware prices** | List prices (satsearch, vendor pages) | Formal quotes | RF engineer |
| **Antenna Magus, SimScale, SPENVIS** | Web-checked | Licence terms for commercial use | Systems engineer |
| **iThemba LABS radiation testing** | 2020 thesis | Current access and pricing | Systems engineer |
| **Radio parameters** | Illustrative | Datasheets and measurements | RF engineer |
| **HDG ownership flags** | Placeholders | Verification | Counsel |

#### Key sources

- ICASA and Starlink: advanced-television.com (May 2026); furtherafrica.com (Aug 2026); newsroom.co.za; techinafrica.com
- ITU NGSO milestones: itu.int (Resolution 35 announcement; 2024 workshop on Resolutions 8 and 35)
- IoT pricing: itbrief.com.au (Myriota); myriota.com; iotone.com (Sateliot); hubble.com (NTN cost breakdown)
- Starlink scale: driveteslacanada.ca; kalkine.com; earthsims.com
- Hosting and buses: loftorbital.com; payloadspace.com; satsearch.co (Dragonfly); spaceinafrica.com (Transporter-17)
- RF hardware: satsearch.co (EnduroSat S-band, X-band, SDR)
- Tools and testing: 3ds.com (Antenna Magus); spenvis.oma.be; pricingsaas.com (SimScale); scholar.sun.ac.za (iThemba LABS proton SEE facility); elreferente.es (Valispace)

Full links are in `docs/verification/register.yaml`. *Not financial or legal advice.*
