# Charts for the DSH blog series beyond psychology, in the same style as ../make_blog_charts.R.
#   Rscript make_series_charts.R <series>      series: education | business | social
# Input: <series>/{summary,methods,trends}.csv from analyze_series.py.
# Output: PNGs in the DSH site (dist/images/blog/<series>-methods/) and <series>/post_stats.csv
# (the numbers quoted in the posts, with Fisher's exact tests and Benjamini-Hochberg q-values).
suppressPackageStartupMessages({library(ggplot2); library(dplyr); library(tidyr); library(readr); library(forcats); library(scales)})
series <- commandArgs(trailingOnly = TRUE)[1]
cfg <- list(
  education = list(noun = "education", short = c(teaching_learning = "Teaching & learning", online_learning = "Online learning", higher_education = "Higher & adult ed",
                    leadership_policy = "Leadership & policy", early_inclusive = "Early childhood & inclusive"), overall = "Education"),
  business = list(noun = "business", short = c(strategy = "Strategy & management", accounting_finance = "Accounting & finance", marketing = "Marketing",
                   ob_hrm = "OB & HRM", info_tech = "Information systems"), overall = "Business"),
  social = list(noun = "the social sciences & health", short = c(sociology = "Sociology", polisci = "Political science", economics = "Economics",
                 public_health = "Public health", nursing_health = "Nursing & health prof.", communication = "Communication"), overall = "Social sciences & health"))[[series]]
# Output: DSH_CHART_DIR if set; otherwise the DSH site's image folder when it sits next to this project; otherwise ../charts/.
site <- file.path("..", "..", "..", "..", "Dissertation Stats Helper", "standalone", "dist", "images", "blog", paste0(series, "-methods"))
out <- normalizePath(Sys.getenv("DSH_CHART_DIR", if (dir.exists(dirname(site))) site else file.path("..", "charts", paste0(series, "-methods"))), mustWork = FALSE)
dir.create(out, recursive = TRUE, showWarnings = FALSE)

plum <- "#543453"; coral <- "#F1553F"; cream <- "#FAF6F1"; mauve <- "#8A6E88"; rule <- "#E4D9D0"; deep <- "#6F5A6E"; pale <- "#CDBFCB"
short <- c(
  "Correlation" = "Correlation", "Mediation" = "Mediation", "Moderation / interactions" = "Moderation",
  "Linear / multiple / hierarchical regression" = "Linear regression", "Reliability (alpha, omega, ICC)" = "Reliability",
  "Machine learning / NLP" = "Machine learning / NLP", "Growth curve / trajectories" = "Growth models",
  "SEM / path analysis" = "SEM / path analysis", "Scale development / psychometric validation" = "Scale development",
  "ANOVA / ANCOVA / MANOVA" = "ANOVA family", "t test" = "t test", "Logistic / ordinal / multinomial regression" = "Logistic regression",
  "Multilevel / mixed-effects models" = "Multilevel models", "Chi-square / nonparametric" = "Chi-square / nonparametric",
  "Factor analysis (EFA/CFA)" = "Factor analysis", "Dyadic / APIM" = "Dyadic (APIM)", "Latent profile / class / mixture" = "Latent profile / class",
  "Network analysis (psychometric networks)" = "Network analysis", "Time series / dynamic models (VAR, DSEM)" = "Time series",
  "Text analysis (LIWC, sentiment, topic models)" = "Text analysis", "Bayesian" = "Bayesian", "Cluster analysis" = "Cluster analysis",
  "IRT / Rasch / DIF" = "IRT / Rasch", "Count models (Poisson, negative binomial)" = "Count models", "Survival / time-to-event" = "Survival analysis",
  "Missing data / multiple imputation" = "Missing data methods", "Power analysis reported" = "Power analysis",
  "Panel data / fixed effects" = "Panel data / fixed effects", "Causal designs (DiD, RDD, IV, synthetic control)" = "DiD, RDD, IV",
  "Propensity scores / matching" = "Propensity scores", "PLS-SEM" = "PLS-SEM", "Econometric time series (ARDL, GARCH, VECM)" = "Econometric time series",
  "Efficiency analysis (DEA, stochastic frontier)" = "Efficiency analysis (DEA)", "Qualitative comparative analysis (QCA)" = "QCA",
  "Spatial analysis / GIS" = "Spatial / GIS", "Conjoint / discrete choice" = "Conjoint / choice models")
subs <- cfg$short

