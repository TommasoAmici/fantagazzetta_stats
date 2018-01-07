from bs4 import BeautifulSoup
from requests import get
import pandas as pd
import os
import errno


# constants from FG HTML
FG_BONUSES = {"gol subito": -1,
              "malus": -0.5,
              "assist": 1,
              "assist da fermo": 1,
              "gol fatto": 3,
              "ammonizione": -0.5,
              "espulsione": -1,
              "rigore sbagliato": -3,
              "rigore segnato": 3,
              "rigore parato": 3,
              "autorete": -3}

MODULIMANTRA = {
    "343": [["Por"], ["Dc"], ["Dc"], ["Dc"],
            ["E"], ["E"], ["M", "C"], ["M", "C"],
            ["W", "A"], ["W", "A"], ["Pc", "A"]],
    "3412": [["Por"], ["Dc"], ["Dc"], ["Dc"],
             ["E"], ["E"], ["M", "C"], ["M", "C"],
             ["Pc", "A"], ["Pc", "A"], ["T"]],
    "3421": [["Por"], ["Dc"], ["Dc"], ["Dc"],
             ["E"], ["E"], ["M", "C"], ["M", "C"],
             ["T", "W"], ["T", "W"], ["Pc", "A"]],
    "352": [["Por"], ["Dc"], ["Dc"], ["Dc"],
            ["E"], ["E", "W"], ["M", "C"], ["M", "C"],
            ["M"], ["Pc", "A"], ["Pc", "A"]],
    "442": [["Por"], ["Ds"], ["Dc"], ["Dc"],
            ["Dd"], ["E", "W"], ["E", "W"], ["M", "C"],
            ["M"], ["Pc", "A"], ["Pc", "A"]],
    "433": [["Por"], ["Ds"], ["Dc"], ["Dc"],
            ["Dd"], ["M", "C"], ["M", "C"],
            ["M"], ["Pc", "A"], ["W", "A"], ["W", "A"]],
    "4312": [["Por"], ["Ds"], ["Dc"], ["Dc"],
             ["Dd"], ["M", "C"], ["M", "C"],
             ["M"], ["Pc", "A"], ["Pc", "A"], ["T"]],
    "4321": [["Por"], ["Ds"], ["Dc"], ["Dc"],
             ["Dd"], ["M", "C"], ["M", "C"],
             ["M"], ["Pc", "A"], ["T", "W"], ["T", "W"]],
    "4231": [["Por"], ["Ds"], ["Dc"], ["Dc"],
             ["Dd"], ["M"], ["M", "C"],
             ["Pc", "A"], ["T", "W"], ["T", "W"], ["T"]],
    "4411": [["Por"], ["Ds"], ["Dc"], ["Dc"],
             ["Dd"], ["M"], ["M", "C"],
             ["E", "W"], ["E", "W"], ["Pc", "A"], ["T"]],
    "4222": [["Por"], ["Ds"], ["Dc"], ["Dc"],
             ["Dd"], ["M"], ["M"],
             ["W"], ["T"], ["Pc", "A"], ["A"]]
}

MODULICLASSIC = {
    "343": [["P"], ["D"], ["D"], ["D"],
            ["C"], ["C"], ["C"], ["C"],
            ["A"], ["A"], ["A"]],
    "352": [["P"], ["D"], ["D"], ["D"],
            ["C"], ["C"], ["C"], ["C"], ["C"],
            ["A"], ["A"]],
    "442": [["P"], ["D"], ["D"], ["D"],
            ["D"], ["C"], ["C"], ["C"],
            ["C"], ["A"], ["A"]],
    "433": [["P"], ["D"], ["D"], ["D"],
            ["D"], ["C"], ["C"],
            ["C"], ["A"], ["A"], ["A"]],
    "451": [["P"], ["D"], ["D"], ["D"],
            ["D"], ["C"], ["C"],
            ["C"], ["C"], ["C"], ["A"]],
    "532": [["P"], ["D"], ["D"], ["D"],
            ["D"], ["D"], ["C"],
            ["C"], ["C"], ["A"], ["A"]],
    "541": [["P"], ["D"], ["D"], ["D"],
            ["D"], ["D"], ["C"],
            ["C"], ["C"], ["C"], ["A"]]
}


class fg_player(object):
    """class to store a player's performance"""

    def __init__(self, name="", team="", roles=[], bonus={}, fantavoto=0, bench=False, voto=0, malus=False):
        super(fg_player, self).__init__()
        self.name = name.title()
        self.team = team
        self.roles = roles
        self.bonus = bonus
        self.fantavoto = fantavoto
        self.voto = voto
        self.bench = bench
        self.malus = malus

    def fantavoto_no_malus(self):
        if self.malus == False:
            return self.fantavoto - self.bonus.get("malus", 0)
        else:
            return self.fantavoto


