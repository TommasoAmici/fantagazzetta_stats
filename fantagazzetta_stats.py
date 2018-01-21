from bs4 import BeautifulSoup
from requests import get
import pandas as pd
import os
import errno
from constants import *


# parse web page from URL
def make_soup(url):
    page = get(url)
    if page.status_code != 200:
        return None
    return BeautifulSoup(page.text, "html.parser")


# get matches from page
def get_matches(soup):
    matches = []
    for match in soup.find_all("div", attrs={"class": "itemBox"}):
        matches.append(match)
    return matches


# calculates regular vote from fantasy vote and bonuses
def parse_voto(bonus, fantavoto):
    voto = fantavoto
    if voto is None:
        return None
    for b in bonus:
        voto = voto - FG_BONUSES[b] * bonus[b]
    return voto


# parse player row, return player class
def parse_player(player, bench):
    # gets roles of player
    roles = []
    for role in player.find_all("span", attrs={"class": "role"}):
        if role.text in roles:
            continue
        else:
            roles.append(role.text)
    name = player.find("a", attrs={"title": "Statistiche calciatore"}).text
    # gets bonuses for player and updates dictionary
    bonus = {}
    for icon in player.find_all("img"):
        i = icon.get("alt", "")
        bonus[i] = bonus.get(i, 0) + 1
    team = player.find("td", attrs={"class": "pt aleft"}).text
    # gets votes for player
    try:
        pts = player.find_all("td", attrs={"class": "pt"})
        fantavoto = float(pts[2].text.replace(",", "."))
    except Exception as e:
        fantavoto = None
    voto = parse_voto(bonus, fantavoto)
    return fg_player(name, team, roles, bonus, fantavoto, bench, voto)


# parses matchday lineup, returns list of fg_players and other info
def parse_lineup(lineup):
    formation = lineup.find("th", attrs={"class": "thcol3 aleft"}).text[7:]
    if len(formation) != 3 and len(formation) != 4:
        formation = "None"
    try:
        formation_applied = lineup.find(
            "td", attrs={"class": "bold  bblu aright"}).text
    except Exception as e:
        formation_applied = formation
    if lineup.find("td", attrs={"colspan": "6"}).text == "Formazione non inserita":
        return [], formation, formation_applied, "No date"
    else:
        date_lineup = lineup.find("td", attrs={"colspan": "6"}).text
    players = []
    for player in lineup.find_all("tr", attrs={"class": "playerrow"}):
        bench = False
        if "bnc" in player.get("class"):
            bench = True
        players.append(parse_player(player, bench))
    return players, formation, formation_applied, date_lineup


# from scoreline (e.g. "3-1") to results
def parse_score(score):
    if int(score[0]) > int(score[2]):
        return "Vittoria", "Sconfitta"
    elif int(score[0]) == int(score[2]):
        return "Pareggio", "Pareggio"
    else:
        return "Sconfitta", "Vittoria"


def parse_match(soup, fg_teams):
    # header
    score = soup.find("h3", attrs={"class": "numbig3"}).text
    home_result, away_result = parse_score(score)
    home_team = soup.find("div", attrs={"class": "col-lg-5"}).text
    away_team = soup.find("div", attrs={"class": "col-lg-5 aright"}).text

    # columns
    lineups = []
    for lineup in soup.find_all("div", attrs={"class": "col-lg-6 col-md-6 col-sm-6 col-xs-6 greybox"}):
        lineups.append(lineup)
    home_players, home_formation, home_formation_applied, home_date = parse_lineup(
        lineups[0])
    away_players, away_formation, away_formation_applied, away_date = parse_lineup(
        lineups[1])
    fg_teams.append(fg_lineup(home_team, home_result, home_players,
                              home_formation, home_formation_applied, home_date))
    fg_teams.append(fg_lineup(away_team, away_result, away_players,
                              away_formation, away_formation_applied, away_date))

    return fg_match(score,
                    home_team, away_team,
                    home_players, away_players,
                    home_formation, away_formation,
                    home_formation_applied, away_formation_applied,
                    home_date, away_date,
                    home_result, away_result)


