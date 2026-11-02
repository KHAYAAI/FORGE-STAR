# FORGE STAR — Strategy

> Africa's sovereign satellite data network: compliant, locally owned LEO infrastructure that connects the assets, vessels and people that terrestrial networks will never reach.

All figures are illustrative. Re-verify market and regulatory facts before external use.

---

## 1. What FORGE STAR is

FORGE STAR is a South African company in the FORGE ecosystem. It will build a neutral, sovereign LEO communications network for Africa and the Global South: a third option for governments and operators that don't want to depend on Starlink (US) or Guowang/Qianfan (China).

**Why now**
- **Starlink is shut out of South Africa.** ICASA's 30% historically-disadvantaged ownership rule blocks it, and FORGE STAR can comply.
- **Chinese constellations are far behind their targets** and carry alignment risk.
- **Other options don't serve African sovereign demand.** OneWeb is enterprise-only in SA, Amazon Leo is still preparing to enter, and IRIS² has no satellites in orbit.
- **Early-stage costs have collapsed.** Open-source software and AI-assisted design make a demonstrator cheap.

## 2. Refinements to the original plan

| Original issue | Refinement |
|---|---|
| D2C on a $300k small satellite doesn't close | Lead with NB-IoT NTN and store-and-forward; do D2C later via a partner |
| A PocketQube proves software, not the business | Hosted payload first, then a 6U–12U |
| Building our own bus | Buy it from Dragonfly or CubeSpace; own the payload, network, ground and ops |
| 30% rule seen only as a moat | It also binds us; structure for it now; watch equity-equivalent reforms |
| Mega-filing through ICASA | A modest NGSO filing of 24–100 satellites in IoT bands |
| Conflicting figures | Launch at $80–250k per 6U–12U slot; revenue built from unit math |
| Too many products | One wedge first |

**Payload functions:**
1. NB-IoT NTN and store-and-forward messaging
2. Satellite AIS/VDES
3. Sovereign data relay, with data landed in SA

**What FORGE STAR gives the rest of the ecosystem:**
- **FORGE Freight:** tracking
- **Maritime USV venture:** over-the-horizon link and AIS
- **FORGE VOCAL:** satellite USSD fallback
- **ForgePay:** offline settlement
- **FORGE EYE:** sovereign data
- **Autonomy/robotics:** telemetry

## 3. Target market

**Beachhead customers (Stages 0–2)**

| Segment | Buyers | Offer | Pricing |
|---|---|---|---|
| Maritime & security | SA Navy, DFFE, SAMSA, Transnet ports, insurers | AIS vessel tracking, illegal-fishing detection | Subscription / contract |
| Mining & energy | Mining houses, Eskom, IPPs, pipelines | Remote asset monitoring | Per device/month + platform fee |
| Agriculture & water | Farms, co-ops, water boards | Sensors beyond cell coverage | Per device/month |
| Conservation | SANParks, reserves, anti-poaching units | Collars, fence sensors, ranger messaging | Per device or per reserve |
| FORGE ecosystem | Freight, USV, VOCAL, ForgePay, EYE | Tracking, links, offline messaging | Internal contracts |
| Ground station services | Foreign satellite operators | Southern-hemisphere passes | Per pass or per month |

**Expansion customers (Stage 3+)**
- **SA government connectivity** (DCDT/SA Connect, provinces, Education, Health): managed rural sites, priced per site per month.
- **Mobile operators** (MTN, Vodacom, Telkom, Cell C, Rain): wholesale NB-IoT NTN capacity on a revenue share.
- **SADC logistics corridors:** priced per asset per month.
- **Other African governments:** constellation-in-a-box, funded by co-financing plus a revenue share.

## 4. Business model

**Revenue lines**
- **IoT connectivity:** $2–5 per device per month
- **Maritime data:** annual subscriptions
- **Sovereign capacity:** multi-year contracts, partly prepaid
- **Ground station services**
- **Later:** constellation-in-a-box and mobile-operator wholesale

**Why it works**
- The ecosystem supplies captive demand from day one.
- Customers co-finance the build.
- The ownership rule gives a compliance advantage.
- Pricing is competitive against new LEO IoT services (~$1–€8 per device per month) and far below legacy satellite IoT ($40–70).

**Free internet paid for by government**
- **Covering everyone on our own satellites isn't feasible.** 30M users at 10 GB/month needs about 1 Tbps average, which is Starlink-scale.
- **What is feasible:** satellite backhaul to 10–20k government sites (schools, clinics, hotspots), as part of a hybrid national plan aligned with SA Connect.
- **Phasing:** start on leased capacity at Stage 0 and move to our own satellites later. Government pays per site per month.

## 5. Build strategy and stack

- **We buy:** the bus, antennas and solar panels.
- **We build:** the payload, network, ground segment, platform and operations.
- **We accelerate with:** open source, heypcb.ai and Claude Code.

| Layer | Components |
|---|---|
| Flight software | F´, cFS, libcsp, Zephyr/FreeRTOS |
| Reference HW | LibreCube, BIRDS |
| Mech / electronics | FreeCAD, KiCad |
| RF / payload | GNU Radio, SoapySDR, gr-satellites, SatDump, AIS-catcher/gr-ais |
| IoT radio & core | OpenAirInterface NTN, Open5GS/free5GC |
| Ground | SatNOGS, Gpredict+Hamlib, Yamcs/COSMOS, Open MCT, TinyGS |
| Flight dynamics | Orekit, GMAT, Skyfield |
| Constellation | OpenSN |
| Platform | ThingsBoard, Kafka, PostgreSQL+TimescaleDB |

