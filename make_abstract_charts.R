# Charts for the DSH post "How to write a dissertation abstract (APA 7)".
#   Rscript make_abstract_charts.R      (after python abstract_elements.py)
suppressPackageStartupMessages({library(ggplot2); library(dplyr); library(readr); library(forcats); library(scales)})
here <- normalizePath(".")
site <- file.path(here, "..", "..", "..", "Dissertation Stats Helper", "standalone", "dist", "images", "blog", "abstract-guide")
out <- normalizePath(Sys.getenv("DSH_CHART_DIR", if (dir.exists(dirname(site))) site else file.path(here, "charts", "abstract-guide")), mustWork = FALSE)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
plum <- "#543453"; coral <- "#F1553F"; cream <- "#FAF6F1"; mauve <- "#8A6E88"; rule <- "#E4D9D0"; deep <- "#6F5A6E"; pale <- "#CDBFCB"

el <- read_csv("abstract_guide/elements.csv", show_col_types = FALSE)
bins <- read_csv("abstract_guide/length_bins.csv", show_col_types = FALSE)
total <- el %>% filter(element == "Effect size") %>% summarise(n = sum(abstracts)) %>% pull(n)
source_line <- sprintf("Source: OpenAlex, %s English-language dissertation and thesis abstracts, 2021–2026  ·  dissertationstatshelper.com
Fields: psychology, education, business, and the social sciences & health.", comma(total))

theme_dsh <- function(base = 11) {
  theme_minimal(base_size = base, base_family = "Arial") +
    theme(plot.background = element_rect(fill = cream, colour = NA), panel.background = element_rect(fill = cream, colour = NA),
          text = element_text(colour = plum), axis.text = element_text(colour = deep), axis.title = element_text(colour = deep, size = rel(.9)),
          plot.title = element_text(family = "Georgia", size = rel(1.55), colour = plum, margin = margin(b = 4)),
          plot.subtitle = element_text(colour = deep, size = rel(.98), margin = margin(b = 12), lineheight = 1.15),
          plot.caption = element_text(colour = mauve, size = rel(.66), hjust = 0, margin = margin(t = 12), lineheight = 1.1), plot.caption.position = "plot",
          plot.title.position = "plot", panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
          panel.grid.major.x = element_line(colour = rule, linewidth = .4), legend.position = "none", plot.margin = margin(22, 26, 16, 22))
}
save <- function(p, name, h) ggsave(file.path(out, name), p, device = ragg::agg_png, width = 1600, height = h, units = "px", dpi = 200, bg = cream)

# 1. How often abstracts include each element APA asks for (all four fields pooled).
d <- el %>% filter(element != "Sample size and effect size") %>% group_by(element) %>% summarise(share = sum(x) / sum(abstracts), .groups = "drop") %>%
  mutate(stat = element %in% c("Sample size", "Effect size", "Confidence interval", "Statistical significance"), element = fct_reorder(element, share))
p <- ggplot(d, aes(x = share, y = element)) +
  geom_col(aes(fill = stat), width = .66) +
  geom_text(aes(label = percent(share, if_else(share < .02, .1, 1))), hjust = -.15, size = 3.4, colour = plum, family = "Arial") +
  scale_fill_manual(values = c(`TRUE` = coral, `FALSE` = plum)) +
  scale_x_continuous(labels = percent_format(1), expand = expansion(mult = c(0, .12))) +
  labs(title = "What dissertation abstracts include",
       subtitle = "Share of abstracts that include each element APA 7 recommends. Coral: the numbers JARS asks quantitative abstracts to report.",
       x = NULL, y = NULL, caption = paste0(source_line, "\nKeyword matching; elements phrased in other ways are missed, so treat these as lower bounds.")) +
  theme_dsh() + theme(plot.subtitle = element_text(size = 9.3))
save(p, "abstract-elements.png", 900)

# 2. How long abstracts are (all four fields pooled), against APA's 250 words and ProQuest's 350-word print limit.
h <- bins %>% group_by(bin_low) %>% summarise(n = sum(n), .groups = "drop") %>% mutate(over = bin_low >= 250)
over250 <- sum(h$n[h$bin_low >= 250]) / sum(h$n); over350 <- sum(h$n[h$bin_low >= 350]) / sum(h$n)
p <- ggplot(h, aes(x = bin_low + 5, y = n, fill = over)) +
  geom_col(width = 9) +
  geom_vline(xintercept = c(250, 350), colour = plum, linewidth = .6, linetype = c("solid", "22")) +
  annotate("text", x = 256, y = max(h$n) * 1.02, label = "APA: 250 words", hjust = 0, size = 3.3, colour = plum, family = "Arial") +
  annotate("text", x = 354, y = max(h$n) * .86, label = "ProQuest print limit\n(doctoral): 350 words", hjust = 0, size = 3.1, colour = deep, family = "Arial", lineheight = .95) +
  scale_fill_manual(values = c(`TRUE` = coral, `FALSE` = plum)) +
  scale_x_continuous(breaks = c(100, 200, 250, 300, 350, 400, 500, 600, 700, 800), labels = c("100", "200", "250", "300", "350", "400", "500", "600", "700", "800+"),
                     expand = expansion(mult = c(.01, .02))) +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, .05))) +
  labs(title = "Half of dissertation abstracts run past 250 words",
       subtitle = sprintf("Abstract length in words. %s exceed 250 words (coral); %s exceed 350.", percent(over250, 1), percent(over350, 1)),
       x = "Words in the abstract", y = "Abstracts", caption = paste0(source_line, "\nAbstracts of 60 words or fewer were excluded.")) +
  theme_dsh() + theme(panel.grid.major.y = element_line(colour = rule, linewidth = .4), panel.grid.major.x = element_blank())
save(p, "abstract-length.png", 950)
cat("charts written to", out, "\n")