class fg_match(object):
    """stores information about a whole match, both home and away stats"""

    def __init__(self,
                 score,
                 home_team_name,
                 away_team_name,
                 home_players,
                 away_players,
                 home_modulo,
                 away_modulo,
                 home_modulo_applicato,
                 away_modulo_applicato,
                 home_date,
                 away_date,
                 home_result,
                 away_result):
        super(fg_match, self).__init__()
        self.score = score
        self.home_team_name = home_team_name
        self.away_team_name = away_team_name
        self.home_players = home_players
        self.away_players = away_players
        self.home_modulo = home_modulo
        self.away_modulo = away_modulo
        self.home_modulo_applicato = home_modulo_applicato
        self.away_modulo_applicato = away_modulo_applicato
        self.home_date = home_date
        self.away_date = away_date
        self.home_result = home_result
        self.away_result = away_result

    # returns total score for match given home or away team
    def total_points(self, players):
        total = 0.0
        for player in players:
            if player.bench is False:
                total += player.voto
            else:
                continue
        return total

    def total_fantapoints(self, players):
        total = 0.0
        for player in players:
            if player.bench is False:
                total += player.fantavoto
            else:
                continue
        return total

    # returns number of bonus for match, given home/away team
    # e.g. get_bonus(home_players, "gol fatto") returns total number of goals
    def get_bonus(self, players, bonus):
        goals = 0
        for p in players:
            if p.bench is False:
                goals += p.bonus.get(bonus, 0)
            else:
                continue
        return goals


