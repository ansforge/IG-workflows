# Image Docker `fhir-ig-builder`

Ce document décrit l'image Docker utilisée pour builder les guides d'implémentation FHIR (`Dockerfile` + `.github/workflows/build-docker.yml`), distincte de l'action composite elle-même (voir `README.md` pour l'action `ansforge/IG-workflows`).

- **Registre** : `ghcr.io/ansforge/fhir-ig-builder`
- **Page du package** : https://github.com/ansforge/IG-workflows/pkgs/container/fhir-ig-builder
- **Source du build** : `Dockerfile` (racine du repo)
- **Workflow de build/publication** : `.github/workflows/build-docker.yml`

## Contenu de l'image

- Ubuntu 24.04
- Java 17 (`openjdk-17-jdk-headless`)
- Node.js 20 + [SUSHI](https://fshschool.org/) installé globalement
- Jekyll (pour le rendu HTML du IG Publisher)
- GitHub CLI (`gh`)
- Graphviz (`dot`), Python 3
- Le JAR du **IG Publisher** HL7, pré-téléchargé dans `/root/publisher.jar` (version tracée dans `/root/publisher-version.txt`)
- Un **cache pré-chargé de packages FHIR** (`~/.fhir/packages/`), pour éviter de les re-télécharger à chaque build d'IG

### Warmup : pré-chargement des packages FHIR

Les packages listés dans `fhir-packages.txt` (un `<package-id> <version>` par ligne, `latest` accepté) sont téléchargés et indexés (`.index.db`) pendant le build de l'image, via une IG FHIR **synthétique** générée à la volée (`scripts/synthetic-ig/`, config produite par `scripts/generate-warmup-config.mjs`) et passée dans le IG Publisher (`-ig . -tx n/a`, sans serveur de terminologie — le but est uniquement de peupler le cache de packages, pas de valider du contenu).

Cette IG synthétique embarque une page minimale (`scripts/synthetic-ig/input/pagecontent/index.md`) et un `menu:` défini dans le `sushi-config.yaml` généré, nécessaires pour que le IG Publisher puisse générer son `_includes/menu.xml` et terminer le rendu Jekyll sans erreur (cf. historique : sans page/menu, l'étape Jekyll du warmup échouait avec `Could not locate the included file 'menu.xml'` — l'échec était sans conséquence fonctionnelle car masqué par un `|| true`, mais poluait les logs de build).

**Note sur les doublons dans `fhir-packages.txt`** : si un même `package-id` apparaît plusieurs fois avec des versions différentes, seule la **dernière occurrence** est effectivement pré-chargée (`scripts/generate-warmup-config.mjs` ne garde qu'une version par id). Modifier ce fichier et pousser sur `main` déclenche un rebuild automatique de l'image.

## Déclenchement du build

Le workflow `build-docker.yml` se lance :
- sur push sur `main` touchant `Dockerfile`, `fhir-packages.txt`, ou le workflow lui-même,
- manuellement (`workflow_dispatch`),
- automatiquement chaque **lundi à 06:00 UTC** (cron), pour capter les nouvelles versions de SUSHI/IG Publisher sans changement de fichier.

## Labels OCI (métadonnées visibles sur la page du package)

Le workflow résout, avant chaque build (étape *Resolve versions*), et expose comme labels OCI de l'image :
- `org.opencontainers.image.description` : ligne descriptive + version de l'IG Publisher embarquée + version de SUSHI embarquée + liste des packages FHIR préchargés (`id@version`, séparés par des virgules)
- `org.opencontainers.image.created` : date de publication (UTC, RFC 3339)

Ces valeurs sont aussi passées en `build-args` au `Dockerfile` (`PUBLISHER_VERSION`, `SUSHI_VERSION`, `PACKAGES_LIST`, `BUILD_DATE`), afin que la version de SUSHI réellement installée corresponde exactement à celle annoncée dans le label (SUSHI n'est plus installé en `latest` implicite au niveau du `Dockerfile`, mais pinné à la version résolue par le workflow).

Pour inspecter les labels d'une image déjà publiée :
```bash
docker inspect ghcr.io/ansforge/fhir-ig-builder:latest \
  --format '{{ index .Config.Labels "org.opencontainers.image.description" }}'
```

## Tags et politique de rétention

- **`:latest`** est poussé à **chaque** build. C'est le tag à utiliser pour consommer l'image (référencé par les workflows des repos IG qui utilisent cette image en `container:`).
- **`:YYYY-MM`** (ex. `:2026-08`) est poussé **uniquement pour le premier build du mois civil en cours** (détection : le workflow liste les tags déjà présents sur le registre via l'API GitHub Packages ; si aucun tag du mois courant n'existe, il est ajouté à ce build). Ce tag constitue un **snapshot mensuel permanent**.

Après chaque publication, le workflow (étape *Clean up old image versions*) supprime toutes les versions précédentes de l'image, **sauf** :
1. celle qui vient d'être publiée (celle qui porte désormais `:latest`),
2. toute version portant un tag mensuel `YYYY-MM`.

**Objectif** : conserver un historique d'une image par mois (permettant de rebuilder une IG avec les versions de SUSHI/IG Publisher/packages FHIR telles qu'elles étaient à une date donnée), sans accumuler indéfiniment les builds intermédiaires de la semaine/du cron.

La suppression se fait via l'API GitHub Packages (`gh api ... -X DELETE`) avec le `GITHUB_TOKEN` du workflow (qui a le rôle *admin* sur ce package car c'est ce repo qui le publie — pas de PAT nécessaire). Un échec de suppression individuel n'interrompt pas le job (juste un `::warning::` dans les logs) : l'image vient déjà d'être publiée avec succès à ce stade.

L'attestation de provenance (`provenance`) de `docker/build-push-action` est désactivée (`provenance: false`) pour éviter qu'un manifeste supplémentaire non tagué soit créé à chaque build, ce qui compliquerait la logique de rétention ci-dessus.

## Consommer l'image

```yaml
jobs:
  build-ig:
    runs-on: ubuntu-latest
    container: ghcr.io/ansforge/fhir-ig-builder:latest
    steps:
      - uses: actions/checkout@v4
      # sushi, java, jekyll, gh, le JAR du publisher et les packages FHIR courants sont déjà présents
```

Pour figer une version précise (reproductibilité, ex. pour rejouer un build tel qu'il aurait tourné à une date donnée) :
```yaml
container: ghcr.io/ansforge/fhir-ig-builder:2026-08
```

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Définition de l'image (paquets système, SUSHI, Publisher, warmup des packages FHIR, labels OCI) |
| `.github/workflows/build-docker.yml` | Build, résolution des versions/labels, tagging mensuel, publication, nettoyage |
| `fhir-packages.txt` | Liste des packages FHIR à pré-charger dans l'image |
| `scripts/generate-warmup-config.mjs` | Génère le `sushi-config.yaml` de l'IG synthétique de warmup à partir de `fhir-packages.txt` |
| `scripts/synthetic-ig/` | IG FHIR synthétique minimale utilisée uniquement pour le warmup (packages + cache), sans rapport avec les IGs réelles publiées via l'action |
