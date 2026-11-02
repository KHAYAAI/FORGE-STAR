"""FORGE STAR financial model, Stages 0–3.

Reads model/assumptions.yaml, builds a yearly P&L, capex and cash view for the
low/base/high scenarios, and checks the results against the headline numbers
quoted in docs/strategy.md. Outputs:
  model/results/model_<scenario>.csv     yearly line items
  model/results/summary.md               scenario summary + consistency checks
  model/results/FORGE_STAR_Model.xlsx    same tables, one sheet per scenario

Usage: python3 model/financial_model.py
Illustrative only. Not financial advice.
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

HERE = Path(__file__).parent
OUT = HERE / "results"


def apply_overrides(a: dict, sc: dict) -> dict:
    """Return a copy of the assumptions with a scenario's dotted-path overrides applied."""
    import copy
    if not sc.get("overrides"):
        return a
    a = copy.deepcopy(a)
    for path, value in sc["overrides"].items():
        node = a
        *parents, leaf = path.split(".")
        for k in parents:
            node = node[k]
        if leaf not in node:
            raise KeyError(f"scenario override points at unknown assumption: {path}")
        node[leaf] = value
    return a


def build(a: dict, sc: dict) -> list[dict]:
    a = apply_overrides(a, sc)
    yrs = a["years"]; c = a["constellation"]; g = a["ground"]; t = a["team"]
    o = a["other_opex"]; r = a["revenue"]; f = a["funding"]
    rows, cash, stations, prev_sats = [], 0.0, 0, 0
    deferred = 0.0
    for i, y in enumerate(yrs):
        R = sc["revenue"]; K = sc["capex"]; X = sc["opex"]
        # ---- revenue (average active devices across the year) ----
        dev_prev = r["iot"]["devices"][i-1] if i else 0
        dev_avg = (dev_prev + r["iot"]["devices"][i]) / 2 * R
        iot = dev_avg * r["iot"]["arpu_month"][i] * 12
        own_net = y >= r["iot"]["own_network_from_year"]
        ais = r["ais_subscribers"][i] * r["ais_price_year"][i] * R
        sov = r["sovereign"]["contract_value_year"][i] * R
        # prepayments are cash now, revenue later: draw down deferred balance against contract revenue
        prepay_in = r["sovereign"]["prepayment"][i] * R
        deferred += prepay_in
        release = min(deferred, sov); deferred -= release
        gs = r["ground_services"][i] * R
        ms_sites = r["managed_sites"]["sites"][i] * R
        ms = ms_sites * r["managed_sites"]["price_month"] * 12
        eco = r["ecosystem"][i] * R
        revenue = iot + ais + sov + gs + ms + eco

        # ---- cost of revenue ----
        own_rev = (iot if own_net else 0) + ais + sov + eco
        cogs = (0 if own_net else iot * o["cogs_resale_pct"]) + ms * o["cogs_leased_pct"] \
            + (own_rev * o["network_cogs_pct"] if prev_sats or c["sats_in_service"][i] else 0)

        # ---- opex ----
        stations += g["stations_added"][i]
        team = t["headcount"][i] * t["loaded_cost"][i] * X
        ground_opex = stations * g["opex_per_station"] * X
        platform = (o["platform_cloud"][i] + o.get("gateway_leases", [0] * len(yrs))[i]) * X
        spectrum = o["spectrum_legal"][i] * X
        sales = revenue * o["sales_marketing_pct_revenue"]
        ga = o["g_and_a"][i] * X
        opex = team + ground_opex + platform + spectrum + sales + ga

        # ---- capex ----
        new_sats = max(c["sats_in_service"][i] - prev_sats, 0) + round(prev_sats * c["replacement_rate"][i])
        prev_sats = c["sats_in_service"][i]
        sat_capex = new_sats * (c["sat_unit_cost"][i] + c["launch_per_sat"][i]) * (1 + c["insurance_pct"]) * K
        hosted = c["hosted_payloads"][i] * c["hosted_payload_cost"] * K
        ground_capex = g["stations_added"][i] * g["station_cost"][i] * K
        capex = sat_capex + hosted + ground_capex

        ebitda = revenue - cogs - opex
        operating_cash = ebitda + (prepay_in - release)
        funding = sum(f[k][i] for k in ("founder_and_bootstrap", "grants", "angel_seed", "series_a", "series_b", "debt_or_dfi"))
        equity = sum(f[k][i] for k in ("founder_and_bootstrap", "angel_seed", "series_a", "series_b"))
        cash += operating_cash - capex + funding
        rows.append({
            "year": y, "sats_in_service": c["sats_in_service"][i], "devices_avg": round(dev_avg),
            "rev_iot": iot, "rev_ais": ais, "rev_sovereign": sov, "rev_ground_services": gs,
            "rev_managed_sites": ms, "rev_ecosystem": eco, "revenue": revenue,
            "cogs": cogs, "gross_margin_pct": (revenue - cogs) / revenue * 100 if revenue else 0,
            "opex_team": team, "opex_other": opex - team, "opex": opex, "ebitda": ebitda,
            "capex_satellites": sat_capex + hosted, "capex_ground": ground_capex, "capex": capex,
            "prepayment_in": prepay_in, "prepayment_released": release, "funding_in": funding, "equity_in": equity,
            "grants_in": f["grants"][i], "cash_end": cash,
        })
    return rows