class fg_lineup(object):
    """stores stats for a single team in a match"""
    def __init__(self, team_name="", result="", players=[],
                 modulo="", modulo_applicato="", date="", points=0):
        super(fg_lineup, self).__init__()
        self.team_name = team_name
        self.players = players
        self.modulo = modulo
        self.modulo_applicato = modulo_applicato
        self.result = result
        self.date = date
        self.points = points

    # returns total score for lineup given home or away team
    def total_points(self):
        total = 0.0
        for player in self.players:
            if player.bench is False:
                total += player.voto
            else:
                continue
        return total

    def total_fantapoints(self):
        total = 0.0
        for player in self.players:
            if player.bench is False:
                total += player.fantavoto
            else:
                continue
        return total

    # returns number of bonus for lineup, given home/away team
    # e.g. get_bonus(home_players, "gol fatto") returns total number of goals
    def get_bonus(self, bonus):
        b = 0
        for p in self.players:
            if p.bench is False:
                b += p.bonus.get(bonus, 0)
            else:
                continue
        return b

    def calculate_goals(self):
        return ((self.points - 66) // 4) + 1


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
    try:
        pts = player.find_all("td", attrs={"class": "pt"})
        fantavoto = float(pts[2].text.replace(",", "."))
    except Exception as e:
        fantavoto = None
    voto = parse_voto(bonus, fantavoto)
    return fg_player(name, team, roles, bonus, fantavoto, bench, voto)


# parses matchday lineup, returns list of fg_players and other info
def parse_lineup(lineup):
    modulo = lineup.find("th", attrs={"class": "thcol3 aleft"}).text[7:]
    if len(modulo) != 3 and len(modulo) != 4:
        modulo = "None"
    try:
        modulo_applicato = lineup.find(
            "td", attrs={"class": "bold  bblu aright"}).text
    except Exception as e:
        modulo_applicato = modulo
    if lineup.find("td", attrs={"colspan": "6"}).text == "Formazione non inserita":
        return [], modulo, modulo_applicato, "No date"
    else:
        date_lineup = lineup.find("td", attrs={"colspan": "6"}).text
    players = []
    for player in lineup.find_all("tr", attrs={"class": "playerrow"}):
        bench = False
        if "bnc" in player.get("class"):
            bench = True
        players.append(parse_player(player, bench))
    return players, modulo, modulo_applicato, date_lineup


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
    home_players, home_modulo, home_modulo_applicato, home_date = parse_lineup(
        lineups[0])
    away_players, away_modulo, away_modulo_applicato, away_date = parse_lineup(
        lineups[1])
    fg_teams.append(fg_lineup(home_team, home_result, home_players,
                              home_modulo, home_modulo_applicato, home_date))
    fg_teams.append(fg_lineup(away_team, away_result, away_players,
                              away_modulo, away_modulo_applicato, away_date))

    return fg_match(score,
                    home_team, away_team,
                    home_players, away_players,
                    home_modulo, away_modulo,
                    home_modulo_applicato, away_modulo_applicato,
                    home_date, away_date,
                    home_result, away_result)


# if no player available for modulo, applies malus
# reference table_malus.jpg
def find_role_malus(role, modulo):
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
    elif role == "W" and modulo in ["352", "442", "4411"]:
        return ["E", "Dd", "Dc", "Ds", "M"]
    elif role == "W" and modulo not in ["352", "442", "4411"]:
        return ["E", "Dd", "Dc", "Ds", "M", "C"]
    elif role == "T":
        return ["E", "Dd", "Dc", "Ds", "M", "C"]
    elif role == "A":
        return ["E", "Dd", "Dc", "Ds", "M", "C", "W", "T"]
    elif role == "Pc":
        return ["E", "Dd", "Dc", "Ds", "M", "C", "W", "T"]


# finds best player for given modulo
def best11(lineup, modulo, mantra):
    best_names = []
    best_roles = []
    best_players = []
    players = [
        p for p in lineup.players if p.fantavoto is not None and p.fantavoto > 0]
    total = 0.0
    max_malus = 0
    for roles in modulo:
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
        if highest.fantavoto is None or highest.fantavoto == 0 and max_malus < 3 and mantra:
            for role in roles:
                # finds roles that can be filled with a malus
                for r_malus in find_role_malus(role, modulo):
                    for player in players:
                        for r in player.roles:
                            if r in r_malus and player.fantavoto >= highest.fantavoto and player.name not in best_names:
                                highest = player
                                highest.malus = True
                                max_malus += 1
        best_names.append(highest.name)
        best_players.append(highest)
        best_roles.append(role)
        total += highest.fantavoto_no_malus()
    return total, best_players


# finds best modulo for given lineup
def best_lineup(lineup, moduli, mantra):
    highest_score = 0
    best_11 = []
    best_modulo = ""
    for m in moduli:
        score, names = best11(lineup, moduli[m], mantra)
        if score >= highest_score:
            highest_score = score
            best_11 = names
            best_modulo = m
    return fg_lineup(players=best_11, modulo=best_modulo, modulo_applicato=best_modulo, points=highest_score, team_name=lineup.team_name)


# print best lineups for each week
def print_best_lineup(lineup, moduli, mantra):
    lineup = best_lineup(lineup, moduli, mantra)
    print(lineup.team_name)
    print("Fantapunti: {}\t Modulo: {}".format(lineup.points, lineup.modulo))
    best_11 = [p.name + ' *' if p.malus else p.name for p in lineup.players]
    print(best_11, "\n\n")


def print_best_lineups(lineups, mantra=True):
    matchday = 1
    loop_count = 0
    for l in lineups:
        if loop_count % 10 == 0:
            print("\nICDQCMAS GIORNATA {}\n".format(matchday))
            matchday += 1
        if mantra:
            print_best_lineup(l, MODULIMANTRA, mantra)
        else:
            print_best_lineup(l, MODULICLASSIC, mantra)
        loop_count += 1


# creates list of pairs from list
# s -> (s0, s1), (s2, s3), (s4, s5), ...
def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


# calculates and prints table based on best lineups, instead of actual lineups
def ICDQCMAS_table(lineups, mantra=True):
    # calcuates best lineup for each match
    if mantra:
        lineups = [best_lineup(l, MODULIMANTRA, mantra) for l in lineups]
    else:
        lineups = [best_lineup(l, MODULICLASSIC, mantra) for l in lineups]
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
    df = pd.DataFrame({"Modulo": [l.modulo for l in lineups],
                       "Modulo applicato": [l.modulo_applicato for l in lineups],
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


# creates pandas data frame and writes matches to .csv
def matches_pandas(matches, league, directory):
    # append matches to pandas dataframe
    df = pd.DataFrame({"Modulo casa": [m.home_modulo for m in matches],
                       "Modulo applicato casa": [m.home_modulo_applicato for m in matches],
                       "Risultato casa": [m.home_result for m in matches],
                       "Squadra casa": [m.home_team_name for m in matches],
                       "Punti casa": [m.total_points(m.home_players) for m in matches],
                       "Fantapunti casa": [m.total_fantapoints(m.home_players) for m in matches],
                       "Modulo fuori casa": [m.away_modulo for m in matches],
                       "Modulo applicato fuori casa": [m.away_modulo_applicato for m in matches],
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


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def main():
    # prepare files to read
    league = input("Enter league (folder) name: ")
    num_matchdays = int(input("Enter number of files: "))
    mantra = input("M for Mantra, C for classic: ")
    if mantra.lower() == "c":
        mantra = False
    else:
        mantra = True
    html_files = ["{}/{}.html".format(league, p)
                  for p in range(1, num_matchdays + 1)]
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
    # write data to .csv
    directory = os.getcwd() + "/csvs/"
    make_sure_path_exists(directory)
    matches_pandas(matches, league, directory)
    lineups_pandas(lineups, league, directory)
    # calculates and prints table based on best lineups, instead of actual lineups
    best_lineups = ICDQCMAS_table(lineups, mantra)
    lineups_pandas(best_lineups, "ICDQCMAS_table_" + league, directory)
    # print best lineups
    # print_best_lineups(lineups)


main()
