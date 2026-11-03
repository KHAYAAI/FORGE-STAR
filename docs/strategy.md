# FORGE STAR — Strategy

> Africa's sovereign satellite data network

All figures are illustrative. Re-verify market and regulatory facts before external use.

---

## 01 · Executive summary
### FORGE STAR in one page

> **FORGE STAR is Africa's sovereign satellite data network:** compliant, locally owned LEO infrastructure that connects the assets, vessels and people that terrestrial networks will never reach.

FORGE STAR is a South African company in the FORGE ecosystem (MYFORGE PTY LTD). It is building a neutral, sovereign low-Earth-orbit (LEO) communications network for Africa and the Global South: a third option for governments and operators that do not want to depend on Starlink (US) or Guowang/Qianfan (China).

The wedge is **satellite IoT, maritime AIS and sovereign data relay**, not consumer broadband. That is fundable now, serves customers that intermittent coverage already satisfies, and avoids a head-on fight with a ~10,000-satellite incumbent.

| Dimension | FORGE STAR position |
|---|---|
| **Customers** | Maritime/security agencies, mining, agriculture, water, conservation, FORGE ecosystem companies; later SA government connectivity, mobile operators and other African states |
| **Offer** | Sovereign, locally owned satellite data and connectivity anywhere in Africa, data landed in South Africa |
| **Build approach** | Open-source software across the stack + heypcb.ai for boards + Claude Code for integration; satellite bus bought from SA partners |
| **Path** | Ground first (revenue before orbit) → hosted payload → 6–12 satellites → 24–48 satellite operational network |
| **Capital to operational network** | ~$50–105M gross; ~$40–75M equity after revenue, grants and prepayments |
| **Bootstrappable** | First ~2 years: Stage 0 and a hosted payload in orbit for ~$0.3–1M |
| **Most likely success outcome** | Stage 3 operator worth ~$200–500M; $1B+ if African governments co-finance continental scale |

#### Why now

- **Starlink is blocked in South Africa** by ICASA's 30% historically disadvantaged ownership rule, which SpaceX will not meet. FORGE STAR can comply.
- **Chinese constellations are far behind target** (a few hundred satellites against ~28,000 planned) and carry alignment risk.
- **OneWeb is enterprise-only in SA**; Amazon Leo is still preparing entry; the EU's IRIS² has no satellites in orbit.
- **Tooling has collapsed early costs:** open-source flight, ground and NTN software plus AI-assisted design make a demonstrator a tens-of-thousands problem, not a millions problem.

---

## 02 · The company
### What FORGE STAR is, and how the plan was sharpened

The original concept was an Exosat-style mega-constellation: ~$300k satellites at 420–450 km, ITAR/EAR-free, selling IoT, Direct-to-Cell and broadband. Stress-testing it produced seven refinements that make it buildable from South Africa.

| Issue in the original plan | Refinement |
|---|---|
| Direct-to-Cell on a $300k small satellite does not close: phones need very large antennas | Lead with 3GPP Rel-17 NB-IoT NTN and store-and-forward messaging; D2C later through a partner, not our hardware |
| A PocketQube demonstrator proves software, not the business | Fly the real payload: hosted payload first, then a 6U–12U demonstrator |
| Building our own bus wastes engineering | Buy the bus from SA suppliers (Dragonfly Aerospace, CubeSpace); own the payload, network, ground and operations |
| 30% ownership rule treated only as a moat | It also binds us: structure the cap table for it from day one, and watch equity-equivalent reforms that could let Starlink in |
| Mega-filing through ICASA is unrealistic | File a modest NGSO network (24–100 satellites) in IoT-appropriate bands; achievable ITU milestones |
| Conflicting launch and revenue figures | Budget $80–250k per 6U–12U slot via broker; revenue built from unit math (Section 09) |
| Too many products at once | One wedge first; earn the right to D2C, broadband and edge compute |

#### The three payload functions

- **NB-IoT NTN and store-and-forward messaging** for mining, agriculture, water and utility metering, logistics and conservation.
- **Satellite AIS/VDES** for maritime domain awareness across South Africa's very large EEZ: Navy, fisheries enforcement, ports.
- **Sovereign data relay** for government sensors (border, environment, disaster), landed in South Africa to support POPIA and data-sovereignty needs.

#### The FORGE ecosystem advantage

| FORGE venture | What FORGE STAR gives it |
|---|---|
| **FORGE Freight** | Container and truck tracking across African trade corridors |
| **Maritime USV venture** | Over-the-horizon command link and AIS |
| **FORGE VOCAL** | Satellite messaging/USSD fallback for feature-phone users in no-coverage zones |
| **ForgePay** | Offline-tolerant payment settlement over satellite messaging |
| **FORGE EYE** | Sovereign sensor and data feed into the decision platform |
| **Autonomy studio / robotics** | Remote telemetry for field robots and vehicles |

---

## 03 · Target market
### Who we serve and what we offer them

#### Beachhead customers (Stages 0–2)

Customers who can use intermittent coverage and pay early.

