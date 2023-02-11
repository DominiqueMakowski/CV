library(dplyr)
library(ggplot2)


# Get dataframe with stats
get_stats <- function(data_scholar) {

  # Author position
  authors <- tolower(data_scholar$scholar_publications$author)
  authors <- strsplit(authors, ", ")
  position <- sapply(authors, function(x) {
    position <- which(x == "d makowski")
    if(position == 1) return("First")
    if(position == 2) return("Second")
    if(position == length(x)) return("Last")
    "Other"
    })

  position <- as.data.frame(t(as.matrix(table(position))))
  # Manual corrections --------------------
  # Nicolas & Makowski 2016
  position$Last <- position$Last - 1 #
  position$Second <- position$Second + 1
  # Sperduti & Makowski 2017 (fiction 2)
  position$First <- position$First + 1 #
  position$Second <- position$Second - 1

  # Stats
  data.frame(
    "n.Publications" = length(authors),
    "n.FirstAuthor" = position$First,
    "n.SecondAuthor" = position$Second,
    "n.LastAuthor" = position$Last,
    "H.index" = data_scholar$scholar_stats$h_index,
    "Citations" = data_scholar$scholar_stats$total_cites
  )
}

# Make plot with number of publications and number of citations
plot_impact <- function(data_scholar) {
  data <- data_scholar$scholar_data

  data |>
    dplyr::filter(Year >= 2014) %>%
    ggplot(aes(x = Year, y = Number)) +
    geom_bar(aes(alpha=Year), stat="identity") +
    geom_line(aes(colour = Index), linewidth = 2) +
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


# Make plot with number of publications and number of citations
plot_citations_per_paper <- function(data_scholar) {
  data <- data_scholar$scholar_data

  data_scholar[["scholar_publications"]]  %>%
    ggplot(aes(x = Publication, y = cites, label = Journal)) +
    geom_bar(aes(fill=Publication), stat="identity") +
    # geom_text(angle=90, y=1, hjust = 0) +
    see::theme_modern() +
    scale_fill_material_d(palette="rainbow", reverse=TRUE) +
    ylab("Number of citations") +
    scale_y_continuous(expand = c(0, 0), limits = c(0, NA)) +
    theme(
      # axis.title = element_text(face = "plain"),
      axis.title.x = element_blank(),
      axis.text.x = element_text(angle=45, hjust=1),
      legend.position = "none"
    )
}
