#python3.12 importplan.py 
from contextlib import closing
import sqlite3
import json
import sys

# Chemin du fichier de la base de données de l'IG (package.db) 
db_path =  sys.argv[1]
# Chemin du dossier où sera généré le fichier plantuml
output_path = sys.argv[2]

# Dictionnaire des couleurs des différents profils 
colors = {
    'RORHealthcareService': {'back': 'AliceBlue', 'header': 'LightSkyBlue'},
    'ROROrganization': {'back': 'LightGoldenRodYellow', 'header': 'Gold'},
    'RORPractitioner': {'back': 'TECHNOLOGY', 'header': 'LimeGreen'},
    'RORPractitionerRole': {'back': 'MintCream', 'header': 'LightSeaGreen'},
    'RORLocation': {'back': 'LavenderBlush', 'header': 'violet'}
}

# Requête SQL d'extraction des données nécessaires au schéma
sql_query = """ 
select
    json_extract(Resources.json, '$.name') as resource,
    replace(json_extract(Resources.json,'$.baseDefinition'),'http://hl7.org/fhir/StructureDefinition/','') as baseSimple,
    value as element,
    json_extract(Resources.json, REPLACE(fullkey, 'id', 'mapping')) as mapping, 
    json_extract(Resources.json, REPLACE(fullkey,'id', 'type')) as type,
    json_extract(Resources.json, '$.baseDefinition') as baseUrl,
    json_extract(Resources.json, '$.url') as url,
    json_extract(Resources.json, REPLACE(fullkey,'id', 'min')) as min,
    json_extract(Resources.json, REPLACE(fullkey,'id', 'max')) as max
from   
    Resources,
    json_tree(Resources.json,'$.differential.element') as jtree
where   
    Resources.type='StructureDefinition'
    and json_extract(Resources.json,'$.type')!='Extension'
    and (jtree.key='id')
"""

# Fonction utilitaire permettant de garder uniquement les caractères alphanumériques d'une chaîne de caractères
def keep_alnum(text):
    text_alnum = ''.join(filter(str.isalnum, text))
    return text_alnum

# Exécution de la requête et récupération des données
def get_data_from_db(db_path, sql_query):
    data = []
    with closing(sqlite3.connect(db_path)) as conn:  
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql_query)
            data = cursor.fetchall()
    return data

# Extraction des données issues de la requête SQL
def extract_data(data):
    extracted_data = {}
    # Récupération des profils
    for row in data:
        resource = row[0]
        if row[1] != 'Extension':
            # Seuls les éléments pour lesquels un mapping est renseigné sont affichés dans le schéma
            if row[3] is not None:
                mapping = json.loads(row[3])
                for elem in mapping:
                    # Niveau ressource
                    if row[1] == row[2]:
                        if resource not in extracted_data.keys():
                            extracted_data[resource] = {'profil_id': row[6].split('/')[-1], 'base_fhir': row[1], 'urls': [row[5], row[6]], 'mapping': [], 'links': {}}
                        extracted_data[resource]['mapping'].append(elem['map'])
    # Récupération des références
    for row in data:
        resource = row[0]
        if row[1] != row[2]:
            if row[3] is not None and row[4] is not None:
                elem_types = json.loads(row[4])
                for elem_type in elem_types:
                    if elem_type['code'] == 'Reference':
                        for target_profil in elem_type['targetProfile']:
                            for profil in extracted_data.keys():
                                if target_profil in extracted_data[profil]['urls']:
                                    if profil not in extracted_data[resource]['links']:
                                        extracted_data[resource]['links'][profil] = str(row[7]) + '..' + str(row[8])
    return extracted_data

# Génération du schéma de mapping global
def generate_plantuml_global(extracted_data, output_path, colors):
    with open(output_path + '/mapping_global.plantuml', 'w', encoding="utf-8") as f:
        links = '\n'
        f.write("@startuml\n")
        for profil, profil_infos in extracted_data.items():
            color = ''
            if profil in colors.keys():
                color = ' #' + colors[profil]['header']
            mapping_ids = []
            for mapping in profil_infos['mapping']:
                mapping_id = keep_alnum(mapping)
                # Un rectangle par classe fonctionnelle (avec un couleur par profil FHIR)
                f.write('\nrectangle "' + mapping + ' \\n [[' + 'StructureDefinition-' + profil_infos['profil_id'] + '.html ' + profil + ']]" as ' + mapping_id + color +' \n')
                for link, card in profil_infos['links'].items():
                    # Ajout des liens
                    for mapping_ref in extracted_data[link]['mapping']: 
                        if card != '':
                            links += mapping_id + ' -- "' + card + '" ' + keep_alnum(mapping_ref) + '\n'
                        else:
                            links += mapping_id + ' -- ' + keep_alnum(mapping_ref) + '\n'
        f.write(links)
        f.write("\n@enduml")
        
data = get_data_from_db(db_path, sql_query)
extracted_data = extract_data(data)
generate_plantuml_global(extracted_data, output_path, colors)