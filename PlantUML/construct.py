#python3.12 importplan.py 
import sqlite3
from contextlib import closing

dir_path_db =  sys.argv[1] 
file_output = sys.argv[2] 



sqlQuery = """ 
 select a.*,b.name,c.name
 from (
    select
            json_extract(Resources.json,'$.name') as resource,
            json_extract(Resources.json,'$.baseDefinition') as base,
            replace(json_extract(Resources.json,'$.baseDefinition'),'http://hl7.org/fhir/StructureDefinition/','') as baseSimple,
            value as element ,
            json_extract(Resources.json,fullkey) as id,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'short')) as commentaire,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'min')) as min,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'max')) as max,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'binding.valueSet')) as Valueset,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'type')) as type,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'mapping')) as mapping,
            url,
            json_extract(Resources.json, REPLACE(fullkey,'id', 'type[0].profile[0]')) as profileExtension
    from   
            Resources,
            json_tree(Resources.json,'$.differential.element') as jtree
    where   
            Resources.type='StructureDefinition'
            --and json_extract(Resources.json,'$.type')!='Extension'
            and (jtree.key='id' )
) a 
LEFT OUTER JOIN resources b ON a.profileExtension = b.url
LEFT OUTER JOIN resources c ON a.Valueset = c.url;
"""

def get_data_from_db(db_path):
    data = []
    with closing(sqlite3.connect(db_path)) as conn:  # utilisez le chemin de votre base de données ici
        with closing(conn.cursor()) as cursor:
            cursor.execute(sqlQuery)  # remplacez "your_table" par le nom de votre table
            data = cursor.fetchall()
    return data

def write_to_plantuml_file(data, file_path):
    with open(file_path, 'w') as f:  # utilisez le chemin de votre fichier PlantUML ici
        f.write("@startuml\n")
        f.write("set namespaceSeparator ?\n")
        f.write("hide circle\n")
        f.write("hide class fields\n")
        f.write("\npackage IG #DDDDDD{\n")
        resource = ""
        cptClass = 0

        f.write("\n     package Profiles #DDDDDD{\n")        
        for count,row in enumerate(data):
            if(row[2]!='Extension'):
                if(resource!=row[0]) :
                    if(cptClass !=0) :
                        f.write( "\n        } \n")
                    f.write( "\n        class " +   row[0] +"{\n")
                    cptClass =  cptClass + 1
                if(row[2] != row[3]) : 
                    f.write("\n             "+ row[4] )     
                    f.write(" => ");    
                    if( "extension:" in row[4]) :
                        f.write("<&plus>")
                    f.write("["+ str(row[6])+ ".."+ str(row[7]) +"]");   
            resource = row[0]
        f.write("\n         }\n")   
        f.write("\n     }")      


        #Ecritures des dépendances avec  les extension
        f.write("\n     package extension #paleturquoise {\n")


        #Ecritures des dépendances avec  les extension
        resource = ""
        cptClass = 0
        for count,row in enumerate(data):
            if(row[2]!='Extension'):
                if(row[2] != row[3]) :  
                    if( "extension:" in row[4]) :
                        f.write('\n     ' + row[0] + ' -[#black,dashed,thickness=2]-> ' +  str(row[13]) +"") 
            resource = row[0]
        f.write("\n")   


        resource = ""
        cptClass = 0
        for count,row in enumerate(data):

            if(row[2] =='Extension'):
                if(resource!=row[0]) :
                    if(cptClass !=0) :
                        f.write( "\n        } ")
                    f.write( "\n        class " +   str(row[0]) +"{\n")
                    cptClass =  cptClass + 1
                if(row[2] != row[3]) : 
                    f.write("\n          " +row[4] )     
                    f.write(" => ");    
                    f.write("["+ str(row[6])+ ".."+ str(row[7]) +"]");   
            resource = row[0]
        f.write("\n         }")
        f.write("\n     }")

        #Ecritures des dépendances aevc les valueset
        f.write("\n     package valueset #PaleVioletRed{\n")
        for count,row in enumerate(data):
            if(row[8]) : 
                f.write( '\n        class ' +   str(row[14]) +"  \n")
                f.write('\n     ' + row[0] + ''+  ' -[#black,dotted,thickness=2]-> ' +  str(row[14])  +"\n") 
        f.write("       }\n")
        f.write("}\n")
        #Ecritures des dépendances avec  les ressources de base
        f.write("\npackage fhir #palegreen {\n")
        resource = ""
        for count,row in enumerate(data):

            if(resource!=row[0]) :
                if(row[2] != 'Extension') : 
                    f.write( "\n    class " +   row[2] +"\n")
                    f.write( "\n    "  + row[2] + ' --> ' +  row[0] +"\n")
            resource = row[0]
        f.write("}")

        f.write("\n@enduml")

data = get_data_from_db(dir_path_db)
write_to_plantuml_file(data, file_output)


