# Run as: cat taxc_rules.py taxc_build.py | docker exec ... python -I -
# Places ECI's 57 benchmarks and EEE's benchmarks in the Combined taxonomy; writes runs/TAX/combined_*.
import re, collections
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); pd.set_option('display.max_colwidth', 80)
OUT = 'runs/TAX/'
B = 'runs/EEE/'

def full(code): return D[code] if code else ''

# ======================= 1. ECI =======================
a = pd.read_csv(B + 'input/eee_fit_input_annotated.csv')
assert a.benchmark.nunique() == 57 and set(a.benchmark) == set(ECI), set(a.benchmark) ^ set(ECI)
ep = pd.read_csv(OUT + 'epoch_domain_map.csv')[['benchmark', 'tags']].rename(columns={'tags': 'epoch_tags'})
cells = a.groupby('benchmark').agg(cells=('Model', 'size'), models=('Model', 'nunique')).reset_index()
rows = []
for b, (d1, s1, d2, s2, x1, x2, mod, it, lang, conf, why) in ECI.items():
    rows.append(dict(benchmark=b, primary_domain=full(d1), sub_theme=s1, secondary_domain=full(d2), secondary_sub_theme=s2,
                     axis2_property=A[x1], axis2_secondary=A[x2] if x2 else '', modality=mod,
                     interaction_style=I.get(it, it), language=lang, confidence=conf, rationale=why))
em = pd.DataFrame(rows).merge(cells, on='benchmark').merge(ep, on='benchmark', how='left')
em['coded_by'] = 'our coding (artifact gives no per-benchmark assignments)'
em = em.sort_values(['primary_domain', 'sub_theme', 'cells'], ascending=[True, True, False])
cols = ['benchmark', 'cells', 'models', 'primary_domain', 'sub_theme', 'secondary_domain', 'secondary_sub_theme', 'axis2_property',
        'axis2_secondary', 'modality', 'interaction_style', 'language', 'epoch_tags', 'confidence', 'coded_by', 'rationale']
em[cols].to_csv(OUT + 'combined_eci_map.csv', index=False)

a2 = a.merge(em[['benchmark', 'primary_domain', 'sub_theme', 'secondary_domain', 'secondary_sub_theme', 'axis2_property',
                 'axis2_secondary', 'modality', 'interaction_style', 'language']], on='benchmark')
nmod = a.Model.nunique(); ncell = len(a)
# by domain: primary, and primary-or-secondary
long = pd.concat([a2.assign(domain=a2.primary_domain, sub=a2.sub_theme, role='primary'),
                  a2[a2.secondary_domain != ''].assign(domain=lambda x: x.secondary_domain, sub=lambda x: x.secondary_sub_theme, role='secondary')])
prim = a2.groupby('primary_domain').agg(eci_benchmarks=('benchmark', 'nunique'), eci_cells=('Model', 'size'), eci_models=('Model', 'nunique'))
anyr = long.drop_duplicates(['Model', 'benchmark', 'domain']).groupby('domain').agg(eci_benchmarks_incl_secondary=('benchmark', 'nunique'),
                                                                                  eci_cells_incl_secondary=('Model', 'size'))
dom = pd.DataFrame(index=DOMAIN_ORDER).join(prim).join(anyr).fillna(0).astype(int)
dom['eci_cell_share'] = (dom.eci_cells / ncell).round(3)
dom['eci_benchmark_list'] = [', '.join(em[em.primary_domain == d].benchmark) for d in dom.index]
dom.index.name = 'domain'
dom.to_csv(OUT + 'combined_eci_by_domain.csv')

# by sub-theme, listing every Combined sub-theme (empty ones included)
st = []
for code, subs in SUBTHEMES.items():
    for s, n in subs:
        p = long[(long.domain == D[code]) & (long['sub'] == s)]
        pp = p[p.role == 'primary']
        st.append(dict(domain=D[code], sub_theme=s, doc_benchmark_count=n, eci_benchmarks_primary=pp.benchmark.nunique(),
                       eci_cells_primary=len(pp), eci_benchmarks_incl_secondary=p.benchmark.nunique(),
                       eci_cells_incl_secondary=len(p.drop_duplicates(['Model', 'benchmark'])),
                       eci_benchmarks=', '.join(sorted(set(p.benchmark)))))
