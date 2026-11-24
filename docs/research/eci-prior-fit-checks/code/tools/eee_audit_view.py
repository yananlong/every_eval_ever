"""Print the facts needed to audit the 50 drawn pairs (M9 step 7). Re-opens each EEE JSON and Epoch's rows."""
import sys, json, pandas as pd, numpy as np
sys.path.insert(0, "../tools"); from eee_xwalk_lib import *
seed = sys.argv[1] if len(sys.argv) > 1 else "20261113"
a = pd.read_csv(XW + f"/audit_draw_{seed}.csv")
bm = zread("benchmark_metadata.csv").set_index("benchmark"); mm = zread("model_metadata.csv").dropna(subset=["model_version"])
fi = zread("epoch_capabilities_index/processed_data_for_eci.csv").set_index(["Model", "benchmark"])
vers = mm.groupby("model_group").model_version.agg(lambda s: sorted(set(s)))
recs = []
for i, r in a.iterrows():
    d = json.load(open("ext/eee/repo/" + r.object_path)); e = d["evaluation_results"][int(r.res_idx)]
    mc = e.get("metric_config", {}); raw = e["score_details"]["score"]
    mx = mc.get("max_score"); unit = mc.get("metric_unit")
    pct = str((e["score_details"].get("details") or {}).get("canonical_rescale_factor", "")) == "" and str((mc.get("additional_details") or {}).get("pwc_scale", "")) in ("0-100", "percent")
    if isinstance(mx, str): mx = float("inf")   # "Infinity": unbounded metric recorded in percent points
    scale_by_hand = 0.01 if (mx == 100 or unit in ("percent", "percentage") or (mx in (None, float("inf")) and raw > 1.5) or pct) else 1.0
    b = bm.loc[r.eci_benchmark]
    nh = float(np.clip((raw * scale_by_hand - b.random_baseline) / (b.score_ceiling - b.random_baseline), 0, 1))
    ep = fi.loc[(r.model_group, r.eci_benchmark)]
    v = vers[r.model_group]
    sd = e.get("source_data") or {}
    extra = {k: (sd.get("additional_details") or {}).get(k) for k in ("benchmark_version", "raw_benchmark_id", "pwc_dataset_slug", "task_key") if (sd.get("additional_details") or {}).get(k)}
    gc = json.dumps((e.get("generation_config") or {}).get("additional_details") or {})[:80]
    print(f"[{i+1:2}] {r.eci_benchmark} | group={r.model_group} | EEE id={d['model_info'].get('id')} name={d['model_info'].get('name')} how={r.how}")
    print(f"     epoch versions({len(v)}): {', '.join(v)[:230]}")
    print(f"     coll={r.collection} eval={e.get('evaluation_name')} ds={sd.get('dataset_name')} metric={mc.get('metric_id')} unit={unit} max={mx} {extra} gen={gc}")
    print(f"     raw={raw} scale_hand={scale_by_hand} norm_hand={nh:.4f} stored={r.norm:.4f} match={abs(nh-r.norm)<1e-9} | epoch_norm={ep.performance:.4f} (ver {ep.model_version})")
    print(f"     src={r.src} kind={r.src_kind} rel={d['source_metadata'].get('evaluator_relationship')} stype={d['source_metadata'].get('source_type')} class={r.source_class} ({r.class_reason})")
    print(f"     refs={str(r.ref_urls)[:170]} title={str(r.ref_title)[:70]} | epoch_source={ep.source} | epoch-run={'_external' not in str(b.source_file)}")
