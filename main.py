from csv import DictReader
import time
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

def create_popup(line):
    html = line["Établissement"] + "-" + line["cod_aff_form"]
    
    return html

def points_to_cards(table, category):
    for l in animate(table, title="Placement des points sur la carte", title_end="Points placés", char="block"):
        print_anim()
        if not "," in l[category]:
            continue 
        x, y = eval(l[category])
        pop = create_popup(l.copy())
        folium.Marker(location=(x, y), popup=pop).add_to(fg)
        
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
    return lower[:-1] + upper[:-1]   

def create_zone(table, location_category, tooltip="Click Me!", popup="Test"):
    
    locations = []

    for ligne in table:
        if not "," in ligne[location_category]:
            continue
        locations.append(eval(ligne[location_category]))

    locations = create_polygon(locations)
    
    folium.Polygon(
        locations=locations,
        color="blue",
        weight=6,
        fill_color="red",
        fill_opacity=0.5,
        fill=True,
        popup=popup,
        tooltip=tooltip,
    ).add_to(carte)


def table_to_zone(table, category, localisation_category="Coordonnées GPS de la formation", exception_values=["", "Etranger"]):
    localisations = uniticite(table, category, [category]) # Toutes les valeurs de la catégorie

    for ligne in localisations:
        zone = ligne[category]

        if zone in exception_values:
            continue

        points = donneesV10(table, [category], [zone], [])
        create_zone(points, localisation_category, zone)

# Importer toutes les tables dans /ressources + initialiser les variables
tables = import_all()

# Initialiser les catégories
CATEGORIES = creer_categories()

print("Nombre de catégories : ")
for t_ in tables: # Compter les catégories
    print(t_, len(tables[t_][0]), sep=" : ")

#print("Nom des catégories", CATEGORIES.keys(), sep=" : ")

# Chercher dans les categories
print(search_category("région"))

print("Nombre de lignes trouvées :", len(donneesV10(tables["parcoursup_"+default_year], ["\ufeffSession"], ["2024"], ["Statut de l’établissement de la filière de formation (public, privé…)"])))

#print(len(jointure(tables["parcoursup_2020"], tables["parcoursup_2019"], ["Code UAI de l'établissement"], ["Établissement"])))

carte = folium.Map(location=[46.8566, 2.3522], zoom_start=7)
fg = folium.FeatureGroup(name="Icon collection", control=False).add_to(carte)

ETABLISSEMENTS = uniticite(tables["parcoursup_"+default_year], "Code UAI de l'établissement")

vienne = filtrer_localisation(tables["parcoursup_"+default_year], ["région"], ["Nouvelle Aquitaine"])

#points_to_cards(ETABLISSEMENTS, "Coordonnées GPS de la formation")
table_to_zone(ETABLISSEMENTS, "Département de l’établissement")

folium.LayerControl().add_to(carte)

carte.save("carte.html")

# https://www.data.gouv.fr/fr/datasets/parcoursup-2023-voeux-de-poursuite-detudes-et-de-reorientation-dans-lenseignement-superieur-et-reponses-des-etablissements/#/resources
# https://stackoverflow.com/questions/59287928/algorithm-to-create-a-polygon-from-points