# if no player available for formation, applies malus
# reference table_malus.jpg
def find_role_malus(role, formation):
    if role == "Por":
        return []
    elif role == "Ds":
        return ["Dc", "Dd"]
    elif role == "Dd":
        return ["Dc", "Ds"]
    elif role == "Dc":
        return ["Ds", "Dd"]
    elif role == "E":
        return ["M", "Dd", "Dc", "Ds"]
    elif role == "M":
        return ["E", "Dd", "Dc", "Ds"]
    elif role == "C":
        return ["E", "Dd", "Dc", "Ds"]
    elif role == "W" and formation in ["352", "442", "4411"]:
        return ["E", "Dd", "Dc", "Ds", "M"]
    elif role == "W" and formation not in ["352", "442", "4411"]:
        return ["E", "Dd", "Dc", "Ds", "M", "C"]
    elif role == "T":
        return ["E", "Dd", "Dc", "Ds", "M", "C"]
    elif role == "A":
        return ["E", "Dd", "Dc", "Ds", "M", "C", "W", "T"]
    elif role == "Pc":
        return ["E", "Dd", "Dc", "Ds", "M", "C", "W", "T"]


# copies value from fg_player object A to B
def clone_player(highest, player, r, role):
    highest.name = player.name
    highest.team = player.team
    highest.roles = player.roles
    highest.bonus = player.bonus
    highest.fantavoto = player.fantavoto
    highest.voto = player.voto
    highest.bench = player.bench
    if r != role:
        highest.malus = True
    else:
        highest.malus = False
    return highest


# finds best player for given formation
def best11(lineup, formation, mantra):
    best_names = []
    best_roles = []
    best_players = []
    players = [
        p for p in lineup.players if p.fantavoto is not None and p.fantavoto > 0]
    total = 0.0
    max_malus = 0
    for roles in formation:
        highest = fg_player()
        # each role can have multiple roles, e.g. M/C
        for role in roles:
            # finds best fitting player for role
            for player in players:
                # players can have multiple roles
                for r in player.roles:
                    if r in role and player.fantavoto >= highest.fantavoto and player.name not in best_names:
                        highest = player
        # if no player fills role, apply malus
        if mantra:
            if highest.fantavoto == 0 and max_malus < 3:
                for role in roles:
                    # finds roles that can be filled with a malus
                    if find_role_malus(role, formation) is None:
                        continue
                    for r_malus in find_role_malus(role, formation):
                        for player in players:
                            for r in player.roles:
                                if ((r in r_malus and player.fantavoto >= highest.fantavoto and player.name not in best_names) and max_malus < 3):
                                    highest = clone_player(highest, player, r, role)
                                else:
                                    continue
                if highest.malus:
                    max_malus += 1
        best_names.append(highest.name)
        best_players.append(highest)
        best_roles.append(role)
        total += highest.fantavoto_no_malus()
    return total, best_players


# finds best formation for given lineup
def best_lineup(lineup, formations, mantra):
    highest_score = 0
    best_11 = []
    best_formation = ""
    for m in formations:
        score, names = best11(lineup, formations[m], mantra)
        if score >= highest_score:
            highest_score = score
            best_11 = names
            best_formation = m
    return fg_lineup(players=best_11, formation=best_formation, formation_applied=best_formation, points=highest_score, team_name=lineup.team_name)


# print best lineups for each week
def print_best_lineup(lineup, formations, mantra):
    lineup = best_lineup(lineup, formations, mantra)
    print(lineup.team_name)
    print("Fantapunti: {}\t formation: {}".format(lineup.points, lineup.formation))
    best_11 = [p.name + ' *' if p.malus else p.name for p in lineup.players]
    print(best_11, "\n\n")


def print_best_lineups(lineups, mantra):
    matchday = 1
    loop_count = 0
    for l in lineups:
        if loop_count % 10 == 0:
            print("\nICDQCMAS GIORNATA {}\n".format(matchday))
            matchday += 1
        if mantra:
            print_best_lineup(l, FORMATIONSMANTRA, mantra)
        else:
            print_best_lineup(l, FORMATIONSCLASSIC, mantra)
        loop_count += 1


