# Charts for the Dissertation Stats Helper blog series "Methods in psychology dissertations".
# Input: psych_subfields/{summary,methods,trends}.csv from analyze_subfields.py.
# Output: PNGs in the DSH site (dist/images/blog/psych-methods/) and psych_subfields/post_stats.csv
# (the numbers quoted in the posts, with Benjamini-Hochberg q-values per subfield and test family).
suppressPackageStartupMessages({library(ggplot2); library(dplyr); library(tidyr); library(readr); library(forcats); library(scales)})

here <- normalizePath(".")
# Output: DSH_CHART_DIR if set; otherwise the DSH site's image folder when it sits next to this project; otherwise charts/.
site <- file.path(here, "..", "..", "..", "Dissertation Stats Helper", "standalone", "dist", "images", "blog", "psych-methods")
out <- normalizePath(Sys.getenv("DSH_CHART_DIR", if (dir.exists(dirname(site))) site else file.path(here, "charts", "psych-methods")), mustWork = FALSE)
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
  "Missing data / multiple imputation" = "Missing data methods", "Power analysis reported" = "Power analysis")
subs <- c(clinical = "Clinical", social = "Social", developmental_educational = "Developmental & educational",
          experimental_cognitive = "Experimental & cognitive", applied = "Applied")

summary <- read_csv("psych_subfields/summary.csv", show_col_types = FALSE)
methods <- read_csv("psych_subfields/methods.csv", show_col_types = FALSE) %>% mutate(label = short[method])
trends <- read_csv("psych_subfields/trends.csv", show_col_types = FALSE) %>% mutate(label = short[method])
stopifnot(!anyNA(methods$label), !anyNA(trends$label))

# Fisher's exact tests (robust for rare methods), one family per subfield and question, adjusted with Benjamini-Hochberg.
fisher_p <- function(x1, n1, x2, n2) mapply(function(a, b, c, d) fisher.test(matrix(c(a, b - a, c, d - c), 2))$p.value, x1, n1, x2, n2)
all_q <- methods %>% filter(subfield == "all") %>% select(method, all_x = x_quant, all_n = n_quant)
methods <- methods %>% left_join(all_q, by = "method") %>%
  mutate(p_vs_rest = if_else(subfield == "all", NA_real_, fisher_p(x_quant, n_quant, all_x - x_quant, all_n - n_quant)))
trends <- trends %>% mutate(p = fisher_p(early_x, early_n, late_x, late_n))
methods <- methods %>% group_by(subfield) %>% mutate(q_vs_rest = if (all(is.na(p_vs_rest))) NA_real_ else p.adjust(p_vs_rest, "BH")) %>% ungroup() %>%
  mutate(contrast = case_when(!is.na(q_vs_rest) & q_vs_rest < .05 & share_quant > rest_share_quant ~ "More common than elsewhere",
                              !is.na(q_vs_rest) & q_vs_rest < .05 ~ "Less common than elsewhere",
                              TRUE ~ "No clear difference"))
trends <- trends %>% group_by(subfield) %>% mutate(q = p.adjust(p, "BH")) %>% ungroup()
write_csv(left_join(methods, trends %>% select(subfield, method, early_x, early_n, late_x, late_n, early_share, late_share, p_trend = p, q_trend = q),
                    by = c("subfield", "method")), "psych_subfields/post_stats.csv")

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
          legend.text = element_text(colour = deep, size = rel(.85)), legend.title = element_blank(), legend.box = "vertical", legend.box.just = "left", legend.spacing.y = unit(2, "pt"), plot.margin = margin(22, 26, 16, 22),
          strip.text = element_text(family = "Georgia", colour = plum, size = rel(1.05), hjust = 0))
}
save <- function(p, name, h = 1000) ggsave(file.path(out, name), p, device = ragg::agg_png, width = 1600, height = h, units = "px", dpi = 200, bg = cream)

# Per-subfield chart 1: the methods named most, against the rest of psychology.
methods_chart <- function(key) {
  d <- methods %>% filter(subfield == key) %>% slice_max(share_quant, n = 12, with_ties = FALSE) %>% mutate(label = fct_reorder(label, share_quant))
  n_q <- d$n_quant[1]; n_all <- summary$abstracts[summary$subfield == key]
  ggplot(d, aes(y = label)) +
    geom_col(aes(x = share_quant, fill = contrast), width = .68) +
    geom_point(data = function(x) filter(x, !is.na(rest_share_quant)), aes(x = rest_share_quant, shape = "Rest of psychology (other four subfields)"), size = 2.6, colour = plum, fill = cream, stroke = .9) +
    geom_text(aes(x = pmax(share_quant, coalesce(rest_share_quant, 0)) + .006, label = percent(share_quant, 1)), hjust = 0, size = 3.3, colour = plum, family = "Arial") +
    scale_fill_manual(values = c("More common than elsewhere" = coral, "No clear difference" = plum, "Less common than elsewhere" = pale),
                      breaks = c("More common than elsewhere", "No clear difference", "Less common than elsewhere")) +
    scale_shape_manual(values = c("Rest of psychology (other four subfields)" = 21)) +
    scale_x_continuous(labels = percent_format(1), expand = expansion(mult = c(0, .1))) +
    guides(fill = guide_legend(order = 1, nrow = 1), shape = guide_legend(order = 2)) +
    labs(title = sprintf("%s psychology: the methods abstracts name", c(subs, all = "All")[[key]]),
         subtitle = sprintf("Share of the %s abstracts that name at least one quantitative method", comma(n_q)),
         x = NULL, y = NULL, caption = paste0(source_line(n_all), "\nColour marks differences that hold after a false-discovery-rate correction (q < .05).")) +
    theme_dsh()
}

