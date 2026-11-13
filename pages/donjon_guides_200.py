"""Guides des donjons niveau 200 (onglet Donjons) — synthèses rédigées à partir
de dofuspourlesnoobs.com / DofusDB, fusionnées dans DEFAULT_GUIDES par
pages/donjon_guides.py. Même rendu que les guides historiques (titres colorés,
emphases) mais construit via de petits helpers plutôt que du HTML en vrac.

Texte inline : <b>gras</b>, <u>souligné</u>, ok dans toutes les fonctions.
Un guide = "".join([...]) de blocs h()/p()/ul()/note().
"""

RED, ORANGE, GREEN, GOLD = "#ff5c5c", "#ff8a1e", "#6dc96d", "#c8a000"


def h(title, color=GOLD):
    return (f'<h3 style="color:{color}; font-size:13px; margin:0 0 6px 0; '
            f'letter-spacing:.3px;">{title}</h3>')


def p(text):
    return f'<p style="margin:0 0 10px 0; line-height:1.55;">{text}</p>'


def ul(items):
    lis = "".join(f'<li style="margin-bottom:5px;">{i}</li>' for i in items)
    return f'<ul style="margin:0 0 10px 0; padding-left:18px;">{lis}</ul>'


def note(text, color=RED, label="IMPORTANT"):
    return (f'<p style="margin:0 0 10px 0; line-height:1.5; padding:8px 10px; '
            f'border-left:3px solid {color}; background:rgba(255,255,255,0.03); '
            f'border-radius:4px;"><b style="color:{color};">{label}</b> : {text}</p>')


def r(t):
    return f'<b style="color:{RED};">{t}</b>'


def g(t):
    return f'<b style="color:{GREEN};">{t}</b>'


def o(t):
    return f'<b style="color:{ORANGE};">{t}</b>'


from pages.donjon_visuals import fig, figs

GUIDES_200 = {}

GUIDES_200["solar"] = "".join([
    h("Prérequis", ORANGE),
    p("Sort <b>Nécronyx</b> obligatoire (quête « L'arme fatale »). Lançable tous les 2 tours sur un ennemi : "
      "le monstre ressuscité ne joue plus, n'inflige plus de renvoi/dégâts de mort. En contrepartie, "
      "sur Solar ou un Calciné : <b>20% d'érosion pendant 3 tours</b>. Depuis la 3.7, Nécronyx "
      "<u>ne passe plus le tour</u> du lanceur."),
    note("Solar (et chaque monstre) doit être sous <b>Nécronyx AVANT de mourir</b>, sinon il se "
         "ressuscite / <u>OS toute l'équipe</u>. Même s'il ne reste que Solar : Nécronyx d'abord, "
         "kill ensuite.", RED, "RÈGLE N°1"),
    fig("dp_solar_0.png", "Sort Nécronyx — coût 3 PA, portée 1, relance 2", 366),
    h("Pyrozomb (tous les monstres)", RED),
    p("Chaque monstre qui meurt est <b>ressuscité par un allié</b>, renvoie les dégâts subis en zone carrée de 1 "
      "autour de lui et inflige des dégâts Terre (cercle 2) à sa mort. Nécronyx annule tout ça."),
    h("Les 4 états de Solar (cycle de 3 tours)", GOLD),
    ul([
        f"{o('Tours 1-3 · Aurore')} : soin de ~700 PV à lui et ses alliés, +1000 esquive PA/PM. Vous : +1 PA. <u>Invulnérable</u>.",
        f"{o('Tours 4-6 · Zénith')} : alliés +200 puissance, vous perdez 6 PO. Lui : Lourd + Intaclable. Vous : +2 PA. <u>Invulnérable</u>. Phase la plus dangereuse.",
        f"{o('Tours 7-9 · Crépuscule')} : retire 1 PA. <u>Invulnérable</u>.",
        f"{g('Tour 10+ · Nadir')} : vous perdez 2 PA — <b>seul état où il est vulnérable</b>.",
    ]),
    p("Nécronyx sur Solar le fait passer à l'état suivant à son prochain tour (1 état par Nécronyx, "
      "donc minimum 3 tours pour atteindre Nadir)."),
    h("Glyphe du pourtour", ORANGE),
    p("Se déclenche si vous <b>commencez votre tour dessus</b>, selon l'état de Solar : Aurore −300 puissance · "
      "Zénith 20% érosion · Crépuscule −2 PA · Nadir −4 PO. <u>Ne finissez pas vos tours sur le bord.</u>"),
    h("Le tuer (état Nadir)", GREEN),
    ul([
        "Solar <b>renvoie les dégâts</b> subis en carré de 1 : tapez à distance / écartez vos alliés.",
        "Pas assez de dégâts pour le finir en 1 tour ? Tapez-le un tour <u>sans</u> Nécronyx, puis le tour suivant "
        "<b>Nécronyx avec le 1er perso en initiative</b> (plus de renvoi) pour que les autres le finissent.",
        "Il doit rester sous Nécronyx jusqu'au kill, sinon retour en Aurore (invulnérable) à son tour.",
        "Prévoir un gros tour de dégâts (Colère de Iop, réseau Sram…).",
    ]),
    h("Ordre conseillé", GREEN),
    p("Tacler les monstres avec un tank et laisser Solar libre. Tuer le <b>Moribombe</b> en priorité "
      "(Grenade Collante : +50% dégâts subis). Après la mort de Solar, chaque monstre ressuscité "
      "<u>perd son Nécronyx</u> : le remettre avant chaque kill. Priorité : celui qui a ressuscité Solar, "
      "puis enchaîner les autres vite."),
    h("Sorts de Solar (par état)", GOLD),
    ul([
        f"{o('Aurore')} — Lève-tôt (bouclier 1300 allié en croix + 1200 Terre) · Aube Saine (+2 PM/tacle alliés, 900 Feu, ligne 4) · Rossée Matinale (Eau selon PV érodés, 4 PO).",
        f"{o('Zénith')} — Coup de Soleil (1100 Terre, 1400 si Pesanteur, mêlée) · Éruption Solaire (800 Feu à tous, 1200 si Pesanteur, −6 PO) · Démons de Midi (téléporte, 950 Air, −40 fuite).",
        f"{o('Crépuscule')} — Le Grand Soir (400 Terre en ligne infinie, −80 tacle) · Cours du Soir (400 Air + Affaibli) · Coucher de Soleil (−4 PM + Pesanteur/Indéplaçable/Lourd en ligne 4).",
        f"{o('Nadir')} — Nuit Blanche (200 Eau + poison 400, −20% PV) · Protecteur d'émoi (150 Feu portée 12, −60 PA/PM + poison PM) · Démons de Minuit (150 Air + poison par PA, +20% dégâts distance).",
    ]),
    h("Succès « La mort sait attendre » (aucun ennemi sous Nécronyx avant la mort de Solar)", GOLD),
    p("Tuer Solar en premier : Nécronyx au <b>tour 1 et 2</b> (il atteint Crépuscule au tour 3), "
      "puis Nécronyx au tour 3 pour qu'il soit en Nadir au tour 4. Finir au tour 4 ou 5, "
      "en re-Nécronyxant juste avant le kill. Entamer les monstres entre-temps."),
    h("Expéditions de guilde", GOLD),
    ul([
        f"{o('Audace')} : Solar boost tout le monde en fin de cycle (Aurore 1000 PB · Zénith 300 puissance · Crépuscule 3 PA · Nadir 3 PM), effet de l'état <u>précédent</u>. "
        "Tuer tous les monstres avant Solar (Moribombe d'abord), le passer en Zénith via Nécronyx, le finir au tour suivant Crépuscule→Nadir.",
        f"{o('Bravoure')} : Solar pose des glyphes autour de vos persos (invocations incluses) à chaque tour selon son état, "
        "qui se cumulent et disparaissent au changement de phase. Peu de persos et peu d'invocations, "
        "espacer les persos (glyphes Crépuscule −2 PA), abuser de Nécronyx pour passer les phases.",
    ]),
])

GUIDES_200["chaloeil"] = "".join([
    h("Principe : le plateau de dés", ORANGE),
    p("Map rectangulaire <b>sans obstacle</b>, chaque cellule est une face de dé (1 à 6, valeur indiquée sur la case — "
      "désactiver le mode tactique pour la voir). À la <u>fin de son tour</u>, selon la face où le Chaloeil "
      "termine, il <b>invoque des Dés</b> et pose des <b>glyphes blancs</b> sur toutes les cellules de même valeur."),
    ul([
        "<b>Dés</b> : invocations ennemies statiques, indéplaçables, ne taclent pas, 2000 PV (3000 sous Puissance Cyclique), 0% rés. "
        "Apparaissent en fin de tour du Chaloeil, disparaissent au début du suivant. Posés à <b>distance paire</b> de lui. "
        "On peut les tuer pour débloquer une ligne de vue. Pas d'invocation si une entité est déjà sur la case.",
        "<b>Glyphes blancs</b> : posés à <b>distance impaire</b> du Chaloeil, <b>soignent intégralement</b> ceux qui finissent leur tour dessus.",
        "12 placements possibles (6 faces × case paire/impaire).",
    ]),
    fig("dp_chaloeil_17.png", "Valeur de chaque cellule : 1 bleu · 2 vert · 3 rouge · 4 jaune · 5 orange · 6 violet"),
    fig("dp_chaloeil_18.jpg", "Exemple : Dés (orange) et glyphes blancs de soin posés selon la face où termine le Chaloeil"),
    p("<b>Placement des Dés (orange) et des glyphes blancs (blanc) selon la face</b> — rouge = position finale du Chaloeil, case paire ou impaire :"),
    figs([("dp_chaloeil_20.png", "Dé 1 · cellule paire"), ("dp_chaloeil_21.png", "Dé 1 · cellule impaire"),
          ("dp_chaloeil_22.png", "Dé 2 · cellule paire"), ("dp_chaloeil_23.png", "Dé 2 · cellule impaire"),
          ("dp_chaloeil_24.png", "Dé 3 · cellule paire"), ("dp_chaloeil_25.png", "Dé 3 · cellule impaire"),
          ("dp_chaloeil_26.png", "Dé 4 · cellule paire"), ("dp_chaloeil_27.png", "Dé 4 · cellule impaire"),
          ("dp_chaloeil_28.png", "Dé 5 · cellule paire"), ("dp_chaloeil_29.png", "Dé 5 · cellule impaire"),
          ("dp_chaloeil_30.png", "Dé 6 · cellule paire"), ("dp_chaloeil_31.png", "Dé 6 · cellule impaire")]),
    h("États de Dé & monstres", RED),
    p("Chaque entité a un état de Dé = la face où elle a fini son tour. À partir du tour 2, <b>chaque monstre</b> "
      "(sauf le Chaloeil) inflige <b>20% érosion + 450 dégâts aléatoires</b> à tous les persos/invocations "
      "<u>dans le même état de Dé que lui</u> : ne finissez pas vos tours sur la même face qu'un monstre."),
    p("<b>Gros Yeux</b> (tours 3, 6, 9…) boost le Chaloeil et les monstres selon leur Dé : "
      "1 → 200 esquive PM · 2 → 5 PO · 3 → Indéplaçable · 4 → 3 PM · 5 → soin 20% PV · 6 → 600 puissance."),
    fig("dp_chaloeil_19.jpg", "États de Dé des entités (le chiffre s'affiche au-dessus de chaque entité)", 308),
    h("Invulnérabilité", GOLD),
    p("Le Chaloeil est <b>invulnérable jusqu'au tour 21</b> (impossible de le retirer, il faut survivre), "
      "même tour que la 5<sup>e</sup> et dernière vague. Vagues de monstres aux tours <b>1 / 6 / 11 / 16 / 21</b>. "
      "Une fois vulnérable : +200 esquive PM et Inébranlable pour le reste du combat."),
    figs([("dp_chaloeil_32.png", "Jeu du Chaloeil : Invulnérable pendant 20 tours"),
          ("dp_chaloeil_33.png", "Au tour 21 : Inébranlable + 200 esquive PM")]),
    h("Ses sorts", GOLD),
    ul([
        "<b>Farce et Attrape</b> (dès le tour 2, 3×/tour, 1×/cible, 6 PO sans LDV) : échange de place avec allié ou ennemi ; sur un ennemi 1000 Terre + Pesanteur.",
        "<b>Toilette Écaflip</b> (ligne, 2 PO) : 1000 Eau, repousse 3 cases, −4 PM.",
        "À partir du tour 2 : retire 50 de tacle aux ennemis dans un rayon 2, pendant 5 tours (il est quasi intaclable : 350+ de fuite).",
    ]),
    h("Routourne (monstres du Grand Jeu)", ORANGE),
    p("Chaque monstre alterne un bonus d'1 tour sur un cycle de 3 tours (désenvoûtable seulement quand actif) : "
      "<b>Cavalier Chanceux</b> 2 PM / 100% crit / 1000 poussée · <b>Dame du Hasard</b> 4 PA / crit / 200 dmg · "
      "<b>Roi Joueur</b> 2000 PB / 400 puissance / crit · <b>Soldat de Fortune</b> crit / 100 fuite / 5 PO · "
      "<b>Valet Veinard</b> 100 esq. PM / dégâts subis ×80% / crit."),
    h("Conseils tactiques", GREEN),
    ul([
        "<b>Retrait PM = votre meilleur allié</b> : il n'a que 4 PM, vous choisissez où il finit son tour (donc où tombent les dés).",
        "Le placer sur une face qui vous arrange avant son tour ; sans retrait PM, manipuler son IA.",
        "<b>L'éloigner des monstres</b> (surtout à l'apparition des vagues) pour qu'il ne s'échange pas avec eux.",
        "Rester à <b>11 PO minimum</b> de lui : il peut s'échanger jusqu'à 10 PO (6 PO sort + 4 PM).",
    ]),
    h("Succès « Liberté » (aucun retrait PM/PO)", GOLD),
    p("Un <b>tank</b> (idéalement Pandawa) en coin bas-gauche attire le Chaloeil au contact (face Dé 6), "
      "vos autres persos à l'opposé (bas-droite). Le tank, max résistances, se soigne chaque tour sur les glyphes blancs. "
      "Surveiller les monstres à 10 PO du Chaloeil : leur mettre <u>Pesanteur</u> avant son tour pour bloquer l'échange."),
    fig("dp_chaloeil_34.png", "Succès Liberté — placement conseillé (rouge Chaloeil · bleu vos persos · orange dés · blanc glyphes de soin)"),
])

