'''
constants.py: constants and classes for fantagazzetta_stats.py
'''

# constants of bonus images from FG HTML, using the alt of <img> tags
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

FORMATIONSMANTRA = {
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

FORMATIONSCLASSIC = {
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
            try:
                return self.fantavoto + self.bonus["malus"] * 0.5
            except:
                return self.fantavoto
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
                 home_formation,
                 away_formation,
                 home_formation_applied,
                 away_formation_applied,
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
        self.home_formation = home_formation
        self.away_formation = away_formation
        self.home_formation_applied = home_formation_applied
        self.away_formation_applied = away_formation_applied
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
        req_bonus = 0
        for p in players:
            if p.bench is False:
                req_bonus += p.bonus.get(bonus, 0)
            else:
                continue
        return req_bonus


class fg_lineup(object):
    """stores stats for a single team in a match"""
    def __init__(self, team_name="", result="", players=[],
                 formation="", formation_applied="", date="", points=0):
        super(fg_lineup, self).__init__()
        self.team_name = team_name
        self.players = players
        self.formation = formation
        self.formation_applied = formation_applied
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
        req_bonus = 0
        for p in self.players:
            if p.bench is False:
                req_bonus += p.bonus.get(bonus, 0)
            else:
                continue
        return req_bonus

    def calculate_goals(self):
        return ((self.points - 66) // 4) + 1
