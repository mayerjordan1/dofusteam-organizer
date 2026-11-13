"""Guides des avis de recherche niveau 200 (onglet Donjons) — synthèses rédigées à
partir de dofuspourlesnoobs.com. Même mise en forme que donjon_guides_200 ; les
images (schémas, fiches) sont ajoutées par donjon_visuals.compose."""
from pages.donjon_guides_200 import h, p, ul, note, r, g, o, RED, ORANGE, GREEN, GOLD

GUIDES_WANTED = {}


def _zone(zone, rec):
    return p(f"<b>Zone</b> : {zone} · <b>Récompenses</b> : {rec}. Un recherché disparaît plusieurs heures une fois vaincu ; "
             "tous ont l'état <b>Alliés de circonstance</b> (malus de vitalité et de puissance pour chaque monstre qui l'accompagne).")


GUIDES_WANTED["w_chevalier_glace"] = "".join([
    _zone("Bastion des froides légions (Frigost III)", "2 040 Avitons + 5 Kamas de glace"),
    note("Prérequis : niveau 179+ et la quête « Les marcheurs blancs » (terminer les 6 avis de Frigost III). Avis à la milice du château de Harebourg.", GOLD, "QUÊTE"),
    h("Garde à vous", RED),
    p("Le Chevalier n'a pas d'état Invulnérable de base, mais <b>il devient Invulnérable 2 tours</b> si vous le <b>poussez</b>, tentez un <b>retrait PA</b> ou un <b>retrait PM</b> "
      "(un Cra qui le repousse, un Enutrof qui retire des PM…)."),
    note("Pendant tout le combat, <b>tout perso qui subit des dommages de poussée est OS</b> (attention aux Verglasseurs qui repoussent).", RED, "OS"),
    h("Sorts", GOLD),
    ul([
        "<b>La force du faible</b> (2-15 PO, 2×/tour, 1×/cible) : 400 Air + vole 50 dommages (80 en crit) 3 tours, cumulable.",
        "<b>Souffle amollissant</b> (14 PO, relance 4) : 500 Eau en cercle 2, <b>minimise les effets aléatoires</b> 2 tours.",
        "<b>Rafraîchissement</b> (dès le tour 2, tous les 5 tours) : se désenvoûte et se met un châtiment 500 sur 2 tours, se soigne de 50% des frappes.",
        "<b>Tranchant absorbant</b> (2 PO sans LDV, 2×/tour) : 600 Air + 600 Eau en vol de vie (~1200) + <b>Pesanteur</b> 1 tour — le plus dangereux.",
        "<b>Saut</b> (5 PO sans LDV, relance 4) : téléportation + Pesanteur 1 tour. <b>Souffler n'est pas jouer</b> (14 PO, relance 3) : boost allié +4 PM/+4 PO et échange de place (+ Pesanteur).",
    ]),
    h("Conseils", GREEN),
    ul([
        "Accompagné de monstres : jouer à distance et <b>tuer les alliés d'abord</b>. Garder les monstres éloignés de l'équipe (échange de place).",
        "<b>Pandawa</b> : porter/jeter ne le rend pas Invulnérable — l'éloigner et le placer à volonté. Un Pandawa tank peut aussi le bloquer au contact.",
        "Faiblesses <b>Feu (−15%)</b> et <b>Eau (−20%)</b> : y concentrer les dégâts. Rester à distance de Tranchant absorbant.",
    ]),
])

GUIDES_WANTED["w_culbutoeuf"] = "".join([
    _zone("Frigost III", "2 040 Avitons + 5 Kamas de glace"),
    h("Reste à ta place", RED),
    ul([
        "<b>Tout le monde est Inébranlable</b> (ni poussée ni attirance, alliés comme ennemis).",
        "Culbutoeuf <b>réduit de 2200 les dégâts subis en mêlée</b> tout le combat : <u>il faut le taper à distance</u>, même une Colère de Iop en mêlée est inutile. Pas d'état Invulnérable.",
        "Vos persos : <b>−2 PM</b> (infini) et <b>−50% de résistance cumulable</b> à chaque échange de position ou téléportation.",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>De bon cœur</b> : +10 esquive PM (15 en crit) 2 tours à chaque retrait PM tenté. <b>Sinistro vole</b> : alliés +3 PM, +50 tacle (cercle 2).",
        "<b>Roule ma boule</b> (4 PO) : 500 Terre + poison Feu 151-200 qui arrive dans 2-3 tours. <b>Du fond du cœur</b> (cases adjacentes) : 1300 Feu, −10 PM, −200 puissance, 40% érosion — à éviter.",
        "<b>Va te faire cuire un œuf</b> (ligne 2-14 PO sans LDV, relance 2) : poison par PA utilisé, Pesanteur, soigne les monstres qui attaquent la cible.",
    ]),
    h("Conseils", GREEN),
    ul([
        "<b>6 PM minimum</b> par perso (−2 PM infini), si possible un <b>Dofus Abyssal</b>. Éviter échanges de place et téléportations.",
        "Tuer Culbutoeuf en premier, en <b>Terre et Air</b>. Un <b>Pandawa tank</b> au contact pour le tacler ; éviter sa mêlée.",
    ]),
])