# creates list of pairs from list
# s -> (s0, s1), (s2, s3), (s4, s5), ...
def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


# calculates and prints table based on best lineups, instead of actual lineups
def ICDQCMAS_table(lineups, mantra):
    # calcuates best lineup for each match
    if mantra:
        lineups = [best_lineup(l, FORMATIONSMANTRA, mantra) for l in lineups]
    else:
        lineups = [best_lineup(l, FORMATIONSCLASSIC, mantra) for l in lineups]
    # no bench in optimal lineups
    for lineup in lineups:
        for player in lineup.players:
            player.bench = False
    for l, m in pairwise(lineups):
        if l.calculate_goals() > m.calculate_goals():
            l.result = "Vittoria"
            m.result = "Sconfitta"
        elif l.calculate_goals() < m.calculate_goals():
            m.result = "Vittoria"
            l.result = "Sconfitta"
        elif l.calculate_goals() == m.calculate_goals():
            m.result = "Pareggio"
            l.result = "Pareggio"
    return lineups


# creates pandas data frame and writes lineups to .csv
def lineups_pandas(lineups, league, directory):
    # append lineups to pandas dataframe
    df = pd.DataFrame({"Modulo": [l.formation for l in lineups],
                       "Modulo applicato": [l.formation_applied for l in lineups],
                       "Risultato": [l.result for l in lineups],
                       "Squadra": [l.team_name for l in lineups],
                       "Punti": [l.total_points() for l in lineups],
                       "Fantapunti": [l.total_fantapoints() for l in lineups],
                       "Goal": [l.get_bonus("gol fatto") for l in lineups],
                       "Goal subito": [l.get_bonus("gol subito") for l in lineups],
                       "Autorete": [l.get_bonus("autorete") for l in lineups],
                       "Assist": [l.get_bonus("assist") for l in lineups],
                       "Assist da fermo": [l.get_bonus("assist da fermo") for l in lineups],
                       "Ammonizione": [l.get_bonus("ammonizione") for l in lineups],
                       "Espulsione": [l.get_bonus("espulsione") for l in lineups],
                       "Rigore segnato": [l.get_bonus("rigore segnato") for l in lineups],
                       "Rigore sbagliato": [l.get_bonus("rigore sbagliato") for l in lineups],
                       "Rigore parato": [l.get_bonus("rigore parato") for l in lineups],
                       "Malus": [l.get_bonus("malus") for l in lineups]})
    df.to_csv(directory + "lineups_{}.csv".format(league), sep=",")
    return df


