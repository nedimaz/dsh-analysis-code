# Statistical methods in recent dissertations and theses

Analysis code behind the [Dissertation Stats Helper blog](https://dissertationstatshelper.com/blog) series on which statistical methods recent dissertations and theses name in their abstracts:

| Series | Abstracts | Overview post |
|---|---|---|
| Psychology | 21,308 | [statistical-methods-in-psychology-dissertations](https://dissertationstatshelper.com/blog/statistical-methods-in-psychology-dissertations) |
| Education | 18,617 | [statistical-methods-in-education-dissertations](https://dissertationstatshelper.com/blog/statistical-methods-in-education-dissertations) |
| Business | 22,179 | [statistical-methods-in-business-dissertations](https://dissertationstatshelper.com/blog/statistical-methods-in-business-dissertations) |
| Social sciences & health | 50,799 | [statistical-methods-in-social-science-dissertations](https://dissertationstatshelper.com/blog/statistical-methods-in-social-science-dissertations) |

## What the analysis does

1. **Pull** every English-language work that [OpenAlex](https://openalex.org) types as a dissertation or thesis, with an abstract, published from 2021 onward, for a set of OpenAlex subfields (`pull_openalex.py`).
2. **Classify** each title and abstract with a keyword dictionary of about 40 statistical methods and study designs (`classify_methods.py`, dictionary `M`). Abstracts of 60 words or fewer and records with impossible future dates are dropped.
3. **Summarize** by field or area:
   - **Method shares:** the share of all abstracts, and of abstracts that name at least one quantitative method, that mention each method, with Wilson intervals.
   - **Area comparisons:** each area vs. the rest of its series.
   - **Change over time:** 2021–22 vs. 2025–26.
   - **Tests:** comparisons use Fisher's exact tests with a Benjamini–Hochberg correction within each area and question.
4. **Chart** the results with ggplot2 in the site's colors.

A percentage is the share of abstracts that *mention* a method, not how often the method was used. See the "How we did this" section of each overview post for the limitations:
- keyword matching;
- loose subfield boundaries (OpenAlex assigns them by algorithm);
- international coverage that changes over time;
- country known for a minority of works.

## Files

| File | Purpose |
|---|---|
| `pull_openalex.py` | Download works for one or more OpenAlex subfields (cursor paging with `--all`). |
| `classify_methods.py` | The method dictionary (`M`). When run as a script, it prints a quick one-sample scan. |
| `explore_openalex.py` | Count works by subfield, overall and for US-tagged institutions. |
| `analyze_subfields.py`, `make_blog_charts.R`, `report_psych.py` | Psychology series (five subfields). |
| `series/analyze_series.py`, `series/make_series_charts.R`, `series/report.py` | Education, business, and social sciences & health series. The group definitions (subfields and education topic clusters) are in `SERIES` in `analyze_series.py`. |
| `psych_subfields/*.csv`, `series/<series>/*.csv` | Results: `summary.csv` (design mix), `methods.csv`, `trends.csv`, `topics.csv`, and `post_stats.csv` (every number quoted in the posts, with p and q values). |

The raw OpenAlex downloads (`*.json`) are not committed. They are large and can be rebuilt with the commands below. OpenAlex data are CC0.

## Reproduce

Requirements:
- Python 3.10+ (standard library only);
- R 4.x with `ggplot2`, `dplyr`, `tidyr`, `readr`, `forcats`, `scales`, and `ragg`.

An OpenAlex API key is optional. Set `OPENALEX_API_KEY` or put the key in `~/.secrets/OpenAlexApi.txt`.

```bash
# Psychology: clinical 3203, social 3207, developmental & educational 3204, experimental & cognitive 3205, applied 3202
python pull_openalex.py primary_topic.subfield.id 3203 psych_subfields/clinical.json --all
python pull_openalex.py primary_topic.subfield.id 3207 psych_subfields/social.json --all
python pull_openalex.py primary_topic.subfield.id 3204 psych_subfields/developmental_educational.json --all
python pull_openalex.py primary_topic.subfield.id 3205 psych_subfields/experimental_cognitive.json --all
python pull_openalex.py primary_topic.subfield.id 3202 psych_subfields/applied.json --all
python analyze_subfields.py
Rscript make_blog_charts.R

# Other series (run from series/)
cd series
python ../pull_openalex.py primary_topic.subfield.id 3304 raw/education.json --all
python ../pull_openalex.py primary_topic.subfield.id 1408 raw/bus_strategy.json --all
python ../pull_openalex.py primary_topic.subfield.id "1402|2003" raw/bus_accounting_finance.json --all
python ../pull_openalex.py primary_topic.subfield.id 1406 raw/bus_marketing.json --all
python ../pull_openalex.py primary_topic.subfield.id 1407 raw/bus_ob_hrm.json --all
python ../pull_openalex.py primary_topic.subfield.id "1404|1405" raw/bus_info_tech.json --all
python ../pull_openalex.py primary_topic.subfield.id 3312 raw/soc_sociology.json --all
python ../pull_openalex.py primary_topic.subfield.id 3320 raw/soc_polisci.json --all
python ../pull_openalex.py primary_topic.subfield.id 2739 raw/soc_public_health.json --all
python ../pull_openalex.py primary_topic.subfield.id "2900|2902|2903|2904|2905|2906|2907|2908|2909|2910|2911|2912|2913|2914|2915|2916|2917|2918|2919|2920|2921|2922|2923|3600" raw/soc_nursing_health_prof.json --all
python ../pull_openalex.py primary_topic.subfield.id 3315 raw/soc_communication.json --all
python ../pull_openalex.py primary_topic.subfield.id 2002 raw/soc_economics.json --all
for s in education business social; do python analyze_series.py $s && Rscript make_series_charts.R $s; done
```

Charts go to `charts/` by default. Set `DSH_CHART_DIR` to write them somewhere else.

OpenAlex keeps adding and reclassifying works, so a fresh pull will give slightly different counts than the published posts. The committed CSVs are the exact numbers behind the posts, from the pulls of September 27, 2026.

## Changes to the dictionary

On 2026-09-27, spot checks across fields led to tighter patterns for three methods, and all four series were rerun:
- **Mediation** had been counting "computer-mediated", "remediation" and conflict mediation.
- **Growth models** had been counting everyday uses of "trajectory", such as career or historical trajectories.
- **Vector autoregression (VAR)** had been counting "VaR" (value at risk).
