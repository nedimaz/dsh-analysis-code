# Method statistics for the DSH blog series beyond psychology (education, business, social sciences & health).
#   python analyze_series.py <series>      series: education | business | social
# Input: raw/*.json from pull_openalex.py --all (English dissertations/theses with abstracts, 2021+).
# Output (series/<series>/): summary.csv, methods.csv, trends.csv, topics.csv. Same definitions as
# ../analyze_subfields.py (psychology), plus methods that matter outside psychology (EXTRA). The psychology
# script is left untouched so its published numbers stay reproducible.
import csv, json, math, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw")
src = open(os.path.join(HERE, "..", "classify_methods.py"), encoding="utf-8").read()
block = src[src.index("M = {"):src.index("\n}\n", src.index("M = {")) + 3]
ns = {}; exec(block, ns); M = dict(ns["M"])
EXTRA = {
    "Panel data / fixed effects": ("Analysis", r"panel data|fixed[- ]effects?|\bGMM\b|generalized method of moments"),
    "Causal designs (DiD, RDD, IV, synthetic control)": ("Analysis", r"difference-in-difference|diff-in-diff|regression discontinuity|instrumental variable|two-stage least squares|\b2SLS\b|synthetic control|event study"),
    "Propensity scores / matching": ("Analysis", r"propensity score|inverse probability (of treatment )?weight|coarsened exact|matching estimator|matched comparison"),
    "PLS-SEM": ("Analysis", r"partial least squares|\bPLS\b|smartpls"),
    "Econometric time series (ARDL, GARCH, VECM)": ("Analysis", r"\bARDL\b|GARCH|cointegrat|\bVECM\b|unit root|granger"),
    "Efficiency analysis (DEA, stochastic frontier)": ("Analysis", r"data envelopment|\bDEA\b|stochastic frontier"),
    "Qualitative comparative analysis (QCA)": ("Analysis", r"qualitative comparative analysis|fsQCA|\bQCA\b"),
    "Spatial analysis / GIS": ("Analysis", r"\bGIS\b|spatial (analysis|regression|autocorrelation|econometric)|geographically weighted|geospatial"),
    "Conjoint / discrete choice": ("Analysis", r"conjoint|discrete choice|choice experiment"),
    "Content analysis": ("Design", r"content analysis"),
}
M.update(EXTRA)
COMP = {k: re.compile(v, re.I) for k, (g, v) in M.items()}
QUANT = [k for k, (g, _) in M.items() if g in ("Analysis", "Measurement")] + ["Experiment / randomized design", "Quasi-experimental / program evaluation"]
DESIGN = ["Qualitative (thematic, IPA, grounded theory, interviews)", "Mixed methods", "Experiment / randomized design", "Systematic review / meta-analysis",
          "Survey / questionnaire study", "Case study", "Action research / improvement science", "Quasi-experimental / program evaluation", "Content analysis"]

EDU = {  # topic clusters for education (OpenAlex primary topics); unlisted topics stay in the overview only
    "teaching_learning": ("Teaching, learning & curriculum", ["Educational Methods and Outcomes", "Educational Curriculum and Learning Methods", "Educational Methods and Impacts", "STEM Education",
        "Education and Critical Thinking Development", "Mathematics Education and Teaching Techniques", "Science Education and Pedagogy", "Student Assessment and Feedback",
        "Writing and Handwriting Education", "Innovative Teaching Methods", "Literacy and Educational Practices", "Evaluation of Teaching Practices", "Education Methods and Practices",
        "Educational Assessment and Pedagogy", "Innovations in Educational Methods", "Problem and Project Based Learning", "Educational Methods and Analysis",
        "Education Practices and Evaluation", "Educational Methods and Psychological Studies", "Reflective Practices in Education", "Music Education and Analysis",
        "Chemistry Education and Research", "Physical Education and Gymnastics", "Innovative Teaching Methodologies in Social Sciences", "Innovative Educational Techniques"]),
    "online_learning": ("Online & technology-enhanced learning", ["Online Learning Methods and Innovations", "Online and Blended Learning", "Technology-Enhanced Education Studies",
        "Education and Technology Integration", "E-Learning and COVID-19", "Information Technology and Learning", "Education during COVID-19 pandemic", "Education Methods and Technologies"]),
    "higher_education": ("Higher & adult education", ["Higher Education Research Studies", "Higher Education and Employability", "Sustainability in Higher Education",
        "Higher Education Practises and Engagement", "Higher Education Learning Practices", "Service-Learning and Community Engagement", "Higher Education Teaching and Evaluation",
        "University Challenges and Reforms", "Higher Education and Sustainability", "Knowledge Management in Higher Education", "Adult and Continuing Education Topics",
        "Vocational and Entrepreneurial Education", "Education and Vocational Training", "Vocational Education and Training"]),
    "leadership_policy": ("Leadership, teachers & policy", ["Teacher Education and Leadership Studies", "School Leadership and Teacher Performance", "Education Systems and Policy",
        "Educational Leadership and Innovation", "School Choice and Performance", "Education Discipline and Inequality", "Teacher Professional Development and Motivation",
        "Education and Teacher Training", "Educational Leadership and Practices", "Educational Practices and Policies", "Diverse Education Studies and Reforms",
        "Educational Environments and Student Outcomes", "Impact of Education Environments", "Educational Leadership and Administration", "Teacher Education and Assessments",
        "Global Education Systems and Policies"]),
    "early_inclusive": ("Early childhood, family & inclusive education", ["Early Childhood Education and Development", "Child Development and Education", "Parental Involvement in Education",
        "Collaborative Teaching and Inclusion", "Child Development and Digital Technology", "Inclusive Education and Diversity", "Youth Substance Use and School Attendance",
        "Social Skills and Education"]),
}
SERIES = {
    "education": {"all": ("Education overall", ["education.json"]), "groups": {k: (v[0], ["education.json"], v[1]) for k, v in EDU.items()}},
    "business": {"all": ("Business overall", None), "groups": {
        "strategy": ("Strategy & management", ["bus_strategy.json"], None), "accounting_finance": ("Accounting & finance", ["bus_accounting_finance.json"], None),
        "marketing": ("Marketing", ["bus_marketing.json"], None), "ob_hrm": ("Organizational behavior & HRM", ["bus_ob_hrm.json"], None),
        "info_tech": ("Information systems & technology management", ["bus_info_tech.json"], None)}},
    "social": {"all": ("Social sciences & health overall", None), "groups": {
        "sociology": ("Sociology", ["soc_sociology.json"], None), "polisci": ("Political science & international relations", ["soc_polisci.json"], None),
        "economics": ("Economics", ["soc_economics.json"], None), "public_health": ("Public health", ["soc_public_health.json"], None),
        "nursing_health": ("Nursing & health professions", ["soc_nursing_health_prof.json"], None), "communication": ("Communication", ["soc_communication.json"], None)}},
}