# ECI rows with no sub-theme (LMCA)
p = long[(long['sub'] == '') & (long.role == 'primary')]
st.append(dict(domain=D['GEN'], sub_theme='(no sub-theme)', doc_benchmark_count=None, eci_benchmarks_primary=p.benchmark.nunique(),
               eci_cells_primary=len(p), eci_benchmarks_incl_secondary=p.benchmark.nunique(), eci_cells_incl_secondary=len(p),
               eci_benchmarks=', '.join(sorted(set(p.benchmark)))))
st = pd.DataFrame(st)
st.to_csv(OUT + 'combined_eci_by_subtheme.csv', index=False)

fac = []
for col in ['axis2_property', 'modality', 'interaction_style', 'language']:
    g = a2.groupby(col).agg(eci_benchmarks=('benchmark', 'nunique'), eci_cells=('Model', 'size'))
    for k, r in g.iterrows(): fac.append(dict(facet=col, value=k, basis='primary', **r))
for k, r in pd.concat([a2.assign(v=a2.axis2_property), a2[a2.axis2_secondary != ''].assign(v=lambda x: x.axis2_secondary)]) \
        .groupby('v').agg(eci_benchmarks=('benchmark', 'nunique'), eci_cells=('Model', 'size')).iterrows():
    fac.append(dict(facet='axis2_property', value=k, basis='primary or secondary', **r))
for x in AXIS2:
    if x not in set(a2.axis2_property) | set(a2.axis2_secondary):
        fac.append(dict(facet='axis2_property', value=x, basis='primary or secondary', eci_benchmarks=0, eci_cells=0))
fac = pd.DataFrame(fac); fac.to_csv(OUT + 'combined_eci_by_facet.csv', index=False)

ncnt = a.groupby('Model').size()
print('ECI: cells', ncell, 'models', nmod, 'sparse models (<=6 cells)', int((ncnt <= 6).sum()))
print(dom.drop(columns='eci_benchmark_list').to_string())
print(st[st.eci_benchmarks_incl_secondary > 0][['domain', 'sub_theme', 'doc_benchmark_count', 'eci_benchmarks_primary', 'eci_cells_primary', 'eci_benchmarks']].to_string())
print('EMPTY sub-themes:', (st.eci_benchmarks_incl_secondary == 0).sum(), 'of', len(st) - 1)
print(fac.to_string())

# ======================= 2. EEE =======================
f = pd.read_parquet(B + 'crosswalk/flat.parquet', columns=['collection', 'model_id', 'model_name', 'source_name', 'source_org',
                                                           'dataset_name', 'evaluation_name', 'metric_id'])
f = f.fillna({'dataset_name': '', 'metric_id': '', 'evaluation_name': ''})
COSTLAT = re.compile(r'price|tokens_per_second|time_to_first|latency|cost')
def key(c, d, m):
    d = d.strip().lower()
    if c == 'artificial-analysis-llms':
        k = m.replace('artificial_analysis.', '')
        return '__costlat' if COSTLAT.search(k) else 'aa:' + k
    if c == 'arc-agi': return 'arcagi'
    if c == 'bfcl': return 'bfcl'
    if ' - ' in d: d = d.split(' - ')[0]
    if '/' in d: d = d.split('/')[-1]
    d = re.sub(r'\(.*?\)', '', d); d = re.sub(r'[^a-z0-9]', '', d)
    return d or '__blank'