summary <- read_csv(file.path(series, "summary.csv"), show_col_types = FALSE)
methods <- read_csv(file.path(series, "methods.csv"), show_col_types = FALSE) %>% mutate(label = short[method])
trends <- read_csv(file.path(series, "trends.csv"), show_col_types = FALSE) %>% mutate(label = short[method])
stopifnot(!anyNA(methods$label), !anyNA(trends$label))

fisher_p <- function(x1, n1, x2, n2) mapply(function(a, b, c, d) fisher.test(matrix(c(a, b - a, c, d - c), 2))$p.value, x1, n1, x2, n2)
methods <- methods %>% mutate(p_vs_rest = if_else(subfield == "all", NA_real_, fisher_p(x_quant, n_quant, coalesce(rest_x, 0), coalesce(rest_n, 1)))) %>%
  group_by(subfield) %>% mutate(q_vs_rest = if (all(is.na(p_vs_rest))) NA_real_ else p.adjust(p_vs_rest, "BH")) %>% ungroup() %>%
  mutate(contrast = case_when(!is.na(q_vs_rest) & q_vs_rest < .05 & share_quant > rest_share_quant ~ "More common than elsewhere",
                              !is.na(q_vs_rest) & q_vs_rest < .05 ~ "Less common than elsewhere", TRUE ~ "No clear difference"))
trends <- trends %>% mutate(early_share = early_x / early_n, late_share = late_x / late_n, p = fisher_p(early_x, early_n, late_x, late_n)) %>%
  group_by(subfield) %>% mutate(q = p.adjust(p, "BH")) %>% ungroup()
write_csv(left_join(methods, trends %>% select(subfield, method, early_x, early_n, late_x, late_n, early_share, late_share, p_trend = p, q_trend = q),
                    by = c("subfield", "method")), file.path(series, "post_stats.csv"))

source_line <- function(n) sprintf("Source: OpenAlex, %s English-language dissertation and thesis abstracts, 2021–2026  ·  dissertationstatshelper.com", comma(n))
theme_dsh <- function(base = 11) {
  theme_minimal(base_size = base, base_family = "Arial") +
    theme(plot.background = element_rect(fill = cream, colour = NA), panel.background = element_rect(fill = cream, colour = NA),
          text = element_text(colour = plum), axis.text = element_text(colour = deep), axis.title = element_text(colour = deep, size = rel(.9)),
          plot.title = element_text(family = "Georgia", size = rel(1.55), colour = plum, margin = margin(b = 4)),
          plot.subtitle = element_text(colour = deep, size = rel(.98), margin = margin(b = 12), lineheight = 1.15),
          plot.caption = element_text(colour = mauve, size = rel(.72), hjust = 0, margin = margin(t = 12)), plot.caption.position = "plot",
          plot.title.position = "plot", panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
          panel.grid.major.x = element_line(colour = rule, linewidth = .4), legend.position = "top", legend.justification = "left",
          legend.text = element_text(colour = deep, size = rel(.85)), legend.title = element_blank(), legend.box = "vertical", legend.box.just = "left",
          legend.spacing.y = unit(2, "pt"), plot.margin = margin(22, 26, 16, 22), strip.text = element_text(family = "Georgia", colour = plum, size = rel(1.05), hjust = 0))
}
save <- function(p, name, h = 1000) ggsave(file.path(out, name), p, device = ragg::agg_png, width = 1600, height = h, units = "px", dpi = 200, bg = cream)
file_key <- function(key) gsub("_", "-", key)
long <- setNames(summary$label, summary$subfield)
n_groups <- length(subs)