| Segment | Example buyers | What we offer | How they pay |
|---|---|---|---|
| **Maritime and security** | SA Navy, DFFE fisheries, SAMSA, Transnet ports, shipping insurers | Satellite AIS vessel tracking, illegal-fishing detection | Annual data subscription or government contract |
| **Mining and energy** | Mining houses, Eskom, renewable IPPs, pipeline operators | Remote monitoring of dams, pumps, generators, grid sensors, vehicles | Per device per month + platform fee |
| **Agriculture and water** | Commercial farms, co-ops, water boards | Soil, water-level, irrigation and livestock sensors beyond cell coverage | Per device per month |
| **Conservation** | SANParks, private reserves, anti-poaching units | Animal collars, fence sensors, ranger messaging | Per device or per reserve |
| **FORGE ecosystem** | Freight, USV, VOCAL, ForgePay, EYE | Tracking, vessel links, offline messaging and payments | Internal contracts; first references |
| **Ground station services** | Foreign satellite operators | Southern-hemisphere downlink passes | Per pass or per month |

#### Expansion customers (Stage 3+)

| Segment | Example buyers | What we offer | How they pay |
|---|---|---|---|
| **SA government connectivity** | DCDT / SA Connect, provinces, municipalities, Education, Health | Managed rural connectivity for schools, clinics, hotspots; sovereign data relay; disaster comms | Per site per month, multi-year |
| **Mobile operators** | MTN, Vodacom, Telkom, Cell C, Rain | Wholesale NB-IoT NTN capacity and coverage extension; continental distribution | Wholesale per device/MB + revenue share |
| **Logistics corridors** | Rail, trucking, cold-chain across SADC | Cross-border cargo and fleet tracking without roaming gaps | Per asset per month |
| **Other African governments** | SADC and wider African states | Constellation-in-a-box: their flag and filing, our satellites and operations | Upfront co-financing + revenue share |

---

## 04 · Business model
### How FORGE STAR makes money

> We charge for IoT and maritime data per device and per contract, sell sovereign capacity to governments under multi-year agreements, and use customer co-financing so we do not carry the full constellation cost ourselves.

| Revenue line | Customer | Pricing |
|---|---|---|
| **IoT connectivity (NB-IoT NTN + store-and-forward)** | Mines, agriculture, utilities, logistics, conservation, FORGE Freight | $2–5 per device per month, volume tiers |
| **Maritime data (AIS/VDES)** | Navy, fisheries, ports, insurers | Annual data subscription |
| **Sovereign capacity** | SA government departments | Multi-year capacity contract, partly prepaid |
| **Ground station services** | Third-party satellite operators | Per pass or per month |
| **Constellation-in-a-box (later)** | Other African states | Upfront fees + revenue share on co-financed satellites |
| **Mobile operator wholesale (later)** | MTN, Vodacom and others | Wholesale IoT/messaging capacity |

#### Why the model works

- **Captive early demand** from the FORGE ecosystem gives reference customers before the first satellite.
- **Customers fund the build:** sovereign buyers prepay or co-finance capacity, moving capex off our balance sheet.
- **Local-ownership compliance** lets FORGE STAR operate where Starlink currently will not.
- **IoT pricing benchmarks:** new LEO IoT entrants price from roughly $1 to €8 per device per month; legacy satellite IoT sits at $40–70. FORGE STAR competes on sovereignty and local service at competitive prices.

#### Could South Africa have free internet, paid by government?

Free to citizens, paid by government, is a sound model, but not with our own satellites alone early on. Serving 30 million users at 10 GB/month needs ~1 Tbps average (~3 Tbps peak) of capacity, which means thousands of broadband satellites: Starlink-scale capital.

| Approach | Who gets connected | Feasibility |
|---|---|---|
| Satellite backhaul to government sites (schools, clinics, police stations, hotspots) | ~10–20k rural sites, free WiFi around each | **Feasible.** Leased capacity first, own broadband layer later |
| Hybrid national plan: fibre/towers in cities, FORGE STAR for the last 10–15% | Rural and remote communities | **Best model.** Aligns with SA Connect |
| Everyone, everywhere, on our satellites only | All ~63 million people | **Not feasible** without Starlink-scale capital |

The sellable version: FORGE STAR as government's sovereign operator for rural connectivity, paid per connected site per month, starting on leased capacity from Stage 0 and migrating to our own satellites later.

---

## 05 · Build strategy
### What we build, what we buy, and the full component stack

- **We buy:** the satellite bus (structure, power, attitude control) from SA partners such as Dragonfly Aerospace and CubeSpace; antennas and solar panels.
- **We build:** the payload (NB-IoT NTN radio + AIS receiver), the network, the ground segment and data platform, and sovereign operations. This is our IP.
- **We accelerate:** with open source across the stack, heypcb.ai for boards, and Claude Code for integration, testing and analysis.

