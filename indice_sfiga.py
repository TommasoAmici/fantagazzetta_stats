# misurare quanto il tuo avversario overperforma 
# (something something santi beati) la sua media, in media

import pandas as pd
import os


def vert_sum(df):
    num_matches = len(df.index) / len(df.Squadra.unique())
    df = df[["Squadra", "Fantapunti"]]
    # vertical sum
    df = df.groupby(df.Squadra).sum()
    df.Fantapunti = df.Fantapunti / num_matches
    return df.to_dict()


def parse_matches(team, df):
    df_home = df.loc[df['Squadra casa'] == team][["Squadra fuori casa", "Fantapunti fuori casa"]]
    df_home.columns = ["Squadra", "Fantapunti giornata"]
    df_away = df.loc[df['Squadra fuori casa'] == team][["Squadra casa", "Fantapunti casa"]]
    df_away.columns = ["Squadra", "Fantapunti giornata"]
    df_final = pd.concat([df_home, df_away])
    return df_final


def calc_sfiga_index(matches, teams):
    matches_teams = list(matches["Squadra"])
    avg_points = [teams["Fantapunti"][team] for team in matches_teams]
    matches["Media fantapunti"] = avg_points
    matches["Net rating"] = matches["Fantapunti giornata"] - matches["Media fantapunti"]
    return matches["Net rating"].mean()


def calc_sfiga(df, df_matches):
    sfiga_index = []
    teams_total = vert_sum(df)
    teams = df.Squadra.unique()
    for team in teams:
        total_matches = parse_matches(team, df_matches)
        sfiga_index.append(calc_sfiga_index(total_matches, teams_total))
    df = pd.DataFrame({"Squadre": teams, "Sfiga": sfiga_index})
    return df


def main():
    cwd = os.getcwd() + "/csvs/"
    # read data from disk
    ek = pd.read_csv(cwd + "lineups_ekstraklasa.csv")
    sa = pd.read_csv(cwd + "lineups_seriea.csv")
    cl = pd.read_csv(cwd + "lineups_classic.csv")
    ek_matches = pd.read_csv(cwd + "matches_ekstraklasa.csv")
    sa_matches = pd.read_csv(cwd + "matches_seriea.csv")
    cl_matches = pd.read_csv(cwd + "matches_classic.csv")
    # calculates index and writes to csv
    df1 = calc_sfiga(ek, ek_matches)
    df2 = calc_sfiga(sa, sa_matches)
    df_classic = calc_sfiga(cl, cl_matches)
    df_mantra = pd.concat([df1, df2])
    df_mantra.to_csv(cwd + "sfiga_mantra.csv", sep=",")
    df_classic.to_csv(cwd + "sfiga_classic.csv", sep=",")
    print("All good in the hood!")


main()