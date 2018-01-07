# import data from disk
classic <- read.csv("~/Dev/Data/fantagazzetta_stats/lineups_classic.csv")
seriea <- read.csv("~/Dev/Data/fantagazzetta_stats/lineups_seriea.csv")
ekstraklasa <- read.csv("~/Dev/Data/fantagazzetta_stats/lineups_ekstraklasa.csv")
ICDQCMAS_seriea <- read.csv("~/Dev/Data/fantagazzetta_stats/lineups_ICDQCMAS_table_seriea.csv")
ICDQCMAS_classic <- read.csv("~/Dev/Data/fantagazzetta_stats/lineups_ICDQCMAS_table_classic.csv")
ICDQCMAS_ekstraklasa <- read.csv("~/Dev/Data/fantagazzetta_stats/lineups_ICDQCMAS_table_ekstraklasa.csv")

library(ggplot2)
library(scales)
# bar plot
moduli <- function(df, title) {
  levels(df$Risultato) <- c("Sconfitta", "Pareggio", "Vittoria")
  df$Modulo <- as.factor(df$Modulo)
  ggplot(data=df, aes(x=Modulo, fill=Risultato)) +
    geom_bar(stat="count") +
    ggtitle(title)
}
# box plot
modulibox <- function(df, title) {
  levels(df$Risultato) <- c("Sconfitta", "Pareggio", "Vittoria")
  df$Modulo <- as.factor(df$Modulo)
  ggplot(data=df, aes(Modulo, Punti)) +
    geom_boxplot() +
    ggtitle(title)
}

moduli(classic, "Classic")
modulibox(classic, "Classic")

moduli(ekstraklasa, "Ekstraklasa")
modulibox(ekstraklasa, "Ekstraklasa")

moduli(seriea, "Serie A")
modulibox(seriea, "Serie A")

library(gmodels)
with(seriea, CrossTable(Modulo, Squadra, missing.include=TRUE))

# extract by modulo
modulo352 <- seriea[seriea$Modulo == 352,]
modulo4231 <- seriea[seriea$Modulo == 4231,]

# calculates ICDQCMAS index from non optimized and optimized lineups
ICDQCMAS <- function(df, df2) {
  df$ICDQCMAS_index <- df$Fantapunti / df2$Fantapunti
  return(df)
}

ekstraklasa <- ICDQCMAS(ekstraklasa, ICDQCMAS_ekstraklasa)
seriea <- ICDQCMAS(seriea, ICDQCMAS_seriea)

# sum all values for each team
library(plyr)
vertical.sum <- function(df){
  # new variables for team record
  df$W <- ifelse(df$Risultato == "Vittoria", 1, 0)
  df$T <- ifelse(df$Risultato == "Pareggio", 1, 0)
  df$L <- ifelse(df$Risultato == "Sconfitta", 1, 0)
  # vertical sum of duplicate teams
  df <- ddply(df, "Squadra", numcolwise(sum))
  # put together assist numbers
  df$Assist <- df$Assist + df$Assist.da.fermo
  # remove other columns
  df$Assist.da.fermo <- NULL
  df$Modulo <- NULL
  df$Modulo.applicato <- NULL
  df$X <- NULL
  return(df)
}
ekstraklasa.vertical <- vertical.sum(ekstraklasa)
seriea.vertical <- vertical.sum(seriea)
classic.vertical <- vertical.sum(classic)

table.fg <- function(df){
  df$Classifica <- df$W*3 + df$T
  df$Ammonizione <- NULL
  df$Assist <- NULL
  df$Autorete <- NULL
  df$Espulsione <- NULL
  df$Fantapunti <- df$Fantapunti / (df$W + df$T + df$L)
  df$ICDQCMAS_index <- df$ICDQCMAS_index / (df$W + df$T + df$L)
  df$Goal <- NULL
  df$Goal.subito <- NULL
  df$Malus <- NULL
  df$Punti <- NULL
  df$Rigore.parato <- NULL
  df$Rigore.sbagliato <- NULL
  df$Rigore.segnato <- NULL
  return(df)
}

ekstraklasa.table <- table.fg(ekstraklasa.vertical)
seriea.table <- table.fg(seriea.vertical)

# offense scatterplot
scatter.goal <- function(df) {
  library(ggrepel)
  ggplot(df, aes(x=Goal, y=W, label=Squadra)) +
    geom_point(shape=1) +
    geom_point(color = 'red') +
    geom_text_repel()
}
scatter.goal(classic.vertical)
scatter.goal(ekstraklasa.vertical)
scatter.goal(seriea.vertical)
