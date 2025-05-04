from csv import DictReader
import folium
import os
import math

from animation import *

variables = {
    "C": 5, # Constante de coeff maximum 
    "A": 0.25, # Taux de décroissance de la courbe
    "default_year": "2024",
    "start": "ressource/",
    "tables": {},
    "location_start": [46.8566, 2.3522], # France,
    "location_zoom": 7, # Zoom de la carte
}

constantes = set([ # Initialise les variables qui ne peuvent pas être modifiées par l'utilisateur
    "tables"
])

# Ajuster les valeurs en fonction de la taille de l'élément sélectionné
# Region : 5, 0.25
# Département : 

def importer_table(fichier):
    with open(fichier, encoding="UTF-8") as f:
        u = []
        for dict in animate(list(DictReader(f, delimiter=";")), title=f"Importation de {fichier}", title_end=f"Importation de {fichier} terminée", char="circle"):
            u.append(dict)
            print_anim()
    return u

def import_all():
    tables = {}
    start = variables["start"]
    for filename in os.listdir(start):
        tables[filename[:-4]] = importer_table(start+filename)
    return tables

def creer_categories():
    categories = {}

    for table in animate(variables["tables"], title="Création des catégories", title_end="Création des catégories terminées", char="square"):
        for cat in variables["tables"][table][0]:
            if cat in categories:
                categories[cat].append(table)
            else:
                categories[cat] = [table]
        print_anim()
                
    return categories

def search_category(inp):
    """
    Retourne une liste des categories similaires à l'input
    """
    res = []
    
    for cat_name in CATEGORIES:
        if inp.lower() in cat_name.lower():
            res.append(cat_name)
        
    return res

def donneesV10(T, categories, valeurs, resultats):
    """
    Renvoie le tableau contenant les valeurs dans resultats qui respectent une condition valeurs[i] == categories[i]

    Parameters
    ----------
    T:list
        Liste de dictionnaires
    categories:list
        Nom des categories dans l'ordre qui doivent être vérifiées
    valeurs:list
        Valeurs à vérifier dans l'ordre
    resultats:list
        Categories à renvoyer
    """
    
    for cat in categories:
        if cat not in T[0]:
            print(f"Erreur : la catégorie {cat} n'existe pas dans la table.")
            return []

    t = []
    
    if resultats == []:
        resultats = list(T[0].keys())

    for el in animate(T, char="block", title=f"Récupération des données {categories} = {valeurs}", title_end=f"Données {categories} = {valeurs} trouvées"):
        if any([el[categories[idx]] == valeurs[idx] for idx in range(len(categories))]) or categories == []:
            t.append({res:el[res] for res in resultats})
        print_anim()
    return t

def jointure(table1, table2, categories, resultats):
    t = []
    
    for i1 in range(len(table1)):
        for i2 in range(len(table2)):
            if (any([table1[i1][categories[idx]] == table2[i2][categories[idx]] for idx in range(len(categories))]) or categories == []):
                 t.append({res: table1[i1][res] if res in table1[i1] else table2[i2][res] for res in resultats})
    return t

def sort(table, category, reverse=True):
    try:
        if type(table[0][category]) == str and table[0][category].isdigit():
            return sorted(table, key=lambda x: int(x[category]), reverse=reverse)
        else:
            return sorted(table, key=lambda x: x[category], reverse=reverse)
    except (KeyError, ValueError, TypeError) as e:
        print(f"Erreur lors du tri : {e}")
        return table

def create_popup(line):
    html = line["Établissement"] + "-" + line["cod_aff_form"]
    
    return html

def points_to_cards(table, category, size_category, min_size=5, max_size=35):
    """
    category:str
        Categorie devant être un str
        Définit la localisation du marker sous forme de coordonnées GPS
    size_category:str
        Categorie devant être un int
        Définit la taille du marker
    """

    table_sort = sort(table, size_category)
    max_, min_ = int(table_sort[0][size_category]), int(table[-1][size_category])

    for l in animate(table, title="Placement des points sur la carte", title_end="Points placés", char="block"):
        print_anim()
        if not "," in l[category]:
            continue 
        x, y = eval(l[category])
        pop = create_popup(l.copy())

        folium.CircleMarker(location=(x, y),
                            radius=min_size+(int(l[size_category])*(max_size-min_size)/max_),
                            fill=True,
                            popup=pop
                        ).add_to(fg)
        
