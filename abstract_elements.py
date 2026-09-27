# How often dissertation and thesis abstracts include the elements APA 7 and JARS ask for, and how long they are.
#   python abstract_elements.py            -> abstract_guide/elements.csv, abstract_guide/lengths.csv
# Uses the same pulls as the methods series (psych_subfields/*.json, series/raw/*.json), abstracts longer than 60 words, 2021-2026.
import csv, json, os, re, statistics

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "abstract_guide"); os.makedirs(OUT, exist_ok=True)
FIELDS = {
    "Psychology": [os.path.join("psych_subfields", f + ".json") for f in ("clinical", "social", "developmental_educational", "experimental_cognitive", "applied")],
    "Education": [os.path.join("series", "raw", "education.json")],
    "Business": [os.path.join("series", "raw", f) for f in ("bus_strategy.json", "bus_accounting_finance.json", "bus_marketing.json", "bus_ob_hrm.json", "bus_info_tech.json")],
    "Social sciences & health": [os.path.join("series", "raw", f) for f in ("soc_sociology.json", "soc_polisci.json", "soc_economics.json", "soc_public_health.json", "soc_nursing_health_prof.json", "soc_communication.json")],
}
UNITS = r"participants|respondents|students|teachers|educators|principals|adults|adolescents|patients|children|individuals|people|nurses|employees|workers|managers|firms|companies|banks|women|men|subjects|parents|mothers|households|schools|universities|couples|veterans|clients|undergraduates|consumers|customers|countries|articles|studies|interviews|cases"
ELEMENTS = {  # APA 7 / JARS abstract element: regex (case-insensitive)
    "Purpose, question, or hypothesis": r"hypothes|research questions?|the (purpose|aim|goal|objective)s? of this|this (study|dissertation|research|thesis|project) (examine|investigate|explore|aim|seek|sought|assess|evaluate|test)",
    "Research design": r"cross-sectional|correlational (design|study|research)|descriptive (design|study|research)|causal[- ]comparative|quasi[- ]experiment|experiment(al)? (design|study)|randomi[sz]ed|longitudinal|survey|questionnaire|qualitative|mixed[- ]methods?|case stud|phenomenolog|grounded theory|ethnograph|meta-analy|systematic review|scoping review|secondary (data|analysis)|action research|panel data|interviews?",
    # A number followed within three words by a unit; not grade ranges ("K-12") or years ("2021 students").
    "Sample size": r"\b[Nn]\s*=\s*\d|(?<![-\w])(?!(?:19|20)\d\d\b)\d[\d,]*\s+(?:[a-zA-Z-]+\s+){0,3}(?:" + UNITS + r")\b",
    "Effect size": r"effect sizes?|cohen'?s\s*d|\bd\s*=\s*-?\.?\d|η2|η²|eta[- ]squared|odds ratios?|\bOR\s*=|hazard ratios?|\bHR\s*=|\bβ\s*=|\bbeta\s*=|\br\s*=\s*-?\.?\d|\bR2\s*=|R²\s*=|\bR-squared",
    "Confidence interval": r"confidence intervals?|\b\d{2}\s*%\s*CI\b|\bCI\s*[=:\[\(]",
    "Statistical significance": r"\bp\s*[<=>≤]\s*0?\.\d|statistically significant|significant(ly)? (positive|negative|differen|effect|relationship|association|correlat|predict|increase|decrease|improve)",
    "Implications or recommendations": r"implication|recommend|practitioners|policy ?makers|future research",
}
COMP = {k: re.compile(v, re.I) for k, v in ELEMENTS.items()}
# "Quantitative" = names at least one analysis or measurement method from the shared dictionary (as in the methods series).
_src = open(os.path.join(HERE, "classify_methods.py"), encoding="utf-8").read()
_ns = {}; exec(_src[_src.index("M = {"):_src.index("\n}\n", _src.index("M = {")) + 3], _ns)
QUANT = re.compile("|".join(f"(?:{v})" for g, v in _ns["M"].values() if g in ("Analysis", "Measurement")), re.I)

rows_e, rows_l, rows_h = [], [], []
for field, files in FIELDS.items():
    recs, seen = [], set()
    for f in files:
        for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
            if r["id"] in seen or r["year"] > 2026: continue
            words = len(r["abstract"].split())
            if words > 60: seen.add(r["id"]); recs.append((r["abstract"], words))
    n = len(recs); lens = [w for _, w in recs]
    rows_l.append({"field": field, "abstracts": n, "median_words": statistics.median(lens), "p25": statistics.quantiles(lens, n=4)[0], "p75": statistics.quantiles(lens, n=4)[2],
                   "share_over_150": sum(w > 150 for w in lens) / n, "share_over_250": sum(w > 250 for w in lens) / n, "share_over_350": sum(w > 350 for w in lens) / n})
    quant = [(a, w) for a, w in recs if QUANT.search(a)]
    for k, c in COMP.items():
        x = sum(bool(c.search(a)) for a, _ in recs); xq = sum(bool(c.search(a)) for a, _ in quant)
        rows_e.append({"field": field, "element": k, "abstracts": n, "x": x, "share": x / n, "quant_abstracts": len(quant), "x_quant": xq, "share_quant": xq / len(quant)})
    for lo in range(60, 800, 10):  # word-count histogram in 10-word bins; the last bin collects 800+
        rows_h.append({"field": field, "bin_low": lo, "n": sum(lo < w <= lo + 10 for w in lens)})
    rows_h.append({"field": field, "bin_low": 800, "n": sum(w > 800 for w in lens)})
    both = sum(bool(COMP["Sample size"].search(a)) and bool(COMP["Effect size"].search(a)) for a, _ in recs)
    bq = sum(bool(COMP["Sample size"].search(a)) and bool(COMP["Effect size"].search(a)) for a, _ in quant)
    rows_e.append({"field": field, "element": "Sample size and effect size", "abstracts": n, "x": both, "share": both / n, "quant_abstracts": len(quant), "x_quant": bq, "share_quant": bq / len(quant)})

for name, rows in (("elements.csv", rows_e), ("lengths.csv", rows_l), ("length_bins.csv", rows_h)):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows_l: print(f"{r['field']:26} n={r['abstracts']:6} median={r['median_words']:.0f} IQR {r['p25']:.0f}-{r['p75']:.0f}  >150 {r['share_over_150']:.0%}  >250 {r['share_over_250']:.0%}  >350 {r['share_over_350']:.0%}")
for f in FIELDS: print(f, "|", "; ".join(f"{r['element']} {r['share']:.1%}" for r in rows_e if r["field"] == f))
