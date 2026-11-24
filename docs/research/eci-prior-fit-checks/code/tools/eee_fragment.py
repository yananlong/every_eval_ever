"""Write runs/EEE/SUMMARY.md, runs/EEE/fragment.html and runs/EEE/chart_data.json. Run from eci_work/v11 with python3,
after eee_summary.py (headline.json), eee_compare_eci.py / eee_compare_bench.py (eci_compare.json) and eee_report.py (side_by_side.json).
Prose paragraphs live in runs/EEE/prose.json (hand-written from the numbers; keys used below), so the tables stay data-driven."""
import json, os, csv, html
E = "runs/EEE"
S = json.load(open(f"{E}/side_by_side.json")); rows = S["rows"]; cov = S["coverage"]; aud = S["audit"]; c = S["eci"]
H = json.load(open(f"{E}/headline.json")); ep, ex = H["epoch"], H["eee"]
P = json.load(open(f"{E}/prose.json")) if os.path.exists(f"{E}/prose.json") else {}
bb = list(csv.DictReader(open(f"{E}/input/coverage_by_benchmark.csv")))
esc = html.escape


def pill(ok, text): return f'<span class="pill {"pass" if ok else "fail"}">{esc(text)}</span>'


NCL = ' class="n"'
def table(head, body, num_from=1):
    th = "".join(f'<th{NCL if i >= num_from else ""}>{h}</th>' for i, h in enumerate(head))
    trs = []
    for r in body:
        trs.append("<tr>" + "".join(f'<td{NCL if i >= num_from else ""}>{v}</td>' for i, v in enumerate(r)) + "</tr>")
    return '<div class="tblwrap"><table>\n      <thead><tr>' + th + "</tr></thead>\n      <tbody>\n        " + "\n        ".join(trs) + "\n      </tbody>\n    </table></div>"


def para(key):
    return "".join(f"\n  <p>{t}</p>" for t in P.get(key, []))


# ---------- tables
cls = cov["by_class"]
chg = {}
for r in csv.DictReader(open(f"{E}/input/eee_fit_input_annotated.csv")):
    if float(r["absdiff"]) > 0.0015: chg[r["eee_class"]] = chg.get(r["eee_class"], 0) + 1
t_cov = table(["Source class of the EEE score", "Cells", "Share of 2,879", "Cells that differ from Epoch's value by more than 0.0015"],
              [[k, f"{cls.get(kk, 0):,}", f"{100 * cls.get(kk, 0) / cov['cells']:.1f}%", f"{chg.get(kk, 0):,}"] for k, kk in
               (("Independent (the source ran the benchmark itself)", "independent"), ("Same-upstream (copied from the measurement Epoch used)", "same-upstream"),
                ("Upstream-unknown (aggregated, provenance not tied to Epoch's source)", "upstream-unknown"), ("No EEE score, Epoch's value kept", "none"))]
              + [["All cells", f"{cov['cells']:,}", "100%", f"{cov['changed_gt_0015']:,}"]])
t_bench = table(["Benchmark", "Cells", "With EEE score", "Independent", "Same-upstream", "Upstream-unknown", "Changed", "Mean absolute difference"],
                [[esc(r["benchmark"]), r["cells"], r["eee"], r["independent"], r["same_upstream"], r["unknown"], r["changed"], f"{float(r['mean_absdiff']):.3f}"] for r in bb if int(r["eee"]) >= 8])
strata = [("All non-anchor models", "all"), ("Frontier", "frontier"), ("Sparse (6 or fewer scores)", "sparse"), ("Dense", "dense")]
t_eci = table(["Stratum", "Models", "Spearman", "Mean shift", "Median absolute shift", "Largest shift", "Moved by more than 0.25 W", "90% intervals intersect", "Median width ratio"],
              [[lab, c[k]["n"], f"{c[k]['spearman']:.4f}", f"{c[k]['mean_shift']:+.2f}", f"{c[k]['median_abs_shift']:.2f}", f"{c[k]['max_abs_shift']:.1f}", c[k]["n_shift_gt_quarter_W"],
                f"{100 * c[k]['share_intervals_intersect']:.0f}%", f"{c[k]['median_width_ratio']:.2f}"] for lab, k in strata])