**heypcb.ai builds:** payload processor boards, radio carriers, bus-interface boards, and ground/test boards. **It doesn't cover:** structure, thermal design, high-performance RF/antennas, radiation qualification or bus integration.

**Four things decide whether the satellite is usable:**
1. Permission to transmit (ICASA licence and ITU filing)
2. Qualification
3. Launch
4. Ground devices and coverage

## 6. Coverage (first-order, ~550 km inclined)

| Service | SA | SADC | Africa |
|---|---|---|---|
| Store-and-forward IoT (hours) | 2–6 | 4–8 | 6–12 |
| Frequent IoT (20–40 min) | 16–24 | 24–36 | 30–48 |
| Continuous narrowband | 50–90 | 60–110 | 80–150 |
| Broadband | set by capacity | | |

LEO satellites can't be parked over SA, so how often they revisit matters more than the size of the region.

## 7. Stages and build-strategy coverage

| Stage | Sats | Timing | What works | Capital | Tech / total covered |
|---|---|---|---|---|---|
| 0 Ground first | 0 | 0–12 mo | Ground stations, platform, resold capacity, licences | $1–3M | ~90% / ~50% |
| 1 Demonstrator | 1–2 | 12–30 mo | Store-and-forward IoT, AIS, full-chain proof | $5–12M | ~60% / ~30% |
| 2 Early service | 6–12 | yr 2.5–3.5 | Africa-wide IoT in 1–3 h | $15–30M | ~55% / ~25% |
| 3 Operational | 24–48 | yr 3.5–5 | IoT in ~30 min, ITU filing secured, sovereign contract | $30–60M | ~50% / ~20% |
| 4 Continuous | 80–150 | yr 5–7 | Real-time messaging | $100–250M | ~35% / ~15% |
| 5 Broadband | hundreds+ | yr 7+ | National rural connectivity | $0.5–2B+ | ~15–20% / ~5–10% |

## 8. Distance to full launch (24–48 satellites)

| Component | Share | OSS + heypcb | + Claude | Contribution |
|---|---|---|---|---|
| Software | 20% | 80% | ~94% | 18.8% |
| Simulation | 5% | 90% | ~98% | 4.9% |
| Electronics | 10% | 55% | ~66% | 6.6% |
| Payload RF | 10% | 20% | ~40% | 4.0% |
| Bus | 10% | 0% | ~10% | 1.0% |
| Testing | 10% | 0% | ~20% | 2.0% |
| Spectrum | 10% | 0% | ~25% | 2.5% |
| Launch | 5% | 0% | ~5% | 0.25% |
| Capital & sales | 20% | 0% | ~15% | 3.0% |
| **Total** | 100% | **~28%** | | **~43%** |

## 9. Capital and bootstrapping

- **Capital to reach Stage 3:** $51–105M gross, about $40–75M equity.
- **What bootstrapping can fund:** Stage 0 plus a hosted payload, about $0.3–1M over roughly 2 years.
- **Stage 0 revenue:** IoT resale, ground-station services, managed rural sites on leased capacity, and contracts from the FORGE ecosystem.
- **Non-dilutive funding to pursue:** TIA, DSI, SANSA, NEF, IDC, DTIC.
- **Raising equity:** Series A ($15–30M) at Stage 2.
- **Founding team:**
  - CEO
  - RF/SDR engineer
  - Software/ground engineer
  - Embedded engineer (using heypcb.ai)
  - Part-time spectrum advisor
  - Sales lead

## 10. Competition

| Competitor | FORGE STAR's angle |
|---|---|
| Starlink | Don't fight on broadband; win on sovereignty and compliance |
| Guowang/Qianfan | Win the non-aligned segment |
| OneWeb/IRIS² | Neither serves African sovereign demand or mass IoT |
| Amazon Leo | A future competitor |
| Exosat | Closest comparable; FORGE STAR is Africa-first |
| Kinéis/Myriota/Sateliot | Compete on sovereignty and local service |

## 11. Potential (illustrative)

| Stage | Revenue | Valuation |
|---|---|---|
| 0–1 | R5–30M | $5–30M |
| 2 | $3–10M | $50–150M |
| 3 | $25–45M | $200–500M |
| 4 | $100–300M | $1–3B |
| 5 | $500M+ | $3–10B+ |

**Stage 3 revenue build:**
- IoT: 300k devices × $3 ≈ $11M
- AIS: $3–6M
- Sovereign capacity: $10–25M
- Ground stations: $1–2M
- **Total: ≈ $25–45M**

This is not financial advice.

## 12. Risks and next 90 days

**Risks:**
- Spectrum
- Changes to the ownership rules
- Qualification and RF
- Capital
- Government sales cycles
- Launch slippage

**Next 90 days:**
1. ICASA pre-application meeting and spectrum counsel
2. Bus partner quotes and hosted-payload slots
3. Ecosystem LOIs, plus one mining group and one fisheries/Navy contact
4. Design the 30% ownership structure
5. TIA/DSI grant for the NB-IoT NTN lab
6. First SatNOGS station and platform, plus an IoT reseller deal
7. Regulatory watch on Starlink
