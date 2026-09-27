# Per-subfield method statistics for the DSH "methods in psychology dissertations" posts.
# Input: psych_subfields/<name>.json (every English OpenAlex dissertation with an abstract, 2021+, per subfield).
# Uses the same method dictionary as classify_methods.py. Output (psych_subfields/):
#   summary.csv   one row per subfield (and "all"): abstracts, share naming a quantitative method, design mix
#   methods.csv   subfield x method: share of all abstracts, share of method-naming abstracts (Wilson CI),
#                 rest-of-psychology share of method-naming abstracts and a two-proportion p for the difference
#   trends.csv    subfield x method: 2021-22 vs 2025-26 counts and shares of all abstracts, two-proportion p
import csv, json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "psych_subfields")
src = open(os.path.join(HERE, "classify_methods.py"), encoding="utf-8").read()
block = src[src.index("M = {"):src.index("\n}\n", src.index("M = {")) + 3]
ns = {}; exec(block, ns); M = ns["M"]
COMP = {k: re.compile(v, re.I) for k, (g, v) in M.items()}
QUANT = [k for k, (g, _) in M.items() if g in ("Analysis", "Measurement")] + ["Experiment / randomized design", "Quasi-experimental / program evaluation"]
DESIGN = ["Qualitative (thematic, IPA, grounded theory, interviews)", "Mixed methods", "Experiment / randomized design", "Systematic review / meta-analysis",
          "Longitudinal / repeated measures", "Survey / questionnaire study"]
SUBFIELDS = {"clinical": "Clinical psychology", "social": "Social psychology", "developmental_educational": "Developmental and educational psychology",
             "experimental_cognitive": "Experimental and cognitive psychology", "applied": "Applied psychology"}

def wilson(x, n, z=1.959964):
    if n == 0: return (float("nan"), float("nan"))
    p = x / n; den = 1 + z * z / n; mid = (p + z * z / (2 * n)) / den; half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (mid - half, mid + half)

def two_prop_p(x1, n1, x2, n2):
    if min(n1, n2) == 0: return float("nan")
    p = (x1 + x2) / (n1 + n2)
    if p in (0, 1): return 1.0
    z = (x2 / n2 - x1 / n1) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

records = {}
for key in SUBFIELDS:
    rows = [r for r in json.load(open(os.path.join(D, key + ".json"), encoding="utf-8")) if len(r["abstract"].split()) > 60 and r["year"] <= 2026]  # drop 15 records with impossible future dates
    for r in rows:
        text = r["title"] + " " + r["abstract"]
        r["flags"] = {k: bool(c.search(text)) for k, c in COMP.items()}
        r["quant"] = any(r["flags"][k] for k in QUANT)
    records[key] = rows
records["all"] = [r for k in SUBFIELDS for r in records[k]]
labels = dict(SUBFIELDS, all="Psychology overall")

summary, methods, trends = [], [], []
for key, rows in records.items():
    n = len(rows); q = [r for r in rows if r["quant"]]
    rest_q = [r for k2 in SUBFIELDS if k2 != key for r in records[k2] if r["quant"]] if key != "all" else []
    s = {"subfield": key, "label": labels[key], "abstracts": n, "quant_n": len(q), "quant_share": len(q) / n}
    for dsg in DESIGN: s[dsg] = sum(r["flags"][dsg] for r in rows) / n
    summary.append(s)
    early = [r for r in rows if r["year"] in (2021, 2022)]; late = [r for r in rows if r["year"] in (2025, 2026)]
    for m, (g, _) in M.items():
        if g not in ("Analysis", "Measurement"): continue
        xq = sum(r["flags"][m] for r in q); lo, hi = wilson(xq, len(q))
        row = {"subfield": key, "method": m, "group": g, "share_all": sum(r["flags"][m] for r in rows) / n, "n_quant": len(q), "x_quant": xq,
               "share_quant": xq / len(q), "ci_low": lo, "ci_high": hi}
        if rest_q:
            xr = sum(r["flags"][m] for r in rest_q)
            row.update(rest_share_quant=xr / len(rest_q), p_vs_rest=two_prop_p(xr, len(rest_q), xq, len(q)))
        methods.append(row)
        xe = sum(r["flags"][m] for r in early); xl = sum(r["flags"][m] for r in late)
        trends.append({"subfield": key, "method": m, "early_n": len(early), "early_x": xe, "late_n": len(late), "late_x": xl,
                       "early_quant_n": sum(r["quant"] for r in early), "late_quant_n": sum(r["quant"] for r in late),
                       "early_share": xe / max(1, len(early)), "late_share": xl / max(1, len(late)), "p": two_prop_p(xe, len(early), xl, len(late))})

def write(name, rows):
    with open(os.path.join(D, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + [k for k in ("rest_share_quant", "p_vs_rest") if k not in rows[0]])
        w.writeheader(); w.writerows(rows)
write("summary.csv", summary); write("methods.csv", methods); write("trends.csv", trends)

for s in summary:
    print(f"{s['label']:44} n={s['abstracts']:5}  quant={s['quant_share']:.0%} (n={s['quant_n']})  qual={s[DESIGN[0]]:.0%}  exp={s[DESIGN[2]]:.0%}  review={s[DESIGN[3]]:.0%}")