GUIDES_200["sylargh"] = "".join([
    fig("dp_sylargh_24.png", "Sylargh — niveau 220, 13 000 PV", 300),
    h("Rendre Sylargh vulnérable", RED),
    p("Sylargh démarre <b>invulnérable</b> et <b>Lourd</b> tout le combat. Tous les monstres (lui compris) ont l'effet "
      "<b>Nécromignon</b> : un monstre tué est <u>réinvoqué en Zombi</u> (10% de ses PV, ~660) par le prochain monstre qui joue, "
      "à exactement <b>6 PO</b> de son invocateur (1<sup>re</sup> case libre dans le sens horaire)."),
    p("Tuer un monstre réinvoqué déclenche <b>Zombidule</b> (cercle 5) : 1200 Feu dégressif à <u>tout le monde</u>, "
      "+100 dommages 2 tours (cumulable ×3), OS les autres Zombis, et si <b>Sylargh est entre 5 et 10 PO</b> "
      "du Zombi tué → il est <b>vulnérable 1 tour</b>."),
    note("Placer Sylargh à <b>5-10 PO</b> d'un Zombi avant de le tuer (pile 5 PO : vulnérable avant de prendre les "
         "dégâts). Trop près, il reste invulnérable. Chaîne de Zombis proches de lui = énormes dégâts Feu.", ORANGE, "CLÉ"),
    figs([("dp_sylargh_28.png", "Réinvocation à 6 PO : cases 1 à 7, dans l'ordre (sens horaire)"),
          ("dp_sylargh_29.png", "Zone 5-10 PO autour du Zombi tué : Sylargh y devient vulnérable"),
          ("dp_sylargh_34.png", "Zombidule : explosion en cercle de 5 (dégressif)"),
          ("dp_sylargh_31.png", "Effet Nécromignon : état Zombi")]),
    h("État Pacifiste", RED),
    p("Tuer un Zombi rend <b>Pacifiste 1 tour</b> (non débuffable) tous les persos à <b>90% PV ou plus</b>. "
      "Restez <u>sous 90% PV</u> en permanence : tapez un allié si besoin, ne prenez pas de pain en début de combat."),
    fig("dp_sylargh_30.png", "Rester sous 90 % de PV (le pourcentage s'affiche en survolant l'allié)", 341),
    h("Réinvocation en chaîne", GOLD),
    p("C'est toujours le <b>dernier monstre tué</b> qui est réinvoqué ; plusieurs morts = réinvocations à la chaîne "
      "(Sylargh inclus s'il meurt alors qu'il reste des monstres). <b>Focus le 1<sup>er</sup> monstre réinvoqué</b> : "
      "ceux qu'il a invoqués meurent avec lui. Les Zombis sont Indéplaçables 1 tour, +300 dommages 2 tours, ne jouent pas leur 1<sup>er</sup> tour."),
    fig("dp_sylargh_33.jpg", "Réinvocations en chaîne : Sylargh → Mécanofoux → Mansordide → Brikoglours, chacun à 6 PO du précédent"),
    h("Sorts de Sylargh", GOLD),
    ul([
        "<b>Dégage de qualité</b> (mêlée) : un monstre allié +500 dommages / +200 tacle 1 tour et repoussé de 3.",
        "<b>Mortier</b> (10 PO modifiable, 2×/tour) : 650 Terre + 650 Eau par ligne de dégâts mêlée subie → <u>jouer à distance</u>.",
        "<b>Poinçon</b> (1 PO) : 1100 Air vol de vie, retire tous les envoûtements, −100 fuite.",
    ]),
    figs([("dp_sylargh_25.png", "Dégage de qualité"), ("dp_sylargh_26.png", "Mortier (portée modifiable)")]),
    h("Les monstres", ORANGE),
    ul([
        "<b>Brikoglours</b> : inoffensif à distance mais énorme à 2 PO, attire de 2 cases jusqu'à 6 PO en ligne.",
        "<b>Mécanofoux</b> (Expulsar) : 2 tours sur 3 repousse tout en étoile 4 de 4 cases ; tape en ligne sans LDV à longue distance.",
        "<b>Mansordide</b> (Rotativernal) : 2 tours sur 3 renvoie 100% des dégâts aux ennemis alignés avec lui ; soigne ses alliés. Ne pas le taper avec des alliés en ligne.",
    ]),
    h("Stratégie", GREEN),
    ul([
        "Retirer PO/PM de Sylargh (Mortier à PO modifiable).",
        "Focus les monstres avant Sylargh : <b>Mansordide</b> (soin) puis <b>Mécanofoux</b>.",
        "Placer Sylargh/monstres plutôt à gauche pour que les réinvocations (priorité horaire) ne tombent pas sur vous.",
        "S'écarter à 5 PO des Zombis avant de les finir (dégâts dégressifs).",
    ]),
    fig("dp_sylargh_35.jpg", "Sylargh placé tout à gauche : les Zombis réapparaissent loin de l'équipe"),
])

GUIDES_200["klime"] = "".join([
    h("Rendre Klime vulnérable", RED),
    p("Klime est <b>invulnérable</b> (impossible avant le début du tour 3). Pour lui retirer l'état 1 tour : "
      "il doit subir des <b>dommages de poussée indirects</b> — pousser un allié, une invocation ou un ennemi <u>sur Klime</u>."),
    note("<b>Tuer Klime en dernier.</b> Ne lui retirez pas l'invulnérabilité tant qu'il reste des monstres : "
         "devenu vulnérable il gagne <b>Cuir à feu doux</b> (renvoie tout le monde à sa position de début de tour, "
         "échange avec vos persos présents sur ces cases, −6 PM, +100 tacle +300 dommages ; relance 2 tours).", ORANGE, "ORDRE"),
    h("Pacifiste & glyphes (Carcassetagne)", RED),
    p("À chaque début de tour Klime met <b>tous ses ennemis Pacifistes 1 tour</b>. Vos persos sont protégés les "
      "2 premiers tours par <b>Peau lisse</b>. Ensuite, la seule parade : <b>finir son tour sur un glyphe blanc</b> "
      "(taille 1, posé par Klime et chaque monstre à chaque début de tour, dure 2 tours → 2 glyphes par monstre)."),
    ul([
        "Placer dès le <b>tour 2</b> tous les persos qui doivent taper sur un glyphe. Un glyphe donne Peau lisse aux persos "
        "et <b>+300 dommages 2 tours</b> aux monstres qui finissent dessus (débuffable).",
        "Un perso qui joue après un autre peut le <u>déloger</u> du glyphe pour prendre sa place. Un support qui ne tape pas peut rester Pacifiste.",
        "Un monstre tué = ses 2 glyphes disparaissent. Si tous les monstres sont morts avant le tour 3, Pacifiste arrive seulement au tour 4.",
        "Quand il ne reste que Klime et que les 2 glyphes sont pris, déplacer les occupants pour se mettre dessus.",
    ]),
    h("Sorts de Klime", GOLD),
    ul([
        "<b>Cuir Moustache</b> (ligne, 7 PO sans LDV, 2×/tour) : attire de 6 cases + poison Feu 250 sur 3 tours.",
        "<b>Moustacheron</b> (mêlée, 2×/tour) : 250 Feu + 250 Air vol de vie + 10% de ses PV manquants en Neutre.",
    ]),
    h("Conseils", GREEN),
    ul([
        "<b>Moins il a de PV, plus il tape fort</b> : le finir vite une fois entamé.",
        "Ne pas se mettre en ligne avec le <b>Cuirboule</b>.",
        "Inutile de finir sur un glyphe avec un perso qui ne tape pas.",
    ]),
])

GUIDES_200["missiz_frizz"] = "".join([
    h("États de base", RED),
    p("Missiz Frizz et tous les monstres sont <b>Lourds</b> et <b>Invulnérables</b> au départ. "
      "On retire l'invulnérabilité d'un ennemi (1 tour) en le <b>repoussant</b> avec les congères ou l'effet Monogel."),
    h("Congères de Missiz", ORANGE),
    p("À chaque début de tour d'un perso (pas les invocations), un glyphe noir apparaît sur ses <b>4 cases adjacentes</b>. "
      "Marcher sur l'une d'elles : <b>soigne 15% PV max</b>, vous repousse d'1 case de plus, puis (fin de déplacement) "
      "<b>repousse d'1 case</b> tous les alliés et ennemis en croix de taille 6 et croix diagonale de taille 3 autour de vous, "
      "et révèle si invisible. La congère disparaît une fois utilisée."),
    note("Un ennemi repoussé par une congère <b>perd son invulnérabilité 1 tour</b>. Si vous ne bougez pas, un 2<sup>e</sup> glyphe "
         "se pose dessus et les effets s'appliquent en double.", GREEN, "ASTUCE"),
    p("<b>Monogel</b> (sur tout le monde) : toute entité <u>poussée</u> par un sort de déplacement se soigne de 15% et repousse "
      "d'1 case les entités en ligne/diagonale à 6 PO — autre moyen de casser l'invulnérabilité. "
      "<b>Attention aux dommages de poussée</b>, amplifiés par Missiz Frizz."),
    h("Glace de pic & Surgelé", RED),
    p("Quand Missiz Frizz subit des dégâts, elle <b>attire au contact</b> tous les persos en ligne/diagonale avec elle et leur met "
      "l'état <b>Surgelé</b> (Sang froid fait alors +800 Eau en vol de vie)."),
    h("Sorts", GOLD),
    ul([
        "<b>Cristallisation</b> (dès le tour 2, relance 3) : elle et tous les monstres deviennent Intacleurs 1 tour ; tout retrait PM sur un ennemi lui <u>donne 3 PM</u>.",
        "<b>Sang froid</b> (4 PO, 2×/tour) : 800 Feu, +800 Eau vol de vie si Surgelé ; invocations touchées Intacleurs 2 tours.",
        "<b>Glace trop physique</b> (8 PO) : 20% érosion, 550 Feu + 35% des PV érodés en Air, Intaclable 1 tour.",
    ]),
])

