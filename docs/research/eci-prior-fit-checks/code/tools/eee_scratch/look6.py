import sys, pandas as pd
sys.path.insert(0,'../tools'); from eee_xwalk_lib import *
from eee_bmap_rules import INCLUDE
fi=zread('epoch_capabilities_index/processed_data_for_eci.csv'); mm=zread('model_metadata.csv')
print(mm[mm.model_group.astype(str).str.contains('DeepSeek.V4|Qwen.?3.8 Max|Kimi K2 \(')][['model_version','model_group','date']].drop_duplicates('model_group').to_string())
bs=sorted({r[0] for r in INCLUDE}); bm=zread('benchmark_metadata.csv').set_index('benchmark')
for b in bs:
    if '_external' in str(bm.loc[b,'source_file']):
        vc=fi[fi.benchmark==b].source.value_counts(dropna=False)
        print(b,'|',len(fi[fi.benchmark==b]),'|','; '.join(f"{str(k)[:60]}={v}" for k,v in vc.head(12).items()))
