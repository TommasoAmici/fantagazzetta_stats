# exploration for best formation

df <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_classic.csv")
# select team
df <- df[df$Squadra == "SS Condom",]
df$Modulo <- as.factor(df$Modulo)
df$Modulo.applicato <- as.factor(df$Modulo.applicato)

library(plyr)
vertical.sum <- function(df){
  # new variables for team record
  df$W <- ifelse(df$Risultato == "Vittoria", 1, 0)
  df$T <- ifelse(df$Risultato == "Pareggio", 1, 0)
  df$L <- ifelse(df$Risultato == "Sconfitta", 1, 0)
  df$TOT <- df$T + df$W + df$L
  # vertical sum of duplicate teams
  df <- ddply(df, "Modulo", numcolwise(sum))
  # put together assist numbers
  df$Assist <- df$Assist + df$Assist.da.fermo
  # remove other columns
  df$Assist.da.fermo <- NULL
  df$X <- NULL
  df$Media.fantapunti <- df$Fantapunti / df$TOT
  return(df)
}

df <- vertical.sum(df)