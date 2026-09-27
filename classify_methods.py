# Count method mentions in an OpenAlex dissertation sample (title + abstract).
# Keyword/regex dictionary; a mention means the abstract names the method, not that it was the
# main analysis. Denominator: records with abstracts over 60 words.
#   python classify_methods.py [sample.json] [output-prefix]
# Defaults reproduce the 2026-09-26 psychology run (method_prevalence*.csv).
import json, re, csv, sys
from collections import Counter
SRC = sys.argv[1] if len(sys.argv) > 1 else "openalex_psych_dissertations_2021_2026_sample.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "method_prevalence"
rows = [r for r in json.load(open(SRC, encoding="utf-8")) if len(r["abstract"].split()) > 60]
M = {  # name: (group, regex)
 "Qualitative (thematic, IPA, grounded theory, interviews)": ("Design", r"qualitative|thematic analysis|interpretative phenomenolog|\bIPA\b|grounded theory|phenomenolog|semi-structured interview|focus group|narrative analysis|discourse analysis"),
 "Mixed methods": ("Design", r"mixed[- ]methods?"),
 "Experiment / randomized design": ("Design", r"randomi[sz]ed|randomly assigned|between-subjects|within-subjects|\bRCT\b|experimental (condition|design|manipulation|group)|manipulat(ed|ion)"),
 "Quasi-experimental / program evaluation": ("Design", r"quasi-experiment|propensity score|difference-in-difference|regression discontinuity|interrupted time series|program evaluation"),
 "Single-case design": ("Design", r"single[- ]case|single[- ]subject|multiple[- ]baseline|\bABAB\b|reversal design|alternating treatments"),
 "Longitudinal / repeated measures": ("Design", r"longitudinal|repeated[- ]measures|follow-up|\bwaves?\b|panel data|prospective"),
 "Daily diary / EMA / experience sampling": ("Design", r"daily diar|ecological momentary|\bEMA\b|experience sampling|intensive longitudinal"),
 "Systematic review / meta-analysis": ("Design", r"meta-analy|systematic review|scoping review"),
 "Scale development / psychometric validation": ("Measurement", r"scale development|psychometric|validat(ion|e the|ed the) (of )?(a |the )?(scale|measure|instrument|questionnaire)|factor structure|construct validity|measurement invariance"),
 "Factor analysis (EFA/CFA)": ("Measurement", r"factor analy|\bCFA\b|\bEFA\b|confirmatory factor|exploratory factor"),
 "IRT / Rasch / DIF": ("Measurement", r"item response|\bIRT\b|rasch|differential item"),
 "Reliability (alpha, omega, ICC)": ("Measurement", r"reliabilit|cronbach|internal consistency|omega\b|intraclass"),
 "t test": ("Analysis", r"\bt[- ]tests?\b"),
 "ANOVA / ANCOVA / MANOVA": ("Analysis", r"\bA?N?C?OVA\b|ANOVA|ANCOVA|MANOVA|MANCOVA|analysis of (co)?variance"),
 "Correlation": ("Analysis", r"correlat(?!es\b(?! with))"),  # skips the noun "correlates of" (2026-09-27)
 "Linear / multiple / hierarchical regression": ("Analysis", r"(multiple|hierarchical|linear|multivariate|OLS) regression|regression analys|regression models?"),
 "Logistic / ordinal / multinomial regression": ("Analysis", r"logistic regression|ordinal regression|multinomial|odds ratio|probit"),
 "Count models (Poisson, negative binomial)": ("Analysis", r"poisson|negative binomial|zero-inflated"),
 "Chi-square / nonparametric": ("Analysis", r"chi[- ]square|mann-whitney|wilcoxon|kruskal|non-?parametric|fisher'?s exact"),
 # Mediation, growth and VAR tightened 2026-09-27. The broad patterns caught "computer-mediated", "remediation", conflict
 # mediation, everyday "trajectory" (career, historical, robot) and "VaR" (value at risk). Spot-checked across fields.
 "Mediation": ("Analysis", r"mediation (analys|model|effect|test|path|hypothes)|mediat(ed|ing) (effect|role|variable|mechanism|pathway)s?|mediators?\b|indirect (effect|path|association)s?|mediated moderation|moderated mediation|mediation (was|were) (tested|examined|found)|mediat(es|ed|ing) (the )?(relation|relationship|association|link|effect|impact)s?|(partial|full|complete|serial|parallel|significant) mediation|mediation of|mediating|evidence (of|for) mediation|(?<![-\w])mediated by|\bmediated? (the|this|these)\b"),
 "Moderation / interactions": ("Analysis", r"moderat(ion|ed|ing|or)|interaction effect|conditional process|johnson-neyman|simple slopes"),
 "SEM / path analysis": ("Analysis", r"structural equation|\bSEM\b|path analy|path model|latent variable model"),
 "Multilevel / mixed-effects models": ("Analysis", r"multilevel|hierarchical linear model|\bHLM\b|mixed[- ]effects?|linear mixed|random[- ]effects|mixed models?"),
 "Growth curve / trajectories": ("Analysis", r"growth curve|latent growth|growth mixture|(group-based|latent|developmental|symptom|longitudinal) trajector|trajectory (analysis|model|modell?ing|class|group)s?|trajectories of (change|depress|anxi|symptom|internaliz|externaliz|PTSD|posttraumatic|well-being|distress)|(multilevel|hierarchical|piecewise|latent|linear|mixed|individual|conditional|unconditional) growth model"),
 "Latent profile / class / mixture": ("Analysis", r"latent (class|profile|transition)|mixture model|\bLPA\b|\bLCA\b|growth mixture"),
 "Cluster analysis": ("Analysis", r"cluster analy|k-means|hierarchical clustering"),
 "Network analysis (psychometric networks)": ("Analysis", r"network analy|psychometric network|network model|symptom network"),
 "Machine learning / NLP": ("Analysis", r"machine learning|random forest|\blasso\b|neural network|deep learning|natural language processing|\bNLP\b|support vector|classifier"),
 "Bayesian": ("Analysis", r"bayes"),
 "Survival / time-to-event": ("Analysis", r"survival analy|\bcox\b|time-to-event|hazard ratio|kaplan"),
 "Missing data / multiple imputation": ("Analysis", r"missing data|multiple imputation|\bFIML\b|full information maximum"),
 "Dyadic / APIM": ("Analysis", r"\bdyadic\b|\bdyads\b|actor[- ]partner|\bAPIM\b"),
 "Time series / dynamic models (VAR, DSEM)": ("Analysis", r"time[- ]series|autoregress|(?-i:\bVAR\b)|\bDSEM\b|dynamic structural"),
 "Text analysis (LIWC, sentiment, topic models)": ("Analysis", r"\bLIWC\b|sentiment analy|topic model|text analy|linguistic inquiry"),
 "Neuro / physiological (EEG, fMRI, eye tracking, cortisol)": ("Data", r"\bfMRI\b|\bEEG\b|\bERPs?\b|event-related potential|neuroimaging|eye[- ]track|cortisol|heart rate variability|\bHRV\b|psychophysiolog"),
 "Power analysis reported": ("Analysis", r"power analys|a priori power|sample size calculation"),
 # Added for the education scan (2026-09-26). Kept out of the Analysis/Measurement groups so the
 # psychology run's quantitative denominator is unchanged.
 "Survey / questionnaire study": ("Design", r"\bsurvey|questionnaire"),
 "Case study": ("Design", r"case study|case studies"),
 "Action research / improvement science": ("Design", r"action research|improvement science|\bPDSA\b|plan-do-study-act|design-based research"),
 "Delphi / Q methodology": ("Design", r"delphi|q[- ]methodology"),
 "Descriptive statistics only named": ("Design", r"descriptive statistic|frequenc(y|ies) and percentages|means and standard deviations"),
 "Large-scale / administrative data (NAEP, ECLS, PISA, IPEDS...)": ("Data", r"\bNAEP\b|\bECLS|\bPISA\b|TIMSS|\bHSLS|\bIPEDS\b|\bNSSE\b|\bELS:?2002|\bBPS\b|administrative data|state longitudinal data|secondary data|national dataset"),
 "Survey weights / complex samples": ("Data", r"sampling weights?|survey weights?|complex (sample|survey)"),
 "Inter-rater agreement (kappa)": ("Data", r"inter-?rater|interrater|cohen'?s kappa|\bkappa\b"),
 "Learning analytics / log data": ("Data", r"learning analytics|educational data mining|log data|clickstream|learning management system data"),
}
comp = {k: re.compile(v, re.I) for k, (g, v) in M.items()}
hits = Counter()
for r in rows:
    t = r["title"] + " " + r["abstract"]
    for k, c in comp.items():
        if c.search(t): hits[k] += 1