FUND_KEYS = ("founder_and_bootstrap", "grants", "angel_seed", "series_a", "series_b", "debt_or_dfi")


def monthly(a: dict, rows: list[dict]) -> list[dict]:
    """Monthly cash: operating flows spread evenly, capex front-loaded, funding in its month."""
    fm = a.get("funding_month", {}); front = a.get("capex_front_load", 0.5)
    out, cash = [], 0.0
    for i, r in enumerate(rows):
        op_year = r["ebitda"]
        prepay_net = r["prepayment_in"] - r["prepayment_released"]  # cash received ahead of revenue
        for mth in range(1, 13):
            capex = r["capex"] * (front / 6 if mth <= 6 else (1 - front) / 6)
            fund = sum(a["funding"][k][i] for k in FUND_KEYS if fm.get(k, 1) == mth)
            prepay = prepay_net / 12
            cash += op_year / 12 - capex + fund + prepay
            out.append({"year": r["year"], "month": mth, "operating": op_year / 12, "capex": capex,
                        "funding": fund + prepay, "cash_end": cash})
    return out


def cap_table(a: dict) -> list[dict]:
    """Ownership after each round, and the HDG (historically disadvantaged group) share."""
    o = a["ownership"]
    holders = [dict(name=f["name"], shares=float(f["shares"]), hdg=1.0 if f.get("hdg") else 0.0,
                    pool=bool(f.get("pool"))) for f in o["founders"]]
    def snapshot(label):
        tot = sum(h["shares"] for h in holders)
        hdg = sum(h["shares"] * (o["esop_hdg_share"] if h["pool"] else h["hdg"]) for h in holders)
        return {"after": label, "total_shares": tot, "hdg_pct": 100 * hdg / tot,
                "holders": {h["name"]: 100 * h["shares"] / tot for h in holders}}
    snaps = [snapshot("Founding")]
    for rd in o["rounds"]:
        tot = sum(h["shares"] for h in holders)
        price = rd["pre_money"] / tot
        new = rd["raise"] / price
        holders.append(dict(name=rd["name"] + " investors", shares=new, hdg=rd["investor_hdg_share"], pool=False))
        if rd.get("esop_topup_pct"):
            post = sum(h["shares"] for h in holders)
            pool = next(h for h in holders if h["pool"])
            pool["shares"] += post * rd["esop_topup_pct"] / 100 / (1 - rd["esop_topup_pct"] / 100)
        trust = (o.get("hdg_trust_issue_pct") or {}).get(rd["name"])
        if trust:
            post = sum(h["shares"] for h in holders)
            holders.append(dict(name="HDG trust", shares=post * trust / 100 / (1 - trust / 100), hdg=1.0, pool=False))
        snaps.append(snapshot(rd["name"]) | {"price_per_share": price, "post_money": rd["pre_money"] + rd["raise"]})
    return snaps