t_top = table(["Model", "Rank, Epoch data", "Rank, EEE data", "ECI, Epoch data", "ECI, EEE data", "Shift"],
              [[esc(x["model"]), x["rank_epoch"], x["rank_eee"], f"{x['eci_epoch']:.1f}", f"{x['eci_eee']:.1f}", f"{x['eci_eee'] - x['eci_epoch']:+.2f}"] for x in c["top10_table"]])
t_band = table(["ECI in the Epoch-data fit", "Models", "Mean shift", "Largest absolute shift"],
               [[b["band"].replace("below-", "below ").replace("-above", " and above").replace("-", " to "), b["n"], f"{b['mean_shift']:+.2f}", f"{b['max_abs']:.1f}"] for b in c.get("shift_by_band", [])])
t_edi = table(["Benchmark", "EDI, Epoch data", "EDI, EEE data", "Shift", "Cells", "Cells changed"],
              [[esc(x["benchmark"]), f"{x['edi_epoch']:.1f}", f"{x['edi_eee']:.1f}", f"{x['edi_shift']:+.1f}", x["cells"], x["changed"]] for x in c.get("benchmarks", {}).get("top", [])[:6]])


def sbs(sections):
    body = []
    for s, l, a, b in rows:
        if s in sections: body.append([esc(l).replace("; ", ", "), esc(str(a)).replace("; ", ", "), esc(str(b)).replace("; ", ", ")])
    return table(["Quantity", "Epoch data", "EEE data"], body)


verd = P.get("verdicts", [])   # [question, epoch result text, epoch ok, eee result text, eee ok]
t_verd = table(["Question", "Epoch data", "EEE data"], [[esc(q), pill(ao, a), pill(bo, b)] for q, a, ao, b, bo in verd], num_from=9)

frag = f'''<section id="eee">
  <h2>N. Mirror on EEE data: {P.get("title", "the same checks on a matrix with Every Eval Ever scores")}</h2>{para("intro")}

  <div class="sub-sec" id="eee-data"><h3 class="ssh">N.1 Data, crosswalk and audit</h3>{para("data")}
    {t_cov}
    <p class="src">Source: runs/EEE/input/coverage.json, runs/EEE/crosswalk/pairs.csv, audit_result.json.</p>
    {t_bench}
    <p class="src">Benchmarks with at least 8 cells carrying an EEE score. Source: runs/EEE/input/coverage_by_benchmark.csv.</p>{para("data2")}
  </div>

  <div class="sub-sec" id="eee-eci"><h3 class="ssh">N.2 ECI on the two matrices</h3>{para("eci")}
    {t_eci}
    <p class="src">EEE-data fit against Epoch-data fit, Reproduction fit (W2), seed 12345. W is the 90% interval width in the Epoch-data fit. Source: runs/EEE/eci_compare.json.</p>
    {t_top}
    <p class="src">The ten highest-ranked models of either fit.</p>{para("eci2")}
    {t_band}
    {t_edi}
    <p class="src">Benchmarks with the largest change in difficulty (EDI). Source: runs/EEE/edi_compare.csv.</p>{para("eci3")}
  </div>

  <div class="sub-sec" id="eee-verdicts"><h3 class="ssh">N.3 The checks, side by side</h3>{para("checks")}
    {t_verd}
    <div class="fig"><h3 id="eee-w3">Reproduction fit and Simulation study (W2, W3)</h3>
    {sbs(["W2 reproduction fit", "W3 simulation study", "W3 power", "W3 convergence", "W3 positive control", "W3 SBC (M13)", "W3 gate G1", "W3M rank tests (Modrak-style)"])}
    </div>{para("w3")}
    <div class="fig"><h3 id="eee-w4">Posterior predictive checks and localisation (W4, W4d)</h3>
    {sbs(["W4 residual checks", "W4 marginal fit", "W4 localisation", "W4 verdict"])}
    </div>{para("w4")}
    <div class="fig"><h3 id="eee-wa">Anchors (WA and extension)</h3>
    {sbs(["Anchors"])}
    </div>{para("wa")}
    <div class="fig"><h3 id="eee-w5">Prior sensitivity (W5)</h3>
    {sbs(["W5 prior sensitivity"])}
    </div>{para("w5")}
    <p class="src">Source: runs/EEE/headline.json and side_by_side.json, built from runs/W/ (Epoch data) and runs/EEE/ (EEE data) by the same extraction code.</p>
  </div>

  <div class="sub-sec" id="eee-limits"><h3 class="ssh">N.4 What this mirror can and cannot show</h3>{para("limits")}
  </div>
</section>
'''
open(f"{E}/fragment.html", "w").write(frag)