n = len(rows)
quant_keys = [k for k, (g, _) in M.items() if g in ("Analysis", "Measurement")] + ["Experiment / randomized design", "Quasi-experimental / program evaluation"]
quant = sum(1 for r in rows if any(comp[k].search(r["title"] + " " + r["abstract"]) for k in quant_keys))
with open(OUT + ".csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["method", "group", "n", "pct"])
    for k, (g, _) in M.items(): w.writerow([k, g, hits[k], round(100 * hits[k] / n, 1)])
print(f"N = {n} abstracts; any quantitative method named: {100*quant/n:.0f}%")
for g in ("Design", "Measurement", "Analysis", "Data"):
    print(f"\n{g}")
    for k, (gg, _) in sorted(M.items(), key=lambda kv: -hits[kv[0]]):
        if gg == g: print(f"  {100*hits[k]/n:5.1f}%  {hits[k]:5}  {k}")

# Share among abstracts that name at least one quantitative method, and early vs recent years.
qrows = [r for r in rows if any(comp[k].search(r["title"] + " " + r["abstract"]) for k in quant_keys)]
early = [r for r in rows if r["year"] in (2021, 2022)]; late = [r for r in rows if r["year"] in (2025, 2026)]
def pct(rs, k): return 100 * sum(1 for r in rs if comp[k].search(r["title"] + " " + r["abstract"])) / max(1, len(rs))
print(f"\nAmong the {len(qrows)} abstracts naming a quantitative method (analysis + measurement groups):")
with open(OUT + "_quant.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["method", "pct_of_quant", "pct_2021_22", "pct_2025_26"])
    for k, (g, _) in sorted(M.items(), key=lambda kv: -pct(qrows, kv[0])):
        if g not in ("Analysis", "Measurement"): continue
        a, e, l = pct(qrows, k), pct(early, k), pct(late, k)
        w.writerow([k, round(a, 1), round(e, 2), round(l, 2)])
        print(f"  {a:5.1f}%   early {e:4.1f}% -> recent {l:4.1f}%   {k}")
print(f"(early n={len(early)}, recent n={len(late)})")