GUIDES_200["nileza"] = "".join([
    p("Le plus abordable des donjons 200 : <b>pas d'invulnérabilité</b>, mais un passif <b>Cohobation</b> à 5 mécaniques."),
    h("1. One shot : Chifouchimie", RED),
    note("Si un perso <b>finit son tour au contact d'un autre perso</b>, ce dernier est <u>OS</u> (invocations ignorées). "
         "Toujours finir ses tours séparés.", RED, "OS"),
    h("2. Ogavodra & Molalité illéplochable", ORANGE),
    ul([
        "<b>Ogavodra</b> : à chaque ligne de dégâts <u>à distance</u>, Nileza <b>échange de place</b> avec l'attaquant, qui reçoit un glyphe rose "
        "(10% de ses PV érodés en Neutre, −100 fuite et −100 tacle 1 tour, cumulable, persiste hors glyphe).",
        "<b>Molalité</b> : à chaque dégât à distance, 40% d'érosion 1 tour et <b>renvoie 200% des dégâts en Air</b> à toutes les entités "
        "(alliés et ennemis) dans un cercle 2 autour de sa nouvelle case — <u>après</u> l'échange de place. Pratique pour tuer les monstres qui l'entourent.",
        "Frapper en mêlée est déconseillé : Liqueur de Fée Ling (2 tours sur 3) le soigne de 5% et le boost +300 dommages par ligne de mêlée.",
    ]),
    h("3. Pacifiste à distance", RED),
    p("Tours impairs dès le 3 (début de son tour), les persos <b>trop loin de lui</b> deviennent Pacifistes 2 tours "
      "(non débuffable) et la zone se resserre :"),
    ul([
        "<b>Tour 3</b> — plus de 11 PO : Pacifiste · tous −200 fuite.",
        "<b>Tour 5</b> — plus de 9 PO : Pacifiste · tous −200 tacle.",
        "<b>Tour 7</b> — plus de 7 PO : Pacifiste · tous Pesanteur 2 tours.",
        "<b>Tour 9, 11, 13…</b> — plus de 5 PO : Pacifiste · tous Insoignable 2 tours.",
    ]),
    p("Nileza est <b>fuyard</b> et recule après ses sorts : le taper pour s'échanger avec lui le ramène près de vous."),
    h("4. Mélange Instable (selon ses PV)", GOLD),
    ul([
        "<b>75-100% · Acide</b> : +1% dommages finaux, −2% résistances à chaque attaque (2 tours, cumulable).",
        "<b>40-74% · Amer</b> : +10% soins finaux, mais soigné = dégâts Neutre de 5% des PV actuels.",
        "<b>0-39% · Aigre</b> : +30% critique, mais chaque coup critique fait perdre 1 PM (2 tours, cumulable).",
    ]),
    h("Sorts de Nileza", GOLD),
    ul([
        "<b>Fraction de molaire</b> (ligne, 12 PO modifiable, 2×/tour) : 550 Eau + Terre = 10% (15% crit) de ses PV manquants, repousse de 3.",
        "<b>Glace sèche</b> (2 PO sans LDV) : échange de place + 750 Feu en croix 1 ; la cible subit même hors zone.",
        "<b>Liqueur de Fée Ling</b> (tour 1 puis tous les 3 tours) : vampirisme/boost sur les dégâts de mêlée subis.",
    ]),
])

GUIDES_200["merkator"] = "".join([
    h("Mer Kantile (tout le combat)", RED),
    ul([
        "Merkator <b>réduit de 50%</b> les dégâts subis <u>à distance</u> et gagne <b>+2% dommages finaux</b> à chaque dégât à distance reçu.",
        "Lui et tous les monstres sont <b>Indéplaçables</b>.",
    ]),
    h("Mer Veille", ORANGE),
    p("Toute tentative de <b>retrait PM</b> sur un monstre vous inflige ~500 Feu en vol de vie : éviter."),
    h("Mer Cure : seul moyen de déplacer les monstres", GREEN),
    ul([
        "<b>Taper un monstre en mêlée</b> : il repousse de 3 cases ses alliés en croix 3 (malgré Indéplaçable) <u>et</u> ses ennemis en croix diagonale 3.",
        "<b>Taper un allié avec une arme</b> : il repousse de 3 les monstres en croix diagonale 3 autour de lui et vos persos en croix 3.",
    ]),
    h("Marée descendante (tours impairs, dès le 3)", RED),
    p("Via <b>Baphe Thysca</b> : Merkator <b>attire jusqu'à 11 cases</b> tous les persos en croix de taille 12 à son contact et leur retire 4 PM. "
      "Baphe Thysca fait aussi monter les dégâts de Sondage de Bronze de +30 par dégât subi (cumulable 5 fois, 1 tour). Dès le tour 2, relance 2 tours."),
    h("Sorts", GOLD),
    ul([
        "<b>Sondage de Bronze</b> (ligne, 3 PO) : 950 Terre en ligne de 5.",
        "<b>Torpillage de Glace</b> (mêlée, 2×/tour) : 1100 Eau, −50% vitalité de la cible (60% crit) 1 tour + Pesanteur.",
        "<b>Bouche-à-Bouche</b> (dès le tour 7, relance 5) : réinvoque le dernier allié mort avec 50% de ses PV, 6 PO sans LDV → <u>garder un monstre vivant en fin de combat ou le finir vite</u>.",
    ]),
])

GUIDES_200["roi_nidas"] = "".join([
    p("Donjon de dimension relativement accessible : vagues de monstres tous les 5 tours (<b>tours 1, 6, 11, 16, 21</b>), "
      "monstres de la 1<sup>re</sup> vague à 6600 PV, Roi Nidas 15 000-22 000 PV selon le nombre de persos. "
      "Les vagues réapparaissent aux cases de départ ; si des monstres restent, les nouveaux jouent en fin de timeline. "
      "Jeu à distance conseillé : dégâts distance, entrave (PM/PO), placement."),
    h("Sorts du Roi Nidas (IA agressive)", RED),
    ul([
        "<b>Attrape-mutin</b> (ligne 1-6 PO, LDV, dès le tour 2) : 600 Neutre, attire de 6 et échange de place.",
        "<b>Confusion</b> (1-5 PO, LDV) : 500 Air cercle 2 + état <b>Zizanie</b> : à son tour suivant, les persos Zizanie infligent des dégâts "
        "autour d'eux (cercle 2) et retirent 2 tours d'effets aux touchés → <u>aucun perso à 2 PO d'un Zizanie</u>.",
        "<b>Liquidation</b> (1-5 PO, croix diagonale 1) : 500 Feu + Eau = 20% des PV érodés du lanceur.",
        "<b>Mon Précieux</b> (10 PO sans LDV, tours 3, 5, 7…) : échange de place avec la Boubourse.",
    ]),
    p("<b>Astuce</b> : tenir Roi Nidas à distance jusqu'à sa mort."),
    h("La Boubourse", ORANGE),
    ul([
        "Commence collée au Roi Nidas, <b>n'est pas une invocation</b>, joue en dernier à l'initiative.",
        "<b>Seuil à 1 PV</b> : elle passe dans <u>votre camp 2 tours</u> puis retourne au contact du Roi.",
        "Côté ennemi : <b>Cadeau Empoisonné</b> = +200 puissance et +30% crit à tous les monstres (+300 / +50% crit sur le Roi).",
        "Côté allié : +500 bouclier à vos persos (hors invocations), retire 2 tours d'effets sur la bourse, tue les invocations en mêlée de la cible.",
    ]),
    h("Stratégie", GREEN),
    p("Tuer vite pour ne pas être submergé à l'arrivée de la vague suivante. Surveiller le <b>Lévitrof</b> "
      "(échange de position avec Reflets placides), le <b>Kamastérisk</b>, le <b>Piloztère</b> et la Boubourse."),
    h("Succès", GOLD),
    ul([
        "<b>Premier</b> (Roi Nidas tué en premier) : éviter l'élément <u>Terre</u> (42% rés.), prendre de l'entrave pour ne pas être gêné. Base : Roublard + Pandawa, ou Eliotrope + Écaflip/Iop.",
        "<b>Statue</b> (finir chaque tour sur sa case de départ) : compo très forte à distance avec beaucoup d'entrave, placement final rapide (Pandawa conseillé). Dangers : Lévitrof, Roi Nidas.",
        "<b>Pingrerie</b> (n'attaquer qu'en ligne/diagonale de la cible) : attention aux sorts de zone qui touchent des monstres hors ligne.",
    ]),
])

GUIDES_200["protozorreur"] = "".join([
    p("Le Protozorreur est <b>invulnérable</b> (les coups touchent la <b>Malamibe</b>, comme pour les autres Krobes) et "
      "<b>indéplaçable</b>. Il se tue en le maintenant <b>6 tours d'affilée</b> dans l'état « Infection »."),
    h("Le déplacer : attirance", ORANGE),
    p("Si vous lui infligez des dégâts <u>en étant aligné avec lui</u>, il est <b>attiré à votre contact</b> — uniquement sur le "
      "<b>premier coup reçu dans le tour</b>."),
    h("Protoglyphe infectieux", RED),
    p("Tout perso qui subit des dégâts (de n'importe quelle source) laisse un <b>glyphe violet de taille 1</b> : 550 Air au passage, "
      "et si le Protozorreur s'y retrouve il entre en <b>Infection 3 tours</b> (+2 PM tant qu'il y est)."),
    note("Méthode : aligner le Protozorreur avec un glyphe violet, placer le glyphe <b>entre vous et lui</b>, le frapper avec un sort <u>peu coûteux en PA</u> "
         "→ il est attiré et s'arrête dans le glyphe. Pas besoin d'être à 1 case : un glyphe sur le trajet l'arrête. "
         "Renouveler <b>au minimum tous les 2 tours</b> (au bout de 3 tours l'Infection se perd et il faut tout recommencer). "
         "<b>6 tours d'Infection d'affilée = mort.</b>", GREEN, "PROCÉDURE"),
    note("À l'entrée en Infection, son passif est réinitialisé : si votre 1<sup>re</sup> attaque est alignée il sera de nouveau attiré. "
         "Le taper d'abord une fois <u>sans être en ligne</u>. Le perso qui l'attire doit jouer <b>tôt dans l'initiative</b> : "
         "seuls les premiers dégâts du tour comptent, les persos qui jouent avant lui ne pourront pas le taper (Malamibe).", ORANGE, "ATTENTION"),
    h("Sorts (différents en et hors Infection)", GOLD),
    ul([
        "<b>Protomatisme</b> : +100 puissance à chaque début de tour (réinitialisé à l'Infection).",
        "<b>Jet Proto</b> (ligne, 10 PO, 2×/tour) : 500 Air ; hors Infection +5 dégâts cumulés à chaque lancer ; en Infection, attire au contact.",
        "<b>Électrocution</b> (2 PO sans LDV, 2×/tour) : 1000 Feu ; hors Infection −6 PM, en Infection −6 PA (1 tour, débuffable).",
        "<b>Infection</b> (dès le tour 3, relance 3) : tue les invocations en mêlée. Hors Infection : 20% érosion + repousse 3 (cercle 3). En Infection : Eau = 50% des PV érodés à tous + attire de 3 (cercle 4).",
    ]),
])

GUIDES_200["capitaine_meno"] = "".join([
    h("Principe : survivre et monter en puissance", ORANGE),
    p("Le Capitaine Meno <b>n'est pas invulnérable</b> mais a <b>40 000 PV</b> (butin 4 ; 60 000 en butin 8) et "
      "<b>réduit de 50% les dégâts qu'il subit</b> (sauf <u>poisons</u>). En contrepartie, tous vos persos gagnent <b>+20% dommages finaux "
      "à chaque tour</b> (infini, cumulable) : peu de dégâts au début, énormes ensuite. Il faut environ <b>une dizaine de tours</b> "
      "pour l'abattre — le combat est un combat de survie."),
    ul([
        "Chaque dégât infligé à vos persos (par lui ou un monstre) <b>soigne Meno</b> du même montant.",
        "<b>Dès le tour 2</b> il invoque <b>2 monstres par tour</b> (3 à partir du butin 5), selon un cycle fixe parmi Crabe Yoloniste, Mol Husk, Gambaf, Mantaze, Tilamproie.",
        "Tous les monstres sont <b>invulnérables</b> (Mutation Instable) et perdent <b>25% de leurs PV max par tour</b> : morts au bout de 4 tours, −1 PM permanent. Inutile de les focus.",
    ]),
    h("Sorts de Meno", GOLD),
    ul([
        "<b>Matière Volatile</b> (4 PO sans LDV) : 500 Air.",
        "<b>Crystalisation</b> (10 PO, 2×/tour) : 500 Eau + <b>glyphe permanent</b> de taille 1 sur la cible (état « Crystalisation » si on y finit son tour).",
        f"<b>Déclenchement</b> : au début de son tour, chaque glyphe <u>occupé</u> inflige {r('1300 Feu')} à tous les persos alignés avec l'occupant jusqu'à 5 PO (et dévoile les invisibles). Glyphe vide = aucun effet.",
    ]),
    h("Conseils", GREEN),
    ul([
        "Classes à <b>retrait PM / placement à distance</b> (Cra, Enutrof, Sadida…) pour tenir.",
        "<b>Poisons</b> : seuls dégâts non réduits de moitié sur Meno.",
        "Se placer chacun <b>sur un glyphe</b> (bouclier à chaque tour) <u>sans jamais être en ligne à ≤5 PO d'un autre perso/monstre sur glyphe</u> : en diagonale les uns des autres.",
        "Laisser Meno poser les glyphes sur vous (1 par perso). Taper Meno dès que possible : toujours de l'érosion en plus.",
        "Soigner les cibles d'<b>Éclair Obscur</b> (Mantaze) pour retirer l'état « Conducteur ».",
    ]),
])

