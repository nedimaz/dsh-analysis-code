# Compact text report of post_stats.csv + summary.csv + topics.csv for writing posts.  python report.py <series>
import csv, sys
s = sys.argv[1]; f = lambda x: float(x) if x not in ("", "NA") else float("nan")
rows = list(csv.DictReader(open(f"{s}/post_stats.csv", encoding="utf-8"))); summ = list(csv.DictReader(open(f"{s}/summary.csv", encoding="utf-8")))
tops = list(csv.DictReader(open(f"{s}/topics.csv", encoding="utf-8")))
for sm in summ:
    k = sm["subfield"]; r = [x for x in rows if x["subfield"] == k]
    print(f"\n== {sm['label']} ({k}) n={sm['abstracts']} quant={f(sm['quant_share']):.1%} (n={sm['quant_n']}) US={f(sm['us_share']):.1%} known={f(sm['country_known']):.0%}")
    print("   early quant %.1f%% (n=%s) late quant %.1f%% (n=%s)" % (100*int(sm['early_quant_n'])/int(sm['early_n']), sm['early_n'], 100*int(sm['late_quant_n'])/int(sm['late_n']), sm['late_n']))
    print("   design:", {c[:14]: round(100*f(v),1) for c, v in sm.items() if c not in ("subfield","label","abstracts","quant_n","quant_share","early_n","early_quant_n","late_n","late_quant_n","us_share","country_known")})
    print("   topics:", "; ".join([f"{t['topic']} ({t['n']})" for t in tops if t["subfield"] == k][:9]))
    print("   top:", "; ".join(f"{x['label']} {100*f(x['share_quant']):.1f}" for x in sorted(r, key=lambda x: -f(x["share_quant"]))[:16]))
    d = [x for x in r if f(x["q_vs_rest"]) < .05]
    if d: print("   distinct:", "; ".join(f"{x['label']} {100*f(x['share_quant']):.1f} vs {100*f(x['rest_share_quant']):.1f}" for x in sorted(d, key=lambda x: -abs(f(x['share_quant'])-f(x['rest_share_quant'])))))
    print("   sig trends:", "; ".join(f"{x['label']} {x['early_x']}->{x['late_x']} ({100*f(x['early_share']):.1f}->{100*f(x['late_share']):.1f}) q={f(x['q_trend']):.3f}" for x in r if f(x["q_trend"]) < .05) or "none")
    print("   top raw moves:", "; ".join(f"{x['label']} {x['early_x']}->{x['late_x']} ({100*f(x['early_share']):.1f}->{100*f(x['late_share']):.1f}) p={f(x['p_trend']):.3f}" for x in sorted(r, key=lambda x: f(x['p_trend']))[:4]))
    print("   power/missing (x_all):", [(x['label'], x['x_all']) for x in r if x['label'] in ('Power analysis', 'Missing data methods')])