GUIDES_WANTED["w_mekamouth"] = "".join([
    _zone("Frigost III", "2 040 Avitons + 5 Kamas de glace"),
    h("Invulnérable permanent & glyphes", RED),
    p("Mekamouth est <b>Invulnérable</b> tout le combat. Pour le rendre vulnérable 1 tour, il doit <b>finir son tour dans le glyphe bleu en croix de taille 1</b> posé par son sort <b>Surtension</b>. "
      "Il retire <b>2 PA</b> à tous vos persos pour le combat et vous met un poison : <b>chaque PM utilisé fait perdre 15 PV Eau</b>."),
    p("Il pose ses glyphes en ligne sans LDV à très grande portée ; ils s'empilent :"),
    ul([
        f"{o('Bleu en croix 1')} (delock) : monstres +3 PA, vos persos −3 PA.",
        f"{o('Rouge cercle 2')} : soigne les monstres, tape vos persos en Feu.",
        f"{o('Vert cercle 2')} : monstres +20% résistance, vos persos −20% résistance + Pesanteur (boosts cumulables).",
        f"{o('Bleu cercle 2')} (différent du delock) : monstres +25% de vitalité max, vos persos 25% érosion + poison 100 Eau si vous subissez les dégâts du glyphe.",
        "Il peut aussi poser un <b>glyphe invisible</b>.",
    ]),
    h("Conseils", GREEN),
    ul([
        "Piéger Mekamouth sur le glyphe bleu (retrait PM, placement) pour ouvrir ses fenêtres de vulnérabilité.",
        "Surveiller l'empilement des glyphes (un perso peut subir le malus 5 fois). Limiter ses déplacements (poison au PM).",
    ]),
])

GUIDES_WANTED["w_takomako"] = "".join([
    _zone("Sufokia", "2 040 Avitons"),
    h("Mipieuvre Mirequin", RED),
    ul([
        "Pas d'état Invulnérable de base, mais il se met <b>Invulnérable 1 tour</b> si <u>aucun de vos persos n'est dans un rayon de 5</u> autour de lui au début de son tour : toujours avoir un perso à 5 PO ou moins.",
        "Il gagne <b>+1 PM par début de tour</b> (infini, 10 maximum) et grossit.",
        "Chaque tour il peut mettre jusqu'à 2 persos <b>Pacifiste</b> et <b>Insoignable</b>.",
    ]),
    h("Son seul sort de frappe", ORANGE),
    p("Les dégâts dépendent de ses <b>PM restants</b> : ~2 500 Neutre au maximum (s'il n'a utilisé aucun PM), réduits proportionnellement aux PM dépensés ce tour "
      "(5 PM au début, 3 utilisés → −60%). Il vous met aussi un état de <b>FOLIE</b>."),
    h("FOLIE ! (1 à 10)", RED),
    ul([
        "<b>Folie 2</b> : vous infligez 100% des dégâts de votre sort à tous les alliés dans 2 PO.",
        "<b>Folie 4</b> : soins reçus ×50%. <b>Folie 6</b> : dégâts subis ×100%. <b>Folie 10</b> : <b>OS</b>.",
        "Les malus se cumulent. Les actions qui incrémentent la Folie sont listées dans le guide complet.",
    ]),
])

