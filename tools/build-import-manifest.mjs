// Build the IMPORT subtree + import-manifest.json from local source folders.
//
// Reads OIB (OpenIntuneBaseline) Settings Catalog files and CIS Win11
// Benchmark files, writes them VERBATIM into `import/<baseline>/<slug>.json`
// (server-only fields are stripped by the M365++ Settings Catalog provider
// at POST time, so re-shaping here is unnecessary), and emits a single
// `import-manifest.json` at repo root listing both baselines.
//
// Idempotent: re-running deletes + rebuilds `import/`. Designed to be run
// from the repo root: `node tools/build-import-manifest.mjs`.

import { readdir, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');

const OIB_SOURCE =
  'E:/Downloads-Archive/OIB/OpenIntuneBaseline/WINDOWS/IntuneManagement/SettingsCatalog';
const CIS_SOURCE =
  'E:/Downloads-Archive/IntuneBaselines-reference/4.0 - CIS Benchmarks/CIS -  Intune for Windows 11 Benchmarks';

const IMPORT_DIR = join(REPO_ROOT, 'import');

// ─── Helpers ──────────────────────────────────────────────────────────────

function slugify(name) {
  return name
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 120);
}

/** Pick the bits we care about for the manifest from a full policy JSON. */
function summarize(policy) {
  return {
    name: policy.name ?? '(unnamed)',
    platforms: policy.platforms ?? null,
    technologies: policy.technologies ?? null,
    settingCount: policy.settingCount ?? (policy.settings?.length ?? 0),
    templateFamily: policy.templateReference?.templateFamily ?? null,
  };
}

/** Parse CIS L1/L2/BL/NG/other from filename. */
function cisLevel(name) {
  if (/ L1 /.test(name)) return 'L1';
  if (/ L2 /.test(name)) return 'L2';
  if (/ BL /.test(name)) return 'BL';
  if (/ NG /.test(name)) return 'NG';
  return 'other';
}

/** Parse OIB category (SC = Settings Catalog, ES = Endpoint Security) from name. */
function oibCategory(name) {
  const m = name.match(/Win - OIB - (\w+) -/);
  return m ? m[1] : null;
}

async function ensureCleanDir(dir) {
  if (existsSync(dir)) await rm(dir, { recursive: true, force: true });
  await mkdir(dir, { recursive: true });
}

async function readJson(path) {
  // CIS files come from PowerShell `Out-File` which defaults to UTF-16 LE
  // with BOM on Windows; OIB files are plain UTF-8. Detect by reading raw
  // bytes and decoding accordingly.
  const buf = await readFile(path);
  let text;
  if (buf[0] === 0xff && buf[1] === 0xfe) {
    text = new TextDecoder('utf-16le').decode(buf.subarray(2));
  } else if (buf[0] === 0xfe && buf[1] === 0xff) {
    text = new TextDecoder('utf-16be').decode(buf.subarray(2));
  } else if (buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf) {
    text = new TextDecoder('utf-8').decode(buf.subarray(3));
  } else {
    text = buf.toString('utf8');
  }
  return JSON.parse(text);
}

// ─── Per-baseline builders ────────────────────────────────────────────────

async function buildBaseline({ sourceDir, baselineId, slugTag, tagger }) {
  const outDir = join(IMPORT_DIR, baselineId);
  await ensureCleanDir(outDir);

  const files = (await readdir(sourceDir)).filter((f) => f.endsWith('.json'));
  const policies = [];
  const seenSlugs = new Set();

  for (const file of files) {
    const full = join(sourceDir, file);
    let policy;
    try {
      policy = await readJson(full);
    } catch (e) {
      console.warn(`SKIP ${file} — invalid JSON (${e.message})`);
      continue;
    }
    const meta = summarize(policy);
    let slug = slugify(meta.name);
    if (!slug) slug = slugify(file.replace(/\.json$/, ''));
    // Ensure uniqueness — CIS has near-duplicate names.
    let unique = slug;
    let n = 2;
    while (seenSlugs.has(unique)) {
      unique = `${slug}-${n++}`;
    }
    seenSlugs.add(unique);

    const outFile = `import/${baselineId}/${unique}.json`;
    await writeFile(join(REPO_ROOT, outFile), JSON.stringify(policy, null, 2), 'utf8');

    policies.push({
      slug: unique,
      name: meta.name,
      platforms: meta.platforms,
      technologies: meta.technologies,
      settingCount: meta.settingCount,
      templateFamily: meta.templateFamily,
      ...tagger(meta, file),
      file: outFile,
    });
  }

  policies.sort((a, b) => a.name.localeCompare(b.name));
  console.log(`${baselineId}: wrote ${policies.length} policies`);
  return policies;
}

// ─── Main ─────────────────────────────────────────────────────────────────

async function main() {
  await mkdir(IMPORT_DIR, { recursive: true });

  const oibPolicies = await buildBaseline({
    sourceDir: OIB_SOURCE,
    baselineId: 'oib-windows-v3.8',
    tagger: (meta) => ({ category: oibCategory(meta.name) }),
  });

  const cisPolicies = await buildBaseline({
    sourceDir: CIS_SOURCE,
    baselineId: 'cis-windows11-v4',
    tagger: (_meta, file) => ({ level: cisLevel(file) }),
  });

  const manifest = {
    baselines: [
      {
        id: 'oib-windows-v3.8',
        name: 'OpenIntuneBaseline — Windows',
        version: '3.8',
        credit: 'SkipToTheEndpoint',
        license: 'GPL-3.0',
        source: 'https://github.com/SkipToTheEndpoint/OpenIntuneBaseline',
        platform: 'windows10',
        policyCount: oibPolicies.length,
        policies: oibPolicies,
      },
      {
        id: 'cis-windows11-v4',
        name: 'CIS - Intune for Windows 11 (v4.0)',
        version: '4.0',
        credit: 'intuneAdmin',
        license: 'MIT',
        source: 'https://github.com/IntuneAdmin/IntuneBaselines',
        platform: 'windows10',
        policyCount: cisPolicies.length,
        policies: cisPolicies,
      },
    ],
  };

  await writeFile(
    join(REPO_ROOT, 'import-manifest.json'),
    JSON.stringify(manifest, null, 2),
    'utf8',
  );
  console.log(`import-manifest.json written (${oibPolicies.length + cisPolicies.length} total)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
