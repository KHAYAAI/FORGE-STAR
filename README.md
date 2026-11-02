# FORGE STAR

Africa's sovereign satellite data network. Strategy, models and Stage 0 platform.

| Path | What | Run |
|---|---|---|
| `docs/strategy.md` | Full strategy (source of truth) | |
| `scripts/build_pdf.py` | Renders strategy.md to `output/FORGE_STAR_Strategy.pdf` | `pip install reportlab && python3 scripts/build_pdf.py` |
| `sim/` | Coverage and revisit simulation | `python3 sim/coverage_sim.py` |
| `model/` | Financial model, Stages 0–3 | `pip install pyyaml openpyxl && python3 model/financial_model.py` |
| `ground/` | Stage 0 platform: Kafka → TimescaleDB, ThingsBoard, SatNOGS | `cd ground && docker compose up -d` |
| `docs/ntn-testbed-plan.md` | NB-IoT NTN lab plan | |
| `research/` | Original inputs | |

Check what the platform has stored:

```bash
cd ground && docker compose exec timescaledb psql -U forge -d forgestar -c "select kind, count(*) from uplinks join devices using(device_id) group by 1;"
```

All figures are illustrative. Not financial advice.
