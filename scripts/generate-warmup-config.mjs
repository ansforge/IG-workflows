// Génère un sushi-config.yaml de warmup à partir de fhir-packages.txt.
// Pour les packages listés plusieurs fois (ex: hl7.fhir.fr.core 2.1.0 et 2.2.0),
// conserve la dernière version rencontrée (la plus récente dans le fichier).
import { readFileSync, writeFileSync } from 'fs';

const [,, inputFile, outputFile] = process.argv;
const lines = readFileSync(inputFile, 'utf8').split('\n');
const pkgs = {};
for (const line of lines) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const [id, version = 'current'] = trimmed.split(/\s+/);
  pkgs[id] = version;
}
const deps = Object.entries(pkgs).map(([id, v]) => `  ${id}: ${v}`).join('\n');
const yaml = `id: oid-index-warmup
canonical: https://example.org/oid-warmup
name: OIDIndexWarmup
status: draft
version: 0.0.1
fhirVersion: 4.0.1
copyrightYear: 2026+
releaseLabel: ci-build
dependencies:
${deps}
`;
writeFileSync(outputFile, yaml);
console.log(`Warmup sushi-config généré avec ${Object.keys(pkgs).length} dépendances : ${Object.keys(pkgs).join(', ')}`);