| Layer | Components | Job |
|---|---|---|
| **Flight software** | NASA F´ (primary), NASA cFS (alt.), libcsp, Zephyr / FreeRTOS | Onboard command, telemetry, scheduling, fault handling, subsystem messaging, real-time OS |
| **Reference hardware** | LibreCube, BIRDS CubeSat designs | Proven board and bus starting points |
| **Mechanical / electronics** | FreeCAD, KiCad | Structure, enclosures, board design files |
| **RF and payload** | GNU Radio, SoapySDR, gr-satellites, SatDump, AIS-catcher / gr-ais | Signal processing, SDR abstraction, decoding, AIS payload |
| **IoT radio and core** | OpenAirInterface NTN, Open5GS / free5GC | NB-IoT NTN stack and 5G core |
| **Ground segment** | SatNOGS, Gpredict + Hamlib, Yamcs or OpenC3 COSMOS, NASA Open MCT, TinyGS | Ground network, antenna control, mission control, dashboards, LoRa backup |
| **Flight dynamics** | Orekit, NASA GMAT, Skyfield | Orbit determination, manoeuvre planning, pass calculation |
| **Constellation design** | OpenSN | Coverage, revisit and routing emulation |
| **Customer platform** | ThingsBoard, Apache Kafka, PostgreSQL + TimescaleDB | Device management, data pipeline, SA-hosted storage |

#### Where heypcb.ai fits

heypcb.ai is AI-assisted circuit-board design: schematics, routing, Gerbers, BOMs and KiCad projects, with a Circuit World library of 8,800+ open-hardware boards to fork. **It builds:** payload processor boards, NB-IoT/AIS radio carrier boards, payload-to-bus interface boards, ground-station and test electronics. **It does not handle:** structure, thermal design, high-performance RF and antennas, radiation qualification, or bus integration.

#### In-house PCB pipeline (open-source alternative to heypcb.ai)

`hardware/` builds boards from code with open-source tools only. SKiDL describes the circuit using KiCad's libraries. KiCad's Python API places the parts and applies the rules. Freerouting autoroutes. KiCad checks the design and exports Gerbers, drill files, pick-and-place data and a BOM. The first board is the **payload interface board**: an STM32L432 running the flight core, CAN to the bus, a radio power switch, current and temperature telemetry. It passes the electrical rule check with no errors and is placed with no blocking DRC issues. Autorouting is the next step.

Proven open CubeSat boards (LibreCube, OreSat, PyCubed, BIRDS) replace heypcb's library of boards to fork. ngspice and openEMS cover circuit and antenna simulation. **We can do the board work in house.** As with heypcb, it doesn't cover radiation qualification, thermal design, RF tuning or bus integration.

#### Flight software, radio link and customer API

- **Flight core (`flight/libforge`).** Portable C99 with no dynamic memory: the store-and-forward buffer, frame encoding and Reed–Solomon error correction. Its output is byte-identical to the Python ground code, which the shared test vectors prove.
- **F´ component (`flight/fprime`).** `StoreForward` wraps the core with commands, telemetry and events. It's built and unit-tested in NASA F´ v3.5.1, and the ground decodes its downlink.
- **Radio link layer.** CCSDS concatenated coding: Reed–Solomon (255,223) in the dual basis, plus the K=7 rate-1/2 convolutional code with a soft-decision Viterbi decoder, the CCSDS randomiser and a sync marker. It decodes at about 2.5 dB Eb/N0, against about 6 dB for Reed–Solomon alone. A software BPSK modem handles Doppler, timing and phase.
- **Command security.** Commands are ChaCha20-encrypted and HMAC-SHA256-authenticated, with replay protection, and checked on board before anything executes.
- **Customer API (`ground/api`).** Per-customer keys, devices, messages, delivery SLA and monthly usage, with data hosted in SA.

#### Can we physically build the satellite?

Yes, with the bus bought in. The four things that decide whether it is actually usable are: **(1) permission to transmit** (ICASA licence + ITU filing; without it a satellite is scrap in orbit), **(2) qualification** (vibration, thermal vacuum, radiation), **(3) launch** (achievable but external, rideshare via broker, dates slip), and **(4) something on the ground to talk to** (NTN devices and enough coverage for the use case).

---

## 06 · Coverage
### How many satellites South Africa, SADC and Africa need

LEO satellites cannot be parked over South Africa: they circle Earth roughly every 95 minutes. Covering SA continuously means covering its whole latitude band worldwide, so SA, SADC and Africa need similar numbers. **Revisit time matters more than region size.**

| Service level | User experience | South Africa | SADC | All of Africa |
|---|---|---|---|---|
| **Store-and-forward IoT** | Data delivered within a few hours | 2–6 | 4–8 | 6–12 |
| **Frequent IoT** | Data within 20–40 minutes | 16–24 | 24–36 | 30–48 |
| **Continuous narrowband** | Real-time messaging; always one satellite overhead | 50–90 | 60–110 | 80–150 |
| **Broadband** | Internet-grade speeds | Set by capacity demand, not coverage |  |  |

*Original first-order estimates. Checked below by simulation.*

#### Simulation check (November 2026)

`sim/coverage_sim.py` simulates Walker constellations at 550 km over 13 sites from Cape Town to Tunis, including the SA EEZ and Marion Island. It includes Earth's rotation and J2 drift, and runs over three days. The elevation mask comes from the link budget (below). The worst site in each region is shown.