u = f[['collection', 'dataset_name', 'metric_id']].drop_duplicates()
u['key'] = [key(*t) for t in u.itertuples(index=False)]
f = f.merge(u, on=['collection', 'dataset_name', 'metric_id'], how='left')
# cost/latency metrics are not capability evaluations
nall = len(f); ncost = int((f.key == '__costlat').sum())
f = f[f.key != '__costlat']
# ECI model mapping
mm = pd.read_csv(B + 'crosswalk/model_map.csv')
m = mm[mm.cls == 'mapped'][['model_id', 'model_name', 'model_group']].drop_duplicates(['model_id', 'model_name'])
f = f.merge(m, on=['model_id', 'model_name'], how='left')
eci_models = set(pd.read_csv(B + 'eci_compare.csv').model)
assert set(m.model_group) <= eci_models
# same-benchmark-as-ECI flag from the crosswalk benchmark map
bm = pd.read_csv(B + 'crosswalk/benchmark_map.csv', keep_default_na=False)[['collection', 'evaluation_name', 'dataset_name', 'metric_id', 'eci_benchmark', 'cls']]
bm = bm.drop_duplicates(['collection', 'evaluation_name', 'dataset_name', 'metric_id'])
f = f.merge(bm, on=['collection', 'evaluation_name', 'dataset_name', 'metric_id'], how='left')
f['eci_same'] = f.cls.isin(['include', 'metric-mismatch', 'split-mismatch'])
f['eci_variant'] = f.cls.eq('version-mismatch')
print('EEE rows', nall, 'cost/latency excluded', ncost, 'capability rows', len(f), 'ECI-model rows', int(f.model_group.notna().sum()),
      'same-as-ECI rows', int(f.eci_same.sum()), 'variant rows', int(f.eci_variant.sum()))

# key profile and code set: top 300 keys by rows plus every key scoring >= 10 ECI models
kp = f.groupby('key').agg(rows=('model_id', 'size'), models=('model_id', 'nunique'), eci_models=('model_group', 'nunique'),
                          sources=('source_org', 'nunique'), collections=('collection', 'nunique'),
                          eci_same_rows=('eci_same', 'sum'), eci_variant_rows=('eci_variant', 'sum'),
                          example_dataset=('dataset_name', 'first')).sort_values('rows', ascending=False)
kp['in_codeset'] = False
kp.loc[kp.index[:300], 'in_codeset'] = True
kp.loc[kp.eci_models >= 10, 'in_codeset'] = True
CR = [(re.compile(p), fam, d, s, x, mo, it, la) for p, fam, d, s, x, mo, it, la in R]
FR = [(re.compile(p), n) for p, n in FAM]
def code(k):
    for rx, fam, d, s, x, mo, it, la in CR:
        if rx.fullmatch(k):
            fm = next((n for r2, n in FR if r2.fullmatch(k)), None) or fam or k
            return fm, D[d], s, A[x], mo, I[it], la
    return (k, '', '', '', '', '', '')
cc = pd.DataFrame([code(k) for k in kp.index], index=kp.index,
                  columns=['family', 'domain', 'sub_theme', 'axis2_property', 'modality', 'interaction_style', 'language'])
kp = kp.join(cc)
kp['coded'] = kp.domain != ''
kp['eci_relation'] = np.where(kp.eci_same_rows > 0, 'same benchmark as an ECI benchmark',
                     np.where(kp.eci_variant_rows > 0, 'variant of an ECI benchmark', 'not in ECI'))
unc = kp[kp.in_codeset & ~kp.coded]
print('UNCODED in codeset:', len(unc)); print(unc[['rows', 'eci_models', 'example_dataset']].to_string())
capr = kp.rows.sum()
print('codeset keys', int(kp.in_codeset.sum()), 'codeset row share', round(kp[kp.in_codeset].rows.sum() / capr, 4),
      'coded keys (any)', int(kp.coded.sum()), 'coded row share', round(kp[kp.coded].rows.sum() / capr, 4))
kp.index.name = 'key'
kp_out = kp.reset_index()[['key', 'family', 'domain', 'sub_theme', 'axis2_property', 'modality', 'interaction_style', 'language',
                           'eci_relation', 'rows', 'models', 'eci_models', 'sources', 'collections', 'in_codeset', 'coded', 'example_dataset']]
kp_out['example_dataset'] = kp_out.example_dataset.str.replace('\u2014', '-', regex=False).str.replace('\u2013', '-', regex=False)
kp_out.to_csv(OUT + 'combined_eee_benchmark_map.csv', index=False)

f = f.merge(kp[['family', 'domain', 'sub_theme', 'axis2_property', 'language', 'coded']], left_on='key', right_index=True, how='left')
f.loc[~f.coded, 'domain'] = '(uncoded tail)'
# coverage of ECI-model rows
er = f[f.model_group.notna()]
print('coded share of ECI-model rows', round(er.coded.mean(), 4), 'ECI models in EEE', er.model_group.nunique())

