#python3.12 importplan.py 
import sqlite3
import sys
import hashlib
from contextlib import closing

dir_path_db =  sys.argv[1] 
file_output = sys.argv[2] 



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
                if((row[2] != row[3]) and (str(row[13]) != 'None')) :  
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
            if(row[8] and (str(row[14])!='None')) : 
                print (row[14])
                f.write( '\n        class ' +   str(row[14]) +"  \n")
                f.write('\n     ' + row[0] + ''+  ' -[#black,dotted,thickness=2]-> ' +  str(row[14])  +"\n") 
        f.write("       }\n")
   
        #Ecritures des dépendances avec  les ressources de base
        f.write('\npackage "Ressources de base" #palegreen {\n')
        resource = ""
        for count,row in enumerate(data):

            if(resource!=row[0]) :
                if(row[2] != 'Extension') : 
                    f.write( '\n class "' +   row[2] +'" as  ' +  f"class{hashlib.md5(row[2].encode()).hexdigest()}" +" \n")
                    f.write( "\n    "  +  f"class{hashlib.md5((row[2].encode())).hexdigest()}"  + " --> " +  row[0] +"\n")
            resource = row[0]
        f.write("}")

        f.write("\n@enduml")

data = get_data_from_db(dir_path_db)
write_to_plantuml_file(data, file_output)