| Constellation | SA typical wait | SA longest wait | Africa longest wait | Gateway passes/day |
|---|---|---|---|---|
| **1 sat, SSO rideshare** | ~10 h | 13 h | 72 h | 3 |
| **6 sats, 45°** | ~75 min | 6.9 h | 11 h | 27 |
| **12 sats, 45°** | ~40 min | 5.9 h | 5.9 h | 56 |
| **24 sats, 45°** | ~17 min | 2.8 h | 4.2 h | 113 |
| **48 sats, 45°** | ~8 min | 1.7 h | 2.3 h | 221 |
| **80 sats, 50°** | ~5 min | 44 min | 83 min | 320 |
| **120–150 sats, 50°** | 2–3 min | 3–6 min | 44 min | 480–600 |

Mask: 22°, where the NB-IoT uplink closes with a 3 dB margin. A 10° mask (`MIN_ELEV_DEG=10`) roughly halves the longest waits.

What changes:
- **On average, the original numbers hold up.** 16–24 satellites give SA a typical wait of about 15–20 minutes.
- **The longest wait is worse than assumed.** Promising "every 20–40 minutes, guaranteed" needs **~48–80 satellites for SA** and **~80–120 for Africa**.
- **Sell typical latency, not worst case**, until Stage 3. Customer SLAs should be written as "95% of messages within X". The platform's `latency_sla` view measures exactly this.
- **A 45° inclination beats sun-synchronous (SSO)** for Africa. A first rideshare will probably go to SSO, which is fine for a demo but not for service. Mixing the two in one constellation leaves long gaps.
- **For continuous narrowband, 80–150 is right.** It needs the top of the range at a 22° mask.

#### Link budget check

`forgestar/linkbudget.py` uses illustrative 6U–12U parameters. Replace them with datasheet values.

| Link | Closes (3 dB margin) from | Implication |
|---|---|---|
| **NB-IoT uplink** (23 dBm device → 14 dBi sat patch) | ~22° elevation | Sets the coverage mask above |
| **NB-IoT downlink** (2 W into 14 dBi, ±30° beam) | ~37° elevation | **The payload design driver.** Devices need the downlink to attach. Fix it with a shaped (isoflux) or steerable antenna, more RF power, or a narrower downlink carrier. Budget RF engineering for this |
| **AIS receive** (VHF monopole) | horizon | AIS is limited by message collisions, not link budget |
| **Feeder downlink** (X-band → 3.7 m SA dish) | ~4° | Gateway passes are long and the link closes easily |

#### Antenna trade study

`sim/antenna_trade.py` compares payload antennas. The usable mask is the higher of uplink and downlink. Service is shown for 24 satellites at 45°, at the worst SA site.

| Option | Usable mask | SA typical / longest wait | DC power | Est. cost |
|---|---|---|---|---|
| **Patch 14 dBi, 2 W (baseline)** | 37° | 32 min / 4.2 h | 12 W | ~$15k |
| **Baseline + deeper coverage enhancement** | 26° | 21 min / 3.5 h | 12 W | ~$15k |
| **Patch, 10 W amplifier** | 24° | 20 min / 3.3 h | 45 W | ~$40k |
| **Shaped (isoflux) beam, 7 dBi, 5 W** | 21° | 16 min / 2.5 h | 25 W | ~$45k |
| **Shaped (isoflux) beam, 5 dBi, 8 W** | 16° | 11 min / 1.6 h | 38 W | ~$55k |
| **4×4 phased array, 4 W** | 20° | 16 min / 2.2 h | 30 W | ~$150k |

**Recommendation:** fly the demonstrator with the simple patch plus deeper NB-IoT repetition, which is a software change. Design the Stage 2 payload around a shaped isoflux antenna, provided the bus can supply about 25–40 W during passes. That's a question for the bus partner. Keep the phased array for Stage 4.

*Simplified model: circular orbits with J2. Checked against SGP4 (`sim/sgp4_crosscheck.py`): orbit planes agree to within 3 km over 3 days, and the remaining difference is a timing offset equal to 1–3 km of altitude. Firm up with Orekit, then OpenSN, before external use. All antenna figures are illustrative.*

#### Delivery time: satellites vs gateways

`sim/latency_sim.py` follows each message end to end. It waits for a satellite overhead, rides on board, then lands at the first gateway pass. Devices re-send on each pass until the ground acknowledges.

| Setup (95% of messages delivered within…) | Johannesburg | Maputo corridor | Lusaka | Dar es Salaam | Nairobi | Lagos |
|---|---|---|---|---|---|---|
| **24 sats, 22° mask, SA gateways only** | 1.6 h | 81 min | 1.8 h | 3.4 h | 5.8 h | 4.3 h |
| **24 sats, 16° mask, 4 gateways** | 77 min | 57 min | 74 min | 2.7 h | 3.7 h | 3.8 h |
| **36 sats, 16° mask, 4 gateways** | 44 min | 71 min | 12 min | 44 min | 1.8 h | 1.9 h |
| **48 sats, 16° mask, 4 gateways** | 42 min | 53 min | 9 min | 50 min | 1.9 h | 1.8 h |

