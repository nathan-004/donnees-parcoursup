from csv import DictReader
import folium
import os
import math
import matplotlib.pyplot as plt 

from animation import *

# Constants
C = 5  # Constante de coeff maximum
A = 0.25  # Taux de décroissance de la courbe
default_year = "2024"
start = "ressource/"
location_start = [46.8566, 2.3522]  # France
location_zoom = 7  # Zoom de la carte

# Adjust values based on the size of the selected element
# Region : 5, 0.25
# Département : 

def transform(string:str): 
    """
    Prends une chaîne de caractère en entrée et renvoie l'équivalent de son type

    "test" -> "test"
    "1" -> int(1)
    "1.0" -> float(1.0)
    "[1,0,2]" -> list([1,0,2])
    "(1,2)" -> tuple((1,2))
    """
    if string == "" or string.startswith("http"):
        return string
    
    string.strip()

    if string.isdigit():
        if string[0] == "-" and int(string) > 0:
            return int(string) * -1
        else:
            return int(string)
    elif string[0] == "[" and string[-1] == "]":
        string = string[1:-1].split(",")
        return [transform(el) for el in string]
    elif "," in string:
        string = string.split(",")
        return [transform(el) for el in string]
    elif "." in string in string:
        char = "."
        string = list(string)
        # Enlever expaces

        first_n, last_n = string[:string.index(char)], string[string.index(char)+1:]

        try:
            res = int("".join(first_n)) + int("".join(last_n)) / 10 ** len(last_n)
        except ValueError:
            return 0.0
        if string[0] == "-" and res > 0:
            res *= -1
        return res 
    else:
        return string

def importer_table(fichier):
    with open(fichier, encoding="UTF-8") as f:
        u = []
        for dict in animate(list(DictReader(f, delimiter=";")), title=f"Importation de {fichier}", title_end=f"Importation de {fichier} terminée", char="circle"):
            for el in dict:
                dict[el] = dict[el]
            u.append(dict)
            print_anim()
    return u

def import_all():
    tables = {}
    for filename in os.listdir(start):
        tables[filename[:-4]] = importer_table(start + filename)
    return tables

def creer_categories(tables):
    categories = {}

    for table in animate(tables, title="Création des catégories", title_end="Création des catégories terminées", char="square"):
        for cat in tables[table][0]:
            if cat in categories:
                categories[cat].append(table)
            else:
                categories[cat] = [table]
        print_anim()
                
    return categories

def search_category(inp, categories=None):
    """
    Retourne une liste des categories similaires à l'input
    """
    if categories is None:
        categories = CATEGORIES

    res = []
    
    for cat_name in categories:
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
            t.append({res: el[res] for res in resultats})
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

def create_popup(tables, zone_name, zone_part=""):
    in_folder = not (zone_part == search_category("Région ")[0])
    if zone_name == search_category("Académie", CATEGORIES):
        return "test"
    else:
        popup_html = '<a href="carte_autre.html" target="_blank">Voir une autre carte</a>\n' + graph(tables, zone_name, in_folder=in_folder)
    popup = folium.Popup(popup_html, max_width=370)
    return popup

def points_to_cards(table, category, size_category, fg:folium.FeatureGroup, min_size=5, max_size=35):
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
                            radius=min_size + (int(l[size_category]) * (max_size - min_size) / max_),
                            fill=True,
                            popup=pop
                        ).add_to(fg)
        
    return fg
        
def filtrer_localisation(table, categories, values):
    """
    Categories -> commune, code départemental, "département ", académie, région
    """

    new_categories = []

    for el in categories:
        t = search_category(el, CATEGORIES)
        if len(t) != 0:
            new_categories.append(t[0])
    
    return donneesV10(table, new_categories, values, [])

def uniticite(table, category, resultats=[]):
    """
    Regarde pour chaques éléments pour que chaques valeurs de category n'apparaissent qu'une seule fois

    Pour chaque integer, choix d'addition ou de moyenne
    Pour un string : 
    """
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
            max_ = dist
        moy_dist += dist

    moy_dist /= len(points)

    max_value_coeff = C * math.exp(-A * moy_dist)

    seuil = moy_dist * max_value_coeff

    new_points = []

    for p in distances:
        if distances[p] <= seuil:
            new_points.append(p)
        else:
            pass
            """folium.CircleMarker(
                    location=p,
                    radius=5,
                    color="red",
                    fill=True,
                    fill_color="red",
                    fill_opacity=0.6,
                    popup=f"Écarté : distance={distances[p]:.2f}",
            ).add_to(fg)"""

    return new_points

