import fpi from 'fhir-package-installer';
import { readFileSync } from 'fs';

const lines = readFileSync(process.argv[2] || 'fhir-packages.txt', 'utf8').split('\n');

for (const line of lines) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const [id, version = 'latest'] = trimmed.split(/\s+/);
  const packageId = version === 'latest' ? id : `${id}@${version}`;
  console.log(`Installing ${packageId}...`);
  await fpi.install(packageId);
}
