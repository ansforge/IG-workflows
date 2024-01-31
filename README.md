# GitHub Action pour la publication d'IG

GitHub Action pour les IG FHIR : 
- Lancement de sushi
- Tests avec le validateur_cli 
- Incorporation des projets de simplifier (Metode bake)
- Publication sur les pages github
- Publication des releases sur un repo github

## Usage

### Example Workflow file

Un exemple pour publier sur les pages github avec lancement des tests

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:      
          path: igSource
      - uses: M-Priour/IG-workflows@main
        with:      
          repo_ig: "./igSource"   
          github_page: "true"
          github_page_token: ${{ secrets.GITHUB_TOKEN }}
          bake: "true"
          nos: "true"
          validator_cli: "true"
          publish_repo: "ansforge/IG-website-release"
          publish_repo_token :  ${{ secrets.GITHUB_TOKEN }} 
```


### Inputs

| name               | value   | default               | description                                                                                                                                                                                                                                                                                                     |
|--------------------|---------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| github_page_token       | string  |  | Token pour passer les GitHub Pages du repo |
| github_page                | boolean | false                 | Publication de l'IG dans les GitHub pages                                                                                                                                                                                                                                                                          |
| repo_ig             | string  |             | Chemin d'accés au repertoire des sources de l'IG                                                                                                                                                                                                                          |
| bake              | boolean | false                 | Permet d'inclure les les projets annuaires et FrCore qui sont sur simplifier                                                                                                                                                                                                                                                                               |
| nos   | boolean | false                 | Pour la vérification. Permet d'installer le NOS (A partie du ZIP)  a                                                                                                                                          |
| validator_cli             | boolean | False                  | Permet de lancer les tests aevc le validatorècli d'HL7                                                                                                                                                                                                  |
| termino_server | string  | 'http://tx.fhir.org'           | Permet la verification sur le serveur de terminologie passé en paramètre.                                                                                                                                                                                                                     |
| publish_repo               | string | ''                 | Permet d'indiquer le repo git de publication  de l'IG                                                                                                                                                                                                                                                                                |
| publish_repo_token          | string  |                   | Token pour publier sur le repo GIT de publication                                                                                                                                                                                                                                                                  |

