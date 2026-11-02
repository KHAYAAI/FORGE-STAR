# FORGE STAR

Africa's sovereign satellite data network. Strategy, models and Stage 0 platform.

| Path | What | Run |
|---|---|---|
| `docs/strategy.md` | Full strategy (source of truth) | |
| `scripts/build_pdf.py` | Renders strategy.md to `output/FORGE_STAR_Strategy.pdf` | `pip install reportlab && python3 scripts/build_pdf.py` |
| `forgestar/` | Shared package: orbits (J2), link budget, store-and-forward logic | |
| `sim/` | Coverage, revisit, gateway passes, link budget | `python3 sim/coverage_sim.py` |
| `model/` | Financial model, Stages 0–3 | `pip install pyyaml openpyxl && python3 model/financial_model.py` |
| `ground/` | Stage 0 platform: devices → Kafka → store-and-forward satellites → TimescaleDB; ThingsBoard; SatNOGS | `cd ground && docker compose up -d` |
| `ground/thingsboard/provision.py` | Creates ThingsBoard devices and the operations dashboard | `docker compose --profile full up -d` then `python3 ground/thingsboard/provision.py` |
| `ground/gateway/` | Downlink handler: decodes satellite frames into device messages | runs in the stack |
| `readiness/` | ICASA/ITU, funding, lab, orbit and customer milestones with dependencies | `python3 readiness/tracker.py` → `readiness/STATUS.md` |
| `sim/antenna_trade.py`, `sim/sgp4_crosscheck.py` | Antenna options; orbit model validation | `python3 sim/antenna_trade.py` |
| `tests/` | Test suite (also run by CI) | `pip install -r requirements.txt && python3 -m pytest` |
| `docs/ntn-testbed-plan.md` | NB-IoT NTN lab plan | |
| `research/` | Original inputs | |

Delivery latency by path (what customer SLAs are written against):

```bash
cd ground && docker compose exec timescaledb psql -U forge -d forgestar -c "select * from latency_sla;"
```

All figures are illustrative. Not financial advice.