GUIDES_200["dantinea"] = "".join([
    h("Grokillages : lien et dégâts réduits", RED),
    p("Dantinéa <b>n'est pas invulnérable</b>. Au début, elle invoque <b>autant de Grokillages</b> (0 PA/PM, 1000 PV) que de persos. "
      "Chaque perso est lié à un Grokillage (par numéro) : <b>tant qu'il est vivant, votre perso ne fait que 50% de ses dégâts</b> "
      "(monstres, Grokillages, Dantinéa) et <b>perd 1 PM par tour</b>."),
    ul([
        "Positions des Grokillages et numéros <u>toujours fixes</u>. L'attribution dépend de la case de départ de chaque perso "
        "(10 cases de placement avec ordre de priorité) — depuis la 3.7, une <b>rune</b> indique où le Grokillage apparaît.",
        "Un Grokillage tué = son perso retrouve sa force de frappe normale.",
    ]),
    note("Tous les <b>5 tours</b> (tours 6, 11, 16…) Dantinéa <u>OS tous ses Grokillages encore en vie ET les persos liés</u>, puis en réinvoque. "
         "Avoir tué <b>tous les Grokillages avant le tour 6, 11, 16…</b>", RED, "DEADLINE"),
    p("Tuer Dantinéa élimine tous les Grokillages restants, définitivement, et libère les dégâts de tout le monde."),
    h("Sorts de Dantinéa", GOLD),
    ul([
        "<b>Pacte Maléfique</b> : invoque les Grokillages liés aux persos.",
        "<b>Siphon d'Âme</b> (3 PO, 2×/tour, 1×/cible) : 1000 Neutre en vol de vie.",
        "<b>Danse Tentaculaire</b> (autour d'elle, cercle 2) : 600 Terre + 600 Air.",
        "<b>Cooquillation</b> (6 PO sans LDV, dès le tour 2 puis tous les 2 tours) : échange de place avec un de ses Grokillages.",
        "<b>Début de chaque tour</b> : 600 Eau à tous les persos <u>en ligne avec les Grokillages</u> ; elle peut se téléporter via eux.",
    ]),
    h("Stratégie", GREEN),
    ul([
        "D'abord tuer les Grokillages des persos <b>à plus forte force de frappe</b> pour les libérer.",
        "Ensuite les monstres, par proximité, avec ce focus : <b>Tryde</b> (le plus gênant) → <b>Rilur</b> → <b>Diondin</b>.",
        "Les persos encore liés frappent ce qu'ils peuvent (leurs propres Grokillages en priorité).",
        "Éviter de finir en ligne avec un Grokillage.",
    ]),
])

GUIDES_200["tal_kasha"] = "".join([
    h("Invulnérabilité & monstres infinis", RED),
    p("Tal Kasha est <b>invulnérable</b> (Malédiction de la pyramide), qui lui permet aussi de réutiliser les monstres à l'infini. "
      "Quand un monstre meurt il laisse un <b>glyphe marron</b> sur sa case et est <b>ressuscité au tour suivant par Tal Kasha</b> "
      "exactement là (il passe son premier tour et perd 1 PM, non cumulable). Retuer un monstre déplace le glyphe sur sa dernière mort."),
    note("<b>Désactiver l'invulnérabilité</b> : faire passer Tal Kasha sur <b>3 glyphes laissés par 3 monstres différents</b> "
         "(chiffres romains I à III au-dessus d'elle). Même règle à plus de 4 persos (3 glyphes de 3 monstres suffisent). "
         "Il faut donc tuer des monstres puis la déplacer dessus.", GREEN, "CLÉ"),
    p("<b>Érodez les monstres au maximum</b> : ressuscités avec très peu de vitalité, ils se retuent en un coup et ne gênent plus."),
    h("Piège du retrait PM", ORANGE),
    p("Quand vous lui retirez des PM, elle <b>échange de place avec vous</b> (1×/tour), impossible à éviter (même avec Stabilisation/Pesanteur). "
      "Ne lui retirez pas de PM trop tôt, elle atterrirait au milieu de votre équipe. Un Pandawa qui porte le perso peut contourner."),
    h("Sorts", GOLD),
    ul([
        "<b>Filature</b> (ligne, 5 PO, LDV) : 500 Feu + attire de 4 cases.",
        "<b>Transe-Perse</b> (mêlée) : 1700 Neutre.",
        "<b>Cheveux partir de là</b> (uniquement vulnérable, ligne, relance 2 tours) : téléportation jusqu'à 4 PO — attention à ne pas la laisser arriver au centre de l'équipe.",
    ]),
    note("Elle peut lancer <b>Filature et Transe-Perse comme si elle était à la place de n'importe lequel de ses alliés</b> : "
         "ne <u>jamais</u> rester en ligne avec elle ou un monstre (au tour de Tal Kasha). Plusieurs persos alignés : elle vise le plus proche du monstre.", RED, "ALIGNEMENT"),
    h("Stratégie", GREEN),
    ul([
        "Jeu à distance, retrait PM. <b>Enutrof</b> (retrait PM) pour placer les monstres/Tal Kasha sur les glyphes, <b>Cra</b> pour la repousser loin et éloigner les monstres.",
        "Vulnérable ensuite : la tuer à distance, sans retoucher aux monstres (succès Focus).",
    ]),
    h("Succès Focus", GOLD),
    p("Un ennemi attaqué doit être achevé avant d'en attaquer un autre : érodez chaque monstre au maximum avant de les tuer un par un, "
      "puis, une fois le boss désactivé et entamé, <u>ne plus toucher aux monstres</u>."),
])

GUIDES_200["bethel"] = "".join([
    note("Il faut le sort <b>Nécronyx</b> : tout monstre (Bethel compris) doit être sous Nécronyx <u>avant de mourir</u>, sinon toute l'équipe est OS. "
         "Depuis la mise à jour du 20/01/2026, Bethel <b>retire son Nécronyx au bout de 3 tours</b> (au tour du perso qui l'a posé) : "
         "tour 1 → à refaire au tour 4.", RED, "NÉCRONYX"),
    h("Glyphe de bord de map", ORANGE),
    p("Le pourtour de la map vous met <b>−100 PM et Pesanteur</b>. Bethel (sans Nécronyx, à 6 PO) vous <b>repousse</b> dedans : "
      "<u>Nécronyx Bethel dès le tour 1</u>."),
    h("Aquazomb", RED),
    p("À partir du tour 2, <b>finir son tour à moins de 6 PO d'un monstre</b> ou de Bethel (invocations, Monolithe et monstres réinvoqués ne comptent pas). "
      "Sinon : +2 PM et +1 PO 1 tour (cumulable, débuffable) à tous les monstres et déclenchement de leurs effets spéciaux."),
    h("Le rendre vulnérable", GREEN),
    ul([
        "<b>1. Tuer le Monolithe</b> : invulnérable à distance (mêlée uniquement), gagne 20% PV max en bouclier (2600 en butin 4) et repousse de 2 à son contact.",
        "<b>2.</b> Il meurt : le <b>Dagon des profondeurs</b> est réinvoqué <u>dans votre camp</u>, contrôlé par le perso le plus proche à ce moment. "
        "S'il meurt, Bethel réinvoque Monolithe + Dagon ennemis.",
        "<b>3.</b> Seul le Dagon peut frapper Bethel (≈1000 par tour), en mêlée via <b>Souffle Chaud</b> : le booster au maximum.",
        "Bethel gagne alors <b>Étoile de Mer</b> : grand glyphe en étoile, 700 Eau et −4 PA/−2 PM tant qu'on y reste.",
    ]),
    h("Dagon des Profondeurs (ennemi)", ORANGE),
    p("Frappe fort en mêlée et retire beaucoup de PA, 4 PM mais <b>s'attire jusqu'à 8 PO</b> en ligne (Charge Aquatique, −60 fuite). "
      "Intaclable. <b>Le pousser une fois par tour</b> le met Inébranlable 1 tour : il ne peut plus s'attirer. Toujours le même perso, qui joue tôt."),
    h("Sorts de Bethel", GOLD),
    ul([
        "<b>Contrat Indicible</b> : invoque un Monolithe et un Dagon (Bethel et Dagon invulnérables).",
        "<b>Pantang</b> (1-12 PO) : 500-800 Air. <b>Offrande Monolithique</b> : Amas de Tentacules (110 PV) collés à vos persos, +300 puissance Bethel / +200 monstres.",
        "<b>Monolithe — Hiéroglyphes</b> : bouclier 2600 aux monstres en cercle 4, +200 puissance aux invocations.",
        "<b>Dagon</b> : Présence Effrayante (−3 PA au contact), Souffle Chaud (600-900 Feu, −2/3 PA).",
    ]),
])

GUIDES_200["dazak"] = "".join([
    h("Résistances à plus de 100%", RED),
    p("Dazak Martegel a <b>plus de 100% de résistance dans chaque élément</b>. Pour les faire baisser : "
      "il gagne un niveau de <b>Nimpatience</b> à chaque tour où il <u>ne vous tape pas</u> (+50% dommages finaux et +1 PM infini par niveau). "
      "Au niveau 3 (<b>Nimpatience 3</b> : +3 PM et +150% dommages finaux 2 tours), il ne gagne plus de Nimpatience pendant <b>2 tours</b> :"),
    ul([
        "<b>Chaque fois que vous le poussez ou l'attirez</b> : −5% de résistances dans tous les éléments (infini).",
        "Dommages de <u>poussée</u> (contre obstacle) : il gagne +10% de résistances — à éviter.",
        "Les résistances perdues <b>ne se regagnent pas</b> : si ce n'est pas assez, recommencer au prochain Nimpatience 3.",
        "Iop : <b>Friction</b> / <b>Coup par coup</b> retirent 5% par déplacement lors du coup — à abuser.",
    ]),
    h("Sorts de Dazak", GOLD),
    ul([
        "<b>Empalement royal</b> (mêlée, 2×/tour) : 1500 Neutre, 40% érosion 2 tours, −10% résistance (infini).",
        "<b>Ninfiltration</b> (ligne, 5 PO, tours pairs dès le 2) : bond de 5 cases, 900 Air, −4 PM esquivables autour de l'arrivée (hache 1).",
        "<b>Nintrépidité</b> (tours 3, 5, 7…) : alliés +2 PM et 1500 PB 1 tour (désenvoûtable : Souillure, Pelle Fantomatique…).",
    ]),
    h("Les monstres", ORANGE),
    ul([
        "<b>Tanklume</b> : éviter à tout prix son Nimpatience 3 — le tuer avant, ou le laisser taper un perso pour qu'il ne gagne pas de Nimpatience. Utiliser son <b>Ninrmure</b> (sacrifice) pour le tuer en zone.",
        "<b>Boufbos</b> : son seul sort se lance à 3 PO minimum, en ligne : le tacler (bloqué contre un mur pour empêcher Forte tête) ou <u>couper les lignes</u> avec des obstacles.",
    ]),
    h("Stratégie", GREEN),
    p("Retrait PM apprécié, <b>Cra</b> très fort. Surveiller les tours pairs (Ninfiltration). Il existe plusieurs stratégies selon les succès visés "
      "(voir le guide complet)."),
])

