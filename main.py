from csv import DictReader
import folium
import os

from animation import *

default_year = "2024"

def importer_table(fichier):
    with open(fichier, encoding="UTF-8") as f:
        u = []
        for dict in animate(list(DictReader(f, delimiter=";")), title=f"Importation de {fichier}", title_end=f"Importation de {fichier} terminée", char="circle"):
            u.append(dict)
            print_anim()
    return u

def import_all():
    tables = {}
    start = "ressource/"
    for filename in os.listdir(start):
        tables[filename[:-4]] = importer_table(start+filename)
    return tables

def creer_categories():
    categories = {}

    for table in animate(tables, title="Création des catégories", title_end="Création des catégories terminées", char="square"):
        for cat in tables[table][0]:
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

def sort(table, category):
    # Category must be an integer

    return sorted(table, key= lambda x : int(x[category]), reverse=True)

def create_popup(line):
    html = line["Établissement"] + "-" + line["cod_aff_form"]
    
    return html

def points_to_cards(table, category, size_category, min_size=5, max_size=35):
    """
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
        
def filtrer_localisation(table, categories, values):
    """
    Categories -> commune, code départemental, "département ", académie, région
    """

    new_categories = [search_category(el)[0] for el in categories]
    
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

def filtrer_distance(points, max_value_coeff=4.5):
    if not points:
        return []

    xs = [x for x, y in points]
    ys = [y for x, y in points]
    
    print(xs, ys)

    # Médiane
    med_x = mediane(xs)
    med_y = mediane(ys)

    moyenne = (med_x, med_y)

    folium.CircleMarker(
        location=moyenne,
        radius=6,
        color="green",
        fill=True,
        fill_color="green",
        fill_opacity=0.7,
        popup="Centre",
    ).add_to(fg)

    distances = {}
    moy_dist = 0
    max_ = 0

    for point in points:
        dist = ((point[0] - moyenne[0]) ** 2 + (point[1] - moyenne[1]) ** 2) ** 0.5
        distances[point] = dist
        if dist > max_:
            if dist > max_ * max_value_coeff and max_ != 0:
                print(dist)
                continue
            max_ = dist
        if max_ > dist * max_value_coeff and max_ != 0:
            moy_dist -= max_
            max_ = dist
        moy_dist += dist

    moy_dist /= len(points)
    seuil = moy_dist * max_value_coeff

    new_points = []

    for p in distances:
        if distances[p] <= seuil:
            new_points.append(p)
            folium.Marker(
                    location=p,
                    radius=10,
                    color="blue",
                    fill=True,
                    fill_color="blue",
                    fill_opacity=1.5,
                    tooltip=f"Écarté : distance={distances[p]:.2f}</br>Seuil : {seuil}",
                    popup=f"Écarté : distance={distances[p]}</br>Seuil : {seuil}",
            ).add_to(fg)
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

def create_polygon(points):
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
    new_result = filtrer_distance(result)

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

        values[zone] = somme/idx+1

    maximum = max(values.values())

    for ligne in localisations:
        zone = ligne[category]

        if zone in exception_values:
            continue

        points = donneesV10(table, [category], [zone], [])
        col = get_hex_color(values, zone, maximum)

        create_zone(points, localisation_category, zone, fill_color=col, color=col)

# Importer toutes les tables dans /ressources + initialiser les variables
tables = import_all()

# Initialiser les catégories
CATEGORIES = creer_categories()

print("Nombre de catégories : ")
for t_ in tables: # Compter les catégories
    print(t_, len(tables[t_][0]), sep=" : ")

# print("Nom des catégories", CATEGORIES.keys(), sep=" : ")

# Chercher dans les categories
print(search_category("académie"))

print("Nombre de lignes trouvées :", len(donneesV10(tables["parcoursup_"+default_year], ["\ufeffSession"], ["2024"], ["Statut de l’établissement de la filière de formation (public, privé…)"])))

#print(len(jointure(tables["parcoursup_2020"], tables["parcoursup_2019"], ["Code UAI de l'établissement"], ["Établissement"])))

carte = folium.Map(location=[46.8566, 2.3522], zoom_start=7)
fg = folium.FeatureGroup(name="Icon collection", control=False).add_to(carte)

ETABLISSEMENTS = uniticite(tables["parcoursup_"+default_year], "Code UAI de l'établissement")

#loc = filtrer_localisation(tables["parcoursup_"+default_year], ["région"], ["Nouvelle Aquitaine"])

#points_to_cards(ETABLISSEMENTS, "Coordonnées GPS de la formation")

#table_to_zone(ETABLISSEMENTS, "Région de l’établissement")

#points_to_cards(tables["parcoursup_"+default_year], "Coordonnées GPS de la formation", "Capacité de l’établissement par formation") # Affiche les formations par un cercle dont la taille change en fonction de la capacité de cet établissement

table_to_zone(tables["parcoursup_"+default_year], "Académie de l’établissement", "Effectif total des candidats pour une formation")

folium.LayerControl().add_to(carte)

carte.save("carte.html")

# https://www.data.gouv.fr/fr/datasets/parcoursup-2023-voeux-de-poursuite-detudes-et-de-reorientation-dans-lenseignement-superieur-et-reponses-des-etablissements/#/resources