Gateways: Hartebeesthoek, Cape Town, Walvis Bay, Mauritius. A 16° mask needs the shaped (isoflux) antenna.

- **Gateways are the cheap lever** for sites far from SA. They can be leased passes or partner stations relaying data to the SA platform, so data still lands in SA.
- **The 60-minute SLA is reachable across SADC** with about 36–48 satellites, the isoflux antenna and 4 gateways.
- **Equatorial sites (Nairobi, Lagos) stay around 2 hours.** They need a low-inclination plane or equatorial gateways before an SLA is offered there.
- **Devices must re-send until acknowledged.** Handing each message to a single satellite can make waits worse, because that satellite may be heading away from every gateway. This is now built: ACK frames, gateway duplicate removal, satellites dropping acked copies, devices stopping re-sends. In a live platform run on 24 satellites with SA gateways only, 95% of messages landed within about **40 minutes**, against 85 minutes with the single-copy policy.

#### Closing the equatorial gap

`sim/equatorial_study.py` (isoflux antenna, re-send until acked) gives 95% delivery time in minutes:

| Option | Jhb | Agulhas | Maputo | Lusaka | Dar | Nairobi | Lagos | Extra capex vs 36 sats |
|---|---|---|---|---|---|---|---|---|
| **36 @45°, 4 gateways** | 44 | 10 | 71 | 12 | 44 | 110 | 116 | — |
| **+ Malindi + Lagos gateways** | 44 | 10 | 69 | 10 | 44 | 96 | 60 | ~$0.7M |
| **+ 6 sats @10° + Malindi + Lagos** | 44 | 10 | 69 | 10 | 21 | 10 | 25 | ~$5.2M |
| **42 @45° + 6 @10° + Malindi + Lagos** | 8 | 6 | 8 | 26 | 11 | 9 | 11 | ~$9.7M |

**Stage 3 design: 42 satellites at 45° plus 6 in a 10° plane (48 in total) and 6 gateways** (Hartebeesthoek, Cape Town, Walvis Bay, Mauritius, Malindi, Lagos). Every customer site is within 26 minutes for 95% of messages. A Maputo gateway does not help: the Maputo corridor is limited by the wait for a satellite overhead, which the extra 45° satellites fix.

> **Key takeaway:** a 24–48 satellite constellation gives the whole continent useful IoT and maritime data on average, which is why the Africa-wide pitch works early. Tight worst-case revisit needs ~48 (SA) to ~80 (Africa) satellites. Real-time continuous coverage needs ~80–150 (Iridium-class).

---

## 07 · Stages
### What is possible at each point, and what our build strategy covers

| Stage | Satellites | Timing | What works | Capital |
|---|---|---|---|---|
| **0: Ground first** | 0 | Months 0–12 | Ground stations, IoT platform, resold capacity, rural sites on leased capacity, licences lodged | $1–3M |
| **1: Demonstrator** | 1–2 | Months 12–30 | Store-and-forward IoT, AIS snapshots, full chain proven, government demo | $5–12M |
| **2: Early service** | 6–12 | Years 2.5–3.5 | Africa-wide IoT in 1–3 h; useful maritime picture | $15–30M |
| **3: Operational network** | 24–48 | Years 3.5–5 | IoT in ~30 min across Africa; ITU filing secured; sovereign contract; MNO wholesale | $30–60M + prepayments |
| **4: Continuous narrowband** | 80–150 | Years 5–7 | Real-time messaging/IoT; emergency messaging to NTN phones; other states | $100–250M, co-financed |
| **5: Broadband layer** | Hundreds+ | Years 7+ | Own capacity for national rural connectivity programme | $0.5–2B+, gov./DFI |

#### Schedule check (November 2026)

`readiness/tracker.py` chains the 30 outside tasks in `readiness/readiness.yaml` by their dependencies. These are spectrum, ownership, funding, lab, orbit and customers.

| Plan | Stage 2 (6–12 sats) ready | From start |
|---|---|---|
| **Everything in sequence** | Jan 2032 | ~61 months |
| **Seed raised alongside the HDG-anchor search** | Dec 2031 | ~60 months |
| **+ own demonstrator built alongside the hosted payload** | Dec 2030 | ~48 months |
| **+ Series A on the hosted-payload result, tighter builds** | Jul 2030 | ~43 months |

The stage table's "years 2.5–3.5" for early service is **only reachable on the fast track**, and even then it lands at the late end, about 3.6 years. The biggest lever is to **build our own 6U–12U demonstrator in parallel with the hosted payload, not after it**. That saves about a year. It needs a seed round large enough to fund both. The second lever is to **raise the Series A on the hosted-payload result**. Both should become plan decisions.

*Durations are planning estimates. Update `readiness/readiness.yaml` as quotes and ICASA timelines firm up.*

#### Build-strategy coverage by stage

