"""Shared helpers for the EEE crosswalk (M9 on the latest EEE manifest)."""
import io, re, json, zipfile
import pandas as pd, numpy as np
ZIP = "ext/epoch_zip/benchmark_data.zip"
XW = "runs/EEE/crosswalk"
TOOLS = "../tools"

def zread(n):
    with zipfile.ZipFile(ZIP) as z:
        return pd.read_csv(io.BytesIO(z.read(n)))

def norm_text(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def norm_model(s):
    s = str(s).strip().lower()
    s = s.split("/")[-1]
    s = re.sub(r"[ _.]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    s = re.sub(r"^claude-(\d)(\d)-", r"claude-\1-\2-", s)          # claude-35-sonnet -> claude-3-5-sonnet
    m = re.match(r"^claude-(\d+(?:-\d)?)-(opus|sonnet|haiku|fable)(.*)$", s)  # claude-4-5-sonnet -> claude-sonnet-4-5
    if m and not re.match(r"^claude-3", s):
        s = f"claude-{m.group(2)}-{m.group(1)}{m.group(3)}"
    return s

SETTING = r"(max|xhigh|high|medium|low|minimal|none|unknown|\d+k)"
DATE_PATS = [r"-20\d{2}-\d{2}-\d{2}$", r"-20\d{6}$", r"-\d{4}$", r"-(preview|exp)-\d{2}-\d{2}$", r"-00\d$", r"-(preview|exp|latest)$"]
EFFORT_TOK = {"thinking", "reasoning", "non-reasoning", "nonreasoning", "high", "medium", "low", "xhigh", "max", "minimal", "none",
              "adaptive", "provider", "adapter", "default", "fallback", "effort", "extended", "no", "with", "non",
              "hf", "turbo", "together", "fp8", "openrouter", "bedrock"}

def strip_date(k):
    for p in DATE_PATS:
        k2 = re.sub(p, "", k)
        if k2 != k:
            return k2
    return k

def date_of(k):
    """Date information carried by a key suffix: ('full', Timestamp) | ('four', 'dddd') | None."""
    m = re.search(r"-(20\d{2})-(\d{2})-(\d{2})$", k)
    if m: return ("full", pd.Timestamp(f"{m.group(1)}-{m.group(2)}-{m.group(3)}"))
    m = re.search(r"-(20\d{2})(\d{2})(\d{2})$", k)
    if m:
        try: return ("full", pd.Timestamp(f"{m.group(1)}-{m.group(2)}-{m.group(3)}"))
        except Exception: return None
    m = re.search(r"-(\d{4})$", k)
    if m: return ("four", m.group(1))
    return None

def date_ok(info, dates, tol=45):
    """Is the date in an EEE id consistent with one of the Epoch group's version dates (within tol days)?"""
    if info is None: return True
    dates = [d for d in dates if pd.notna(d)]
    if not dates: return False
    if info[0] == "full":
        return any(abs((d - info[1]).days) <= tol for d in dates)
    a, b = int(info[1][:2]), int(info[1][2:])
    for d in dates:
        if 1 <= b <= 12 and 20 <= a <= 30:                      # YYMM
            if abs((d - pd.Timestamp(year=2000 + a, month=b, day=15)).days) <= tol: return True
        if 1 <= a <= 12 and 1 <= b <= 31:                       # MMDD in the version's year
            try:
                if abs((d - pd.Timestamp(year=d.year, month=a, day=b)).days) <= tol: return True
            except Exception: pass
    return False

def strip_effort(k):
    t = k.split("-")
    while len(t) > 1 and (t[-1] in EFFORT_TOK or re.fullmatch(r"\d+k", t[-1])):
        t = t[:-1]
    return "-".join(t)

PAREN_OK = re.compile(r"^(?:\s|,|/|'|non-?reasoning|reasoning|thinking|no thinking|unknown thinking|max effort|high effort|medium effort|low effort|xhigh|high|medium|low|minimal|none|max|default|adaptive|effort|"
                      r"\d+-shot|cot|\d+k|1m|ga|preview|with fallback|fallback|anthropic system card|"
                      r"(?:jan|feb|mar|apr|may|june?|july?|aug|sept?|oct|nov|dec)[a-z]*\.? ?'? ?\d{2,4}|\d{4}-\d{2}-\d{2})+$", re.I)

def noparen(s):
    """Drop parentheticals only when they hold settings (effort, shots, dates); a parenthetical naming a
    fine-tune, scaffold or method marks a different system and is kept, so the name does not match."""
    s = str(s)
    for inner in re.findall(r"\(([^)]*)\)", s):
        if not PAREN_OK.match(inner):
            return s
    return re.sub(r"\([^)]*\)", "", s).strip()

# hand-resolved collisions: the undated name is itself the name of one specific release
RESOLVED_KEYS = {"qwq-32b": "QwQ-32B-Preview is a separately named release", "deepseek-v3-2": "V3.2-Exp is a separately named release",
                 "phi-4": "Phi-4 Reasoning is a separate model", "kimi-k2-instruct": "the September build is named Kimi-K2-Instruct-0905"}
COLLIDE = {}

def epoch_keys():
    """key -> set(groups), at exact level and at date-less level, over ALL Epoch model versions."""
    mm = zread("model_metadata.csv").dropna(subset=["model_version", "model_group"])
    exact, loose = {}, {}
    global GROUP_DATES
    GROUP_DATES = pd.to_datetime(mm["date"], errors="coerce").groupby(mm.model_group).agg(list).to_dict()
    def add(d, k, g):
        if k: d.setdefault(k, set()).add(g)
    for v, g, dn in zip(mm.model_version, mm.model_group, mm.display_name):
        raw = str(v)
        base = re.sub(r"_" + SETTING + r"$", "", raw, flags=re.I)
        k0, k1 = norm_model(raw), norm_model(base)
        add(exact, k0, g); add(exact, k1, g); add(exact, norm_model(g), g)
        if isinstance(dn, str):
            add(exact, norm_model(dn), g); add(loose, strip_effort(norm_model(noparen(dn))), g)
        add(loose, strip_date(k1), g); add(loose, strip_date(strip_effort(k1)), g); add(loose, norm_model(noparen(g)), g)
    # Base-name collisions (M9 step 4): a key that names one group exactly but, once dates are dropped, also fits
    # another dated group. An EEE id that lacks the date is ambiguous unless resolved by hand below.
    global COLLIDE
    COLLIDE = {k: sorted(gs | loose.get(k, set())) for k, gs in exact.items() if len(gs) == 1 and len(gs | loose.get(k, set())) > 1 and k not in RESOLVED_KEYS}
    return exact, loose, mm

def eee_keys(mid, name):
    ks = []
    for x in (mid, name):
        if not isinstance(x, str) or not x: continue
        e0 = norm_model(x); e1 = strip_effort(e0)
        if e1.startswith("meta-llama-"): e1 = e1[5:]
        e2 = strip_date(e1); e3 = strip_effort(norm_model(noparen(x)))
        ks.append((e0, e1, e2, e3))
    return ks

def auto_map(mid, name, exact, loose):
    """returns (status, groups, how)"""
    ks = eee_keys(mid, name)
    g = set()
    for e0, e1, e2, e3 in ks:      # the id is tried first; a unique exact id match wins over the display name
        gi = set()
        for k in (e0, e1):
            gi |= exact.get(k, set())
        for k in (e0, e1):
            if k in COLLIDE and exact.get(k): return "ambiguous", COLLIDE[k], "undated-collision"
        if len(gi) == 1 and not g: return "mapped", sorted(gi), "exact"
        g |= gi
    if len(g) == 1: return "mapped", sorted(g), "exact"
    if len(g) > 1: return "ambiguous", sorted(g), "exact-multi"
    for e0, e1, e2, e3 in ks:
        for k in (e0, e1, e2, e3):
            cand = loose.get(k, set()) | exact.get(k, set())
            if k == e2 and e2 != e1:      # a date was stripped from the EEE id: it must fit the group's dates
                cand = {c for c in cand if date_ok(date_of(e1), GROUP_DATES.get(c, []))}
            g |= cand
    if len(g) == 1: return "mapped", sorted(g), "dateless-unique"
    if len(g) > 1: return "ambiguous", sorted(g), "dateless-multi"
    return "unmapped", [], ""