def eee_tab(df, by):
    g = df.groupby(by)
    t = g.agg(eee_benchmarks=('family', 'nunique'), eee_rows=('model_id', 'size'), eee_models=('model_id', 'nunique'),
              eee_sources=('source_org', 'nunique'), eee_collections=('collection', 'nunique'),
              eci_models_any=('model_group', 'nunique'))
    new = df[~df.eci_same & ~df.eci_variant]
    gn = new.groupby(by)
    t['eee_benchmarks_not_in_eci'] = gn.family.nunique()
    t['eee_rows_not_in_eci'] = gn.size()
    t['eci_models_on_non_eci_benchmarks'] = gn.model_group.nunique()
    # density: ECI models scored on >= 3 distinct non-ECI benchmark families in the group
    mf = new[new.model_group.notna()].groupby(by + ['model_group']).family.nunique().reset_index()
    t['eci_models_ge3_non_eci_benchmarks'] = mf[mf.family >= 3].groupby(by).size()
    # benchmarks with >= 20 ECI models
    fm = new[new.model_group.notna()].groupby(by + ['family']).model_group.nunique().reset_index()
    t['non_eci_benchmarks_ge20_eci_models'] = fm[fm.model_group >= 20].groupby(by).size()
    return t.fillna(0)

ed = eee_tab(f, ['domain'])
ed = ed.reindex(DOMAIN_ORDER + ['(uncoded tail)']).fillna(0).astype(int)
ed.index.name = 'domain'
ed.to_csv(OUT + 'combined_eee_by_domain.csv')
print(ed.to_string())

es = eee_tab(f[f.coded], ['domain', 'sub_theme']).astype(int).reset_index()
es.to_csv(OUT + 'combined_eee_by_subtheme.csv', index=False)

# candidate benchmarks for extending ECI: not in ECI, >= 20 ECI models
new = f[~f.eci_same & ~f.eci_variant & f.coded]
cand = new.groupby(['domain', 'sub_theme', 'family']).agg(eci_models=('model_group', 'nunique'), rows=('model_id', 'size'),
        sources=('source_org', lambda s: '|'.join(sorted(set(s)))), collections=('collection', 'nunique')).reset_index()
cand = cand[cand.eci_models >= 20].sort_values(['domain', 'eci_models'], ascending=[True, False])
cand.to_csv(OUT + 'combined_eee_candidates.csv', index=False)

# ======================= 3. Gap tables =======================
gap = dom[['eci_benchmarks', 'eci_cells', 'eci_models', 'eci_benchmarks_incl_secondary']].join(
    ed[['eee_benchmarks', 'eee_rows', 'eee_models', 'eee_sources', 'eci_models_any', 'eee_benchmarks_not_in_eci',
        'eci_models_on_non_eci_benchmarks', 'eci_models_ge3_non_eci_benchmarks', 'non_eci_benchmarks_ge20_eci_models']], how='outer')
gap = gap.reindex(DOMAIN_ORDER + ['(uncoded tail)']).fillna(0).astype(int)
def label(r):
    if r.Index == '(uncoded tail)': return 'not coded'
    if r.eci_benchmarks == 0 and r.eci_models_ge3_non_eci_benchmarks >= 50: return 'gap: dense EEE data on ECI models, no ECI benchmark'
    if r.eci_benchmarks == 0 and r.eee_benchmarks > 0: return 'gap: EEE data, no ECI benchmark'
    if r.eci_benchmarks > 0 and r.non_eci_benchmarks_ge20_eci_models >= 3: return 'ECI covered; EEE adds dense non-ECI benchmarks'
    if r.eci_benchmarks > 0: return 'ECI covered'
    return ''
gap['reading'] = [label(r) for r in gap.itertuples()]
gap.index.name = 'domain'
gap.to_csv(OUT + 'combined_gap_by_domain.csv')
print(gap.to_string())

# Axis 2 and language gaps (ECI primary or secondary property vs EEE property)
ax_e = pd.concat([a2.assign(v=a2.axis2_property), a2[a2.axis2_secondary != ''].assign(v=lambda x: x.axis2_secondary)]) \
    .drop_duplicates(['Model', 'benchmark', 'v']).groupby('v').agg(eci_benchmarks=('benchmark', 'nunique'), eci_cells=('Model', 'size'))