# creates pandas data frame and writes matches to .csv
def matches_pandas(matches, league, directory):
    # append matches to pandas dataframe
    df = pd.DataFrame({"Modulo casa": [m.home_formation for m in matches],
                       "Modulo applicato casa": [m.home_formation_applied for m in matches],
                       "Risultato casa": [m.home_result for m in matches],
                       "Squadra casa": [m.home_team_name for m in matches],
                       "Punti casa": [m.total_points(m.home_players) for m in matches],
                       "Fantapunti casa": [m.total_fantapoints(m.home_players) for m in matches],
                       "Modulo fuori casa": [m.away_formation for m in matches],
                       "Modulo applicato fuori casa": [m.away_formation_applied for m in matches],
                       "Risultato fuori casa": [m.away_result for m in matches],
                       "Squadra fuori casa": [m.away_team_name for m in matches],
                       "Punti fuori casa": [m.total_points(m.away_players) for m in matches],
                       "Fantapunti fuori casa": [m.total_fantapoints(m.away_players) for m in matches],
                       "Risultato": [m.score for m in matches],
                       "Goal casa": [m.get_bonus(m.home_players, "gol fatto") for m in matches],
                       "Goal fuori casa": [m.get_bonus(m.away_players, "gol fatto") for m in matches],
                       "Goal subito casa": [m.get_bonus(m.home_players, "gol subito") for m in matches],
                       "Goal subito fuori casa": [m.get_bonus(m.away_players, "gol subito") for m in matches],
                       "Autorete casa": [m.get_bonus(m.home_players, "autorete") for m in matches],
                       "Autorete fuori casa": [m.get_bonus(m.away_players, "autorete") for m in matches],
                       "Assist casa": [m.get_bonus(m.home_players, "assist") for m in matches],
                       "Assist fuori casa": [m.get_bonus(m.away_players, "assist") for m in matches],
                       "Assist da fermo casa": [m.get_bonus(m.home_players, "assist da fermo") for m in matches],
                       "Assist da fermo fuori casa": [m.get_bonus(m.away_players, "assist da fermo") for m in matches],
                       "Ammonizione casa": [m.get_bonus(m.home_players, "ammonizione") for m in matches],
                       "Ammonizione fuori casa": [m.get_bonus(m.away_players, "ammonizione") for m in matches],
                       "Espulsione casa": [m.get_bonus(m.home_players, "espulsione") for m in matches],
                       "Espulsione fuori casa": [m.get_bonus(m.away_players, "espulsione") for m in matches],
                       "Rigore segnato casa": [m.get_bonus(m.home_players, "rigore segnato") for m in matches],
                       "Rigore segnato fuori casa": [m.get_bonus(m.away_players, "rigore segnato") for m in matches],
                       "Rigore sbagliato casa": [m.get_bonus(m.home_players, "rigore sbagliato") for m in matches],
                       "Rigore sbagliato fuori casa": [m.get_bonus(m.away_players, "rigore sbagliato") for m in matches],
                       "Rigore parato casa": [m.get_bonus(m.home_players, "rigore parato") for m in matches],
                       "Rigore parato fuori casa": [m.get_bonus(m.away_players, "rigore parato") for m in matches],
                       "Malus casa": [m.get_bonus(m.home_players, "malus") for m in matches],
                       "Malus fuori casa": [m.get_bonus(m.away_players, "malus") for m in matches]})
    df.to_csv(directory + "matches_{}.csv".format(league), sep=",")
    return df


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def prepare_files():
    # prepare files to read
    league = input("Enter league (folder) name: ")
    try:
        num_matchdays = int(input("Enter number of files: "))
    except:
        # max number of days in league
        num_matchdays = 38
    mantra = input("M for Mantra, C for classic: ")
    if mantra.lower() == "c":
        mantra = False
    else:
        mantra = True
    html_files = ["{}/{}.html".format(league, p)
                  for p in range(1, num_matchdays + 1)]
    return mantra, html_files, league


def parse_files(html_files):
    # parse lineups
    matches = []
    lineups = []
    for file in html_files:
        try:
            raw_data = open(file, 'r')
        except Exception as e:
            print("File {} does not exist".format(file))
            continue
        matches_soup = get_matches(BeautifulSoup(raw_data, "html.parser"))
        for match in matches_soup:
            matches.append(parse_match(match, lineups))
        raw_data.close()
    return matches, lineups


# write data frames to csv
def write_to_csv(matches, lineups, league, mantra):
    directory = os.getcwd() + "/csvs/"
    make_sure_path_exists(directory)
    matches_df = matches_pandas(matches, league, directory)
    lineups_df = lineups_pandas(lineups, league, directory)
    # calculates and prints table based on best lineups, instead of actual lineups
    best_lineups = ICDQCMAS_table(lineups, mantra)
    lineups_ICDQCMAS_df = lineups_pandas(best_lineups, "ICDQCMAS_table_" + league, directory)
    return matches_df, lineups_df, lineups_ICDQCMAS_df


def main():
    # prepare files
    mantra, html_files, league = prepare_files()
    # parse files
    matches, lineups = parse_files(html_files)
    # write data to .csv and returns pandas dataframes
    matches_df, lineups_df, lineups_ICDQCMAS_df = write_to_csv(matches, lineups, league, mantra)
    # print best lineups to screen
    print_best_lineups(lineups, mantra)


main()