def orientation(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def create_polygon(points, filtre=True):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts.copy()

    lower = []
    for p in pts:
        while len(lower) >= 2 and orientation(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and orientation(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    result = lower[:-1] + upper[:-1]
    
    if filtre:
        new_result = filtrer_distance(result)
    else:
        new_result = result

    return new_result

def create_zone(table, location_category, carte, tooltip="Click Me!", popup="Test", fill_color="black", color="blue"):
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

    return carte

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

def table_to_zone(table, category, color_category, carte, fg, localisation_category="Coordonnées GPS de la formation", exception_values=["", "Etranger"]):
    """
    table:liste
        Table à utiliser
    category:str
        Nom de la catégorie de zone
    color_category:str
        Nom de la catégorie qui rougit la couleur en fonction de sa valeur (integer)
    carte
    localisation_category:str
    """
    localisations = uniticite(table, category, [category])

    values = {}

    for ligne in localisations:
        zone = ligne[category]

        if zone in exception_values:
            continue
        
        points = donneesV10(table, [category], [zone], [])

        somme = 0

        for idx, el in enumerate(points):
            somme += int(el[color_category])

        values[zone] = somme / (idx + 1)

    maximum = max(values.values())

    for ligne in localisations:
        zone = ligne[category]

        if zone in exception_values:
            continue

        points = donneesV10(table, [category], [zone], [])
        col = get_hex_color(values, zone, maximum)

        carte = create_zone(points, localisation_category, carte,fill_color=col, color=col, popup=create_popup(tables, zone, category))

    return carte
        
def graph(tables,
          zone,
          localisation_category="Région de l’établissement",
          count_category="Effectif total des candidats pour une formation",
          in_folder=True):
    """
    Pour chaque table (année) dans `tables`, calcule la somme de `count_category`
    pour la zone donnée, trace l'évolution année → total, et retourne un Popup.
    """
    # 1. Extraire les années et trier
    data = []
    for table_name, table in tables.items():
        # on suppose que le nom de la table est "parcoursup_2022", "parcoursup_2023", etc.
        if not table_name.startswith("parcoursup_"):
            continue
        try:
            annee = int(table_name.split("_")[-1])
        except ValueError:
            continue

        # 2. Somme des candidats dans la zone
        total = 0
        for rec in table:
            if rec.get(localisation_category) == zone:
                try:
                    total += int(rec.get(count_category, 0))
                except (TypeError, ValueError):
                    pass

        data.append((annee, total))

    if not data:
        # Pas de données → simple message
        return folium.Popup(f"<i>Aucune donnée pour {zone}</i>", max_width=200)

    # 3. Trier par année et séparer en deux listes
    data.sort(key=lambda x: x[0])
    années, totaux = zip(*data)

    # 4. Créer le dossier des graphes
    os.makedirs("graphes", exist_ok=True)
    safe_zone = zone.replace(" ", "_").replace("/", "_")
    filename = f"graphes/graph_{safe_zone}.png"

    # 5. Tracer
    plt.figure()
    plt.plot(années, totaux, marker="o")
    plt.title(f"{zone} — Candidatures Parcoursup")
    plt.xlabel("Année")
    plt.ylabel(count_category)
    plt.xticks(années)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    # 6. Construire le Popup HTML
    if in_folder:
        html = f'<img src="../{filename}" width="350"><br><small>Evolution {zone}</small>'
    else:
        html = f'<img src="{filename}" width="350"><br><small>Evolution {zone}</small>'
    return html

def creer_index(val_category):
    """
    Créer une carte contenant toutes les régions, toute la France, les couleurs seront en fonction de val_category
    Et la sauvegarder comme carte.html
    Carte d'origine
    """

    carte = folium.Map(location=location_start, zoom_start=location_zoom)
    fg = folium.FeatureGroup(name="Régions", control=False).add_to(carte)

    carte = table_to_zone(tables["parcoursup_"+default_year], "Région de l’établissement", "Effectif total des candidats pour une formation", carte, fg)

    folium.LayerControl().add_to(carte)

    carte.save("carte.html")

# Importer toutes les tables dans /ressources + initialiser les variables
tables = import_all()

# Initialiser les catégories
CATEGORIES = creer_categories(tables)

print("Nombre de catégories : ")
for t_ in tables:  # Compter les catégories
    print(t_, len(tables[t_][0]), sep=" : ")

print(search_category("académie", CATEGORIES))

print("Nombre de lignes trouvées :", len(donneesV10(tables["parcoursup_" + default_year], ["\ufeffSession"], ["2024"], [])))

val_cat = "Effectif total des candidats pour une formation"

# ETABLISSEMENTS = uniticite(tables["parcoursup_"+default_year], "Code UAI de l'établissement")

#loc = filtrer_localisation(tables["parcoursup_"+default_year], ["région"], ["Nouvelle Aquitaine"])

#points_to_cards(ETABLISSEMENTS, "Coordonnées GPS de la formation")

#table_to_zone(ETABLISSEMENTS, "Région de l’établissement")

#points_to_cards(tables["parcoursup_"+default_year], "Coordonnées GPS de la formation", "Capacité de l’établissement par formation") # Affiche les formations par un cercle dont la taille change en fonction de la capacité de cet établissement

creer_index(val_cat)