# ---------- SUMMARY.md
def md_table(head, body): return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in body)
md = [f"# Mirror of the ECI prior and fit checks on EEE data\n\n{P.get('md_intro', '')}\n", "## Crosswalk audit\n", P.get("md_audit", ""), "\n## Coverage\n", P.get("md_coverage", ""),
      "\n## ECI: Epoch-data fit against EEE-data fit\n",
      md_table(["Stratum", "Models", "Spearman", "Mean shift", "Median abs shift", "Largest shift", "Moved > 0.25 W", "Intervals intersect", "Median width ratio"],
               [[lab, c[k]["n"], f"{c[k]['spearman']:.4f}", f"{c[k]['mean_shift']:+.2f}", f"{c[k]['median_abs_shift']:.2f}", f"{c[k]['max_abs_shift']:.1f}", c[k]["n_shift_gt_quarter_W"], f"{100 * c[k]['share_intervals_intersect']:.0f}%", f"{c[k]['median_width_ratio']:.2f}"] for lab, k in strata]),
      "\n", P.get("md_eci", ""), "\n## Side by side: every headline number\n"]
sec = None; body = []
for s, l, a, b in rows:
    if s != sec:
        if body: md.append(md_table(["Quantity", "Epoch data", "EEE data"], body) + "\n"); body = []
        md.append(f"### {s}\n"); sec = s
    body.append([l, a, b])
if body: md.append(md_table(["Quantity", "Epoch data", "EEE data"], body) + "\n")
md += ["## Reading\n", P.get("md_reading", ""), "\n## Deviations and wall-clock\n", P.get("md_deviations", "")]
open(f"{E}/SUMMARY.md", "w").write("\n".join(md))

# ---------- chart data (small)
cd = dict(eci_scatter=[dict(m=r["model"], e=float(r["eci_epoch"]), x=float(r["eci_eee"]), cells=int(r["cells"]), changed=int(r["changed_cells"])) for r in csv.DictReader(open(f"{E}/eci_compare.csv"))],
          shift_by_band=c.get("shift_by_band"), coverage_by_class=cls,
          coverage_by_benchmark=[dict(b=r["benchmark"], cells=int(r["cells"]), eee=int(r["eee"]), changed=int(r["changed"])) for r in bb],
          T_obs={k: dict(epoch={t: v["obs"] for t, v in (ep.get("W4") or {}).get("T", {}).items()}, eee={t: v["obs"] for t, v in (ex.get("W4") or {}).get("T", {}).items()}) for k in ("checks",)},
          T_p_adj=dict(epoch={t: v["p_adj"] for t, v in (ep.get("W4") or {}).get("T", {}).items()}, eee={t: v["p_adj"] for t, v in (ex.get("W4") or {}).get("T", {}).items()}),
          power=dict(epoch={g_: [v["n_reject"], v["n_converged"]] for g_, v in (ep.get("W3") or {}).get("power", {}).items()}, eee={g_: [v["n_reject"], v["n_converged"]] for g_, v in (ex.get("W3") or {}).get("power", {}).items()}),
          edi_top=c.get("benchmarks", {}).get("top"))
json.dump(cd, open(f"{E}/chart_data.json", "w"), separators=(",", ":"))
print("fragment", len(frag), "summary", sum(len(x) for x in md), "chart_data", os.path.getsize(f"{E}/chart_data.json"))