GUIDES_WANTED["w_homard_medali"] = "".join([
    _zone("Sufokia", "2 040 Avitons"),
    h("Invulnérabilité par Télépunch", RED),
    p("Pas d'Invulnérable de base, mais s'il vous frappe (perso ou invocation) avec <b>Télépunch</b> (2-5 PO) il devient <b>Invulnérable à l'infini</b>. "
      "Pour la lui retirer : <b>le frapper en mêlée</b> (perso ou invocation). Jouer à distance l'évite."),
    p("Il gagne <b>+15 de puissance</b> (infini, cumulable) <u>par perso situé à plus de 3 PO de lui</u> à chacun de ses débuts de tour : ne restez pas tous loin."),
    h("Sorts", GOLD),
    ul([
        "<b>Télépunch</b> : échange de position, 650 Air en vol de vie, <b>Invulnérable</b>.",
        "<b>Drachetaulque</b> : 650 Eau, repousse de 3, état <b>Draché</b> 2 tours (ajoute une ligne de dommages).",
        "<b>Hypercut</b> : 400 Terre en carré 3×3, −2 PM esquivables, repousse d'1.",
    ]),
    p("Tuer d'abord les monstres qui l'accompagnent. En mêlée (« bourriner ») ou à distance selon la composition."),
])

GUIDES_WANTED["w_atcham"] = "".join([
    _zone("Ecaflipus", "2 040 Avitons"),
    h("Pierre – Feuille – Ciseaux", ORANGE),
    p("Atcham = trois monstres : <b>Chi (Pierre)</b>, <b>Fou (Ciseaux)</b>, <b>Mi (Feuille)</b>, sans Invulnérable. "
      "À chaque début de tour de Fou, <b>chacun de vos persos reçoit un état Pierre, Feuille ou Ciseaux</b> aléatoire."),
    ul([
        "Vous avez <b>Pierre</b> → frappez <b>Fou</b> · <b>Feuille</b> → frappez <b>Chi</b> · <b>Ciseaux</b> → frappez <b>Mi</b>.",
        "Un coup <u>juste</u> : tous les dégâts sont <b>répartis sur les deux autres monstres</b>.",
        "Un coup <u>faux</u> : <b>Pacifiste 3 tours</b>, pas de répartition et vous subissez <b>300% des dégâts</b> infligés.",
    ]),
    h("Sorts & conseils", GOLD),
    ul([
        "<b>Émoussage</b> 1600 Neutre (jusqu'à 2000 en crit), <b>Coupe</b> 300 Feu (jusqu'à 2200 en crit), <b>Enveloppage</b> ~500 (5 éléments).",
        "Rester à bonne distance de <b>Chi et Fou</b>, qui tapent très fort. Ne jamais se tromper de cible.",
    ]),
])

GUIDES_WANTED["w_buldalazred"] = "".join([
    _zone("Sufokia", "2 040 Avitons"),
    h("Attirance, pièges et glyphe noir", RED),
    ul([
        "Pas d'Invulnérable : <b>focus-le</b> et tue-le vite.",
        "À chaque début de tour il <b>attire de 3 cases</b> tous les ennemis dans sa LDV et pose un <b>glyphe noir invisible de rayon 2</b> (le glyphe visible autour de lui n'est pas sa vraie position).",
        "<b>Piège dimensionnel</b> : jusqu'à 2 pièges de 1 case par tour. Si un perso en déclenche un : tout le monde est attiré de 3 cases vers Buldalazred et le glyphe noir apparaît.",
        "Chaque piège déclenché lui donne <b>+100 puissance</b> (infini, cumulable).",
    ]),
    note("Un perso qui <b>commence ou finit son tour dans le glyphe noir</b> est <b>OS</b>.", RED, "OS"),
    h("Conseils", GREEN),
    ul([
        "Ne jamais commencer/finir dans le glyphe noir. Éviter de se déplacer à outrance, garder <b>3 PM en réserve</b>.",
        "Sorts anti-attirance ou obstacles pour se cacher. <b>Uction</b> : 450 Feu, −3 PM esquivables.",
    ]),
])

GUIDES_WANTED["w_ganos"] = "".join([
    _zone("Osavora (peut être accompagné de Zarbivores)", "2 040 Avitons"),
    h("Saisons & seuils de PV", ORANGE),
    p("Pas d'Invulnérable. Il commence dans l'état de la saison actuelle (<b>Naissance → Chasse → Repos</b>) et en change à chaque <b>seuil de PV : 70% et 30%</b> "
      "(passif <b>Méganos</b>). Il a <b>9 sorts</b>, 3 par saison, et passe par les 3 saisons dans le même combat."),
    h("Ganorage", RED),
    ul([
        "Dès le début : <b>Ganorage 1</b>, +1 à chaque tour (dommages finaux, PM, tacle, fuite, vitalité pour 1 tour), jusqu'à 10 ; au tour 10 : <b>Ganorage Ultime</b>.",
        "À chaque début de tour il <b>repousse de 20 cases</b> le perso ou l'invocation en ligne la plus proche : prévoir des obstacles ou une invocation en ligne.",
    ]),
    p("Tuer vite : l'état Ganorage rend le combat de plus en plus dur. Détail des 9 sorts par saison : voir le guide complet."),
])