ax_x = eee_tab(f[f.coded], ['axis2_property'])
gx = pd.DataFrame(index=AXIS2).join(ax_e).join(ax_x[['eee_benchmarks', 'eee_rows', 'eci_models_any', 'eee_benchmarks_not_in_eci',
                                                    'eci_models_ge3_non_eci_benchmarks', 'non_eci_benchmarks_ge20_eci_models']]).fillna(0).astype(int)
gx.index.name = 'axis2_property'; gx.to_csv(OUT + 'combined_gap_by_axis2.csv'); print(gx.to_string())
lg_e = a2.groupby('language').agg(eci_benchmarks=('benchmark', 'nunique'), eci_cells=('Model', 'size'))
lg_x = eee_tab(f[f.coded], ['language'])
gl = lg_e.join(lg_x[['eee_benchmarks', 'eee_rows', 'eci_models_any', 'eci_models_ge3_non_eci_benchmarks', 'non_eci_benchmarks_ge20_eci_models']], how='outer').fillna(0).astype(int)
gl.index.name = 'language'; gl.to_csv(OUT + 'combined_gap_by_language.csv'); print(gl.to_string())

# ECI benchmarks with no EEE rows of the same benchmark
same = f[f.eci_same].groupby('eci_benchmark').model_group.nunique()
dep = em[['benchmark', 'primary_domain', 'cells']].copy()
dep['eee_same_benchmark_eci_models'] = [int(sum(v for k, v in same.items() if b in str(k).split(';'))) for b in dep.benchmark]
dep.to_csv(OUT + 'combined_eci_eee_dependence.csv', index=False)
print(dep.groupby('primary_domain').apply(lambda x: pd.Series({'benchmarks': len(x), 'no_eee_same': int((x.eee_same_benchmark_eci_models == 0).sum()),
      'cells_no_eee_same': int(x[x.eee_same_benchmark_eci_models == 0].cells.sum())})).to_string())
print(cand.groupby('domain').head(6).to_string())

# ======================= 4. External taxonomies vs ECI (domain level) =======================
# Tags from the Combined doc's domain and sub-theme source tags ([V] Vals, [E] Epoch, [A] AA, [L] LLM Stats)
EXT = {
 'Software & Computing': ('yes','yes','yes','yes'), 'Mathematics': ('yes','yes','no','yes'), 'Natural Sciences': ('yes','yes','yes','no'),
 'Health & Medicine': ('yes','no','yes','yes'), 'Law, Government & Policy': ('yes','no','sub-theme only (legal practice)','yes'),
 'Business, Finance & Professional Work': ('yes','sub-theme only (professional work)','yes','yes'),
 'Computers, Web & Apps': ('sub-theme only (web search)','yes','no','yes'),
 'Everyday Life & Physical World': ('sub-theme only (robotics)','sub-theme only (physical & social)','no','no'),
 'Puzzles & Games': ('yes','yes','no','no'), 'Languages, Cultures & Humanities': ('no','no','no','no'),
 'Media, Arts & Online Content': ('no','sub-theme only (creative writing)','no','yes'), 'General / multi-subject': ('no','no','yes','no'),
}
ext = pd.DataFrame(EXT, index=['vals_ai', 'epoch', 'artificial_analysis', 'llm_stats']).T
ext.index.name = 'domain'
ext = ext.join(dom[['eci_benchmarks', 'eci_cells']]).join(ed[['eee_benchmarks', 'eci_models_on_non_eci_benchmarks']])
extra = pd.DataFrame([
  dict(domain='Axis 2: Safety / harms', vals_ai='sub-area (SAFE-Teen mental health)', epoch='no', artificial_analysis='no', llm_stats='no'),
  dict(domain='Axis 2: Truthfulness & hallucination', vals_ai='no', epoch='no (SimpleQA Verified under World knowledge)', artificial_analysis='yes (AA-Omniscience)', llm_stats='yes'),
  dict(domain='Axis 2: Long context', vals_ai='no', epoch='yes', artificial_analysis='yes', llm_stats='yes'),
  dict(domain='Axis 2: Instruction following', vals_ai='no', epoch='no', artificial_analysis='yes (IFBench)', llm_stats='no'),
  dict(domain='Axis 5: Multilingual', vals_ai='archived (MGSM)', epoch='no', artificial_analysis='yes (Multilingual Index)', llm_stats='no'),
]).set_index('domain')
ax_e2 = ax_e.reindex(AXIS2).fillna(0).astype(int)
extra['eci_benchmarks'] = [ax_e2.loc[A['SAFE']].eci_benchmarks, ax_e2.loc[A['TRUTH']].eci_benchmarks, ax_e2.loc[A['LC']].eci_benchmarks,
                           ax_e2.loc[A['IF']].eci_benchmarks, 0]