def wilson(x, n, z=1.959964):
    p = x / n; den = 1 + z * z / n; mid = (p + z * z / (2 * n)) / den; half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (mid - half, mid + half)

_cache = {}
def load(files):
    key = tuple(files)
    if key not in _cache: _cache[key] = _load(files)
    return _cache[key]

def _load(files):
    out, seen = [], set()
    for f in files:
        for r in json.load(open(os.path.join(RAW, f), encoding="utf-8")):
            if len(r["abstract"].split()) > 60 and r["year"] <= 2026 and r["id"] not in seen:  # drops records with impossible future dates
                seen.add(r["id"]); text = r["title"] + " " + r["abstract"]
                r["flags"] = {k: bool(c.search(text)) for k, c in COMP.items()}; r["quant"] = any(r["flags"][k] for k in QUANT); out.append(r)
    return out

series = sys.argv[1]; cfg = SERIES[series]; OUT = os.path.join(HERE, series); os.makedirs(OUT, exist_ok=True)
records = {}
for key, (label, files, topics) in cfg["groups"].items():
    rows = load(files); records[key] = [r for r in rows if topics is None or r["topic"] in topics]
all_label, all_files = cfg["all"]
records["all"] = load(all_files) if all_files else [r for k in cfg["groups"] for r in records[k]]
labels = {k: v[0] for k, v in cfg["groups"].items()}; labels["all"] = all_label
grouped = [r for k in cfg["groups"] for r in records[k]]  # the pool for "rest of the series" comparisons
# US-tagged vs. everything else (country is known for a minority of records; "other" includes unknown).
records["us"] = [r for r in records["all"] if r.get("country") == "US"]; records["other"] = [r for r in records["all"] if r.get("country") != "US"]
labels["us"] = "US-tagged"; labels["other"] = "Other or unknown country"

summary, methods, trends, topics = [], [], [], []
for key, rows in records.items():
    n = len(rows); q = [r for r in rows if r["quant"]]; ids = {r["id"] for r in rows}
    rest_q = {"all": [], "us": [r for r in records["other"] if r["quant"]], "other": [r for r in records["us"] if r["quant"]]}.get(key)         if key in ("all", "us", "other") else [r for r in grouped if r["quant"] and r["id"] not in ids]
    early = [r for r in rows if r["year"] in (2021, 2022)]; late = [r for r in rows if r["year"] in (2025, 2026)]
    s = {"subfield": key, "label": labels[key], "abstracts": n, "quant_n": len(q), "quant_share": len(q) / n,
         "early_n": len(early), "early_quant_n": sum(r["quant"] for r in early), "late_n": len(late), "late_quant_n": sum(r["quant"] for r in late),
         "us_share": sum(r.get("country") == "US" for r in rows) / n, "country_known": sum(bool(r.get("country")) for r in rows) / n}
    for dsg in DESIGN: s[dsg] = sum(r["flags"][dsg] for r in rows) / n
    summary.append(s)
    for t, c in Counter(r["topic"] for r in rows).most_common(15): topics.append({"subfield": key, "topic": t, "n": c})
    for m, (g, _) in M.items():
        if g not in ("Analysis", "Measurement"): continue
        xq = sum(r["flags"][m] for r in q); lo, hi = wilson(xq, len(q))
        row = {"subfield": key, "method": m, "group": g, "share_all": sum(r["flags"][m] for r in rows) / n, "x_all": sum(r["flags"][m] for r in rows), "n_quant": len(q), "x_quant": xq,
               "share_quant": xq / len(q), "ci_low": lo, "ci_high": hi, "rest_x": "", "rest_n": "", "rest_share_quant": ""}
        if rest_q:
            xr = sum(r["flags"][m] for r in rest_q); row.update(rest_x=xr, rest_n=len(rest_q), rest_share_quant=xr / len(rest_q))
        methods.append(row)
        trends.append({"subfield": key, "method": m, "early_n": len(early), "early_x": sum(r["flags"][m] for r in early),
                       "late_n": len(late), "late_x": sum(r["flags"][m] for r in late)})

def write(name, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
write("summary.csv", summary); write("methods.csv", methods); write("trends.csv", trends); write("topics.csv", topics)
for s in summary:
    print(f"{s['label'][:44]:44} n={s['abstracts']:5}  quant={s['quant_share']:.0%} (n={s['quant_n']})  qual={s[DESIGN[0]]:.0%}  exp={s[DESIGN[2]]:.0%}  survey={s[DESIGN[4]]:.0%}  US={s['us_share']:.0%}")