GUIDES_WANTED["w_glourdorak"] = "".join([
    _zone("Frigost III", "2 040 Avitons + 5 Kamas de glace"),
    h("Fonso Cacnoob : comment le rendre vulnérable", RED),
    p("Glourdorak est <b>Invulnérable tout le combat</b> et <b>Lourd</b> (impossible à porter). <b>Gloursofulgur</b> met l'état <b>Fonso Cacnoob</b> (1×/tour, perso différent à chaque fois, "
      "3 tours avant de pouvoir recibler le même) : <u>le perso Cacnoob qui finit son tour au corps à corps de Glourdorak</u> le rend <b>vulnérable jusqu'à son prochain tour</b> (le perso qui delock ne pourra pas taper)."),
    note("<b>Tour 5</b> : il désenvoûte toute votre team et <b>OS toutes vos invocations</b>.", RED, "TOUR 5"),
    h("Sorts", GOLD),
    ul([
        "<b>Dard des villes</b> : 800 Air, −1 à −2 PM · <b>Ruche Hour</b> : 400 Eau + 600 Feu en vol de vie (cercle 2).",
        "<b>Miel de Jouvence</b> : se désenvoûte, −3 PM au contact · <b>Gloursolaser</b> : vous désenvoûte + malus 2 tours.",
        "<b>Gloursopoing</b> (mêlée) : 800 Terre + 1000 Neutre en vol de vie, 25% érosion (30 en crit).",
    ]),
    h("Conseils", GREEN),
    ul([
        "Prévoir résistances, protection/soin. Rester à distance et hors de sa LDV pour le temporiser ou après l'avoir rendu vulnérable.",
        "Prévoir des classes à gros dégâts : sa fenêtre de vulnérabilité ne dure qu'1 tour.",
    ]),
])

GUIDES_WANTED["w_kongoku"] = "".join([
    _zone("Amakna", "2 040 Avitons"),
    h("Cocolune", RED),
    p("Pas d'Invulnérable, mais à son 1<sup>er</sup> tour il invoque une <b>Cocolune</b> (15 000 PV, 0 PM, Indéplaçable). Tant qu'elle est là : "
      "<b>tous vos persos sont en Pesanteur</b> et Kongoku passe en état <b>Super Singe</b> (effets en plus sur ses sorts)."),
    ul([
        "À chaque début de tour, la Cocolune <b>attire vos persos de 10 cases</b> puis met <b>Pacifiste</b> à tous ceux dans sa LDV. Si Kongoku est dans sa LDV : +500 puissance et +5000 vitalité (infini).",
        "<u>Inutile de la tuer</u> : elle est réinvoquée au tour suivant.",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>Uppercut magistral</b> : 300 Neutre, repousse de 10 (20 en Super Singe, gros dommages de poussée).",
        "<b>Saruharuha</b> : 400 Neutre en ligne de 10 ; Super Singe : +40 de dégâts de base au tour suivant. <b>Déplacement instantané</b> : se téléporte au contact d'un ennemi.",
        "<b>Puissance lunaire</b> (Super Singe) : +500 puissance, +5000 vitalité, état Rayonnement lunaire.",
    ]),
    h("Conseils", GREEN),
    ul([
        "<b>Focus Kongoku</b> (Eau et Air conseillés). Se placer pour ne pas être attiré dans la LDV de la Cocolune.",
        "Sorts anti-poussée ; <b>invocations statiques autour de la Cocolune</b> pour la bloquer. Attention à Puissance lunaire.",
    ]),
])