methods_chart <- function(key, title) {
  d <- methods %>% filter(subfield == key) %>% slice_max(share_quant, n = 12, with_ties = FALSE) %>% mutate(label = fct_reorder(label, share_quant))
  n_all <- summary$abstracts[summary$subfield == key]
  rest <- sprintf("Rest of %s (other %s areas)", cfg$noun, c("two", "three", "four", "five", "six")[n_groups - 2])
  ggplot(d, aes(y = label)) +
    geom_col(aes(x = share_quant, fill = contrast), width = .68) +
    geom_point(data = function(x) filter(x, !is.na(rest_share_quant)), aes(x = rest_share_quant, shape = rest), size = 2.6, colour = plum, fill = cream, stroke = .9) +
    geom_text(aes(x = pmax(share_quant, coalesce(rest_share_quant, 0)) + .006, label = percent(share_quant, 1)), hjust = 0, size = 3.3, colour = plum, family = "Arial") +
    scale_fill_manual(values = c("More common than elsewhere" = coral, "No clear difference" = plum, "Less common than elsewhere" = pale),
                      breaks = c("More common than elsewhere", "No clear difference", "Less common than elsewhere")) +
    scale_shape_manual(values = setNames(21, rest)) +
    scale_x_continuous(labels = percent_format(1), expand = expansion(mult = c(0, .1))) +
    guides(fill = guide_legend(order = 1, nrow = 1), shape = guide_legend(order = 2)) +
    labs(title = title, subtitle = sprintf("Share of the %s abstracts that name at least one quantitative method", comma(d$n_quant[1])),
         x = NULL, y = NULL, caption = paste0(source_line(n_all), "\nColour marks differences that hold after a false-discovery-rate correction (q < .05).")) +
    theme_dsh()
}
trend_chart <- function(key, title) {
  d <- trends %>% filter(subfield == key, early_x + late_x >= 15) %>% slice_max(early_x + late_x, n = 12, with_ties = FALSE) %>%
    mutate(sig = factor(if_else(q < .05, if_else(late_share > early_share, "Rose (q < .05)", "Fell (q < .05)"), "No clear change"),
                        levels = c("Rose (q < .05)", "Fell (q < .05)", "No clear change")), label = fct_reorder(label, late_share))
  n_all <- summary$abstracts[summary$subfield == key]
  ggplot(d, aes(y = label)) +
    geom_segment(aes(x = early_share, xend = late_share, yend = label, colour = sig), linewidth = 1.6, lineend = "round") +
    geom_point(aes(x = early_share), shape = 21, size = 2.8, colour = mauve, fill = cream, stroke = 1) +
    geom_point(aes(x = late_share, fill = sig), shape = 21, colour = cream, size = 3.3, stroke = .6, show.legend = FALSE) +
    scale_fill_manual(values = c("Rose (q < .05)" = coral, "Fell (q < .05)" = plum, "No clear change" = plum), drop = FALSE) +
    scale_colour_manual(values = c("Rose (q < .05)" = coral, "Fell (q < .05)" = mauve, "No clear change" = pale), drop = TRUE,
                        breaks = c("Rose (q < .05)", "Fell (q < .05)", "No clear change")) +
    scale_x_continuous(labels = percent_format(.1), expand = expansion(mult = c(.02, .06))) +
    labs(title = title, subtitle = sprintf("Share of all abstracts naming each method: 2021–22 (open circle, n = %s) vs. 2025–26 (filled, n = %s)",
                                           comma(d$early_n[1]), comma(d$late_n[1])),
         x = NULL, y = NULL, caption = paste0(source_line(n_all), "\nFisher's exact tests with a false-discovery-rate correction across all methods tested.")) +
    theme_dsh()
}

for (key in names(subs)) {
  save(methods_chart(key, sprintf("%s: the methods abstracts name", long[[key]])), sprintf("%s-methods.png", file_key(key)), 1080)
  save(trend_chart(key, sprintf("%s: what changed since 2021", long[[key]])), sprintf("%s-trends.png", file_key(key)), 1000)
}

# Overview chart 1: fingerprint across areas.
top <- methods %>% filter(subfield == "all") %>% slice_max(share_quant, n = 14, with_ties = FALSE)
d <- methods %>% filter(subfield %in% names(subs), method %in% top$method) %>%
  mutate(sub = factor(subs[subfield], levels = subs), label = factor(label, levels = rev(short[top$method])),
         txt = if_else(share_quant >= .16, cream, plum), hi = contrast == "More common than elsewhere")
p <- ggplot(d, aes(x = sub, y = label)) +
  geom_tile(aes(fill = share_quant), colour = cream, linewidth = 1.4) +
  geom_tile(data = filter(d, hi), fill = NA, colour = coral, linewidth = 1.1, width = .9, height = .82) +
  geom_text(aes(label = percent(share_quant, 1), colour = txt), size = 3.2, family = "Arial") +
  scale_fill_gradient(low = "#F1E8E1", high = plum, labels = percent_format(1), guide = "none") + scale_colour_identity() +
  scale_x_discrete(position = "top", labels = function(x) gsub(" & ", " &\n", x)) +
  labs(title = "Each area has its own methods fingerprint",
       subtitle = sprintf("Share of each area's method-naming abstracts that name the method.\nCoral outline: more common than in the other %s areas (q < .05).", c("two", "three", "four", "five", "six")[n_groups - 2]),
       x = NULL, y = NULL, caption = source_line(summary$abstracts[summary$subfield == "all"])) +
  theme_dsh() + theme(panel.grid.major.x = element_blank(), axis.text.x.top = element_text(colour = plum, face = "bold", size = 9, lineheight = .95),
                      plot.subtitle = element_text(size = 9.6))