def filtrer_localisation(table, categories, values, nom_de_la_table):
    """
    Categories -> commune, code départemental, "département ", académie, région
    """

    new_categories = []

    for el in categories:
        t = search_category(el)
        if len(t) != 0:
            new_categories.append(t[0])
    
    return donneesV10(table, new_categories, values, [])

def uniticite(table, category, resultats=[]):
    if resultats == []:
        resultats = list(table[0].keys())
    
    seen = set()
    new_table = []
    
    for ligne in animate(table):
        if ligne[category] not in seen:
            new_table.append({res: ligne[res] for res in resultats})
            seen.add(ligne[category])
        print_anim()
    
    return new_table

def mediane(liste):
    liste_triee = sorted(liste)
    n = len(liste_triee)
    if n % 2 == 1:
        return liste_triee[n // 2]
    else:
        return (liste_triee[n // 2 - 1] + liste_triee[n // 2]) / 2

def filtrer_distance(points):
    if not points:
        return []

    xs = [x for x, y in points]
    ys = [y for x, y in points]

    # Médiane
    med_x = mediane(xs)
    med_y = mediane(ys)

    moyenne = (med_x, med_y)

    distances = {}
    moy_dist = 0
    max_ = 0

    for point in points:
        dist = ((point[0] - moyenne[0]) ** 2 + (point[1] - moyenne[1]) ** 2) ** 0.5
        distances[point] = dist
        if dist > max_:
            #if dist > max_* and max_ != 0:
            #    print(dist)
            #    continue
            max_ = dist
        #if max_ > dist * max_value_coeff and max_ != 0:
        #    moy_dist -= max_
        #    max_ = dist
        moy_dist += dist

    moy_dist /= len(points)

    max_value_coeff = variables["C"] * math.exp(-variables["A"] * moy_dist)

    seuil = moy_dist * max_value_coeff

    new_points = []

    for p in distances:
        if distances[p] <= seuil:
            new_points.append(p)
        else:
            # Point trop éloigné → afficher en rouge
            if fg is not None:
                folium.CircleMarker(
                    location=p,
                    radius=5,
                    color="red",
                    fill=True,
                    fill_color="red",
                    fill_opacity=0.6,
                    popup=f"Écarté : distance={distances[p]:.2f}",
                ).add_to(fg)

    return new_points

def orientation(a, b, c):
    # renvoie >0 si a→b→c tournent à gauche, <0 si à droite
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def create_polygon(points, filtre=True):
    # 1. on trie
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts.copy()

    # 2. chaîne inférieure
    lower = []
    for p in pts:
        while len(lower) >= 2 and orientation(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # 3. chaîne supérieure
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and orientation(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # 4. concatène (sans répéter le premier/dernier)
    result = lower[:-1] + upper[:-1]
    
    # Enlever les points trop éloignés
    if filtre:
        new_result = filtrer_distance(result)
    else:
        new_result = result

    return new_result

def create_zone(table, location_category, tooltip="Click Me!", popup="Test", fill_color="black", color="blue"):
    locations = []

    for ligne in table:
        if not "," in ligne[location_category]:
            continue
        locations.append(eval(ligne[location_category]))

    locations = create_polygon(locations)
    
    folium.Polygon(
        locations=locations,
        color=color,
        weight=6,
        fill_color=fill_color,
        fill_opacity=0.5,
        fill=True,
        popup=popup,
        tooltip=tooltip,
    ).add_to(carte)

def get_hex_color(values, zone, max_=None, lowest_color=(255, 255, 0), highest_color=(255, 0, 0)):
    if max_ is None:
        max_ = max(values.values())

    current_value = values[zone]

    new_color = [
        int(lowest_color[i] + (highest_color[i] - lowest_color[i]) * current_value / max_)
        for i in range(3)
    ]

    hex_color = "#{:02x}{:02x}{:02x}".format(*new_color)

    return hex_color

def table_to_zone(table, category, color_category, localisation_category="Coordonnées GPS de la formation", exception_values=["", "Etranger"]):
    """
    table:list
    category:str
        categorie ou se trouve la zone correspondante
    color_color:str
        catégorie qui doit être un integer
    localisation_category:str
        catégorie contenant la localisation
    """
    localisations = uniticite(table, category, [category]) # Toutes les valeurs de la catégorie

    values = {}

    for ligne in localisations:
        zone = ligne[category]

        if zone in exception_values:
            continue
        
        points = donneesV10(table, [category], [zone], [])

        somme = 0

        for idx, el in enumerate(points):
            somme += int(el[color_category])

        values[zone] = somme/(idx+1)

    maximum = max(values.values())

    for ligne in localisations:
        zone = ligne[category]

        if zone in exception_values:
            continue

        points = donneesV10(table, [category], [zone], [])
        col = get_hex_color(values, zone, maximum)

        create_zone(points, localisation_category, zone, fill_color=col, color=col)

# Importer toutes les tables dans /ressources + initialiser les variables
variables["tables"] = import_all()

# Initialiser les catégories
CATEGORIES = creer_categories()

print("Nombre de catégories : ")
for t_ in variables["tables"]: # Compter les catégories
    print(t_, len(variables["tables"][t_][0]), sep=" : ")

# print("Nom des catégories", CATEGORIES.keys(), sep=" : ")

# Chercher dans les categories
print(search_category("académie"))

print("Nombre de lignes trouvées :", len(donneesV10(variables["tables"]["parcoursup_"+variables["default_year"]], ["\ufeffSession"], ["2024"], ["Statut de l’établissement de la filière de formation (public, privé…)"])))

#print(len(jointure(tables["parcoursup_2020"], tables["parcoursup_2019"], ["Code UAI de l'établissement"], ["Établissement"])))

carte = folium.Map(location=[46.8566, 2.3522], zoom_start=7)
fg = folium.FeatureGroup(name="Icon collection", control=False).add_to(carte)

# ETABLISSEMENTS = uniticite(tables["parcoursup_"+default_year], "Code UAI de l'établissement")

#loc = filtrer_localisation(tables["parcoursup_"+default_year], ["région"], ["Nouvelle Aquitaine"])

#points_to_cards(ETABLISSEMENTS, "Coordonnées GPS de la formation")

#table_to_zone(ETABLISSEMENTS, "Région de l’établissement")

#points_to_cards(tables["parcoursup_"+default_year], "Coordonnées GPS de la formation", "Capacité de l’établissement par formation") # Affiche les formations par un cercle dont la taille change en fonction de la capacité de cet établissement

# table_to_zone(tables["parcoursup_"+default_year], "Département de l’établissement", "Effectif total des candidats pour une formation")

def init_carte(): # Couvre toute la France
    location = variables["location_start"]
    zoom_start = variables["location_zoom"]

    if type(location) != list and len(location) != 2:
        print("Erreur : la localisation doit être une liste de deux éléments")
        return

    carte = folium.Map(location=location, zoom_start=zoom_start)
    fg = folium.FeatureGroup(name="Icon collection", control=False).add_to(carte)

def save_carte(carte, filename="carte.html"):
    filename = 'cartes/' + filename

    if not os.path.exists(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)

    folium.LayerControl().add_to(carte)
    carte.save(filename)

    init_carte()

def aide(command_name=None):
    if command_name is None:
        for com in commands:
            print(com, commands[com]["Description"], sep=' | ')
    else:
        print(command_name)

        for el in commands[command_name]:
            print(el, commands[command_name][el], sep=" | ")

def transform(string:str): 
    """
    Prends une chaîne de caractère en entrée et renvoie l'équivalent de son type

    "test" -> "test"
    "1" -> int(1)
    "1.0" -> float(1.0)
    """

    if string.isdigit():
        return int(string)
    elif "." in string or "," in string:
        char = "." if "." in string else ","
        string = list(string)

        first_n, last_n = string[:string.index(char)], string[string.index(char)+1:]

        try:
            return int("".join(first_n)) + int("".join(last_n)) / 10 ** len(last_n)
        except ValueError:
            pass
    elif string[0] == "[" and string[-1] == "]":
        string = string[1:-1].split(",")
        return [transform(el) for el in string]
    else:
        return string
    
def define(var_name, value, type_var=False):
    if var_name in constantes:
        print(f"Impossible de modifier la variable {var_name} car c'est une constante.")
        return
    if not type_var:
        variables[var_name] = value
    else:
        globals()[var_name] = value # Problème si utilisateur entre des noms de fonctions ou de variables importantes

def stockage():
    for el in variables:
        if el in constantes:
            to_print = (el, list(variables[el].keys())) if el == "tables" else (el, variables[el])
            print(*to_print, sep=" <---> ", end="")
            print(" (Constante)")
            continue
        print(el, variables[el], sep=" <---> ")

def donnees_commande(table, categories, valeurs, resultats, nom_de_la_table=None):
    """
    table:str
        Nom de la table à utiliser
    categories:list
        Nom des catégories dans l'ordre qui doivent être vérifiées
    valeurs:list
        Valeurs à vérifier dans l'ordre
    resultats:list
        Categories à renvoyer
    nom_de_la_table:str
        Nom de la table à créer (si None, le nom sera généré automatiquement)
    """

    if nom_de_la_table is None:
        i = 0
        while str(i) in variables["tables"]:
            i += 1
        nom_de_la_table = f"table_{i}"
    
    if table not in variables["tables"]:
        print(f"Table {table} non trouvée.")
        return

    T = variables["tables"][table]

    variables["tables"][nom_de_la_table] = donneesV10(T, categories, valeurs, resultats)

def sort_commande(table, category, ordre=True):
    """
    table:str
        Nom de la table à trier
    category:str
        Catégorie à trier
    ordre:bool
        True pour un tri décroissant, False pour un tri croissant
    """

    if table not in variables["tables"]:
        print(f"Table {table} non trouvée.")
        return

    T = variables["tables"][table]

    variables["tables"][table] = sort(T, category, ordre)

def points_to_cards_command(table, localisation_category, size_category):
    """
    table:str
        Nom de la table à transformer
    localisation_category:str
        Catégorie contenant la localisation
    size_category:str
        Catégorie contenant la taille du marker
    """

    if table not in variables["tables"]:
        print(f"Table {table} non trouvée.")
        return

    T = variables["tables"][table]

    if localisation_category not in T[0]:
        print(f"Catégorie {localisation_category} non trouvée dans la table {table}.")
        return
    if size_category not in T[0]:
        print(f"Catégorie {size_category} non trouvée dans la table {table}.")
        return
    
    try:
        if type(eval(T[0][size_category])) != int:
            print(f"Catégorie {size_category} doit être un int.")
            return
    except:
        print(f"Catégorie {size_category} doit être un int.")
        return

    points_to_cards(T, localisation_category, size_category)

def filtrer_localisation_commande():
    pass

commands = { # 0 -> Facultatif  1 -> Obligatoire
    "aide": {"Description": "Permet d'afficher toutes les commandes possibles", "Arguments" : {"nom-commande": (str, 0)}, "Commande": aide},
    "carte": {"Description": "Enregistre la carte dans le fichier HTML", "Arguments": {"nom-fichier": (str, 0)}, "Commande": save_carte},
    "chercher": {"Description": "Cherche la catégorie correspondante à l'argument", "Arguments" : {"nom-catégorie" : (str, 1)}, "Commande": search_category},
    "definir": {"Description": "Modifie une variable ou en crée dans le programme", "Arguments": {"nom-variable": (str, 1), "valeur": (type(None), 1), "type-variable": (bool, 0)}, "Commande": define},
    "filtrer": {"Description": "Filtre les données en fonction de la catégorie et de la valeur", "Arguments": {"nom-de-la-table-à-filtrer": (str, 1), "catégories": (list, 1), "valeurs": (list, 1), "nom-de-la-table": (str, 1)}, "Commande": donnees_commande},
    "filtrer-localisation": {"Description": "Filtre les données en fonction de leurs localisations.", "Arguments": {"nom-de-la-table-à-filtrer": (str, 1), "catégories": (list, 1), "valeurs": (list, 1), "nom-de-la-table": (str, 0)}, "Commande": filtrer_localisation_commande},
    "quitter": {"Description": "Quitte le programme", "Arguments": {}, "Commande": quit},
    "stockage": {"Description": "Affiche tous les éléments dans le stockage qui peuvent être modifiés par l'utilisateur avec 'definir'", "Arguments": {}, "Commande": stockage},
    "table-vers-point": {"Description": "Transforme une table en points sur la carte", "Arguments": {"nom-de-la-table-à-transformer": (str, 1), "catégorie-de-localisation": (str, 1), "catégorie-de-taille": (str, 1)}, "Commande": points_to_cards_command},
    "trier": {"Description": "Trie les données en fonction de la catégorie", "Arguments": {"nom-de-la-table-à-trier": (str, 1), "catégorie": (str, 1), "ordre": (bool, 0)}, "Commande": sort_commande},
}

def home(commande=None):
    if commande is not None:
        inp = commande
    else:
        inp = input("user > ")

    elements = inp.split(" ")
    command = "aide"
    args = []

    if elements[0] in commands:
        command = elements[0]
        command_args = list(commands[elements[0]]["Arguments"].keys())
        # Regarder si il n'y a pas d'arguments dans l'input
        for idx, word in enumerate(elements[1:]):
            word = transform(word.replace("-", " "))
            if idx+1 > len(command_args):
                print(f"{command} nécessite {len(command_args)} arguments, {len(elements)-1} trouvés. \n Utiliser des '-' pour remplacer les espaces si nécessaire.")
                return 3
            if commands[elements[0]]["Arguments"][command_args[idx]][0] == type(word) or commands[elements[0]]["Arguments"][command_args[idx]][0] == type(None):
                args.append(word)
            else:
                print(f"{str(type(word))} trouvé au lieu de {str(commands[elements[0]]["Arguments"][command_args[idx]][0])} pour l'argument {command_args[idx]}")
                return 2
    else:
        try:
            variable = False
            for var_name in variables:
                if var_name in inp:
                    if var_name in constantes:
                        print(f"Impossible de modifier la variable {var_name} car c'est une constante.")
                        return 1
                    variable = True

                    # inp = inp.replace(var_name, f"variables['{var_name}']") # Pas nécessaire car on définit les globals() comme variables
            if variable:
                print(eval(inp, variables))
            return 0
        except:
            print('Commande non-existante. Taper "aide" pour voir les commandes existantes.')
            return 1
    
    # Regarder qu'il y a bien tous les inputs nécessaires
    for idx, arg in enumerate(command_args):
        if commands[elements[0]]["Arguments"][arg][1] == 1:
            if len(args) < idx + 1:
                arg_input = None
                while type(arg_input) != commands[elements[0]]["Arguments"][arg][0]:
                    arg_input = input(f"Argument {arg} de type {commands[elements[0]]["Arguments"][arg][0]} : ")
                args.append(arg_input)

    res = commands[command]["Commande"](*args)

    if res != None:
        print(res)

if __name__ == "__main__":
    while True:
        try:
            home()
        except KeyboardInterrupt:
            a = ""
            while a not in ["O", "N"]:
                a = input("Voulez-vous enregistrer la carte ? (O/N) : ").upper()
            if a == "O":
                save_carte(carte, "carte.html")
            else:
                print("Carte non enregistrée.")
            print("Au revoir !")
            break

# https://www.data.gouv.fr/fr/datasets/parcoursup-2023-voeux-de-poursuite-detudes-et-de-reorientation-dans-lenseignement-superieur-et-reponses-des-etablissements/#/resources
