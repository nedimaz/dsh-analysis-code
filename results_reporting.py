# For the DSH Results-chapter guide: among abstracts that name a given test, how often do they also report
# an exact or bounded p value, an effect size, or a confidence interval?
#   python results_reporting.py   -> abstract_guide/results_reporting.csv
# Same data and filters as abstract_elements.py; patterns for p, effect size, and CI are shared with it.
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "abstract_elements.py"), encoding="utf-8").read()
ns = {"__file__": os.path.join(HERE, "abstract_elements.py")}
exec(src[:src.index("rows_e, rows_l")], ns)
FIELDS, ELEMENTS = ns["FIELDS"], ns["ELEMENTS"]
M = ns["_ns"]["M"]
TESTS = {  # label: dictionary key
    "t test": "t test", "ANOVA family": "ANOVA / ANCOVA / MANOVA", "Chi-square / nonparametric": "Chi-square / nonparametric",
    "Correlation": "Correlation", "Linear regression": "Linear / multiple / hierarchical regression",
    "Logistic regression": "Logistic / ordinal / multinomial regression", "Mediation": "Mediation", "SEM / path analysis": "SEM / path analysis",
}
REPORT = {
    "p value": re.compile(r"\bp\s*[<=>≤]\s*0?\.\d", re.I),
    "Effect size": re.compile(ELEMENTS["Effect size"], re.I),
    "Confidence interval": re.compile(ELEMENTS["Confidence interval"], re.I),
}
TEST_RE = {label: re.compile(M[key][1], re.I) for label, key in TESTS.items()}

abstracts, seen = [], set()
for files in FIELDS.values():
    for f in files:
        for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
            if r["id"] in seen or r["year"] > 2026 or len(r["abstract"].split()) <= 60: continue
            seen.add(r["id"]); abstracts.append(r["title"] + " " + r["abstract"])

rows = []
for label, rx in TEST_RE.items():
    hits = [a for a in abstracts if rx.search(a)]
    for what, c in REPORT.items():
        x = sum(bool(c.search(a)) for a in hits)
        rows.append({"test": label, "abstracts": len(hits), "reported": what, "x": x, "share": x / len(hits)})
out = os.path.join(HERE, "abstract_guide", "results_reporting.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"{len(abstracts)} abstracts")
for label in TESTS:
    r = [x for x in rows if x["test"] == label]
    print(f"{label:28} n={r[0]['abstracts']:6} | " + "; ".join(f"{x['reported']} {x['share']:.1%}" for x in r))