def m(x):  # $ millions
    return f"{x/1e6:,.1f}"


def main():
    a = yaml.safe_load((HERE / "assumptions.yaml").read_text())
    OUT.mkdir(exist_ok=True)
    results = {name: build(a, sc) for name, sc in a["scenarios"].items()}

    for name, rows in results.items():
        with open(OUT / f"model_{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader()
            w.writerows({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)

    L = ["# FORGE STAR financial model — results", "",
         "Generated by `model/financial_model.py` from `model/assumptions.yaml`. USD millions. Illustrative; not financial advice.", ""]
    for name, rows in results.items():
        L += [f"## Scenario: {name}", "",
              "| Year | Sats | Revenue | Gross margin | Opex | EBITDA | Capex | Funding in | Cash end |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            L.append(f"| {r['year']} | {r['sats_in_service']} | {m(r['revenue'])} | {r['gross_margin_pct']:.0f}% | "
                     f"{m(r['opex'])} | {m(r['ebitda'])} | {m(r['capex'])} | {m(r['funding_in'])} | {m(r['cash_end'])} |")
        min_cash = min(r["cash_end"] for r in rows)
        gross = sum(r["capex"] + max(-r["ebitda"], 0) for r in rows)
        equity = sum(r["equity_in"] for r in rows)
        last = rows[-1]
        L += ["", f"- Gross capital need to Stage 3 (capex + operating losses): **${m(gross)}M**",
              f"- Equity raised: **${m(equity)}M**; grants ${m(sum(r['grants_in'] for r in rows))}M; "
              f"prepayments ${m(sum(r['prepayment_in'] for r in rows))}M",
              f"- Lowest year-end cash: **${m(min_cash)}M**" + ("  ⚠️ funding gap: raise more or earlier" if min_cash < 0 else ""),
              f"- Year-{last['year']} revenue: **${m(last['revenue'])}M** with {last['sats_in_service']} satellites", ""]

    # consistency checks against the strategy's headline claims (base case)
    b = results["base"]
    stage3 = b[-1]
    gross_b = sum(r["capex"] + max(-r["ebitda"], 0) for r in b)
    eq_b = sum(r["equity_in"] for r in b)
    checks = [
        ("Cumulative gross to Stage 3", "$51–105M", f"${m(gross_b)}M", 51e6 <= gross_b <= 105e6),
        ("Equity to Stage 3", "$40–75M", f"${m(eq_b)}M", 40e6 <= eq_b <= 75e6),
        ("Stage 3 revenue", "$25–45M", f"${m(stage3['revenue'])}M", 25e6 <= stage3["revenue"] <= 45e6),
        ("Stage 0 (yr 1) revenue", "R5–30M (≈$0.3–1.7M)", f"${m(b[0]['revenue'])}M (R{b[0]['revenue']*a['fx_zar_per_usd']/1e6:.0f}M)",
         5e6 / a["fx_zar_per_usd"] <= b[0]["revenue"] <= 30e6 / a["fx_zar_per_usd"]),
        ("Stage 0 spend (yr 1 capex+opex)", "$1–3M", f"${m(b[0]['capex'] + b[0]['opex'] + b[0]['cogs'])}M",
         1e6 <= b[0]["capex"] + b[0]["opex"] + b[0]["cogs"] <= 3e6),
        ("Never runs out of cash (base)", "cash ≥ 0", f"min ${m(min(r['cash_end'] for r in b))}M", min(r["cash_end"] for r in b) >= 0),
    ]
    # monthly cash and ownership
    mon = {name: monthly(a, rows) for name, rows in results.items()}
    caps = cap_table(a)
    hdg_min = a["ownership"]["hdg_minimum_pct"]
    L += ["## Monthly cash (low point and runway)", "", "| Scenario | Lowest month-end cash | When | Months below zero |", "|---|---|---|---|"]
    for name, ms in mon.items():
        lo = min(ms, key=lambda x: x["cash_end"])
        neg = sum(1 for x in ms if x["cash_end"] < 0)
        L.append(f"| {name} | ${m(lo['cash_end'])}M | year {lo['year']}, month {lo['month']} | {neg}{'  ⚠️' if neg else ''} |")
    L += ["", "## Ownership and the 30% HDG rule", "",
          f"HDG = historically disadvantaged group. ICASA minimum {hdg_min:.0f}% (re-verify with counsel). "
          f"Counts founder HDG holdings, {a['ownership']['esop_hdg_share']*100:.0f}% of the ESOP pool and each round's HDG investor share.", "",
          "| After | Post-money | HDG share | OK | Largest holders |", "|---|---|---|---|---|"]
    for c in caps:
        top = ", ".join(f"{k} {v:.0f}%" for k, v in sorted(c["holders"].items(), key=lambda x: -x[1])[:3])
        L.append(f"| {c['after']} | {('$' + m(c['post_money']) + 'M') if 'post_money' in c else '—'} | {c['hdg_pct']:.1f}% | "
                 f"{'✅' if c['hdg_pct'] >= hdg_min else '❌'} | {top} |")
    worst = min(caps, key=lambda c: c["hdg_pct"])
    if worst["hdg_pct"] < hdg_min:
        L += ["", f"⚠️ HDG share falls to {worst['hdg_pct']:.1f}% after {worst['after']}. Options: HDG anchor investors (IDC, NEF, PIC), "
              "a broad-based HDG trust issued at that round (`hdg_trust_issue_pct`), or an approved equity-equivalent programme."]
    checks.append(("HDG ownership ≥30% after every round", "≥30%", f"min {worst['hdg_pct']:.1f}% ({worst['after']})", worst["hdg_pct"] >= hdg_min))
    checks.append(("No month below zero cash (base)", "cash ≥ 0", f"min ${m(min(x['cash_end'] for x in mon['base']))}M",
                   min(x["cash_end"] for x in mon["base"]) >= 0))
    L += ["", "## Consistency checks vs docs/strategy.md (base case)", "",
          "| Claim | Strategy says | Model gives | OK |", "|---|---|---|---|"]
    L += [f"| {c} | {s} | {mm} | {'✅' if ok else '❌'} |" for c, s, mm, ok in checks]
    (OUT / "summary.md").write_text("\n".join(L) + "\n")

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        wb = Workbook(); wb.remove(wb.active)
        for name, rows in results.items():
            ws = wb.create_sheet(name)
            keys = list(rows[0].keys())
            ws.append(["line"] + [f"Year {r['year']}" for r in rows])
            for k in keys[1:]:
                ws.append([k] + [round(r[k], 0) if isinstance(r[k], float) and abs(r[k]) > 100 else r[k] for r in rows])
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="1B1E24")
            ws.column_dimensions["A"].width = 22
            for row in ws.iter_rows(min_row=2, min_col=2):
                for cell in row: cell.number_format = "#,##0"
        ws = wb.create_sheet("monthly_cash")
        ws.append(["year", "month"] + [f"{n}_cash_end" for n in mon])
        for i in range(len(mon["base"])):
            ws.append([mon["base"][i]["year"], mon["base"][i]["month"]] + [round(mon[n][i]["cash_end"]) for n in mon])
        ws = wb.create_sheet("ownership")
        names = list(caps[-1]["holders"].keys())
        ws.append(["after", "post_money", "hdg_pct"] + names)
        for c in caps:
            ws.append([c["after"], c.get("post_money", 0), round(c["hdg_pct"], 2)] + [round(c["holders"].get(n, 0), 2) for n in names])
        for sh in ("monthly_cash", "ownership"):
            for cell in wb[sh][1]:
                cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="1B1E24")
        wb.save(OUT / "FORGE_STAR_Model.xlsx")
    except ImportError:
        pass
    print("\n".join(L))


if __name__ == "__main__":
    main()