# Chart 2: what changed between 2021-22 and 2025-26 (share of all abstracts).
trend_chart <- function(key, title) {
  d <- trends %>% filter(subfield == key, early_x + late_x >= 15) %>% slice_max(early_x + late_x, n = 12, with_ties = FALSE) %>%
    mutate(sig = factor(if_else(q < .05, if_else(late_share > early_share, "Rose (q < .05)", "Fell (q < .05)"), "No clear change"),
                        levels = c("Rose (q < .05)", "Fell (q < .05)", "No clear change")),
           label = fct_reorder(label, late_share))
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
  save(methods_chart(key), sprintf("%s-methods.png", gsub("_", "-", key)), 1080)
  save(trend_chart(key, sprintf("%s psychology: what changed since 2021", subs[[key]])), sprintf("%s-trends.png", gsub("_", "-", key)), 1000)
}

# Hub chart 1: method fingerprint across subfields.
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
  labs(title = "Each subfield has its own methods fingerprint",
       subtitle = "Share of each subfield's method-naming abstracts that name the method.
Coral outline: more common than in the other four subfields (q < .05).",
       x = NULL, y = NULL, caption = source_line(summary$abstracts[summary$subfield == "all"])) +
  theme_dsh() + theme(panel.grid.major.x = element_blank(), axis.text.x.top = element_text(colour = plum, face = "bold", size = 9.5, lineheight = .95),
                      plot.subtitle = element_text(size = 9.6))
save(p, "psychology-fingerprint.png", 1400)

# Hub chart 2: design mix by subfield.
dm <- summary %>% filter(subfield != "all") %>%
  transmute(sub = factor(subs[subfield], levels = rev(subs)), `Names a quantitative method` = quant_share,
            `Qualitative` = `Qualitative (thematic, IPA, grounded theory, interviews)`, `Experiment` = `Experiment / randomized design`,
            `Review or meta-analysis` = `Systematic review / meta-analysis`) %>%
  pivot_longer(-sub) %>% mutate(name = factor(name, levels = c("Names a quantitative method", "Qualitative", "Experiment", "Review or meta-analysis")))
overall <- summary %>% filter(subfield == "all")
ov <- tibble(name = factor(levels(dm$name), levels = levels(dm$name)),
             value = c(overall$quant_share, overall$`Qualitative (thematic, IPA, grounded theory, interviews)`, overall$`Experiment / randomized design`, overall$`Systematic review / meta-analysis`))
p <- ggplot(dm, aes(x = value, y = sub)) +
  geom_vline(data = ov, aes(xintercept = value), colour = coral, linewidth = .8, linetype = "22") +
  geom_col(fill = plum, width = .62) +
  geom_label(aes(label = percent(value, 1)), hjust = -.12, size = 3.1, colour = plum, fill = cream, linewidth = 0,
             label.padding = unit(1.5, "pt"), family = "Arial") +
  facet_wrap(~name, nrow = 1, scales = "free_x", labeller = as_labeller(function(x) sub("Names a quantitative method", "Names a quant. method", sub("Review or meta-analysis", "Review / meta-analysis", x)))) +
  scale_x_continuous(labels = percent_format(1), expand = expansion(mult = c(0, .32)), breaks = pretty_breaks(3)) +
  labs(title = "Most abstracts don't name a statistical method",
       subtitle = "Share of all abstracts in each subfield. Dashed coral line: psychology overall.", x = NULL, y = NULL,
       caption = source_line(overall$abstracts)) +
  theme_dsh() + theme(panel.spacing.x = unit(18, "pt"), axis.text.x = element_text(size = 7.5), strip.text = element_text(size = 9.5))
save(p, "psychology-design-mix.png", 900)

save(methods_chart("all") + labs(title = "Psychology dissertations: the methods abstracts name") + guides(fill = "none", shape = "none") +
       labs(caption = source_line(overall$abstracts)) + aes(fill = "No clear difference"), "psychology-methods.png", 1000)
save(trend_chart("all", "Psychology overall: what changed since 2021"), "psychology-trends.png", 1000)
cat("charts written to", out, "\n"); print(list.files(out))
