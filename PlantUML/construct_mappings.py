#python3.12 importplan.py 
import sqlite3
from contextlib import closing
import json
import re
import sys

# Chemin du fichier de la base de données de l'IG (package.db) 
db_path =  sys.argv[1] 
# Chemin du dossier où seront générées les fichiers plantuml
output_path = sys.argv[2] 

# Dictionnaire des couleurs des différents profils 
colors = {
    'RORHealthcareService': {'back': 'AliceBlue', 'header': 'LightSkyBlue'},
    'ROROrganization': {'back': 'LightGoldenRodYellow', 'header': 'Gold'},
    'RORPractitioner': {'back': 'TECHNOLOGY', 'header': 'LimeGreen'},
    'RORPractitionerRole': {'back': 'MintCream', 'header': 'LightSeaGreen'},
    'RORLocation': {'back': 'LavenderBlush', 'header': 'violet'}
}

# Requête SQL d'extraction des données nécessaires aux schémas
sql_query = """ 
select
    json_extract(Resources.json, '$.name') as resource,
    replace(json_extract(Resources.json,'$.baseDefinition'),'http://hl7.org/fhir/StructureDefinition/','') as baseSimple,
    value as element,
    json_extract(Resources.json, fullkey) as id,
    json_extract(Resources.json, REPLACE(fullkey, 'id', 'mapping')) as mapping, 
    json_extract(Resources.json, REPLACE(fullkey,'id', 'type')) as type,
    json_extract(Resources.json, '$.baseDefinition') as baseUrl,
    json_extract(Resources.json, '$.url') as url
from   
    Resources,
    json_tree(Resources.json,'$.differential.element') as jtree
where   
    Resources.type='StructureDefinition'
    and (jtree.key='id')
"""

# Exécution de la requête et récupération des données
def get_data_from_db(db_path, sql_query):
    data = []
    with closing(sqlite3.connect(db_path)) as conn:  
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql_query)
            data = cursor.fetchall()
    return data

# Fonction utilitaire permettant d'enlever un préfixe à une chaîne de caractères
def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
# Fonction utilitaire permettant d'enlever un suffixe à une chaîne de caractères
def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text
# Fonction utilitaire permettant de garder uniquement les caractères alphanumériques d'une chaîne de caractères
def keep_alnum(text):
    text_alnum = ''.join(filter(str.isalnum, text))
    return text_alnum
# Fonction utilitaire permettant de supprimer les espaces et de remplacer les caractères non alphanumériques (excepté le point) par un tiret du 8
def replace_non_alnum(text):
    text = text.rstrip()
    text_replace = re.sub('[^0-9a-zA-Z.]+', '_', text)
    return text_replace

# Extraction des données issues de la requête SQL
def extract_data(data):
    extracted_data = {'resources': {}, 'resource_extensions': {}, 'complex_extensions': {}, 'mapping_extensions': {}}
    # Problème avec le mapping pour la ressource Organization dans le cadre du ROR (probablement lié à l'héritage)
    url_resource = {'http://interopsante.org/fhir/StructureDefinition/FrOrganization': 'ROROrganization'}
    for row in data:
        resource = row[0]
        # Le mapping des extensions est défini dans la SD de la ressource dans laquelle est utilisée l'extension
        if row[1] != 'Extension':
            # Seuls les éléments pour lesquels un mapping est renseigné sont affichés dans le schéma
            if row[4] is not None:
                mapping = json.loads(row[4])
                # Niveau profil
                for elem in mapping:
                    if row[1] == row[2]:
                        if row[6] not in url_resource:
                            url_resource[row[6]] = row[0]
                        extracted_data['resources'][elem['identity']] = {'resource': row[0], 'class': elem['map'], 'elements': [], 'references': []}
                # Niveau élément
                for elem in mapping:
                    if row[1] != row[2]:
                        if row[5] is not None:
                            elem_type = json.loads(row[5])
                            # Références 
                            if elem_type[0]['code'] == 'Reference':
                                extracted_data['resources'][elem['identity']]['references'].append({'fhir': row[3], 'mapping': elem['map'], 'target_profile': elem_type[0]['targetProfile'][0]})
                            else:
                                extracted_data['resources'][elem['identity']]['elements'].append({row[3] : elem['map']})
                        else:                                                     
                            extracted_data['resources'][elem['identity']]['elements'].append({row[3] : elem['map']})
            # Récupération des extensions de chaque profil
            if row[5] is not None:
                elem_type = json.loads(row[5])
                if elem_type[0]['code'] == 'Extension':
                    if resource not in extracted_data['resource_extensions'].keys():
                        extracted_data['resource_extensions'][resource] = {}
                    extracted_data['resource_extensions'][resource][json.loads(row[5])[0]['profile'][0]] = row[3]
        # Récupération du mapping dans les extensions
        else:
            if row[2].startswith('Extension.extension:'):
                if '.' not in remove_prefix(row[2], 'Extension.extension:'):
                    if row[5] is not None:
                        if row[7] not in extracted_data['complex_extensions'].keys():  
                            extracted_data['complex_extensions'][row[7]] = []
                        extracted_data['complex_extensions'][row[7]].append(json.loads(row[5])[0]['profile'][0])
            if row[4] is not None:
                if row[7] not in extracted_data['mapping_extensions'].keys():
                    extracted_data['mapping_extensions'][row[7]] = {}
                extracted_data['mapping_extensions'][row[7]][row[2]] = json.loads(row[4])[0]['map']
    # Identification des ressources des références
    for mapping_id, mapping in extracted_data['resources'].items():
        for i in range(len(mapping['references'])):
            extracted_data['resources'][mapping_id]['references'][i]['target_profile'] = url_resource[mapping['references'][i]['target_profile']]
    # Problème avec le mapping pour la ressource Organization dans le cadre du ROR (probablement lié à l'héritage)
    del extracted_data['resource_extensions']['ROROrganization']
    return extracted_data