save(p, sprintf("%s-fingerprint.png", series), 1400)

# Overview chart 2: design mix by area.
dm <- summary %>% filter(subfield %in% names(subs)) %>%
  transmute(sub = factor(subs[subfield], levels = rev(subs)), `Names a quant. method` = quant_share,
            Qualitative = `Qualitative (thematic, IPA, grounded theory, interviews)`, `Survey / questionnaire` = `Survey / questionnaire study`,
            Experiment = `Experiment / randomized design`) %>%
  pivot_longer(-sub) %>% mutate(name = factor(name, levels = c("Names a quant. method", "Qualitative", "Survey / questionnaire", "Experiment")))
overall <- summary %>% filter(subfield == "all")
ov <- tibble(name = factor(levels(dm$name), levels = levels(dm$name)),
             value = c(overall$quant_share, overall$`Qualitative (thematic, IPA, grounded theory, interviews)`, overall$`Survey / questionnaire study`, overall$`Experiment / randomized design`))
p <- ggplot(dm, aes(x = value, y = sub)) +
  geom_vline(data = ov, aes(xintercept = value), colour = coral, linewidth = .8, linetype = "22") +
  geom_col(fill = plum, width = .62) +
  geom_label(aes(label = percent(value, 1)), hjust = -.12, size = 3.1, colour = plum, fill = cream, linewidth = 0, label.padding = unit(1.5, "pt"), family = "Arial") +
  facet_wrap(~name, nrow = 1, scales = "free_x") +
  scale_x_continuous(labels = percent_format(1), expand = expansion(mult = c(0, .32)), breaks = pretty_breaks(3)) +
  labs(title = "Most abstracts don't name a statistical method", subtitle = sprintf("Share of all abstracts in each area. Dashed coral line: %s overall.", tolower(cfg$overall)),
       x = NULL, y = NULL, caption = source_line(overall$abstracts)) +
  theme_dsh() + theme(panel.spacing.x = unit(18, "pt"), axis.text.x = element_text(size = 7.5), strip.text = element_text(size = 9.5))
save(p, sprintf("%s-design-mix.png", series), 900)

save(methods_chart("all", sprintf("%s: the methods abstracts name", cfg$overall)) + guides(fill = "none", shape = "none") +
       labs(caption = source_line(overall$abstracts)) + aes(fill = "No clear difference"), sprintf("%s-methods.png", series), 1000)
save(trend_chart("all", sprintf("%s overall: what changed since 2021", cfg$overall)), sprintf("%s-trends.png", series), 1000)
# Overview chart 3: US-tagged abstracts vs. everything else.
us_n <- summary %>% filter(subfield %in% c("us", "other"))
d <- methods %>% filter(subfield %in% c("us", "other"), method %in% top$method[1:12]) %>%
  select(subfield, label, share_quant, q_vs_rest) %>% pivot_wider(names_from = subfield, values_from = c(share_quant, q_vs_rest)) %>%
  mutate(sig = if_else(q_vs_rest_us < .05, "Differs (q < .05)", "No clear difference"), label = fct_reorder(label, share_quant_other))
p <- ggplot(d, aes(y = label)) +
  geom_segment(aes(x = share_quant_other, xend = share_quant_us, yend = label, colour = sig), linewidth = 1.6, lineend = "round") +
  geom_point(aes(x = share_quant_other), shape = 21, size = 3, colour = plum, fill = cream, stroke = 1) +
  geom_point(aes(x = share_quant_us), shape = 21, size = 3.3, colour = cream, fill = coral, stroke = .6) +
  scale_colour_manual(values = c("Differs (q < .05)" = coral, "No clear difference" = pale)) +
  scale_x_continuous(labels = percent_format(1), expand = expansion(mult = c(.02, .06))) +
  labs(title = "US-tagged abstracts look different",
       subtitle = sprintf("Share of method-naming abstracts: US-tagged institutions (coral, n = %s)\nvs. other or unknown country (open, n = %s)",
                          comma(us_n$quant_n[us_n$subfield == "us"]), comma(us_n$quant_n[us_n$subfield == "other"])),
       x = NULL, y = NULL, caption = paste0(source_line(overall$abstracts), "\nOpenAlex records the institution's country for a minority of works, so \"other\" includes many US works too.")) +
  theme_dsh()
save(p, sprintf("%s-us-contrast.png", series), 1000)
cat("charts written to", out, "\n")
