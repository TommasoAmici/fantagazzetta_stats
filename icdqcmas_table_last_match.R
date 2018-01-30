# creates ICDQCMAS table for last matchday

ek.icdq <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_ekstraklasa.csv")
ek <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ekstraklasa.csv")
sa.icdq <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_seriea.csv")
sa <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_seriea.csv")
cl.icdq <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_ICDQCMAS_table_classic.csv")
cl <- read.csv("~/Dev/Data/fantagazzetta_stats/csvs/lineups_classic.csv")

select.last.match <- function(df) {
  df <- tail(df, 10)
  df1 <- data.frame(df$Squadra, df$Fantapunti)
  return(df1)
}

join.df <- function(df, df.icdq) {
  df <- select.last.match(df)
  df.icdq <- select.last.match(df.icdq)
  df.final <- merge(df, df.icdq, by = "df.Squadra")
  df.final$ICDQCMAS.index <- df.final$df.Fantapunti.x / df.final$df.Fantapunti.y
  df.final$ICDQCMAS.abs <- df.final$df.Fantapunti.y - df.final$df.Fantapunti.x
  names(df.final) <- c("Squadra", "Fantapunti", "Fantapunti ICDQCMAS", "ICDQCMAS Index", "ICDQCMAS Assoluto")
  return(df.final)
}

ek <- join.df(ek, ek.icdq)
sa <- join.df(sa, sa.icdq)

all <- rbind(ek, sa)