# Structuration des données extraites pour ensuite générer les schémas
def structure_data(extracted_data):
    structured_data = {}
    # Itération sur les mappings (il peut y en avoir plusieurs par ressource)
    for mapping in list(extracted_data['resources'].values()):
        resource_fhir = mapping['resource']
        class_func = mapping['class']
        elements = mapping['elements']
        references = mapping['references']
        if resource_fhir not in structured_data.keys():
            # Un dictionnaire par profil FHIR
            structured_data[resource_fhir] = {}
        # Pour chaque classe fonctionnelle, on distingue les éléments simples, les éléments complexes, les extensions et les références
        structured_data[resource_fhir][class_func] = {'simple_elements': {}, 'complex_elements': {}, 'references': {}, 'extensions': {}}
        complex_elements = {}
        simple_elements = {}
        extensions = {}
        reference_elements = {}
        # Itération sur le mapping
        for elem in elements:
            (elem_fhir, elem_func), = elem.items()
            elem_fhir = elem_fhir.split('.', 1)[1]
            elem_func = elem_func.rstrip()
            # Elément complexe
            if '.' in elem_fhir and not elem_fhir.startswith('extension:'):
                elem_fhir_base, elem_fhir_sub = elem_fhir.split('.', 1)
                # Elément de second niveau
                if '.' in elem_fhir_sub:
                    elem_fhir_sub_base, elem_fhir_sub_sub = elem_fhir_sub.split('.', 1)
                    if elem_fhir_base not in complex_elements.keys():
                        complex_elements[elem_fhir_base] = {}
                    if elem_fhir_sub_base not in complex_elements[elem_fhir_base].keys():
                        complex_elements[elem_fhir_base][elem_fhir_sub_base] = {}
                    complex_elements[elem_fhir_base][elem_fhir_sub_base][elem_fhir_sub_sub] = elem_func
                # Elément de premier niveau
                else:
                    if elem_fhir_base not in complex_elements.keys():
                        complex_elements[elem_fhir_base] = {}
                    complex_elements[elem_fhir_base][elem_fhir_sub] = elem_func
            else:
                simple_elements[elem_fhir] = elem_func
        # Références
        for ref in references:
            elem_fhir = ref['fhir']
            elem_fhir = elem_fhir.split('.', 1)[1]
            if elem_fhir not in reference_elements.keys():
                reference_elements[elem_fhir] = {'resource': ref['target_profile'].split('/')[-1] , 'mapping': [ref['mapping']]}
            else:
                reference_elements[elem_fhir]['mapping'].append(ref['mapping'])
        structured_data[resource_fhir][class_func]['references'] = reference_elements
        # Structuration des informations
        for fhir_complex, func_complex in complex_elements.items():
            if fhir_complex in simple_elements.keys():
                structured_data[resource_fhir][class_func]['complex_elements'][fhir_complex] = {'mapping': simple_elements[fhir_complex], 'elements': func_complex}
            else: 
                structured_data[resource_fhir][class_func]['complex_elements'][fhir_complex] = {'mapping': None, 'elements': func_complex}
        for fhir_simple, func_simple in simple_elements.items():
            if fhir_simple not in structured_data[resource_fhir][class_func]['simple_elements'].keys():
                structured_data[resource_fhir][class_func]['simple_elements'][fhir_simple] = func_simple
    # Suppression des éléments simples qui sont dans les éléments complexes
    for resource, mapping in structured_data.items():
        for class_func, mapping_elements in mapping.items():
            to_del = []
            for elem_fhir in mapping_elements['simple_elements'].keys():
                if elem_fhir in mapping_elements['complex_elements']:
                    to_del.append(elem_fhir)
            for elem in to_del:
                del structured_data[resource][class_func]['simple_elements'][elem]
    # Extensions
    resource_extensions = []
    for profil, extensions in extracted_data['resource_extensions'].items():
        for extension, path in extensions.items():
            resource_extensions.append(extension)
            class_func_extension = []
            if extension in extracted_data['mapping_extensions'].keys():
                mapping_extension_sub_elements = {}
                extension_id = extension.split('/')[-1]
                mapping_extension = extracted_data['mapping_extensions'][extension]
                mapping_extension_global = None
                class_func_extension = []
                for class_func, mapping in structured_data[profil].items():
                    extension_path = 'extension:' + extension_id
                    if extension_path in mapping['simple_elements'].keys():
                        class_func_extension.append(class_func)
                        mapping_extension_global = mapping['simple_elements'][extension_path]
                        del structured_data[profil][class_func]['simple_elements'][extension_path]
                if len(class_func_extension) == 0:
                    class_func_extension = structured_data[profil].keys()
                for class_func in class_func_extension:
                    # Extension de premier niveau
                    if path.split('.', 1)[1].startswith('extension:'):
                        # Extension simple
                        if list(mapping_extension.keys()) == ['Extension.value[x]']:
                            extension_type = 'simple'
                            if mapping_extension_global is None:
                                mapping_extension_global = mapping_extension['Extension.value[x]']
                        # Extension complexe
                        else:
                            extension_type = 'complex'
                            if 'Extension' in mapping_extension.keys():
                                if mapping_extension_global is None:
                                    mapping_extension_global = mapping_extension['Extension']
                            for elem_fhir, elem_func in mapping_extension.items():
                                if elem_fhir != 'Extension':
                                    elem_fhir = remove_prefix(elem_fhir, 'Extension.extension:')
                                    elem_fhir = remove_suffix(elem_fhir, '.value[x]')
                                    mapping_extension_sub_elements[elem_fhir] = elem_func
                            if extension in extracted_data['complex_extensions'].keys():
                                for sub_extension in extracted_data['complex_extensions'][extension]:
                                    elem_fhir = sub_extension.split('/')[-1]
                                    mapping_sub_extension = extracted_data['mapping_extensions'][sub_extension]
                                    if 'Extension.value[x]' in mapping_sub_extension:
                                        mapping_extension_sub_elements['extension:' + elem_fhir] = mapping_sub_extension['Extension.value[x]']
                                    else:
                                        sub_mapping_elements = {}
                                        elem_func = None
                                        if 'Extension' in mapping_sub_extension.keys():
                                            elem_func = mapping_sub_extension['Extension']
                                            for sub_elem_fhir, sub_elem_func in mapping_sub_extension.items():
                                                if sub_elem_fhir != 'Extension':
                                                    sub_elem_fhir = remove_prefix(sub_elem_fhir, 'Extension.extension:')
                                                    sub_elem_fhir = remove_suffix(sub_elem_fhir, '.value[x]')
                                                    sub_mapping_elements[sub_elem_fhir] = sub_elem_func
                                        if sub_extension in extracted_data['complex_extensions'].keys():
                                            for sub_sub_extension in extracted_data['complex_extensions'][sub_extension]:
                                                if sub_sub_extension in extracted_data['mapping_extensions'].keys():
                                                    if 'Extension.value[x]' in extracted_data['mapping_extensions'][sub_sub_extension]:
                                                        sub_sub_elem_fhir = sub_sub_extension.split('/')[-1]
                                                        sub_sub_elem_func = extracted_data['mapping_extensions'][sub_sub_extension]['Extension.value[x]']
                                                        sub_mapping_elements[sub_sub_elem_fhir] = sub_sub_elem_func
                                        mapping_extension_sub_elements[elem_fhir] = {'mapping': elem_func, 'elements': sub_mapping_elements}
                                        
                        structured_data[profil][class_func]['extensions'][extension_id] = {'mapping': mapping_extension_global, 'elements': mapping_extension_sub_elements, 'type': extension_type}
                    # Extension appliqué sur un élément fhir de premier niveau (pas directement sur la ressource)
                    else:
                        base_element = path.split('.', 1)[1].split('.extension:', 1)[0]
                        sub_extension = path.split('.', 1)[1].split('.', 1)[1]
                        if base_element in structured_data[profil][class_func]['complex_elements']:
                            # Extension simple
                            if 'Extension.value[x]' in mapping_extension and len(mapping_extension) == 1:
                                structured_data[profil][class_func]['complex_elements'][base_element]['elements'][sub_extension] = mapping_extension['Extension.value[x]']
                            # Extension complexe
                            else:
                                elements = {}
                                for elem_fhir, elem_func in mapping_extension.items():
                                    if elem_fhir != 'Extension.value[x]':
                                        elem_fhir = remove_prefix(elem_fhir, 'Extension.value[x].')
                                        elements[elem_fhir] = elem_func
                                structured_data[profil][class_func]['complex_elements'][base_element]['elements'][sub_extension] = {'mapping': mapping_extension_global, 'elements': elements}
    return structured_data