GUIDES_200["kao"] = "".join([
    h("Éclats de Kao & vulnérabilité", RED),
    p("La Prêtresse de Kao est <b>invulnérable</b> (Artisanat du Kao). Pour la rendre vulnérable : <b>tuer 3 Éclats de Kao</b>. "
      "Chaque éclat tué ajoute un chiffre romain (I, II, III, irréversible) ; au <b>III</b> elle est vulnérable <u>pour le reste du combat</u>. "
      "Éclat en vie : elle est <b>Intaclable</b>."),
    ul([
        "Éclat qui <b>meurt seul</b> après 2 tours sans être tué : pas de chiffre.",
        "Éclat qui perd son boost de PV (≤1000 PV) : chiffre ajouté.",
        f"Chaque chiffre donne un état qui boost ses dégâts <u>infiniment</u> : {o('I Forastero')} +52% · {o('II Trinitario')} +74% · {o('III Criollo')} +99% dommages finaux.",
    ]),
    note("Si vous ne visez pas le succès <b>Premier</b> : <u>ne tuez pas les éclats</u> tant que les monstres sont là, pour ne pas booster la Prêtresse inutilement. "
         "Tuer d'abord les monstres, avec des <b>poisons</b> (non affectés par la réduction de 50% de dégâts).", GREEN, "ASTUCE"),
    h("État Chocolathée", ORANGE),
    p("Quand vous <b>entamez</b> un éclat, il met <b>Chocolathée</b> à chaque perso qui lui inflige directement des dégâts "
      "(et Cloches du Kao tape plus fort par perso Chocolathée). Pas d'état si l'éclat est tué <b>en une seule ligne</b>, "
      "par poisons, invocations, bombes ou mur de bombes (le <b>Roublard</b> excelle). Sinon, <u>toujours le même perso</u> pour limiter."),
    h("Sorts", GOLD),
    ul([
        "<b>Cloches du Kao</b> (tours impairs) : 300 Neutre à tous, +50 de dégâts de base par perso Chocolathée.",
        "<b>Equador</b> : alliés +50 dommages et ~200 PV de soin autour d'elle (cercle inversé 6).",
        "<b>Spatule Tranche-Gourmands</b> (ligne 4) : 260 Air, −50 fuite. <b>Commerce Inéquitable</b> (8 PO) : 350 Neutre, vole 1 PM (2 en crit).",
    ]),
    h("Conseils", GREEN),
    ul([
        "<b>Terre</b> : la Prêtresse y est faible (succès Premier). Résistances <b>Neutre</b> utiles (elle et le Torréfactueur tapent en Neutre).",
        "Mettre <b>Pesanteur</b> au Chocoligarque : il ne peut plus échanger de place (Ganache).",
        "Soin et protection (<b>Eniripsa, Zobal, surtout Féca</b>) très utiles : le combat dure à cause des éclats.",
    ]),
])

GUIDES_200["guerre"] = "".join([
    h("Phase 1 : Guerre invulnérable", ORANGE),
    p("<b>Arsenal</b> (dès le début) : Guerre est <b>Indéplaçable</b> tout le combat et garde l'état <b>Compagnon de combat</b> sur ses monstres : "
      "<u>tant qu'il reste un monstre, elle est Invulnérable</u>. Peu dangereuse à ce stade : "
      "<b>Magmaléfice</b> (6 PO, cercle 2, 500 Feu) et <b>Martyre</b> (mêlée, 700 Terre en vol de vie). Si elle vous colle, "
      "son Indéplaçable réduit votre mobilité."),
    p("Tuer tranquillement les monstres : d'abord le <b>Trancharnier</b> (il se téléporte sur vous), puis l'<b>Olgoth</b> "
      "(le descendre à 2750 PV à distance puis finir en mêlée), enfin le <b>Ravalame</b>."),
    h("Phase 2 : Guerre sur sa monture (vulnérable)", RED),
    p("Le tour suivant la mort du dernier monstre, elle devient vulnérable et lance <b>Bravoure</b> (relance 3 tours, indébuffable) "
      "sur elle et un de vos persos/invocations : état <b>Brave</b> 2 tours. Elle gagne +200 tacle/fuite et +2 PM ; "
      "la cible reçoit <b>Pesanteur, Insoignable et Lynchage</b> (Pesanteur/Insoignable débuffables)."),
    ul([
        "Guerre <b>ne tape que le perso Brave</b> pendant ces 2 tours (Lynchage 400 Feu en mêlée, Impact 450 Feu + 20% érosion).",
        "Tout <u>autre</u> perso qui la frappe pendant l'état Brave devient <b>Pacifiste</b> jusqu'à son prochain tour ; le perso Brave peut la taper sans limite.",
        "En état Brave elle <b>ne peut pas lancer Célérité</b> (échange de place) : 2 tours sur 3 tranquilles.",
        "<b>Célérité</b> (PO infinie, sans LDV) : échange avec une arme (déclenche l'attaque de l'arme) et avec un perso (glyphe rouge croix 1).",
        "Elle a peu d'esquive PM : retirer ses PM limite ses actions.",
    ]),
    note("Le perso Brave est celui qui fait le plus de dégâts : optimisez son tour. Désenvoûter son <b>Insoignable</b> pour le soigner. "
         "Un <b>Pandawa</b> peut porter un perso non-Brave : celui-ci tape Guerre sans devenir Pacifiste. "
         "Beaucoup d'<b>érosion</b> (débuffable) : désenvoûter.", GREEN, "ASTUCES"),
    h("Les armes (seuils de PV)", RED),
    p("À <b>chaque tranche de 20% de PV</b> perdue (à 4 persos : 22 000 PV → seuils de 4 400), elle invoque une <b>arme géante</b> "
      "(5 500 PV) à 2 PO au-dessus d'elle (12 h puis sens horaire). Au moment de l'invocation, <u>ses PV se bloquent au seuil</u> "
      "(un énorme coup ne passe pas le seuil)."),
    ul([
        "<b>80% (17 600 PV) · Épée Géante</b> : zone étoile 5, 1400 Feu.",
        "<b>60% (13 200 PV) · Marteau Géant</b> : cercle 3, 1400 Terre.",
        "<b>40% (8 800 PV) · Hache Géante</b> : 4 triangles de hauteur 4, 1400 Air.",
        "<b>20% (4 400 PV) · Morgenstern Géant</b> : grille 5, 1400 Eau.",
        "Les armes frappent à l'invocation et à leur tour ; Guerre s'échange avec elles pour les déclencher.",
    ]),
    p("Boost de Guerre si une arme est en vie à son tour (1 tour) : Épée +2 PM / +100 fuite · Marteau +10% dommages finaux / +100 tacle · "
      "Hache +10% résistances / 1000 PB · Morgenstern +3 PA / soin 5% PV."),
    note("<b>Tuer l'arme AVANT que Guerre rejoue.</b> Si Guerre joue alors qu'une arme est présente, tuer cette arme ensuite "
         "donne à Guerre des résistances (infini), des PM (infini) et la soigne (~1000-1500 PV), cumulable par arme. "
         "Deux stratégies : tuer chaque arme à temps, ou ne pas les tuer (voir le guide complet).", RED, "CRUCIAL"),
    h("Méthode « tuer les armes »", GREEN),
    ul([
        "La taper jusqu'à ~18 000-19 000 PV, <b>placer les persos hors de portée de l'arme</b> à venir, la descendre à 17 600 → épée invoquée → la tuer.",
        "Répéter vers ~14 000 PV (Marteau, seuil 13 200), ~9 500 PV (Hache, seuil 8 800), puis pour le Morgenstern.",
    ]),
    h("Succès Zombie (1 PM par tour)", GOLD),
    p("Guerre vous collera forcément : avoir 80-90 de fuite minimum ou des téléportations. Impossible d'éviter toutes les armes : "
      "<b>focus les armes et les tuer avant que Guerre joue</b> (descendre Guerre au seuil + ~500 PV, puis finir)."),
])

GUIDES_200["corruption"] = "".join([
    h("Kissiphrot Sipique : le poison à retirer", RED),
    p("Corruption et tous ses monstres ont l'état <b>Kissiphrot Sipique</b> (permanent) : <b>chaque ligne de dégâts</b> que vous infligez à un ennemi "
      "vous met un <b>poison Terre ~1400</b> (cumulable, fin de tour). <u>Impossible de gagner sans le retirer</u> : chaque coup = −1400 PV."),
    note("Pour le retirer sur un monstre : <b>soigner un allié ou une invocation (ou soi-même) au contact de ce monstre</b> "
         "(il est repoussé d'1 case). Retiré = retiré pour tout le combat, à refaire <u>pour chaque monstre</u>. "
         "Le vol de vie compte comme soin ; il faut <b>3 soins</b> pour retirer une maladie.", GREEN, "COMMENT"),
    p("<b>Sur Corruption</b> : le retirer le fait <b>descendre de sa monture 3 tours</b> (« délock », il ne lance plus Bouillon de culture). "
      "Après 3 tours, il remonte et remet Kissiphrot à lui et à tous ses alliés vivants."),
    h("Sorts de Corruption", GOLD),
    ul([
        "<b>Aura du Destrier Purulent</b> (début) : Kissiphrot sur lui et ses alliés. <b>Bêche corrompue</b> (ligne 2 PO, 3×/tour) : 600 Feu, −3 PA, −1 durée des effets.",
        f"{o('Sur sa monture')} — <b>Bombe Bactériologique</b> (6-20 PO) : bouclier 660 + maladie aléatoire (11% chacune) à un allié qui explose en fin de tour (cercle 3, 550 Terre) · <b>Bouillon de culture</b> : glyphe violet rayon 3 (300 dégâts + maladie au passage) · <b>Convalescence Prolifique</b> (10 PO, 3×/tour) : 400 Air, repousse 2 · <b>Incu-Batteur</b> (2-14 PO) : 500 Eau, la cible revient à sa position précédente à chaque dégât reçu.",
        f"{o('Descendu (délock)')} — Bombe Bactériologique (6 PO, 2×/tour) · <b>Liquéfaction</b> (2-14 PO sans LDV, 4×/tour) : 350 Eau, 50% de maladie, échange de place · <b>Putréfaction</b> (3-10 PO) : 700 Feu · <b>Éclosion germinal</b> : 350 Neutre cercle 2, −200 puissance, +350 bouclier à ses alliés.",
    ]),
    h("Maladies & Peau pourrissante", ORANGE),
    ul([
        "<b>Peau pourrissante</b> : tant qu'un perso la garde, il ne peut pas attraper d'autre maladie (depuis la 2.68 : −10% de ses PV actuels par fin de tour). "
        "Ne l'enlever <u>que sur les persos qui tapent</u>, pas sur les tanks.",
        "<b>Brutalyte</b> et <b>Gangrainyte</b> sont les pires : Gangrainyte réduit vos soins et se propage, Brutalyte vient du Nheur'Gueule.",
        "Surveiller la maladie posée par Bombe Bactériologique ; éviter le glyphe de Corruption (ou y passer avec un perso encore en Peau pourrissante).",
        "Corruption 3 + une maladie de plus = <b>phase Germinal</b> : tuer vite le Germinial et soigner en priorité ce perso (3 soins).",
    ]),
    h("Stratégie", GREEN),
    ul([
        "Enlever la Peau pourrissante de tous les persos qui tapent.",
        "Tuer les monstres : <b>Nheur'Gueule</b> (retire des PA, Brutalyte) puis <b>Pistilangue</b> (réduit PV et dommages). Un perso/invocation au contact du monstre ciblé, soigné pour retirer Kissiphrot.",
        "<b>Sacrifice du Pistilangue</b> : s'il a encore Kissiphrot et que vous tapez un monstre sans l'état, ce monstre peut être sacrifié et vous prenez quand même le poison.",
        "Prévoir des classes de soin ; armes et sorts à vol de vie multi-lignes très utiles.",
    ]),
])

