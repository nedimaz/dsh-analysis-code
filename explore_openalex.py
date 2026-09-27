# Count English dissertations/theses with abstracts (2021+) by subfield, globally and US-tagged. Key read inside, never printed.
import json, os, sys, urllib.parse, urllib.request
# Optional API key (raises the daily allowance): the OPENALEX_API_KEY environment variable, or the file
# ~/.secrets/OpenAlexApi.txt (either the bare key or KEY=value). The key is never printed or logged.
def read_api_key():
    if os.environ.get("OPENALEX_API_KEY"): return os.environ["OPENALEX_API_KEY"].strip()
    path = os.path.join(os.path.expanduser("~"), ".secrets", "OpenAlexApi.txt")
    if not os.path.exists(path): return None
    raw = open(path, encoding="utf-8-sig").read().strip()
    return raw.split("=", 1)[1].strip() if "=" in raw else raw
API_KEY = read_api_key()
def group(extra, by):
    flt = "type:dissertation,from_publication_date:2021-01-01,has_abstract:true,language:en" + extra
    params = {"filter": flt, "group_by": by, "per-page": 200}
    if API_KEY: params["api_key"] = API_KEY
    q = urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(f"https://api.openalex.org/works?{q}", timeout=60))
g = {x["key"].split("/")[-1]: (x["key_display_name"], x["count"]) for x in group("", "primary_topic.subfield.id")["group_by"]}
u = {x["key"].split("/")[-1]: x["count"] for x in group(",institutions.country_code:us", "primary_topic.subfield.id")["group_by"]}
f = {x["key"].split("/")[-1]: (x["key_display_name"], x["count"]) for x in group("", "primary_topic.field.id")["group_by"]}
json.dump({"subfields": g, "us": u, "fields": f}, open("openalex_subfield_counts.json", "w"), indent=1)
for k, (name, c) in sorted(g.items(), key=lambda kv: -kv[1][1])[:70]:
    print(f"{k:>5} {name[:52]:52} {c:6} US {u.get(k, 0):5}")
print("--- fields"); [print(k, n, c) for k, (n, c) in sorted(f.items(), key=lambda kv: -kv[1][1])[:26]]
