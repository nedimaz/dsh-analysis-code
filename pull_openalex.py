# Pull a random sample of dissertations/theses from OpenAlex for one field or subfield.
#   python pull_openalex.py <filter-key> <id> <out.json> [--n 10000] [--seed 42] [--us] [--all]
# Several ids: separate with | (e.g. 1404|1405). Rows include the first author's institution country.
# e.g. python pull_openalex.py primary_topic.field.id 32 openalex_psych_...json      (Psychology)
#      python pull_openalex.py primary_topic.subfield.id 3304 openalex_edu_...json   (Education)
# Filters: type dissertation, published 2021-01-01 onward, English, has an abstract.
import json, os, sys, time, urllib.parse, urllib.request
from collections import Counter

# Optional API key (raises the daily allowance): the OPENALEX_API_KEY environment variable, or the file
# ~/.secrets/OpenAlexApi.txt (either the bare key or KEY=value). The key is never printed or logged.
def read_api_key():
    if os.environ.get("OPENALEX_API_KEY"): return os.environ["OPENALEX_API_KEY"].strip()
    path = os.path.join(os.path.expanduser("~"), ".secrets", "OpenAlexApi.txt")
    if not os.path.exists(path): return None
    raw = open(path, encoding="utf-8-sig").read().strip()
    return raw.split("=", 1)[1].strip() if "=" in raw else raw
API_KEY = read_api_key()

key, ident, out = sys.argv[1], sys.argv[2], sys.argv[3]
n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 10000
seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 42
flt = f"type:dissertation,from_publication_date:2021-01-01,{key}:{ident},has_abstract:true,language:en"
if "--us" in sys.argv:  # only works whose authors' institutions OpenAlex tags as US (a small, market-relevant subset)
    flt += ",institutions.country_code:us"
ALL = "--all" in sys.argv  # every matching work (cursor paging) instead of a random sample
rows, page, cursor = [], 1, "*"
while True:
    params = {"filter": flt, "per-page": 200, "select": "id,title,publication_year,abstract_inverted_index,primary_topic,authorships"}
    params.update({"cursor": cursor} if ALL else {"sample": n, "seed": seed, "page": page})
    if API_KEY: params["api_key"] = API_KEY
    q = urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            d = json.load(urllib.request.urlopen(f"https://api.openalex.org/works?{q}", timeout=60)); break
        except Exception:
            time.sleep(3 * (attempt + 1))
    else:
        raise SystemExit(f"page {page} failed")
    res = d["results"]
    for w in res:
        inv = w.get("abstract_inverted_index") or {}
        pos = sorted((p, word) for word, ps in inv.items() for p in ps)
        first = [i for a in (w.get("authorships") or [])[:1] for i in (a.get("institutions") or [])[:1]]
        inst = [i.get("display_name") for i in first]; country = [i.get("country_code") for i in first]
        rows.append({"id": w["id"], "year": w["publication_year"], "title": w.get("title") or "",
                     "abstract": " ".join(word for _, word in pos),
                     "subfield": ((w.get("primary_topic") or {}).get("subfield") or {}).get("display_name"),
                     "topic": (w.get("primary_topic") or {}).get("display_name"),
                     "institution": inst[0] if inst else None, "country": country[0] if country else None})
    if ALL:
        cursor = d["meta"].get("next_cursor")
        if not cursor or not res: break
    elif len(res) < 200 or page * 200 >= n: break
    page += 1; time.sleep(0.15)
json.dump(rows, open(out, "w", encoding="utf-8"))
print(("using API key; " if API_KEY else "no API key; ") + str(len(rows)), "records;", sum(1 for r in rows if len(r["abstract"].split()) > 60), "with abstracts over 60 words")
print(Counter(r["year"] for r in rows).most_common())
print(Counter(r["topic"] for r in rows).most_common(10))