GUIDES_200["servitude"] = "".join([
    p("Le plus dur des 4 cavaliers de l'Eliocalypse, surtout à cause de ses invocations régulières. "
      "<b>Plus vous êtes nombreux, plus c'est simple</b> : il invoque le même nombre d'Armécréantes, aux mêmes stats, qu'on soit 4, 6 ou 8."),
    h("Armécréantes", RED),
    p("Une <b>Armécréante tous les tours impairs</b> (dès le tour 1, 6 maximum en vie), à 2 PO de lui dans le sens horaire "
      "(case suivante si occupée), avec 20% de PV en moins (niveau 200 à 4 persos, 212 à 8). "
      "Les <u>tuer dès leur apparition</u>, focus rapide, sinon vous êtes submergé. Elles n'ont que 15% de résistance Eau "
      "(un perso Eau aide ; dofus Nébuleux conseillé)."),
    h("Renvoi de 200% & états Traître", RED),
    p("Servitude <b>renvoie 200% des dégâts</b> reçus (pas les poisons). Pour l'éviter : l'état <b>Traître</b>."),
    ul([
        "<b>Traître 1</b> : finir son tour sur un <b>glyphe blanc</b> posé par Servitude. Le glyphe ne sert qu'à charger le 1<sup>er</sup> état (plusieurs glyphes n'ajoutent rien).",
        "Chaque Traître permet <b>1 ligne de dégâts</b> sur Servitude sans renvoi (consommé à chaque ligne ; infini sinon).",
        "Pour <b>incrémenter</b> (max 5) : un perso <u>déjà Traître 1</u> tape un de ses alliés (1 par ligne de dégâts) — sorts à faible PA et faibles dégâts. Sans l'état initial, rien ne s'ajoute.",
        "Ne pas dépenser son dernier Traître : il faudrait refinir sur un glyphe.",
        "Alternative : sorts d'immunité (Bastion, Barricade, Prohibition, Ataraxie).",
    ]),
    h("Phases", GOLD),
    ul([
        "<b>Phase 1</b> : jusqu'à 50% PV. <b>Phase 2</b> (50% → 1 PV) : il monte sur sa monture et ses sorts gagnent des effets. <b>Phase 3</b> (à 1 PV) : il <b>rollback la map</b> (tout le monde revient à sa position de début de combat) et se soigne de 25%.",
        f"{r('Astuce')} : lui appliquer <b>Insoignable</b> avant de passer à 1 PV (pas de +25%), ou un poison (ébène) pour qu'il meure au début de son tour.",
    ]),
    h("Sorts", GOLD),
    ul([
        "<b>Esclavagisme</b> : invoque une Armécréante à 2 PO (max 6, relance 2).",
        "<b>Asservissement</b> (ligne 2-10 PO) : attire de 9 cases ; phase 2 : vole 1 PM et inflige 650.",
        "<b>Joug Protecteur</b> (5 PO) : 700 Eau + 1000 bouclier + 1 PM à l'allié le plus proche de la cible (et à lui en phase 2).",
        "<b>Tyrannie</b> : 900 Eau, −1 PA, cercle 2 ; phase 2 : échange de place d'une Armécréante avec le perso le plus proche.",
        "<b>Trahison</b> : n'est lancé que si un perso a un état Traître : il l'attire (map entière).",
    ]),
    h("Classes & conseils", GREEN),
    ul([
        "<b>Pandawa</b> (placement, Insoignable, Pesanteur/Stabilisation contre le rollback des Armécréantes), <b>Féca</b> (protections pour taper sans Traître ; Ataraxie = Pesanteur), <b>Eliotrope + Iop</b> (focus rapide via portails et Colère).",
        "<b>Domestication</b> (rollback des Armécréantes) : on peut avancer sans crainte, on revient à la position de début de tour.",
    ]),
])

GUIDES_200["misere"] = "".join([
    h("Phases", ORANGE),
    p("Elle commence <b>à pied</b> (phase 1). À <b>50% de sa vitalité de base</b> (9000 PV à 4 persos) elle monte sur son vautour : "
      "<b>invulnérable 1 tour</b> (jusqu'au tour du perso qui a franchi le seuil), puis <b>+4 PM et Intaclable</b> jusqu'à la fin."),
    h("Attraction Vénale", RED),
    p("À chaque début de tour, Misère <b>attire tous les monstres et persos</b> vers elle d'un nombre de cases selon ses PV : "
      "au-dessus de 75% → 1 case, 75-50% → 2 cases, 49-25% → plus, etc. Rester loin n'est donc pas une option sur la durée."),
    h("Vol de stats & état Collecte", RED),
    p("Un monstre qui vous vole des stats passe en état <b>Collecte</b> (fiole au-dessus de la tête). Au début de son tour, "
      "Misère <b>vole ces stats</b> aux monstres Collecte dans sa ligne de vue (une seule fois par monstre et par tour) et leur retire l'état :"),
    ul([
        "<b>Ferrailleur</b> : 10% de la vitalité max (1800) + 50 dommages · <b>Dawaj</b> : 15% crit + 200 Force · <b>Désosseur</b> : 1 PM + 200 Agilité.",
        "<b>Krèvladal</b> : 1 PA + 200 Chance · <b>Skentu</b> : 2 PO + 200 Intelligence.",
        "Les boosts volés restent sur elle (cumul infini) <u>tant que le monstre d'origine est vivant</u> : tuer ce monstre lui retire les stats.",
        "À chaque début de tour, les monstres sans Collecte (ou Collecte hors ligne de vue) gagnent +1 PM et elle leur vole 5% de résistances.",
        "Chaque retrait PA/PM/PO subi donne <b>+10 esquive PA/PM</b> (infini) au monstre visé.",
    ]),
    h("Sorts (2 phases)", GOLD),
    ul([
        "<b>Balance-Fléau</b> (ligne 6 PO, 2×/tour) : 1000 dans tous les éléments sauf Neutre, <b>vole 200 puissance</b> (cumulé max 5 → 1000). Peut vous laisser à 0 dégât.",
        "<b>Barchan</b> (6 PO, 3×/tour) : 600 Eau, −100 soins et −50% soins reçus.",
        f"{o('Phase 1')} <b>Dakhma</b> (2 PO, relance 2) : 600 Feu, −100 PA/PM, cible <b>invulnérable</b> 1 tour et téléportée à sa position de début de tour (taper l'allié qui a subi l'effet le retire, ex. une flamiche).",
        f"{o('Phase 2')} <b>Funérailles Célestes</b> (4-8 PO sans LDV, relance 2, ignore Pesanteur) : 600 Air, échange de place, dégâts Air et attraction de 2 cases autour des deux positions · <b>Grand Urubu</b> (ligne 2 PO, relance 2) : 500 Neutre, −150 rés. poussée, repousse de 6.",
    ]),
    h("Charognes", ORANGE),
    p("Toute entité qui meurt laisse une <b>charogne (320 PV)</b>. Depuis la 2.67 : 4 charognes maximum et Misère les élimine toutes au début de son tour. "
      "Elles se déclenchent au début du tour d'un monstre/de Misère pour les ennemis à 4 PO ou moins (détail des effets dans le guide complet)."),
])

GUIDES_200["anerice"] = "".join([
    h("Résilience vampyrique", RED),
    p("Anerice <b>réduit de 90% tous les dégâts subis</b> (infini, dès le début du combat). Il faut donc passer par l'<b>état Goule</b> ou l'<b>érosion</b>."),
    h("Sorts", GOLD),
    ul([
        "<b>Goulification</b> (3 PO, 2×/tour) : 1200 Eau et transforme en <b>Goule</b> — +150% de dégâts subis, Anerice peut alors utiliser Coopération sur vous. "
        "On sort de l'état en subissant des dégâts (de soi-même ou d'un allié).",
        "<b>Coopération</b> (PO infinie, sans LDV, relance 2) : se téléporte à votre contact (cible en Goule) et attire de 3 cases les autres persos en ligne avec la cible.",
        "<b>Vampyrisme</b> (ligne, 6 PO, chaque tour) : 1000 Terre en vol de vie, zone rayon 2.",
        "<b>Appétit sanguinaire</b> (tour 2, relance 3) : tous les monstres +2 PM et +50% dommages finaux 1 tour.",
    ]),
    h("Début de combat (commun aux 2 stratégies)", GREEN),
    ul([
        "<b>Tuer tous les monstres avant Anerice</b>, en commençant par la <b>Kérigoule</b> (partage les dégâts entre tous les monstres dès le tour 2 : la tuer avant).",
        "Rester à distance, repousser les monstres, leur retirer des PM. Retirer la <b>PO du Gouligane</b> (il met Pacifiste et retire des PA). Le <b>Goultime</b> fait le plus de dégâts : tuer celui qui gêne le plus.",
        "Attention à Appétit sanguinaire (+2 PM aux monstres au tour 2, puis tous les 3 tours).",
    ]),
    h("Stratégie 1 : la revanche des goules", ORANGE),
    p("Pour des persos qui <b>tankent</b> (Dofus Ivoire préférable) et du soin. Il faut qu'Anerice <b>transforme un maximum d'entités en goules</b> "
      "(invocations comprises, si elles survivent). Chaque goule augmente les dégâts qu'Anerice subit ; à partir de <b>3 goules</b> vous infligez des dégâts "
      "« normaux », l'idéal étant <b>4 goules</b>. Préparer une Colère ou un mur de bombes avant d'être transformé (rester loin du mur de bombes en état Goule)."),
    h("Stratégie 2 : érosion", ORANGE),
    p("Avec des persos qui <b>érodent</b>, idéalement un <b>Cra</b> qui érode à distance en repoussant avec <b>Flèche cinglante</b>. "
      "L'érosion ne tient compte que des résistances présentes <u>avant le début du combat</u> : la Résilience vampyrique (active seulement une fois le combat lancé) "
      "n'est pas prise en compte dans les PV érodés par coup."),
])

GUIDES_200["ilyzaelle"] = "".join([
    h("PV d'Ilyzaelle", ORANGE),
    p("4 persos ou moins : <b>42 000</b> · 5 : 46 000 · 6 : 51 000 · 7 : 55 000 · 8 : 60 000. "
      "Son sort <b>Possession</b> donne <b>+300% de vitalité</b> à tous les monstres, et elle fait apparaître des monstres tous les 3 tours : "
      "<b>2 monstres dès le tour 4</b> (4 persos ou moins), 2 dès le tour 3 (5 persos), <b>3 dès le tour 3</b> (6 persos ou plus)."),
    h("Objectif : retirer la moitié de ses PV", RED),
    p("Le combat se joue en <b>2 phases</b>. À <b>75% de PV</b> puis à <b>50%</b>, Ilyzaelle se téléporte <u>dans votre camp</u> sur une case fixe "
      "(impossible de la déplacer), devient <b>invulnérable</b> 2 tours et ne vous frappe plus :"),
    ul([
        "Elle pose un <b>glyphe orange taille 3</b> : <b>+400% de vos dégâts</b> et −30% de dégâts subis si vous êtes dedans.",
        "Les monstres gagnent <b>+2 PM</b>, mais tout monstre qui entre dans son glyphe prend <b>15 000 dégâts neutres</b>.",
        "Au bout de 2 tours le glyphe disparaît, elle repasse chez l'ennemi (encore invulnérable 1 tour).",
        f"{r('Phase 2 (50%)')} : même chose, <b>moment décisif</b> : survivre 2 tours, puis elle <u>tue tous les monstres présents</u> et le combat se termine.",
    ]),
    h("Sorts d'Ilyzaelle", GOLD),
    ul([
        "<b>Hantâme</b> (3 PO, pas au tour 1) : se téléporte sur la case ciblée, 1800 Feu + 40% érosion 2 tours (rayon 2).",
        "<b>Lance de l'effroi</b> (4 PO, 3×/tour) : 1500 Feu + <b>Pacifiste</b> 1 tour.",
        "<b>Vers les ténèbres</b> (dès le tour 3, relance 3) : <b>attire de 10 cases en ligne</b> tous les persos vers elle ; l'attirance s'arrête au premier obstacle (perso ou bloc).",
    ]),
    h("Conseils", GREEN),
    ul([
        "<b>Évitez le full critique</b> : Ilyzaelle a 250 de résistance critique — retirer Dofus Turquoise/Kokulte, Quatre Feuilles → Stalak, Robuste majeur.",
        "Le <b>Crâme</b> joue juste après votre 1<sup>er</sup> perso : l'état <b>Brûlure</b> peut vous ramener à votre position de début de tour (seul perso en Brûlure). Permet de prendre des risques pour repousser les monstres ou leur retirer des PM.",
        "<b>Ectorche + Brûlure</b> : éloigner les autres persos de celui qui a la Brûlure (diagonale ou 3 PO+ en ligne).",
        "L'érosion est peu utile ici.",
    ]),
])