| Stg | Open source carries | heypcb.ai builds | Not covered (we fill) | Tech / total |
|---|---|---|---|---|
| **0** | SatNOGS, Gpredict, Yamcs/COSMOS, Open MCT, ThingsBoard, Kafka, TimescaleDB, OAI NTN lab, OpenSN, Orekit | Ground-station and lab test boards | Leased capacity, ICASA applications, 30% structure, pilots, sites | ~90% / ~50% |
| **1** | F´/cFS, libcsp, Zephyr, GNU Radio, SatDump, AIS-catcher, OAI NTN, LibreCube/BIRDS, FreeCAD/KiCad | Payload processor, radio carriers, bus interface, payload power | Bus, antennas/RF tuning, qualification, spectrum licence, launch, insurance | ~60% / ~30% |
| **2** | Same flight/payload software reused; Orekit/GMAT fleet planning; OpenSN; Yamcs automation | Rev-2 boards for batch build, fixtures | Batch manufacture/QA, launches, SADC ground stations, landing rights, sales | ~55% / ~25% |
| **3** | Full stack at fleet scale; Kafka/TimescaleDB; OAI + Open5GS for MNO integration | Production variants, gateway electronics | Production line, ITU bring-into-use, security accreditation, 24/7 NOC | ~50% / ~20% |
| **4** | Software reusable; OpenSN routing; OAI NTN (heavy in-house work) | Digital/control boards only | Inter-satellite links, larger satellites, scale manufacturing, multi-country spectrum | ~35% / ~15% |
| **5** | Ground, ops and platform software; network simulation | Support electronics only | Phased arrays, Ka/Ku payloads, terminals, teleports, broadband spectrum | ~15–20% / ~5–10% |

Open source plus heypcb.ai carries Stages 0–2 to a large degree: a working satellite network for tens of millions of dollars, not hundreds. From Stage 3 the value shifts to what we own: payload IP, manufacturing, spectrum, government contracts and operations.

---

## 08 · Distance to launch
### How much of the path to full launch our approach covers

"Full launch" means the 24–48 satellite operational network. Contribution = component share × coverage.

| Component | Share | Open source + heypcb.ai | + Claude Code / Claude assist | Total covered | Contribution |
|---|---|---|---|---|---|
| **Software (flight, ground, network, platform)** | 20% | 80% | ~70% of remainder | ~94% | 18.8% |
| **Simulation and mission design** | 5% | 90% | ~80% of remainder | ~98% | 4.9% |
| **Electronics (boards)** | 10% | 55% | ~25% of remainder | ~66% | 6.6% |
| **Payload RF and antennas** | 10% | 20% | ~25% of remainder | ~40% | 4.0% |
| **Satellite bus** | 10% | 0% | ~10% (interfaces) | ~10% | 1.0% |
| **Testing and qualification** | 10% | 0% | ~20% (automation, analysis) | ~20% | 2.0% |
| **Spectrum and licensing** | 10% | 0% | ~25% (filings, interference analysis) | ~25% | 2.5% |
| **Launch** | 5% | 0% | ~5% (paperwork) | ~5% | 0.25% |
| **Capital raising and sales** | 20% | 0% | ~15% (decks, models, tenders) | ~15% | 3.0% |
| **Total** | **100%** | **~28%** |  |  | **~43%** |

> **Open source + heypcb.ai covers ~28%** of the whole process to launch. **Adding Claude Code takes it to ~43%**, with the biggest gains in software, payload RF analysis, spectrum filings and sales material. The remaining ~57% is physical, regulatory or relational: buying hardware, lab qualification, ICASA/ITU decisions, launch slots, and winning customers and investors.

Claude accelerates rather than replaces: engineers still review and sign off, especially on flight software and RF. The practical effect is that a lean team of 4–6 can carry Stage 0–1 workloads that would normally need 10–15 people.

---

## 09 · Capital
### What it costs, and how far we can bootstrap

| Stage | Satellites | Stage capital | Cumulative | Lean team |
|---|---|---|---|---|
| **0: Ground first** | 0 | $1–3M | $1–3M | 4–6 |
| **1: Demonstrator** | 1–2 | $5–12M | $6–15M | 8–12 |
| **2: Early service** | 6–12 | $15–30M | $21–45M | 15–25 |
| **3: Operational network** | 24–48 | $30–60M | $51–105M | 40–70 |
| **4: Continuous narrowband** | 80–150 | $100–250M | $150–355M | 100+ |
| **5: Broadband layer** | Hundreds+ | $0.5–2B+ | $0.65–2.4B+ | Hundreds |

Gross figures. Revenue, grants and prepayments reduce the equity need to reach Stage 3 to ~$40–75M. Stages 4–5 are funded mainly by government and development-finance co-financing.

#### Financial model check (November 2026)

`model/financial_model.py` builds years 1–6 from `model/assumptions.yaml`, which sets out device counts, prices, team, satellite unit costs, launch, ground stations and funding.

