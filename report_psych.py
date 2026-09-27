# Compact report of psych_subfields/post_stats.csv for checking the psychology posts.
import csv
f = lambda x: float(x) if x not in ("", "NA") else float("nan")
rows = list(csv.DictReader(open("psych_subfields/post_stats.csv", encoding="utf-8")))
summ = {s["subfield"]: s for s in csv.DictReader(open("psych_subfields/summary.csv", encoding="utf-8"))}
for k in ["all", "clinical", "social", "developmental_educational", "experimental_cognitive", "applied"]:
    r = [x for x in rows if x["subfield"] == k]; s = summ[k]
    print(f"\n== {k} n={s['abstracts']} quant={100*f(s['quant_share']):.1f}% (n={s['quant_n']})")
    print("   top:", "; ".join(f"{x['label']} {100*f(x['share_quant']):.1f}" for x in sorted(r, key=lambda x: -f(x["share_quant"]))[:14]))
    d = [x for x in r if f(x.get("q_vs_rest", "")) < .05]
    if d: print("   distinct:", "; ".join(f"{x['label']} {100*f(x['share_quant']):.1f} vs {100*f(x['rest_share_quant']):.1f}" for x in d))
    print("   sig trends:", "; ".join(f"{x['label']} {x['early_x']}->{x['late_x']} ({100*f(x['early_share']):.1f}->{100*f(x['late_share']):.1f}) q={f(x['q_trend']):.3f}" for x in r if f(x["q_trend"]) < .05) or "none")
    print("   raw moves:", "; ".join(f"{x['label']} {x['early_x']}->{x['late_x']} p={f(x['p_trend']):.3f}" for x in sorted(r, key=lambda x: f(x['p_trend']))[:4]))