GUIDES_200["torkelonia"] = "".join([
    h("Lunorbe : tous les ennemis invulnérables", RED),
    p("<b>Appel de la lune</b> invoque une <b>Lunorbe</b> au centre (indéplaçable, invulnérable) qui donne l'état <b>Protégé d'Ixchélonia</b> : "
      "Torkélonia et tous les monstres sont <b>Invulnérables</b>. La Lunorbe pose un <b>glyphe bleu</b> (ligne/diagonale) qui <u>tourne chaque tour dans le sens horaire</u> "
      "(8 positions = cycles lunaires : nouvelle lune, 1<sup>er</sup> croissant, 1<sup>er</sup> quartier, gibbeuse montante, pleine lune, gibbeuse descendante, dernier quartier, dernier croissant). "
      "Un monstre qui passe sur le glyphe se soigne de 10% de ses PV max."),
    note("<b>Retirer l'invulnérabilité</b> : être <u>sur le glyphe bleu</u> et faire <b>une ligne de dégâts</b> sur le monstre (sort à faible coût PA). "
         "La 1<sup>re</sup> ligne retire l'état sans frapper ; ensuite on frappe tant qu'on reste sur le glyphe. À la fin de votre tour (ou si vous sortez du glyphe), il le récupère : "
         "le perso suivant doit recommencer.", GREEN, "CLÉ"),
    h("Forcer la rotation", ORANGE),
    p("Frapper la Lunorbe avance le cadran d'une position, mais <b>tous les monstres cumulent alors les boosts de plusieurs cycles</b> ; "
      "si vous tuez l'un d'eux à ce moment, les autres gardent les boosts en cours (infini). "
      "Un tour de cadran complet déclenche la <b>Parade lunaire</b> : −1 PM <u>ou</u> −1 PA (infini, aléatoire). "
      "Trop forcer (tour complet en moins d'un tour) fait disparaître le glyphe jusqu'au prochain tour."),
    note("Le perso qui <b>tue Torkélonia est OS</b>, sauf si elle meurt en <b>Nouvelle lune</b> ou <b>Pleine lune</b>. "
         "Tuer Torkélonia avec une <u>invocation</u> évite l'OS. Elle mourante : Lunorbe et glyphe disparaissent, les monstres restants deviennent vulnérables. "
         "Garder au moins 2 persos vivants.", RED, "OS"),
    h("Sorts", GOLD),
    ul([
        "<b>Carapace lunaire</b> : dégâts subis ×75% 2 tours.",
        "<b>Faisceau lunaire</b> : 600 Feu en ligne et diagonale, portée infinie.",
        "<b>Goutte lunaire</b> (ligne/diagonale 7 PO) : 600 Eau en carré 1 → croix 1 → cône 3 (cycle) ; cible « Cible lunaire » : −10% érosion.",
        "<b>Ricochet sacré</b> (5 PO) : 900 Eau qui rebondit sur le perso le plus proche (cercle 5) ; cible « Cible lunaire » : −2 PA.",
    ]),
    h("Succès « Dernier »", GOLD),
    p("Tuer Torkélonia en dernier : assez simple, et recommandé car l'<b>Alashasss</b> soigne énormément et doit être tué en premier. Un Pandawa tank peut aider."),
])

GUIDES_200["imagami"] = "".join([
    h("Donjon à vagues", ORANGE),
    p("<b>3 vagues, une tous les 4 tours</b>. Tous les monstres ont <b>+13 500 PV</b> (butin 4) ; les invocations passé le seuil « Lotus » ne l'ont pas. "
      "Vague 1 : Roi Imagami + Imorok + Imafugo + Imetsu · Vague 2 (dans 4 tours) : 2 Imiyama + Imorok + Imafugo · Vague 3 (dans 5 tours) : Imiyama + Imetsu + 2 Imushin."),
    h("3 seuils de PV : forme Lotus", RED),
    p("À <b>75% (20 250 PV), 50% (13 500) et 25% (6 750)</b> (butin 4), le Roi passe en <b>forme Lotus</b> : <b>Enraciné et Invulnérable 5 tours</b>, "
      "il se <u>soigne de la totalité de ses PV</u> et invoque la <b>Reine Amirukam</b> à vos côtés. "
      "Si la Reine est tuée, le Roi reprend son état normal. Le Roi (et les monstres) en forme Lotus peuvent être portés par un Pandawa."),
    ul([
        "À chaque seuil, il pose un <b>glyphe blanc autour de lui</b> qui <u>élimine tous les monstres d'encre</u> qu'il contient quand il reprend sa forme normale "
        "(tête de mort au-dessus d'eux). Taille décroissante : <b>carré 3 → 2 → 1</b>.",
        "S'il a été déplacé hors du glyphe (Pandawa) à ce moment, les monstres du glyphe ne sont <b>pas</b> OS.",
        "Il reviendra à 100% de ses PV : prévoir de le faire descendre au seuil suivant.",
    ]),
    h("Reine Amirukam (alliée, contrôlée)", GREEN),
    p("Invoquée sur la case supérieure d'un allié (le perso le plus proche du Roi) et <b>contrôlée par lui</b>. 9 300 PV (butin 4), <b>20 PA / 6 PM</b> : "
      "<b>Expiration du Wukin ×4 par tour</b> (+1 par perso au-delà de 4) + un des deux sorts de boost en alternance. "
      "« Inspiration du Wukin » inflige ~300 de plus par perso supplémentaire. <u>L'utiliser pour faire un maximum de dégâts aux monstres.</u> "
      "Après le dernier seuil et les 5 tours, plus d'aide : il ne reste qu'à tuer le Roi."),
    h("Sorts du Roi Imagami", GOLD),
    ul([
        "<b>Kami no Jishin</b> (5 PO sans LDV, relance 2) : 450 Terre, −3 PM esquivable, repousse aux extrémités / attire au milieu (cercle 3).",
        "<b>Papetuerie</b> (dès le tour 2, tous les 3 tours) : glyphes blancs en croix 1 sur toutes les entités ; au tour suivant <b>700 Neutre</b> à tous — <u>évité si on reste sur la case centrale du glyphe</u>. Le Roi gagne 440 de bouclier, ses alliés 880.",
        "<b>Parchemin de Traverse</b> (mêlée, 2×/tour) : 600 Neutre + téléporte le monstre de papier le plus proche à votre contact.",
        "<b>Roque Papier Ciseaux</b> : bond, 750 Neutre, malus aléatoire aux adjacents (−100 fuite / −2 tours d'envoûtements / 40% érosion).",
    ]),
    h("Classes conseillées", GREEN),
    ul([
        "<b>Pandawa</b> (placement, mode tank), <b>Roublard</b> (dégâts pour atteindre les seuils, mur de bombes pour les invocations), <b>Eniripsa</b> (soins, beaucoup de dégâts subis), <b>Féca</b> (protection, protège les bombes).",
        "Rester au milieu d'un glyphe blanc de Papetuerie.",
    ]),
])

GUIDES_200["amirukam"] = "".join([
    h("Donjon à vagues", ORANGE),
    p("Même principe que le Roi Imagami : <b>3 vagues, une tous les 4 tours</b>, tous les monstres <b>+13 500 PV</b> (butin 4)."),
    h("3 seuils de PV : forme Lotus", RED),
    p("À <b>75% (20 250 PV), 50% (13 500) et 25% (6 750)</b> (butin 4), la Reine passe en <b>forme Lotus</b> : <b>Enracinée et Invulnérable 5 tours</b>, "
      "soignée à 100%, et elle invoque le <b>Roi Imagami</b> à vos côtés (contrôlé par l'allié qui l'invoque). S'il est tué, la Reine reprend son état normal. "
      "Elle et les monstres en Lotus peuvent être portés par un Pandawa."),
    ul([
        "À chaque seuil, elle pose un <b>glyphe noir</b> autour d'elle : <u>tous les monstres de papier</u> dedans meurent quand elle reprend sa forme normale (tête de mort au-dessus). "
        "Taille décroissante : <b>étoile 3 → 2 → 1</b>.",
        "Déplacée hors du glyphe (Pandawa) à ce moment, les monstres du glyphe ne sont pas OS.",
    ]),
    h("Sorts de la Reine Amirukam", GOLD),
    ul([
        "<b>Brouillard d'Encre</b> (tour 1 puis tous les 3 tours) : glyphes sur toutes les entités ennemies ; au tour suivant ils invoquent des « Rupture d'encre » aussitôt tués par la Reine (cellules occupées : pas d'invocation).",
        "<b>Getsuga Tenshō</b> (3-8 PO en ligne, 16 PO en diagonale) : 600 Feu + état aléatoire (<b>Intacleur 50%, Pesanteur 30%, Insoignable 20%</b>) ; elle recule de 2 en diagonale / 5 en ligne.",
        "<b>Monarchie des Roses Noires</b> (1 PO) : repousse de 4 (cône 5), 600 Eau, −2 PO, +20 fuite.",
        "<b>Toner Deubraiste</b> (4-12 PO ligne, 24 PO diagonale, 2×/tour) : poison 500 Eau + <b>+5% de dommages subis</b> (5 tours, cumulable).",
    ]),
])

GUIDES_200["kabahal"] = "".join([
    h("Invulnérable : on le tape par les Bras", RED),
    p("Kabahal est <b>invulnérable</b>, impossible de lui retirer l'état. Les <b>seuls dégâts</b> qu'il subit viennent des <b>Bras démoniaques</b> qu'il invoque."),
    ul([
        "Il prend des dégâts quand il est dans le <b>glyphe d'un Bras</b> (1×/tour). Mieux : <b>prendre le contrôle d'un Bras</b> (finir son tour sur un de ses glyphes) = <b>2 sorts par tour</b> sur Kabahal.",
        "Glyphe des Bras de Kabahal : <b>cercle de taille 3</b> (taille 2 pour ceux des monstres). Les glyphes <u>disparaissent au début du tour de Kabahal</u> et réapparaissent à la fin de son tour ; "
        "s'il est dedans à ce moment, le Bras le frappe. Le tour suivant un contrôle, le glyphe apparaît dès le début de son tour.",
        "Si vous êtes dans le glyphe d'un Bras quand Kabahal joue, il vous frappe plusieurs fois : beaucoup de dégâts.",
        "<b>Paume Menaçante</b> : +20 de dégâts de base sur les sorts des Bras quand vous les contrôlez.",
        "Les Bras servent aussi à frapper les monstres (plus de dégâts qu'en direct).",
    ]),
    h("Positions des Bras & runes", ORANGE),
    ul([
        "<b>5 cases fixes</b> possibles pour les Bras (toujours les mêmes à chaque combat) ; un Bras apparaît dès le début (case aléatoire parmi les 5).",
        "<b>Dès le tour 2, tous les tours pairs</b> : 2 runes qui invoquent des Bras à son tour suivant + une <b>3<sup>e</sup> rune (signe noir)</b> qui ne fait pas apparaître de Bras mais <u>permet de prendre le contrôle</u> même si les 5 positions sont occupées.",
        "Rune posée sur un Bras existant = <b>Surcharge Démoniaque</b> : Bras totalement soigné et +300 puissance 1 tour.",
        "<b>Sacrifice Revigorant</b> : un monstre placé sur une rune de Bras au début du tour de Kabahal est tué par le Bras qui apparaît.",
    ]),
    h("Sorts de Kabahal", GOLD),
    ul([
        "<b>D'une main de maître</b> : +30% dommages distance les tours <u>impairs</u> · <b>Menace Grandissante</b> : +30% dommages mêlée les tours <u>pairs</u>.",
        "<b>Oeil du Nocher</b> (1 PO, dès le tour 2, relance 3) : −6 PO et −30 esquive PM aux ennemis (cône infini) ; lui et ses alliés +6 PO.",
        "<b>Offrande au Chaos</b> (mêlée) : 650 Air + 650 Feu + <b>Insoignable</b> 1 tour (+20 par Bras sur le terrain) ; les ennemis se soignent de 25% des dégâts infligés.",
        "<b>Paume incandescente</b> (6 PO, 2×/tour) : 500 Feu vol de vie, −25% crit (cercle 3) ; s'il crit : +25% crit.",
        "<b>Ratafia Putride</b> (12 PO, 2×/tour) : poison 500 Air, −50% soins 2 tours ; si la cible est en ligne avec un Bras démoniaque, elle est attirée à son contact.",
    ]),
])