| Check | Strategy | Model (base) | Comment |
|---|---|---|---|
| **Stage 3 revenue (36 sats)** | $25–45M | ~$37M | Consistent, **if** 330k devices and one SA government contract land |
| **Equity to Stage 3** | $40–75M | ~$50M | Consistent |
| **Gross capital to Stage 3** | $51–105M | ~$32–49M (high to low case) | The strategy's range is conservative. Keep it as the budget, since it includes buffers the model doesn't |
| **Stage 0 spend** | $1–3M | ~$0.7M lean | The two numbers describe different plans. Lean bootstrap ≈ $0.5–1M, funded Stage 0 ≈ $1–3M |
| **Cash low point** | | Year 2 | Low case runs short by ~$0.9M in year 2. Close the seed round before the hosted payload is paid for |

**Monthly cash.** Even the base case goes about $0.5M negative for two months at the start of year 2. That's when hosted-payload and first-satellite payments come in before the seed money lands. **Close the seed round by the end of year 1**, or phase the payload deposits. The low case needs a larger seed round, or an earlier Series A.

**Ownership.** The cap table (`model/assumptions.yaml` → `ownership`) keeps HDG ownership above 50% through Series B, as long as about a quarter to a third of each round comes from HDG-qualifying investors (DFIs, BEE funds) and half the ESOP goes to HDG employees. If the rounds come only from foreign VCs, the ratio falls fast. Plan an HDG anchor investor in every round, or a broad-based trust. *Founder HDG flags are placeholders. Confirm each holder's status and the current rule with counsel.*

**Stress tests** (`model/assumptions.yaml` scenarios, 48 satellites, 4 leased gateways):

| Scenario | Year-6 revenue | Year-6 EBITDA | Note |
|---|---|---|---|
| **Base** | $37.5M | $12.6M | Seed closed by month 12; no month below zero cash |
| **IoT at ~$1/device** | $31.6M | $9.2M | Still inside the Stage 3 range |
| **No SA government capacity contract** | $19.5M | $2.2M | Below the Stage 3 range: **the biggest commercial risk** |

**IoT price pressure.** New entrants now price at about $1 per device per month (Myriota from $0.99; Sateliot targeting about €1). That's below our $2–5 assumption. At about $1, year-6 revenue falls from about $37.5M to about $31.6M, which is still in range. The reason: IoT is only about a quarter of Stage 3 revenue, and the **SA government sovereign-capacity contract is the line the plan really depends on**. Price IoT on sovereignty and local support, not on undercutting, and win the government anchor early.

The model's biggest sensitivity is **IoT device adoption**. Revenue from 330k devices at about $3 per month only comes if a mobile operator or a big mining or logistics customer signs. A 40% revenue shortfall still reaches Stage 3, but only with the Series B on time.

#### Bootstrapping: revenue first, payload in orbit second, equity third

| Phase | Funding source | Spend | Team | What we have at the end |
|---|---|---|---|---|
| **Bootstrap (years 0–1.5)** | Revenue, grants, founder equity | ~$0.2–0.5M | 4–6 | Ground network, IoT platform, reseller customers, licence filed, lab-proven payload |
| **Lean demo (years 1.5–2.5)** | Grants, prepayments, small angel round | ~$0.5–3M | 8–12 | Our payload proven in orbit (hosted ~$200–500k, or own 6U ~$1.5–3M) |
| **First raise (year 2.5+)** | Series A $15–30M | Stage 2 | 15–25 | Africa-wide IoT constellation |
| **Growth (years 3.5+)** | Series B + government prepayments | Stage 3 | 40–70 | Operational network, sovereign contract |

#### Stage 0 revenue streams

- **IoT reseller:** resell an existing satellite IoT network under the FORGE STAR brand with our platform on top; move customers to our satellites later.
- **Ground station services:** sell southern-hemisphere passes to foreign operators.
- **Managed rural connectivity:** run government and mining sites on leased capacity; thin margins, but it builds the sovereign relationship.
- **FORGE ecosystem contracts:** Freight and the maritime venture as first paying users.

Non-dilutive sources to target: TIA, DSI, SANSA partnerships (facilities, ground stations), NEF and IDC, DTIC manufacturing and R&D incentives. Verify current calls.

> **What bootstrapping covers:** ~80–100% of the first launch (hosted payload), ~40–60% of our own demonstrator, and ~10% of the work (~1% of the capital) to full launch. It is the stretch that removes the most risk, so the remaining 90% raises on strong terms.

---

## 10 · Competitive landscape
### FORGE STAR against the incumbents

| Competitor | Scale (late 2026) | Sovereignty posture | FORGE STAR's angle |
|---|---|---|---|
| **Starlink** | 10.3M paid subscribers (Mar 2026, S-1), ~12M by mid-2026; ~10,800 working satellites; ~300k African subscribers (unverified) | US-controlled; licence-blocked in SA by ownership rules | Do not compete on broadband; win on sovereignty, compliance and local ownership |
| **Guowang / Qianfan** | A few hundred satellites combined, far behind targets | Chinese state-aligned | Displace in the non-aligned segment |
| **Eutelsat / OneWeb, IRIS²** | OneWeb ~650 satellites, enterprise-only in SA; IRIS² services from ~2030 | European sovereign, not African | Leaves African sovereign and mass IoT open |
| **Amazon Leo** | Hundreds of satellites, enterprise beta, preparing SA entry | US / AWS-adjacent | Future competitor; not serving African sovereign demand yet |
| **Exosat** | Pre-revenue; ~11,000-satellite ITU filing; LOIs claimed $400M+ | Singapore-based; Asia/Middle East focus | Closest comparable; FORGE STAR is Africa-first |
| **IoT specialists (Kinéis, Myriota, Sateliot)** | Niche constellations | Mostly Western | Compete on sovereignty and local service, priced competitively |

