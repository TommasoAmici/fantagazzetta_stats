# calculates average points in week
ek.icdq <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_ekstraklasa.csv")
ek <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ekstraklasa.csv")
sa.icdq <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_seriea.csv")
sa <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_seriea.csv")
cl.icdq <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_classic.csv")
cl <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_classic.csv")


chunks.avg.points <- function(df) {
  n <- nrow(df) / 10
  giornate <- split(df, factor(sort(rank(row.names(df)) %% n)))
  avg.fantapunti <- c()
  for (g in giornate) {
    avg.fantapunti <- c(avg.fantapunti, mean(g$Fantapunti))
  }
  return(avg.fantapunti)
}

avg.punti.ek <- chunks.avg.points(ek)
avg.punti.sa <- chunks.avg.points(sa)
avg.punti.cl <- chunks.avg.points(cl)
avg.punti.ek.icdq <- chunks.avg.points(ek.icdq)
avg.punti.sa.icdq <- chunks.avg.points(sa.icdq)
avg.punti.cl.icdq <- chunks.avg.points(cl.icdq)

library(ggplot2)
plot.vector <- function(df, title) {
  qplot(1:length(df), df, xlab = "Giornate", ylab = "Media fantapunti", main = title) +
    geom_smooth()
}

plot.icdqcmas <- function(df, df.icdq, title) {
  df.plot <- data.frame(df, df.icdq)
  df.plot$x <- 1:length(df)
  ggplot(df.plot, aes(x), main = title) +
    geom_point(aes(y = df)) +
    geom_smooth(aes(y = df, colour = "Normale")) +
    geom_point(aes(y = df.icdq)) +
    geom_smooth(aes(y = df.icdq, colour = "ICDQCMAS")) +
    ggtitle(title) +
    labs(y = "Media fantapunti", x = "Giornate") +
    scale_colour_manual(name = "Legenda", values = c("blue", "red"))
}


plot.vector(avg.punti.ek, "Ekstraklasa")
plot.vector(avg.punti.sa, "Serie A")
plot.vector(avg.punti.cl, "Classic")
plot.vector(avg.punti.ek.icdq, "Ekstraklasa ICDQCMAS")
plot.vector(avg.punti.sa.icdq, "Serie A ICDQCMAS")
plot.vector(avg.punti.cl.icdq, "Classic ICDQCMAS")

plot.icdqcmas(avg.punti.ek, avg.punti.ek.icdq, "Ekstraklasa")
plot.icdqcmas(avg.punti.sa, avg.punti.sa.icdq, "Serie A")
plot.icdqcmas(avg.punti.cl, avg.punti.cl.icdq, "Classic")