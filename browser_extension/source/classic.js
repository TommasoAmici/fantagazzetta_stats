var MODULICLASSIC = [
	{
		modulo: "343", roles: [["P"], ["D"], ["D"], ["D"],
		["C"], ["C"], ["C"], ["C"],
		["A"], ["A"], ["A"]]
	},
	{
		modulo: "352", roles: [["P"], ["D"], ["D"], ["D"],
		["C"], ["C"], ["C"], ["C"], ["C"],
		["A"], ["A"]]
	},
	{
		modulo: "442", roles: [["P"], ["D"], ["D"], ["D"],
		["D"], ["C"], ["C"], ["C"],
		["C"], ["A"], ["A"]]
	},
	{
		modulo: "433", roles: [["P"], ["D"], ["D"], ["D"],
		["D"], ["C"], ["C"],
		["C"], ["A"], ["A"], ["A"]]
	},
	{
		modulo: "451", roles: [["P"], ["D"], ["D"], ["D"],
		["D"], ["C"], ["C"],
		["C"], ["C"], ["C"], ["A"]]
	},
	{
		modulo: "532", roles: [["P"], ["D"], ["D"], ["D"],
		["D"], ["D"], ["C"],
		["C"], ["C"], ["A"], ["A"]]
	},
	{
		modulo: "541", roles: [["P"], ["D"], ["D"], ["D"],
		["D"], ["D"], ["C"],
		["C"], ["C"], ["C"], ["A"]]
	}
];

class FG_BONUSES {
	constructor(golsubito = 0,
		malus = 0,
		assist = 0,
		assistdafermo = 0,
		golfatto = 0,
		ammonizione = 0,
		espulsione = 0,
		rigoresbagliato = 0,
		rigoresegnato = 0,
		rigoreparato = 0,
		autorete = 0,
		total = 0) {
		this.golsubito = golsubito;
		this.malus = malus;
		this.assist = assist;
		this.assistdafermo = assistdafermo;
		this.golfatto = golfatto;
		this.ammonizione = ammonizione;
		this.espulsione = espulsione;
		this.rigoresbagliato = rigoresbagliato;
		this.rigoresegnato = rigoresegnato;
		this.rigoreparato = rigoreparato;
		this.autorete = autorete;
		this.total = (this.golfatto * 3 - this.golsubito -
			this.malus * 0.5 + this.assist + this.assistdafermo +
			this.rigoreparato * 3 + this.rigoresegnato * 3 -
			this.rigoresbagliato * 3 - this.autorete * 3 -
			this.ammonizione * 0.5 - this.espulsione);
	}
};

class fgPlayer {
	constructor(name = "", team = "", roles = [], bonuses = new FG_BONUSES(), fantavoto = 0, voto = 0, bench = false, malus = false) {
		this.name = name;
		this.team = team;
		this.roles = roles;
		this.bonuses = bonuses;
		this.fantavoto = fantavoto;
		this.voto = voto;
		this.bench = bench;
		this.malus = malus;
	}
	get noMalus() {
		return this.calcMalus();
	}
	// return fantavoto with malus correctly applied
	calcMalus() {
		if (this.malus == false) {
			if (this.bonuses.malus == 1) {
				return this.fantavoto + 0.5;
			}
			else {
				return this.fantavoto;
			}
		} else {
			return this.fantavoto;
		}
	}
}

class fgLineup {
	constructor(players, modulo, points) {
		this.players = players;
		this.modulo = modulo;
		this.points = points;
	}
	get goalsScored() {
		return this.calcGoals();
	}
	calcGoals() {
		return (Math.floor((this.points - 66) / 4) + 1);
	}
}

String.prototype.toProperCase = function () {
	return this.replace(/\w\S*/g, function (txt) { return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase(); });
}

