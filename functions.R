# Make plot with number of publications and number of citations
plot_impact <- function(data_scholar) {
  data <- data_scholar$scholar_data

  data %>%
    filter(Year >= 2014) %>%
    ggplot(aes(x = Year, y = Number)) +
    geom_bar(aes(alpha=Year), stat="identity") +
    geom_line(aes(colour = Index), size = 2) +
    see::theme_modern() +
    ylab("") +
    scale_x_continuous(labels = as.character(data$Year), breaks = data$Year) +
    # scale_x_continuous(breaks = seq(min(stats$Year), max(stats$Year), by = 1)) +
    scale_color_manual(values = c("#2196F3", "#E91E63")) +
    facet_wrap(~Index, scales = "free", strip.position = "top") +
    theme(
      strip.background = element_blank(),
      strip.placement = "outside",
      # strip.text.y = element_blank(),
      strip.text = element_text(face = "plain", size = 16),
      axis.title = element_text(face = "plain", size = 16),
      axis.title.x = element_blank(),
      legend.position = "none"
    )
}
