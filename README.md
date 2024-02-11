# GitHub Action pour la publication d'IG FHIR

GitHub Action pour les IG FHIR : 
- Lancement de sushi
- Tests avec le validateur_cli 
- Incorporation des projets de simplifier (Methode bake)
- Publication des releases sur un repo github
- Génération du diagramme plantuml à partir de des données de l'IG
- Publication sur les pages github :
  - IG
  - Diagramme de class plantuml généré à partir des données de l'IG
  - Rapport de validation du validator_cli

## Fonctionnalités

### Sushi

### Tests avec le validator_cli

### Génaration du diagramme plantUML de l'IG

### Publication sur les pages de github 

### Génération de release pour publication

## Usage

### Example Workflow file

Un exemple pour publier sur les pages github avec lancement des tests

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:      
          path: igSource
      - uses: ansforge/IG-workflows@addAction
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
      - uses: ansforge/IG-workflows@addAction
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
      - uses: ansforge/IG-workflows@addAction
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