GUIDES_WANTED["w_hyperscampe"] = "".join([
    _zone("Base des Justiciers", "2 040 Avitons"),
    h("Invulnérable : les glyphes bleus", RED),
    p("L'Hyperscampe est <b>Invulnérable à l'infini</b>. Avec <b>Riveteuse</b> il pose <b>3 à 4 glyphes bleus de 1 case</b> autour du perso ciblé (plusieurs schémas ; une case occupée = pas de glyphe, il en faut au moins 3). "
      "Il faut alors <b>placer au moins 3 persos sur 3 glyphes différents</b> : ils deviennent <b>Indéplaçables 1 tour</b>, soignés de 200 PV, −200 puissance 2 tours en fin de tour."),
    ul([
        "Au début de son tour il retire alors son Invulnérable <b>1 tour</b> ; à refaire chaque tour pour ne pas qu'il la regagne.",
        "On peut <b>réduire le nombre de persos à placer</b> en sacrifiant un ou deux persos (voir le guide complet).",
        "Éviter de le mettre en <b>Pesanteur</b>.",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>Percussion</b> : attire la cible, 450 Air, repousse de 5 et s'attire dessus, poison 50% érosion. <b>Rupture</b> : 900 Feu en cercle 2, −2 PM aux Indéplaçables à son contact sinon repousse de 4.",
        "<b>Forage</b> : téléportation, 1000 Eau, −1 durée d'effets (−2 en crit). <b>Rivet</b> / <b>Plasmide</b> : effets liés à l'état « Petite Sœur » et aux glyphes.",
    ]),
    p("Bien placer ses persos pour ne pas rater la pose des glyphes ; 3 persos sur les glyphes à chaque tour."),
])

GUIDES_WANTED["w_khepricorne"] = "".join([
    _zone("Saharach", "2 040 Avitons"),
    h("Invulnérable : il suffit de le toucher", RED),
    p("Invulnérable au début. <b>Une seule ligne de dégâts</b> (même sans effet) suffit : à son tour suivant il passe <b>vulnérable 3 tours</b>, avec +20 tacle, +3 PM, +50 esquive PM, "
      "Intaclable et −10 aux dégâts subis. En devenant vulnérable il <b>invoque une Boule Puante</b> ; au bout des 3 tours il repasse Invulnérable, <u>élimine sa Boule</u> et frappe en Feu "
      "tous les persos dans un cercle de 2 autour d'elle."),
    h("Effets de début de tour (distances)", ORANGE),
    ul([
        "Persos en <b>mêlée</b> : repoussés d'1 case. Persos à <b>plus de 6 PO</b> : −6 PO et −3 PA 1 tour.",
        "Effets supplémentaires si Khepricorne et sa Boule sont à plus de 10 PO l'un de l'autre (voir le guide complet).",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>Bouse de Feu</b> : 300 Feu + vole 40 Agilité/Intelligence/Chance/Force 6 tours (60 en crit) + 10 de manière infinie.",
        "<b>Coup de Bouse</b> : 550 Neutre en vol de vie, vole 1 PA (2 en crit) 2 tours.",
    ]),
])

GUIDES_WANTED["w_braideur"] = "".join([
    _zone("Alignement", "Alitons"),
    h("Réduction à distance & Pesanteur", RED),
    ul([
        "Pas d'Invulnérable, mais le Fantôme Braïdeur <b>réduit de 75% les dégâts subis à distance</b> tout le combat.",
        "Elle est <b>Intaclable</b> et en <b>Pesanteur</b> ; vos persos aussi sont en <b>Pesanteur</b> tout le combat.",
        "Sous <b>50% de vitalité</b>, à son tour suivant elle invoque <b>3 Images Miroir</b> qui utilisent les mêmes sorts.",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>Carroyage</b> : 400 Feu en ligne de 7, repousse de 6 (gros dommages de poussée).",
        "<b>Mastaba</b> : 150 Terre + 200 Eau (cercle 2), −4 PM esquivables (6 en crit) 2 tours, cumulable 2×.",
        "<b>Paléolitige</b> : 250 Terre, désenvoûte la cible, +100 de dégâts de base dans 3 tours (~700).",
    ]),
    p("Elle tape de très longue distance, repousse fort et retire beaucoup de PM : privilégier le corps à corps pour contourner la réduction de 75%."),
])

