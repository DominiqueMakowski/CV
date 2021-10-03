# ------------------------------
# Scholar data
# ------------------------------
library(dplyr)
library(scholar)
library(ggplot2)
library(forcats)
library(patchwork)
library(see)

data_scholar <- list()

data_scholar[["date"]] <- format(Sys.time(), "%d %B %Y")
data_scholar[["scholar_stats"]] <- scholar::get_profile("bg0BZ-QAAAAJ")
data_scholar[["scholar_history"]] <- scholar::get_citation_history("bg0BZ-QAAAAJ")
data_scholar[["scholar_publications"]] <-  scholar::get_publications("bg0BZ-QAAAAJ", flush = TRUE) |>
  mutate(author = scholar::get_complete_authors("bg0BZ-QAAAAJ", pubid))


data_scholar[["scholar_data"]] <-  data_scholar[["scholar_publications"]]  %>%
  dplyr::filter(year > 1950) %>%
  dplyr::group_by(year) %>%
  dplyr::summarise(
    Publications = n(),
    # Citations = sum(cites)
  ) %>%
  dplyr::mutate(
    Publications = cumsum(Publications)
    # Citations = cumsum(Citations)
  ) %>%
  dplyr::rename(Year = year) %>%
  tidyr::gather(Index, Number, -Year) %>%
  dplyr::mutate(Index = forcats::fct_rev(Index)) %>%
  rbind(data_scholar[["scholar_history"]] %>%
          dplyr::rename(Number = cites,
                        Year = year) %>%
          mutate(Index = "Citations",
                 Number = cumsum(Number)))




# Publications individual
data <- data_scholar[["scholar_publications"]] %>%
  mutate(Authors = paste0(lapply(stringr::str_split(author, " "), `[[`, 2)),
         Authors = stringr::str_to_title(stringr::str_remove_all(Authors, ",")),
         Publication = paste0(Authors, " (", year),
         Journal = stringr::str_to_title(journal))


# Disambiguate unique
suffix <- letters
suffix[1] <- ""
for(i in 1:nrow(data)){
  pub <- data$Publication[i]
  j <- 1
  while(paste0(pub, suffix[j]) %in% data$Publication[1:i-1]){
    j <- j + 1
  }
  data$Publication[i] <- paste0(pub, suffix[j])
}

data_scholar[["scholar_publications"]] <- data %>%
  mutate(Publication = paste0(Publication, ")"),
         Publication = fct_reorder(Publication, cites, .desc = TRUE)) %>%
  filter(Publication != "Makowski (2013)")


save(data_scholar, file="data/data_scholar.Rdata")




# p2 <- data_scholar$scholar_publications %>%
#   ggplot(aes(x = cites)) +
#   geom_histogram(bins = 30) +
#   geom_density(aes(y = 3 * stat(count)), bw="SJ") +
#   see::theme_modern() +
#   theme(
#     strip.background = element_blank(),
#     axis.title = element_text(face = "plain", size = 16),
#     legend.position = "none"
#   )
# p2

# p1 / p2
# ggsave(paste0(path, "img/plot_impact.png"), p1, dpi=450, width=10, height=8)
# ggsave(paste0(path, "img/plot_citations.png"), p2, dpi=450, width=10, height=4)
