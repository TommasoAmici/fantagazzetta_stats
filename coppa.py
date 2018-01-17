'''
coppa.py:

For each team finds the players with the most appearances,
calculates the preferred formation for each coach
'''

import collections
from constants import *
from fantagazzetta_stats import *


# creates players object from counter to run through functions later
def parse_play_counter(counter):
    players = []
    for player in counter:
        parsed_player = fg_player(name=player[0], 
                                  roles=list(player[1]), 
                                  fantavoto=counter[player],
                                  voto=counter[player],
                                  bench=False)
        players.append(parsed_player)
    return players


# calculates appearances for players
def calc_preferred_players(team, lineups):
    # selects data for team
    all_lineups = [l for l in lineups if l.team_name == team]
    all_players = [l.players for l in all_lineups]
    # flatten list of players
    flat_list_players = [item for sublist in all_players for item in sublist]
    players = [(p.name, tuple(p.roles)) for p in flat_list_players if p.bench == False]
    players_counter = collections.Counter(players)
    return parse_play_counter(players_counter)


# from pandas dataframe of all the matches
# calculates most common formation
# calculates appearances for players
def parse_coaches(df, lineups):
    coaches = []
    # calculates most frequent formation for each team
    teams = df.Squadra.unique()
    for team in teams:
        # preferred formation
        formation_counts = df[df.Squadra == team]["formation"].value_counts()
        pref_formation = formation_counts.idxmax()
        # preferred players
        pref_players = calc_preferred_players(team, lineups)
        coach = fg_lineup(team_name=team, formation=pref_formation, players=pref_players)
        coaches.append(coach)
    return coaches


# generate preferred lineups for each coach
# most common formation by mode
# players that best fit the formation, weighted by appearances
def preferred_lineup(coaches, mantra):
    coaches_lineups = []
    for coach in coaches:
        if mantra:
            score, names = best11(coach, FORMATIONSMANTRA[coach.formation], mantra)
        else:
            score, names = best11(coach, FORMATIONSCLASSIC[coach.formation], mantra)            
        coaches_lineups.append(fg_lineup(players=names, formation=coach.formation, formation_applied=coach.formation, points=score, team_name=coach.team_name))
    return coaches_lineups


# create pandas dataframe with data from fantagazzetta
# matching players and their stats
def cup_pandas(lineups, league):
    directory = os.getcwd() + "/csvs/"
    make_sure_path_exists(directory)
    xl_voti = pd.ExcelFile("Statistiche_Fantacalcio_2017-18_Fantagazzetta.xlsx")
    df_voti = xl_voti.parse("Tutti")
    # append lineups to pandas dataframe
    df = pd.DataFrame({"Giocatori":[p.name.upper() for l in lineups for p in l.players],
                       "formation": [l.formation for l in lineups for p in l.players],
                       "Squadra": [l.team_name for l in lineups for p in l.players]})
    df = df.merge(df_voti, how='left', left_on='Giocatori', right_on='Nome')
    df.to_csv(directory + "coppa_di_sosta_{}.csv".format(league), sep=",")
    return df


def main():
    # prepare files
    mantra, html_files, league = prepare_files()
    # parse files
    matches, lineups = parse_files(html_files)
    # write data to .csv and returns pandas dataframes
    matches_df, lineups_df, lineups_ICDQCMAS_df = write_to_csv(matches, lineups, league, mantra)
    coaches = parse_coaches(lineups_df, lineups)
    preferred_lineups = preferred_lineup(coaches, mantra)
    cup_df = cup_pandas(preferred_lineups, league)


main()