function countBonuses(imagesBonus) {
	var bonuses = new FG_BONUSES();
	for (let i = 0; i < imagesBonus.length; i++) {
		switch (imagesBonus[i]) {
			case "gol subito":
				bonuses.golsubito += 1;
				break;
			case "malus":
				bonuses.malus += 1;
				break;
			case "assist":
				bonuses.assist += 1;
				break;
			case "assist da fermo":
				bonuses.assistdafermo += 1;
				break;
			case "gol fatto":
				bonuses.golfatto += 1;
				break;
			case "ammonizione":
				bonuses.ammonizione += 1;
				break;
			case "espulsione":
				bonuses.espulsione += 1;
				break;
			case "rigore sbagliato":
				bonuses.rigoresbagliato += 1;
				break;
			case "rigore segnato":
				bonuses.rigoresegnato += 1;
				break;
			case "rigore parato":
				bonuses.rigoreparato += 1;
				break;
			case "autorete":
				bonuses.autorete += 1;
				break;
		}

	}
	return bonuses;
}

function parseBonuses(player) {
	var imagesBonus = [];
	$("img", player).each(function () {
		imagesBonus.push($(this).attr("alt"));
	});
	return countBonuses(imagesBonus);
}

function parseName(data) {
	if (data.length == 5) {
		return data[1].toProperCase();
	} else {
		return (data[1] + " " + data[2]).toProperCase();
	}
}

function parsePlayer(player) {
	// all information
	var data = player.innerText.match(/\S+/g);
	// split roles
	const regexRoles = /(P|D|C|A)/g;
	var roles = data[0].match(regexRoles);
	// extract team
	const regexTeams = /(ATA|NAP|JUV|ROM|SAM|VER|GEN|INT|SAS|CRO|TOR|MIL|FIO|BOL|LAZ|CAG|SPA|BEN|UDI|CHI)/g
	if (data.length == 5) {
		var team = data[2].match(regexTeams);
	} else {
		var team = data[3].match(regexTeams);
	}
	// extract names
	var name = parseName(data);
	if (data.length == 5) {
		var voto = parseFloat(data[3].replace(",", "."));
		var fantavoto = parseFloat(data[4].replace(",", "."));
	} else {
		var voto = parseFloat(data[4].replace(",", "."));
		var fantavoto = parseFloat(data[5].replace(",", "."));
	}
	// benched?
	if ($(player).hasClass("bnc")) {
		var benched = true;
	}
	else {
		var benched = false;
	}
	// extract bonus
	var bonuses = parseBonuses(player);
	// create player
	var parsedPlayer = new fgPlayer();
	parsedPlayer.name = name;
	parsedPlayer.team = team;
	parsedPlayer.voto = voto;
	parsedPlayer.fantavoto = fantavoto;
	parsedPlayer.roles = roles;
	parsedPlayer.bonuses = bonuses;
	parsedPlayer.bench = benched;
	return parsedPlayer;
}

function parsePlayers(matchClass) {
	var allPlayers = $(matchClass + " tbody tr.playerrow");
	var parsedPlayers = [];
	for (var i = 0; i < allPlayers.length; i++) {
		parsedPlayers.push(parsePlayer(allPlayers[i]));
	}
	return parsedPlayers;
}

// if no player available for modulo, applies malus
// reference table_malus.jpg
function findRoleMalus(role, modulo) {
	if (role == "Por") {
		return [];
	}
	else if (role == "Ds") {
		return ["Dc", "Dd"];
	}
	else if (role == "Dd") {
		return ["Dc", "Ds"];
	}
	else if (role == "Dc") {
		return ["Ds", "Dd"];
	}
	else if (role == "E") {
		return ["M", "Dd", "Dc", "Ds"];
	}
	else if (role == "M") {
		return ["E", "Dd", "Dc", "Ds"];
	}
	else if (role == "C") {
		return ["E", "Dd", "Dc", "Ds"];
	}
	else if (role == "W" && modulo == "352" || modulo == "442" || modulo == "4411") {
		return ["E", "Dd", "Dc", "Ds", "M"];
	}
	else if (role == "W" && modulo != "352" || modulo != "442" || modulo != "4411") {
		return ["E", "Dd", "Dc", "Ds", "M", "C"];
	}
	else if (role == "T") {
		return ["E", "Dd", "Dc", "Ds", "M", "C"];
	}
	else if (role == "A") {
		return ["E", "Dd", "Dc", "Ds", "M", "C", "W", "T"];
	}
	else if (role == "Pc") {
		return ["E", "Dd", "Dc", "Ds", "M", "C", "W", "T"];
	}
};