GUIDES_200["eternel_conflit"] = "".join([
    h("Invulnérable des deux côtés", RED),
    p("L'Éternel Conflit est <b>invulnérable en mêlée et à distance</b>, <b>Lourd</b> tout le combat, avec un <b>seuil à 4 000 PV</b> infranchissable "
      "tant qu'il n'est pas passé en état <b>« X »</b>. Il invoque 2 diablotins dès le début (Intacleurs et Intaclables), qui échangent de place avec lui "
      "s'ils sont adjacents au début de son tour :"),
    ul([
        "<b>Bonraphin</b> : invulnérable <u>à distance</u> — le tuer retire l'invulnérabilité à distance du boss.",
        "<b>Brâklotin</b> : invulnérable <u>en mêlée</u> — le tuer retire l'invulnérabilité en mêlée du boss.",
        "Tuer les deux = plus aucune invulnérabilité. Un diablotin tué est <b>réinvoqué 2 tours plus tard</b> ; à chaque mort, 25% de chance d'invoquer un <b>Cauchemar des Ravageurs</b> 1 tour.",
    ]),
    h("États Colère Bontarienne / Haine Brâkmarienne → « X »", ORANGE),
    p("Début du combat : diablotins à <b>10</b>, boss à <b>0</b> sur les deux états. <b>Chaque fois qu'un état de diablotin décrémente, celui de l'Éternel Conflit incrémente.</b> "
      "Deux moyens de décrémenter : qu'ils lancent <b>Colonne de lumière</b> (Bonraphin) / <b>Colonne de flammes</b> (Brâklotin), ou que vous tapiez le Bonraphin <b>à distance</b> / le Brâklotin <b>en mêlée</b>."),
    note("Le seul moyen de <b>passer le seuil de 4 000 PV</b> est de le mettre en état <b>« X »</b>, qui le rend aussi <b>vulnérable 2 tours</b>. "
         "Pas obligé de le descendre à 4 000 PV avant ; si vous avez la force de frappe, on peut même le tuer uniquement pendant l'état X. "
         "(Conditions exactes de l'état X : voir le guide complet.)", GREEN, "ÉTAT X"),
    h("Sorts de l'Éternel Conflit", GOLD),
    ul([
        "<b>Poing de la Cité Sombre</b> (mêlée) : 900 Feu, repousse de 4 · <b>Poing de la Cité Blanche</b> (3-5 PO) : 500 Eau + 10% érosion.",
        "<b>Cycle de la Violence</b> (7 PO) : attire de 4, −3 PO (croix 3), −2 PA (croix 1).",
        "<b>Massacre de l'Aurore Pourpre</b> (3 PO sans LDV, relance 4, −1 par allié à son contact) : téléportation, retire 4 tours d'envoûtements, Lourd + Indéplaçable 1 tour (lui s'il touche un ennemi), 400 Eau + 400 Feu + 20% érosion.",
    ]),
    h("Les diablotins", ORANGE),
    ul([
        "<b>Bonraphin</b> : Faux Séraphine (ligne 2-12 PO) 400 Eau + repousse 2 · Colonne de Lumière (7 PO modifiable) 300 Air, −20% soins, état « Bonraphin 2 » (600 Air si déjà touché).",
        "<b>Brâklotin</b> : Épée Diablotine (mêlée) 500 Feu + attire de 2 (ligne 5) · Colonne de Flammes (2 PO, 3×/tour) 250 Terre vol de vie, « Brâklotin 2 » ; si déjà dedans, téléporté symétriquement par rapport au lanceur.",
    ]),
])

GUIDES_200["belladone"] = "".join([
    p("Tout le combat repose sur l'effet <b>Bellarchimagie</b>, lancé dès le début."),
    h("Phase 1 : Belladone sur son îlot (invulnérable)", ORANGE),
    p("Elle est seule sur un îlot en haut de la map : <b>Invulnérable</b>, ne bouge pas, n'inflige <u>aucun dégât direct</u> et booste ses alliés. "
      "<b>Chaque monstre tué</b> lui donne un état <b>Ensorcellement</b> (I à III, 3 monstres morts maximum) qui <u>renforce ses sorts de boost</u> :"),
    ul([
        "<b>Ensorcellement explosif</b> (2 tours) sur un allié : s'il est poussé il gagne +3 PM (cumulable) ; échange de place avec le 1<sup>er</sup> perso qui le frappe ; "
        "au 2<sup>e</sup> tour il explose (cercle 2) : <b>1500 Feu</b> sans Ensorcellement, <b>1600 / 1780 / 2130</b> à I / II / III.",
        "<b>Charme maléfique</b> (infini, sans LDV, 2×/tour) : soigne <b>10% / 12% / 14% / 18%</b> PV max et donne <b>+10 / 13 / 16 / 22%</b> dommages finaux.",
        "<b>Enchantement fatal</b> : tous les monstres +PM/PO/bouclier : <b>1 PM/PO + 2% PV</b> (sans état), 2 + 4%, 3 + 6%, <b>4 + 8%</b> (III).",
        "<b>Glyphe de condamnation</b> (LDV, 1×/tour) : poison 74 Neutre par PA utilisé + <b>glyphe noir en étoile infinie</b> autour de la cible (pas sous elle) qui <b>OS ceux qui commencent leur tour dedans</b>.",
    ]),
    h("Phase 2 : elle rejoint le terrain (vulnérable)", RED),
    p("Pour la rendre vulnérable : <b>tuer tous les monstres</b>. Elle se téléporte alors sur le terrain et lance ses propres sorts de dégâts. "
      "Elle ne perd l'invulnérabilité <u>qu'à la fin de son tour</u> après s'être téléportée, puis bouge avec ses <b>10 PM</b> (difficile à attraper sans tacle). "
      "Elle a alors un <b>seuil à 50% de ses PV</b> et redevient invulnérable à ce seuil (voir le guide complet)."),
    ul([
        "<b>Conjuration entravante</b> (14 PO, 4×/tour) : 530 Neutre vol de vie, −4 PA.",
        "<b>Déchaînement fantasmagorique</b> (7 PO) : 380 Feu (croix diag. 3) + 380 Eau (croix 3), <b>Insoignable</b> au centre.",
        "<b>Maléfice immobile</b> (6 PO) : 800 Terre, échange de place, −100 PM, <b>glyphe noir 1 case sous le perso qui OS</b> tout perso qui y finit son tour (1 tour).",
        "<b>Téléportation enivrante</b> (portée infinie) : se téléporte au contact de la cible <u>la plus éloignée</u>, 30% érosion, 1080 Air.",
    ]),
])

GUIDES_200["venerable"] = "".join([
    h("État Endormi", RED),
    p("Le Vénérable commence <b>Endormi</b> : −100 PM, passe ses tours, ne peut pas être déplacé, <b>Intacleur</b>, <b>Invulnérable</b>, "
      "et se soigne de <b>5% de ses PV max par tour</b>."),
    ul([
        "Si un monstre entre dans l'état <b>Alerté</b> à <b>moins de 3 PO</b> du Vénérable, celui-ci s'<b>éveille immédiatement</b>, devient <b>vulnérable 2 tours</b> et joue normalement.",
        "Frapper un monstre alerte les monstres à ≤3 PO de lui ; si ce monstre alerté est à ≤3 PO du Vénérable, <u>celui-ci ne se réveille pas</u> (cas particulier).",
        "Le Vénérable n'est jamais alerté par ses propres dégâts subis, seulement par un monstre alerté proche. Il se rendort après 2 tours s'il n'est plus alerté.",
        "<b>Tuer un monstre ou un bébé alerte aussi</b> les entités à 3 PO, même sans l'avoir frappé : ne tuez pas un monstre dont le bébé est à ≤3 PO du Vénérable.",
        "<u>Éloigner un maximum les monstres du Vénérable.</u> Il ne peut pas être porté par un Pandawa, même éveillé.",
    ]),
    h("Monture du Vénérable", ORANGE),
    p("Invoquée au tour 1 : <b>10 PM, IA fuyarde, Intacleur et Intaclable</b>, non portable. Tant qu'elle vit, tous les monstres alliés gagnent <b>+2% de dommages finaux par tour</b> (cap 20%). "
      "<b>Tuer la Monture</b> retire ce bonus <u>et réveille le Vénérable : il devient vulnérable pour tout le reste du combat</u> (on peut le tuer sans la tuer, mais c'est fortement déconseillé)."),
    h("Seuil de 50% (16 000 PV)", RED),
    p("À 50% de ses PV : <b>Gare au Gorille</b> jusqu'à la fin : <b>+20% dommages finaux, +4 PO, +100 dommages de poussée, −60 PA, −60 PM</b> (retraits). "
      "Mêmes PV du Vénérable et de la Monture quel que soit le butin."),
    h("Sorts", GOLD),
    ul([
        "<b>Boulet Fantastique</b> (3-8 PO modifiable, relance 2) : 700 Terre cercle 2, −1 PA (2 crit), −2 PM (3 crit).",
        "<b>Charge Fantastique</b> (ligne 6 PO modifiable, relance 2) : fonce sur la cible, 800 Neutre, repousse de 3.",
        "<b>Cri Vénérable</b> (relance 4) : 650 Air vol de vie à tous les persos/invocations dans sa LDV, repousse de 4.",
        "<b>Primartèlement</b> (relance 3) : 700 Terre à tous, <b>attire de 4 cases</b> toutes les entités.",
        "<b>Primattaque</b> (ligne 2 PO, 3×/tour, 2×/cible) : 700 Neutre, repousse d'1.",
        "<b>Saut Impérieux</b> (3-6 PO modifiable, relance 2) : téléportation, 800 Terre cercle 2 — <u>impossible en Pesanteur</u>.",
    ]),
    p("Mettre le Vénérable en <b>Pesanteur</b> l'empêche de se téléporter ; il peut aussi rush en ligne jusqu'à 6 PO et taper en zone à longue distance en retirant PA/PM."),
])

GUIDES_200["dechireuse"] = "".join([
    h("Autel de la Chasse", ORANGE),
    p("Au début, un <b>Autel de la Chasse</b> (invulnérable, 100 000 PV) est invoqué. Son seul sort, <b>Répercussion</b> : chaque tour il <u>copie les sorts des monstres et les effets de Réaction Saisonnière</u> lancés, "
      "puis les rejoue en fin de tour sur <b>l'entité la plus proche de l'Autel</b> (effets réduits : un +10% crit devient +6%). "
      "Il ne disparaît qu'une fois toutes les vagues tuées : <b>vagues aux tours 1, 6, 11, 16, 21</b>."),
    h("Réaction Saisonnière", GOLD),
    p("Après <b>5 lignes de dégâts subies</b>, chaque monstre déclenche un effet selon la saison : "
      "<b>Naissances</b> : attire d'1 case le perso le plus proche de la Déchireuse · <b>Chasse</b> : la Déchireuse +200 puissance 3 tours · <b>Repos</b> : retire tous les envoûtements des persos et invocations."),
    h("Sa mécanique d'OS", RED),
    p("Au début de son tour, la Déchireuse <b>se téléporte sur le perso le plus proche dans sa LDV</b> (pas sur les invocations, pas de téléportation sans perso en LDV, "
      "<u>Pesanteur sans effet</u>) : 500 Feu + état <b>« Espèce menacée »</b> (goutte de sang, jusqu'à la fin)."),
    note("Si elle se téléporte sur un perso <b>déjà « Espèce menacée »</b>, il est <b>OS</b>, et elle peut alors se re-téléporter instantanément sur tous les persos en LDV. "
         "Gagne aussi <b>+1 PM (infini) par monstre allié en ligne</b> avec elle (<b>Matriarche</b>).", RED, "OS"),
    h("L'invulnérabilité de la Déchireuse", GREEN),
    p("Elle est <b>Invulnérable</b>. Pour la retirer, utiliser l'<b>Autel</b> et la <b>Réaction Saisonnière</b> : le monstre nécessaire change à chaque saison."),
    ul([
        "<b>Saison des Naissances → Voracle</b> : le taper 5 fois ; il devient invisible jusqu'à ses prochains dégâts. Dans le <u>même tour</u> (avant que l'Autel joue), placer la Déchireuse <b>plus près de l'Autel que toute autre entité</b> : l'Autel lui applique l'invisibilité ; "
        "il suffit alors de la taper (en sachant où elle est) pour lui retirer invisibilité <u>et</u> invulnérabilité pour le reste du combat.",
        "<b>Saison de la Chasse → Domptueuse</b> · <b>Saison du Repos → Ébourifauve</b> : même principe via leur propre Réaction Saisonnière (détails dans le guide complet).",
    ]),
    h("Sorts", GOLD),
    ul([
        f"{o('Phase 1')} <b>Atermoiement</b> (mêlée) : 1000 Eau, repousse d'1 · <b>Brutank</b> (4 PO sans LDV) : 300 Eau + 300 Feu cercle 2, <u>partage les dégâts entre monstres alliés</u> · <b>Hémorasoir</b> (4 PO, 2×/tour) : 500 Feu + poison 90 Feu par PM utilisé.",
        f"{o('Phase 2 — état Barbarisme')} <b>Musculot</b> : 500 Eau + 500 Feu cercle 3, vole 500 vitalité 2 tours · <b>Proxicaire</b> (ligne 4 PO) : s'attire sur la cible, 900 Eau, −100 fuite · <b>Recentrage</b> (5 PO sans LDV, 2×/tour) : 600 Feu + 10% érosion cumulable, attire d'1.",
    ]),
])