# Génération des schémas 
def generate_plantuml(structured_data, output_path, colors):
    # Liste contenant les directions possibles pour les flèches
    directions = ['u', 'd', 'l', 'r']
    for resource_fhir, class_mapping in structured_data.items():
        # Liste des liens entre tableaux 
        links = '\n'
        # Liste permettant de ne pas répéter les éléments complexes pour les ressources contenant plusieurs mappings 
        complex_elements = []
        # Compteur permettant d'alterner la direction des flèche
        cpt_direction = 0 
        # Un fichier par profil FHIR
        with open(output_path + '/' + resource_fhir + '.plantuml', 'w', encoding="utf-8") as f:
            f.write("@startuml\n")
            # Sous-tableaux (doivent être écrit dans le fichier avant les tableaux principaux)
            for class_func, elements in class_mapping.items():
                tables = ''
                # Eléments complexes
                for elem_fhir, sub_elements in elements['complex_elements'].items():
                    extension = False
                    elem_func = sub_elements['mapping']
                    if elem_func is not None:
                        elem_func_id = keep_alnum(elem_func)
                        links += class_func + '::' + replace_non_alnum(elem_func) + ' -' + directions[cpt_direction%4] + '-> ' + elem_func_id + '\n'
                        cpt_direction += 1 
                    if elem_fhir not in complex_elements:
                        elem_fhir_id = keep_alnum(elem_fhir)
                        complex_elements.append(elem_fhir)
                        elem_fhir_display = elem_fhir
                        if elem_fhir.startswith('extension:'):
                            elem_fhir_display = '<&plus> ' + remove_prefix(elem_fhir, 'extension:')
                            extension = True
                        elif ':' in elem_fhir:
                            elem_fhir_display = '<&layers> ' + elem_fhir
                        if elem_func is None:
                            table_title = '\nmap "' + elem_fhir_display + '" as ' + elem_fhir_id + ' #back:WhiteSmoke;header:LightGray {'
                        else: 
                            table_title = '\nmap "' + elem_func + ' : ' + elem_fhir_display + '" as ' + elem_func_id + ' #back:WhiteSmoke;header:LightGray {'
                        tables += table_title
                        sub_table = None
                        # Eléments complexes de niveau 2
                        for sub_elem_fhir, sub_elem_func in sub_elements['elements'].items():
                            sub_elem_fhir_display = sub_elem_fhir
                            if extension:
                                sub_elem_fhir_display = remove_prefix(sub_elem_fhir, 'extension:')
                            else:
                                if sub_elem_fhir.startswith('extension:'):
                                    sub_elem_fhir_display = '<&plus> ' + remove_prefix(sub_elem_fhir, 'extension:')
                                elif ':' in sub_elem_fhir:
                                    sub_elem_fhir_display = '<&layers> ' + sub_elem_fhir
                            if isinstance(sub_elem_func, str):
                                tables += '\n    ' + replace_non_alnum(sub_elem_func) + ' => ' + sub_elem_fhir_display
                            else:
                                if 'mapping' in sub_elem_func.keys():
                                    if sub_elem_func['mapping'] is not None:
                                        tables += '\n    ' + replace_non_alnum(sub_elem_func) + ' => ' + sub_elem_fhir_display
                                        sub_table = '\nmap "' + replace_non_alnum(sub_elem_func) + ' : ' + sub_elem_fhir_display + '" as ' + keep_alnum(sub_elem_func) + ' #back:WhiteSmoke;header:LightGray {'
                                    else:
                                        tables += '\n    ' + sub_elem_fhir_display + ' *--> ' + keep_alnum(remove_prefix(sub_elem_fhir, 'extension:'))
                                        sub_table = '\nmap "' + sub_elem_fhir_display + '" as ' + keep_alnum(remove_prefix(sub_elem_fhir, 'extension:')) + ' #back:WhiteSmoke;header:LightGray {'
                                    for sub_sub_elem_fhir, sub_sub_elem_func in sub_elem_func['elements'].items():
                                        sub_table += '\n    ' + replace_non_alnum(sub_sub_elem_func) + ' => ' + sub_sub_elem_fhir
                                    sub_table += '\n}\n'
                                # Eléments complexes de niveau 3
                                else:
                                    tables += '\n    ' + sub_elem_fhir_display + ' *--> ' + keep_alnum(remove_prefix(sub_elem_fhir, 'extension:'))
                                    sub_table = '\nmap "' + sub_elem_fhir_display + '" as ' + keep_alnum(remove_prefix(sub_elem_fhir, 'extension:')) + ' #back:WhiteSmoke;header:LightGray {'
                                    for sub_sub_elem_fhir, sub_sub_elem_func in sub_elem_func.items():
                                        if sub_sub_elem_fhir.startswith('extension:'):
                                            sub_sub_elem_fhir = '<&plus> ' + remove_prefix(sub_sub_elem_fhir, 'extension:')
                                        sub_table += '\n    ' + replace_non_alnum(sub_sub_elem_func) + ' => ' + sub_sub_elem_fhir
                                    sub_table += '\n}\n'
                                    
                        tables += '\n}\n'
                        if sub_table is not None:
                            f.write(sub_table)
                f.write(tables)
                # Références
                for sub_elements in elements['references'].values():
                    resource = sub_elements['resource']
                    color = ''
                    if resource in colors.keys():
                        color = ' #' + colors[resource]['header']
                    # Un tableau par profil
                    f.write('\nobject "**' + resource + '**" as ' + resource + color + ' {')
                    # Classes fonctionnelles sur la ressource
                    for sub_elem in sub_elements['mapping']:
                        f.write('\n    ' + sub_elem)
                    f.write('\n}\n')
                # Extensions (sous-tableaux pour 2 niveaux max)
                main_table_extensions = ""
                table_extensions = ""
                table_sub_extensions = ""
                for extension, extension_details in elements['extensions'].items():
                    extension_id = keep_alnum(extension)
                    mapping_extension_global = extension_details['mapping']
                    if extension_details['type'] == 'complex':
                        if mapping_extension_global is not None:
                            main_table_extensions += '\n    ' + replace_non_alnum(mapping_extension_global) + ' => <&plus> ' + extension
                            links += class_func + '::' + replace_non_alnum(mapping_extension_global) + ' -' + directions[cpt_direction%4] + '-> ' + extension_id + '\n'
                            cpt_direction += 1
                            if extension not in complex_elements:
                                table_extensions += '\nmap "' + mapping_extension_global + ' : <&plus> ' + extension + '" as ' + extension_id + ' #back:WhiteSmoke;header:LightGray {'
                        else: 
                            main_table_extensions += '\n    ' + extension + ' *-> ' + extension_id
                            if extension not in complex_elements:
                                table_extensions += '\nmap "<&plus> ' + extension + '" as ' + extension_id + ' #back:WhiteSmoke;header:LightGray {'
                        if extension not in complex_elements:
                            complex_elements.append(extension)
                            for sub_elem_fhir, sub_elem_func in extension_details['elements'].items():
                                sub_elem_fhir_display = sub_elem_fhir
                                if isinstance(sub_elem_func, str):
                                    if sub_elem_fhir.startswith('extension:'):
                                        sub_elem_fhir_display = '<&plus> ' + remove_prefix(sub_elem_fhir, 'extension:')
                                    table_extensions += '\n    ' + replace_non_alnum(sub_elem_func) + ' => ' + sub_elem_fhir_display
                                else:
                                    mapping_sub_extension_global = sub_elem_func['mapping']
                                    if mapping_sub_extension_global is not None:
                                        table_extensions += '\n    ' + replace_non_alnum(mapping_sub_extension_global) + ' => <&plus> ' + sub_elem_fhir_display
                                        table_sub_extensions = '\nmap "' + replace_non_alnum(mapping_sub_extension_global) + ' : <&plus> ' + sub_elem_fhir_display + '" as ' + keep_alnum(mapping_sub_extension_global) + ' #back:WhiteSmoke;header:LightGray {'
                                        links += extension_id + '::' + replace_non_alnum(mapping_sub_extension_global) + ' -' + directions[cpt_direction%4] + '-> ' + keep_alnum(mapping_sub_extension_global) + '\n'
                                    else:
                                        table_extensions += '\n    <&plus>' + sub_elem_fhir_display + ' *--> ' + keep_alnum(remove_prefix(sub_elem_fhir, 'extension:'))
                                        table_sub_extensions = '\nmap <&plus>"' + sub_elem_fhir_display + '" as ' + keep_alnum(remove_prefix(sub_elem_fhir, 'extension:')) + ' #back:WhiteSmoke;header:LightGray {'
                                    for sub_sub_elem_fhir, sub_sub_elem_func in sub_elem_func['elements'].items():
                                        table_sub_extensions += '\n    ' + replace_non_alnum(sub_sub_elem_func) + ' => ' + sub_sub_elem_fhir
                                    table_sub_extensions += '\n}\n'
                            table_extensions += '\n}\n'
                    else:
                        if mapping_extension_global is not None:
                            main_table_extensions += '\n    ' + replace_non_alnum(mapping_extension_global) + ' => <&plus> ' + extension
                f.write(table_sub_extensions)
                f.write(table_extensions)
                # Tableaux principal (un par classe fonctionnelle mappée sur la ressource)
                color = ''
                if resource_fhir in colors.keys():
                    color = ' #back:' + colors[resource_fhir]['back'] + ';header:' + colors[resource_fhir]['header']
                f.write('\nmap "**' + class_func + ' : ' + resource_fhir + '**" as ' + class_func +  color + ' {')
                # Eléments simples
                for elem_fhir, elem_func in elements['simple_elements'].items():
                    elem_fhir_display = elem_fhir
                    if elem_fhir.startswith('extension:'):
                        elem_fhir_display = '<&plus> ' + remove_prefix(elem_fhir, 'extension:')
                    elif ':' in elem_fhir:
                        elem_fhir_display = '<&layers> ' + elem_fhir
                    f.write('\n    ' + replace_non_alnum(elem_func) + ' => ' + elem_fhir_display)
                # Eléments complexes
                for elem_fhir, sub_elements in elements['complex_elements'].items():
                    elem_fhir_display = elem_fhir
                    elem_fhir_id = keep_alnum(elem_fhir)
                    elem_func = sub_elements['mapping']
                    if elem_fhir.startswith('extension:'):
                        elem_fhir_display = '<&plus> ' + remove_prefix(elem_fhir, 'extension:')
                    elif ':' in elem_fhir:
                        elem_fhir_display = '<&layers> ' + elem_fhir 
                    if elem_func is None:
                        f.write('\n    ' + elem_fhir_display + ' *-> ' + elem_fhir_id)
                    else:
                        f.write('\n    ' + replace_non_alnum(elem_func) + ' => ' + elem_fhir_display)
                f.write(main_table_extensions)
                f.write('\n}\n')
                # Liens des références             
                for elem_fhir, sub_elements in elements['references'].items():
                    links += class_func + ' -' + directions[cpt_direction%4] + '-> ' + sub_elements['resource'] + ' : ' + elem_fhir + '\n'
                    cpt_direction += 1 
            f.write(links)
            f.write("\n@enduml")
            
data = get_data_from_db(db_path, sql_query)
extracted_data = extract_data(data)
structured_data = structure_data(extracted_data)
generate_plantuml(structured_data, output_path, colors)