// finds best player for given modulo
function best11(lineup, modulo) {
	var bestNames = [];
	var bestRoles = [];
	var bestPlayers = [];
	var lineupPlayers = lineup.players;
	var players = lineupPlayers.filter(player => (player.fantavoto != NaN && player.fantavoto > 0));
	var total = 0.0;
	var maxMalus = 0;
	for (var roles of modulo) {
		var highest = new fgPlayer();
		// each role can have multiple roles, e.g. M/C
		for (var role of roles) {
			// finds best fitting player for role
			for (var player of players) {
				// players can have multiple roles
				for (var r of player.roles) {
					if (role.includes(r) && player.fantavoto >= highest.fantavoto && bestNames.includes(player.name) == false) {
						highest = player;
					}
				}
			}
		}
		bestNames.push(highest.name);
		bestPlayers.push(highest);
		bestRoles.push(role);
		total += highest.fantavoto;
	}
	return {
		score: total,
		bestPlayers: bestPlayers
	};
};

// finds best modulo for given lineup
function bestLineup(lineup) {
	var highestScore = 0;
	var best11Players = [];
	var bestModulo = "";
	for (m of MODULICLASSIC) {
		var result = best11(lineup, m.roles);
		if (result.score >= highestScore) {
			highestScore = result.score;
			best11Players = result.bestPlayers;
			bestModulo = m.modulo;
		}
	}
	var ICDQCMASLineup = new fgLineup(best11Players, bestModulo, highestScore);
	return ICDQCMASLineup;
};

function printBestLineup(ICDQCMASLineup, matchClass) {
	// apply css to players
	var allPlayers = $(matchClass + " tbody tr.playerrow");
	var playersNames = [];
	for (p of ICDQCMASLineup.players){
		playersNames.push(p.name);
	}
	for (player of allPlayers) {
		// finds players for ICDQCMAS lineup among all the players of the match
		if (playersNames.includes(parseName(player.innerText.match(/\S+/g)))) {
			$(player).removeClass("bnc");
			$(player).find("td.pt").each(function(i){
				if (i == 2) {
					$(this).addClass("bold");
				}
			});			
		}
		else {
			$(player).addClass("bnc");
			$(player).find("td.pt.bold").removeClass("bold");
		}
	}
	// apply css to points, modulo
	$(matchClass).find("tr.footgrey.myhidden-xs td span.numbig4.pull-right").text(ICDQCMASLineup.points);
	$(matchClass).find("tr.myhidden-xs th.thcol3.aleft h4").text("MODULO ICDQCMAS " + ICDQCMASLineup.modulo);
	// apply css to score
	var score = $(matchClass).parents("div.row.itemBox").find(".numbig3");
	// determines if left or right side of score
	if (matchClass.slice(-1) % 2 == 0) {
		score.text(ICDQCMASLineup.goalsScored + "-" + score.text().slice(-1));
	}
	else {
		score.text(score.text()[0] + "-" + ICDQCMASLineup.goalsScored);		
	}
}

function getICDQCMAS(matchClass) {
	// grabs moduli with regex
	var modulo = $(matchClass).find("tr.myhidden-xs th.thcol3.aleft h4").text();
	// get match data
	var players = parsePlayers(matchClass);
	var points = $(matchClass).find("tr.footgrey.myhidden-xs td span.numbig4.pull-right").text();
	var lineup = new fgLineup(players, modulo, points);
	// calculates best modulo for given lineup
	var ICDQCMASLineup = bestLineup(lineup);
	// prints results to page
	printBestLineup(ICDQCMASLineup, matchClass);
};

function main() {
	$(".table.table-striped.tbpink").each(function (i) {
		$(this).addClass("lineup" + i);
	});
	$(".col-lg-5 h3").each(function (i) {
		$(this).append("<button type='button' id='button-icdqcmas" + i + "' style='margin-left:10px'>ICDQCMAS</button>");
		// set click listener for each button
		var button = document.getElementById('button-icdqcmas' + i);
		button.addEventListener('click', function () {
			getICDQCMAS(".lineup" + i);
		});
	});
};

console.log("Loaded classic.js");
main();