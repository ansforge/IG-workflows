# Scripts

Ce dossier regroupe l'ensemble des scripts utilitaires utilisés par l'action GitHub (`action.yml`) et par le `Dockerfile` de l'image `fhir-ig-builder`. Si vous déplacez ou renommez un fichier ici, pensez à mettre à jour les chemins correspondants dans `action.yml` et/ou `Dockerfile` (indiqués ci-dessous pour chaque script).

## `generate-warmup-config.mjs`

Génère un `sushi-config.yaml` de warmup à partir de `fhir-packages.txt` (liste des packages FHIR à précharger dans l'image Docker). Pour un package listé plusieurs fois avec des versions différentes, seule la dernière version rencontrée dans le fichier est conservée.

- **Entrées** : `<fichier fhir-packages.txt> <fichier sushi-config.yaml de sortie>`
- **Sortie** : un `sushi-config.yaml` minimal avec les dépendances FHIR correspondantes
- **Appelé par** :
  - `Dockerfile` (étape de warmup, génère `synthetic-ig/sushi-config.yaml`)
  - `.github/workflows/build-docker.yml` (calcule la liste de packages `PACKAGES_LIST` injectée dans le label OCI de l'image)

## `synthetic-ig/`

Fixture d'IG minimale (`ig.ini`, `sushi-config.yaml` placeholder, `input/pagecontent/index.md`, `input/fsh/`) utilisée uniquement au moment du **build de l'image Docker**. Le `Dockerfile` lance un build SUSHI + IG Publisher "à blanc" sur cette IG synthétique (dont le `sushi-config.yaml` est régénéré par `generate-warmup-config.mjs` avec les packages de `fhir-packages.txt`), afin de précharger et valider le cache de packages FHIR (`~/.fhir/packages/`) directement dans l'image.

- **Appelé par** : `Dockerfile` (étape de warmup)

## `plantuml/`

Scripts Python qui interrogent la base sqlite `package.db` (générée par l'IG Publisher dans `output/`) pour produire des diagrammes PlantUML **additionnels** montrant les liens entre les artefacts FHIR d'un IG. Ces diagrammes ne remplacent pas la génération native de diagrammes PlantUML de l'IG Publisher (voir la [documentation HL7](https://build.fhir.org/ig/FHIR/ig-guidance/diagrams-plantuml.html)).

Requièrent Python 3 (aucune dépendance externe, uniquement `sqlite3`/`json`/stdlib).

### `plantuml/construct.py`

Génère `graph.puml` : un diagramme des StructureDefinitions de l'IG (héritage, éléments, cardinalités, ValueSets, mappings).

- **Entrées** : `<chemin vers package.db> <chemin du fichier .puml de sortie>`
- **Appelé par** : `action.yml`, étape "🎨 Run PlantUML (parallel)", quand l'input `generate_plantuml: true`

### `plantuml/construct_mapping_global.py`

Génère, dans le dossier de sortie, un diagramme de mapping global entre les profils de l'IG.

- **Entrées** : `<chemin vers package.db> <dossier de sortie>`
- **Appelé par** : `action.yml`, même étape, quand l'input `generate_mapping_plantuml: true`

### `plantuml/construct_mappings.py`

Génère, dans le même dossier de sortie, un diagramme de mapping détaillé par ressource.

- **Entrées** : `<chemin vers package.db> <dossier de sortie>`
- **Appelé par** : `action.yml`, même étape, quand l'input `generate_mapping_plantuml: true`
