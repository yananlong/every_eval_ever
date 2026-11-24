"""M9 steps 1-2 on the latest EEE manifest: verify sha256 of every aggregate object, flatten to one row
per evaluation_results element. Usage: eee_flatten.py <eee_dir> <out_dir>"""
import sys, json, hashlib, os
from multiprocessing import Pool
import pandas as pd
EEE, OUT = sys.argv[1], sys.argv[2]

def one(e):
    p = os.path.join(EEE, "repo", e["object_path"])
    try:
        raw = open(p, "rb").read()
    except OSError as ex:
        return ("missing", e["object_uuid"], str(ex)), []
    if hashlib.sha256(raw).hexdigest() != e["sha256"] or len(raw) != e["size_bytes"]:
        return ("sha_mismatch", e["object_uuid"], ""), []
    d = json.loads(raw)
    sm, mi = d.get("source_metadata", {}) or {}, d.get("model_info", {}) or {}
    rows = []
    for i, r in enumerate(d.get("evaluation_results", []) or []):
        mc, sd, sdata = r.get("metric_config", {}) or {}, r.get("score_details", {}) or {}, r.get("source_data", {}) or {}
        if not isinstance(sdata, dict): sdata = {}
        mad = mc.get("additional_details") or {}
        rows.append(dict(
            collection=e["benchmark"], object_uuid=e["object_uuid"], object_path=e["object_path"], legacy_path=e["legacy_path"], res_idx=i,
            model_id=mi.get("id"), model_name=mi.get("name"), developer=mi.get("developer"),
            model_extra=json.dumps(mi.get("additional_details") or {}, sort_keys=True)[:600],
            source_name=sm.get("source_name"), source_org=sm.get("source_organization_name"),
            source_type=sm.get("source_type"), evaluator_relationship=sm.get("evaluator_relationship"),
            source_extra=json.dumps(sm.get("additional_details") or {}, sort_keys=True)[:400],
            evaluation_name=r.get("evaluation_name"), dataset_name=sdata.get("dataset_name"),
            source_data_extra=json.dumps({k: v for k, v in sdata.items() if k != "dataset_name"}, sort_keys=True)[:400],
            metric_id=mc.get("metric_id"), metric_name=mc.get("metric_name"), metric_unit=mc.get("metric_unit"),
            metric_desc=(mc.get("evaluation_description") or "")[:300],
            metric_extra=json.dumps(mad, sort_keys=True)[:400],
            min_score=mc.get("min_score"), max_score=mc.get("max_score"), lower_is_better=mc.get("lower_is_better"),
            score=sd.get("score"), score_extra=json.dumps(sd.get("details") or {}, sort_keys=True)[:400],
            gen_cfg=json.dumps(r.get("generation_config") or {}, sort_keys=True)[:400],
            eval_ts=str(r.get("evaluation_timestamp") or d.get("evaluation_timestamp") or ""),
            result_id=r.get("evaluation_result_id")))
    return ("ok", e["object_uuid"], ""), rows

if __name__ == "__main__":
    E = [json.loads(l) for l in open(os.path.join(EEE, "entries.jsonl"))]
    stat, rows = [], []
    with Pool(48) as p:
        for s, r in p.imap_unordered(one, E, chunksize=500):
            stat.append(s); rows.extend(r)
    st = pd.DataFrame(stat, columns=["status", "object_uuid", "msg"])
    print(st.status.value_counts().to_dict())
    st[st.status != "ok"].to_csv(os.path.join(OUT, "download_failures.csv"), index=False)
    df = pd.DataFrame(rows)
    for c in ("score", "min_score", "max_score"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values(["collection", "object_uuid", "res_idx"]).reset_index(drop=True)
    df.to_parquet(os.path.join(OUT, "flat.parquet"))
    json.dump(dict(objects=len(E), status=st.status.value_counts().to_dict(), rows=len(df)), open(os.path.join(OUT, "flatten.json"), "w"))
    print(len(df))