GUIDES_WANTED["w_psikopompe"] = "".join([
    _zone("Frigost III", "2 040 Avitons + 5 Kamas de glace"),
    h("Invulnérable & retrait PM", RED),
    p("Invulnérable tout le combat. <b>Tenter un retrait PM</b> sur lui lui retire l'état <b>1 tour</b>, mais le booste de <b>+63 PO</b> 2 tours (portée modifiable sur tous ses sorts). "
      "Tous les monstres ont +3 PO (infini)."),
    note("Tous vos persos <b>frappent leurs alliés au contact</b> (~600, élément aléatoire) à chaque début de tour : <u>ne finissez jamais collé à un allié</u>.", RED, "ALLIÉS"),
    note("<b>Sentence</b> (zone croix 1) pose l'effet « Tue la cible » 2 tours : <b>le perso qui reçoit un soin est OS</b>. Ne soignez pas (surtout pas en zone) les persos Sentence.", RED, "SOINS"),
    h("Sorts", GOLD),
    ul([
        "<b>Coupe-Jatte</b> : 1000 Air, vole 4 PO (5 en crit). <b>Bondage</b> : ~2000 Neutre s'il est full vitalité, maximise les effets aléatoires 2 tours.",
        "<b>Retour à l'envoyeur</b> : renvoie un sort de rang 6 max 1 tour (croix 1) — le désenvoûter dès qu'il le lance. <b>Flagellation stimulante</b> : alliés +4 PA 3 tours.",
    ]),
    h("Conseils", GREEN),
    ul([
        "Le bloquer au contact d'un <b>Pandawa tank</b> ; éviter sa mêlée quand il est full vitalité. Du retrait PM de préférence à distance.",
        "Une fois vulnérable, se mettre hors de sa LDV ou assez loin ; se cacher derrière des obstacles réduit les dégâts.",
    ]),
])

GUIDES_WANTED["w_sicogne"] = "".join([
    _zone("Xélorium", "2 040 Avitons"),
    h("Mêlée mortelle", RED),
    note("Sicogne <b>OS tous les persos à son contact</b> si l'un d'eux tente de fuir sa mêlée <u>et échoue</u> (taclé). Ne fuyez jamais si vous ne pouvez pas fuir à 100%.", RED, "OS"),
    ul([
        "Pas d'Invulnérable. Si vous le <b>poussez, l'attirez, le téléportez ou échangez</b> avec lui, <b>votre tour se termine</b> automatiquement : à faire en dernière action.",
        "Il <b>OS toutes les invocations</b> chaque tour (Agression) : éviter d'invoquer.",
    ]),
    h("Glyphes bleus des monstres", ORANGE),
    p("Chaque tour, chaque monstre pose un glyphe bleu d'1 case : y passer vous fait <b>échanger de place</b> avec lui et donne un bonus aux deux :"),
    ul([
        "<b>Sicogne</b> : +400 puissance (mais votre tour se termine) · <b>Buboxor</b> : dégâts subis ×50% · <b>Harpille</b> : +200 puissance · <b>Ikargn</b> : +1 PM · <b>Méjaire</b> : soin ~400.",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>Superpuissance</b> : alliés +400 puissance, +4 PA, +10% crit, et vos ennemis frappent au jet max. <b>Agression</b> : 400 Air, −30 fuite, OS des invocations.",
        "<b>Annihilation</b> : 1000 Terre, −3 PM (4 en crit) 4 tours, −150 puissance. <b>Charge Destructrice</b> : téléportation, 250 Air + 250 Terre cercle 3, +100 tacle.",
    ]),
    p("Rester à distance, éviter d'invoquer, le tuer rapidement."),
])

GUIDES_WANTED["w_voldelor"] = "".join([
    _zone("Enutrosor", "2 040 Avitons"),
    h("Susceptibilité & Marque des Mangelors", RED),
    p("Pas d'Invulnérable. Dès qu'il est frappé, il se met l'état <b>Marque des Mangelors</b> 1 tour et <b>le 1<sup>er</sup> perso qui le frappe</b> la reçoit aussi. "
      "La Marque ajoute un effet sur ses sorts de frappe :"),
    ul([
        "<b>Armada Cadavra</b> (cercle 3 à 1 PO) : <b>OS</b> le perso Marqué.",
        "<b>Magitation</b> (portée infinie sans LDV) : échange de place avec le perso Marqué, −50% de ses dégâts subis 1 tour.",
        "<b>Sort Scellé</b> (4-12 PO) : ligne de dégâts de 30% des PV érodés + 20% érosion et poison Eau 61-70 sur 5 tours.",
    ]),
    note("<b>Éviter de se faire OS</b> avec le perso Marqué (loin de son Armada Cadavra, ou sous protection). Un <b>Pandawa</b> qui porte le 1<sup>er</sup> perso qui tape du tour évite la Marque.", GREEN, "ASTUCE"),
    h("Conseils", GREEN),
    ul([
        "Éliminer d'abord les monstres qui l'accompagnent <u>sans jamais le frapper</u>. Il peut <b>ressusciter</b> le dernier monstre mort (Zombi, 70% PV) tous les 3 tours.",
        "Ne pas rester trop groupé (il se soigne en vol de vie). Privilégier <b>Eau et Terre</b>.",
    ]),
])