*Figures are approximate as of the research done for this plan and should be re-verified before external use.*

#### Structural advantages

- **Credible non-alignment** for African and Global South buyers.
- **Real local industry:** CubeSat heritage (ZACUBE, MDASat), CubeSpace (ADCS to 350+ missions), Dragonfly, the MeerKAT/SKA RF talent pool, an automotive supply base.
- **Continental distribution** through SA-headquartered operators (MTN, Vodacom).
- **Co-financing model** means no need to raise billions alone.

#### The lean founding team

- Founder/CEO for government and business development
- RF/SDR payload engineer
- Software and ground-segment engineer (full open-source stack)
- Embedded/electronics engineer (heypcb.ai)
- Part-time spectrum and regulatory advisor
- Sales lead for mining, agriculture and conservation

---

## 11 · Potential
### What FORGE STAR can become

| Stage | Annual revenue | Illustrative valuation | Driver |
|---|---|---|---|
| **0–1: Ground + demonstrator** | R5–30M | $5–30M | Team, licences, payload proven in orbit |
| **2: Early service (6–12)** | $3–10M | $50–150M | Africa-wide IoT, first contracts |
| **3: Operational (24–48)** | $25–45M | $200–500M | Sovereign contract, MNO wholesale |
| **4: Continuous (80–150)** | $100–300M | $1–3B | Continental coverage, other states as customers |
| **5: Broadband layer** | $500M+ | $3–10B+ | National connectivity programmes |

#### Stage 3 revenue build (illustrative)

| Line | Assumption | Annual revenue |
|---|---|---|
| **IoT connectivity** | 300k devices × $3/month | ~$11M |
| **AIS / maritime data** | 3–5 subscribers | ~$3–6M |
| **Sovereign capacity** | 1 SA government deal | ~$10–25M |
| **Ground station services** | Third-party passes | ~$1–2M |
| **Total** | ~40 satellites, ~$15–25M fleet capex | **~$25–45M** |

*Comparables: Sateliot and Kinéis (early satellite IoT), Iridium (continuous narrowband, multi-billion), Eutelsat/OneWeb and Telesat (sovereign-anchored operators). Most likely successful outcome is a $200–500M Stage 3 company and an attractive acquisition target; $1B+ depends on government co-financing. Illustrative ranges, not a formal valuation or financial advice.*

---

## 12 · Risks and next steps
### Where it breaks, and the next 90 days

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Spectrum (ICASA / ITU)** | Binding constraint; no licence means no service. ITU milestones truncate filings if deployment lags | Small, specific filing; specialist counsel; early ICASA engagement; backstop administration option |
| **Ownership rules change** | Equity-equivalent reforms could let Starlink in | Do not build the pitch on Starlink staying out; sell sovereignty and IoT, not broadband |
| **Qualification and RF** | Payload must survive launch and space and meet link budgets | Hosted payload first; partner bus; qualification budget; RF hires |
| **Capital** | Thin SA seed market; Stage 2 needs $15–30M | Bootstrap to proof; grants; raise Series A from strength; blended international capital |
| **Government sales cycles** | LOIs are not contracts; procurement is slow | Revenue-generating Stage 0 services; paid pilots; ecosystem anchor demand |
| **Launch slippage** | Rideshare dates move | Diversified brokers and providers; schedule buffers |

#### Next 90 days

- **Spectrum:** brief specialist counsel; request an ICASA pre-application meeting on NGSO IoT/AIS bands.
- **Bus partners:** approach Dragonfly Aerospace and CubeSpace for partnership and 6U–12U quotes; explore hosted-payload slots.
- **Anchor demand:** internal LOIs from FORGE Freight and the maritime venture; outreach to one mining group and one fisheries or Navy contact.
- **Ownership:** design the 30% ownership structure with a BEE specialist.
- **Funding:** TIA/DSI grant application for the NB-IoT NTN payload lab prototype (OpenAirInterface on SDR).
- **Ground first:** stand up the first SatNOGS-based station and the ThingsBoard/Kafka platform; sign an IoT reseller agreement.
- **Regulatory watch:** confirm current status of Starlink and equity-equivalent rules in South Africa.

> **Bottom line:** FORGE STAR is buildable from South Africa if it runs as a ground and services company before it becomes a satellite company. The tools make the first two years cheap; spectrum, qualification, capital and government contracts set the schedule. Sequenced that way, the plan has a real path to a $200–500M sovereign operator, with continental upside.


*Not financial advice.*