extra['eci_cells'] = [ax_e2.loc[A['SAFE']].eci_cells, ax_e2.loc[A['TRUTH']].eci_cells, ax_e2.loc[A['LC']].eci_cells, ax_e2.loc[A['IF']].eci_cells, 0]
extra['eee_benchmarks'] = [gx.loc[A['SAFE']].eee_benchmarks, gx.loc[A['TRUTH']].eee_benchmarks, gx.loc[A['LC']].eee_benchmarks,
                           gx.loc[A['IF']].eee_benchmarks, gl.loc['multilingual'].eee_benchmarks]
extra['eci_models_on_non_eci_benchmarks'] = [ax_x.loc[A['SAFE']].eci_models_on_non_eci_benchmarks, ax_x.loc[A['TRUTH']].eci_models_on_non_eci_benchmarks,
    ax_x.loc[A['LC']].eci_models_on_non_eci_benchmarks, ax_x.loc[A['IF']].eci_models_on_non_eci_benchmarks, lg_x.loc['multilingual'].eci_models_on_non_eci_benchmarks]
ext = pd.concat([ext, extra])
for c in ['eci_benchmarks', 'eci_cells', 'eee_benchmarks', 'eci_models_on_non_eci_benchmarks']: ext[c] = ext[c].fillna(0).astype(int)
ext.to_csv(OUT + 'combined_external_coverage.csv')
print(ext.to_string())
# multilingual and safety detail
print(f[f.coded & (f.language == 'multilingual')].groupby('family').model_group.nunique().sort_values(ascending=False).head(12).to_string())
print(f[f.coded & (f.axis2_property == A['SAFE'])].groupby('family').model_group.nunique().sort_values(ascending=False).head(12).to_string())

# ======================= 5. Rankability per domain under Epoch's inclusion threshold (>= 4 benchmarks per model) =======================
rk = pd.DataFrame(index=DOMAIN_ORDER)
pb = a2.groupby(['primary_domain', 'Model']).benchmark.nunique().reset_index()
rk['eci_models_ge4_eci_benchmarks'] = pb[pb.benchmark >= 4].groupby('primary_domain').size()
rk['eci_models_ge7_eci_benchmarks'] = pb[pb.benchmark >= 7].groupby('primary_domain').size()
cod = f[f.coded & f.model_group.notna()]
xb = cod.groupby(['domain', 'model_group']).family.nunique().reset_index()
rk['eci_models_ge4_eee_benchmarks'] = xb[xb.family >= 4].groupby('domain').size()
nb = cod[~cod.eci_same & ~cod.eci_variant].groupby(['domain', 'model_group']).family.nunique().reset_index()
rk['eci_models_ge4_non_eci_eee_benchmarks'] = nb[nb.family >= 4].groupby('domain').size()
# combined: ECI benchmarks plus non-ECI EEE families, per model
comb = pd.concat([a2[['primary_domain', 'Model', 'benchmark']].rename(columns={'primary_domain': 'domain', 'Model': 'model_group', 'benchmark': 'family'}),
                  cod[~cod.eci_same & ~cod.eci_variant][['domain', 'model_group', 'family']]]).drop_duplicates()
cb = comb.groupby(['domain', 'model_group']).family.nunique().reset_index()
rk['eci_models_ge4_eci_plus_eee'] = cb[cb.family >= 4].groupby('domain').size()
rk = rk.fillna(0).astype(int); rk.index.name = 'domain'
rk.to_csv(OUT + 'combined_domain_rankability.csv'); print(rk.to_string())
