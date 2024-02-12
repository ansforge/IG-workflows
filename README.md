![Logo_LEF_CI-SIS](https://user-images.githubusercontent.com/48218773/227532484-eff82649-4e42-49c6-966a-dc3ea78cf59c.png)

# GitHub Action pour la publication d'IG FHIR

GitHub Action pour les IG FHIR : 
- [Lancement de sushi](#Sushi)
- [Tests avec le validateur_cli](#Tests-avec-le-validator_cli) 
- [Incorporation des projets de simplifier (Methode bake)](#Incorporation-des-projets-de-simplifier)
- [Publication des releases sur un repo github](#Génération-de-release-pour-publication)
- [Génération du diagramme plantuml à partir de des données de l'IG](#Génaration-du-diagramme-plantUML-de-lIG)
- [Génération des testscripts avec le projet testscript-generator](#Génération-des-fichiers-testscripts)
- [Publication sur les pages github](#Publication-sur-les-pages-de-github) :
  - IG
  - Diagramme de class plantuml généré à partir des données de l'IG
  - Rapport de validation du validator_cli


## Usage

### Example Workflow file

Un exemple pour publier sur les pages github avec lancement des tests, generation du diagramme pantuml et des testscripts

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:      
          path: igSource
      - uses: ansforge/IG-workflows@v0.1.0
        with:      
          repo_ig: "./igSource"   
          github_page: "true"
          github_page_token: ${{ secrets.GITHUB_TOKEN }}
          bake: "true"
          nos: "true"
          validator_cli: "true"
          publish_repo: "ansforge/IG-website-release"
          publish_repo_token :  ${{ secrets.ANS_IG_API_TOKEN }}
          publish_path_outpout : "./IG-website-release/www/ig/fhir"
          generate_plantuml : "true"
          generate_testscript : "true"
```
Un exemple pour publier une release sur le repo "ansforge/IG-website-release" dans les ig/fhir

```yaml
jobs:
  run-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:      
          path: igSource
      - uses: ansforge/IG-workflows@v0.1.0
        with:      
          repo_ig: "./igSource"   
          github_page: "true"
          github_page_token: ${{ secrets.GITHUB_TOKEN }}
          bake: "true"
          nos: "true"
          validator_cli: "true"
          publish_repo: "ansforge/IG-website-release"
          publish_repo_token :  ${{ secrets.ANS_IG_API_TOKEN }} 
          publish_path_outpout : "./IG-website-release/www/ig"
```




Un exemple pour publier une release sur le repo "ansforge/IG-website-release" dans les ig

```yaml
jobs:
  run-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:      
          path: igSource
      - uses: ansforge/IG-workflows@v0.1.0
        with:      
          repo_ig: "./igSource"   
          github_page: "true"
          github_page_token: ${{ secrets.GITHUB_TOKEN }}
          bake: "true"
          nos: "true"
          validator_cli: "true"
          publish_repo: "ansforge/IG-website-release"
          publish_repo_token :  ${{ secrets.ANS_IG_API_TOKEN }} 
          publish_path_outpout : "./IG-website-release/www/ig"
```
### Inputs

| name               | value   | default               | description                                                                                                                                                                                                                                                                                                     |
|--------------------|---------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| github_page_token       | string  |  | Token pour passer les GitHub Pages du repo |
| github_page                | boolean | false                 | Publication de l'IG dans les GitHub pages                                                                                                                                                                                                                                                                          |
| repo_ig             | string  |             | Chemin d'accés au repertoire des sources de l'IG                                                                                                                                                                                                                          |
| bake              | boolean | false                 | Permet d'inclure les les projets annuaires et FrCore qui sont sur simplifier                                                                                                                                                                                                                                                                               |
| nos   | boolean | false                 | Pour la vérification. Permet d'installer le NOS (à partie du ZIP)                                                                                                                                            |
| validator_cli             | boolean | False                  | Permet de lancer les tests avec le validator_cli d'HL7                                                                                                                                                                                                  |
| termino_server | string  | 'http://tx.fhir.org'           | Permet la verification sur le serveur de terminologie passé en paramètre.                                                                                                                                                                                                                     |
| publish_repo               | string | ''                 | Permet d'indiquer le repo git de publication  de l'IG                
| publish_path_outpout               | string | ''                 | Chemin de publication de l'IG                 |
| publish_repo_token          | string  |                   | Token pour publier sur le repo GIT de publication                                                                                                                                                                                                                                                                  |
| generate_plantuml          | string  | false                  | Génération de diagramme plantuml                                                                                                                                                                                                                                                                  |
| generate_testscript          | string  | false                  | Génération des fichiers testscripts                                                                                                                                                                                                                                                                  |





## Fonctionnalités

### Sushi

Principes  :
- Installation de sushi
- Lancement de sushi
- Résulats accéssibles via le terminal
  - ![image](https://github.com/ansforge/IG-workflows/assets/101335975/e8c0b772-b6a9-4006-be8e-403319996346)

### Incorporation des projets de simplifier
Pour installer les dépendances à des projets simplifier, il faut utiliser la methode bake de simplifier : 
- Installation de .NET
- Installation du terminal firely
- Installation des porjets :
  - ans.annuaire.fhir.r4
  - hl7.fhir.fr.core

### Tests avec le validator_cli

Principes : 
- Téléchargement de la dernière version du valitor_cli
- Lancemennt des tests
- Affichage des resultats dans la sortie de l'action
- Publication des résultats dans les pages github (branch gh-pages)

### Génération du diagramme plantUML de l'IG

Principes : 
- Installation de python
- Lancement du script python de génération :
  - Requête sqlite sur la base de données sqlite générée par l'IG
  - Création du fichier plantuml
  - Génération du diagramme png et plantuml
- Publication des diagrammes dans les pages github (branch gh-pages)
  - ![image](https://github.com/ansforge/IG-workflows/assets/101335975/34ac663a-3c35-4da5-b7a1-883b20881eea)

### Génération des fichiers testscripts

Principes : 
- Installation du projet testscript-generator
- Lancement de la génération des testscripts :
  - bundle exec bin/testscript_generator read mustSupport search interaction 
- Publication des testscriots dans les pages github (branch gh-pages)
  - Les fichiers sont présents dans le sous repertoire testscript

### Publication sur les pages de github 

Les élément générés sont publiés sur les pages github (branch gh-pages) avec une sous-aborescence avec le nom de la branche : 
 ![image](https://github.com/ansforge/IG-workflows/assets/101335975/660a6558-525b-4361-bbde-e74de4c1525d)

Les pages sont accéssible via : De publier les pages : https://ansforge.github.io/{nom du repo}/ig/{nom de la branche} 
### Génération de release pour publication
Principes : 
- Création de la version courrante
- Creation la release pour publication
- Push de la release dans le repo distant


