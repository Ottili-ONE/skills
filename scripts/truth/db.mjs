// Isolated PostgreSQL database per job, with a non-superuser application role so row level security is really exercised.
// Usage: node scripts/truth/db.mjs <create|url|env|grant|drop|list|reap|exec|bootstrap> [options]
//   create  --job ID [--fresh]            create (or reuse) the job database, print JSON with admin/migrator/app URLs
//   url     --job ID [--role app|migrator|admin]
//   env     --job ID                      print shell exports (TRUTH_DATABASE_URL, TRUTH_DATABASE_APP_URL, ...)
//   grant   --job ID                      (re)grant the app role on every schema/table/sequence/function (run after migrations)
//   exec    --job ID [--role migrator|app|admin] (--sql "..." | --file path.sql)
//   drop    --job ID
//   list    [--prefix truth_]
//   reap    --older-than 24h [--prefix truth_]
// Environment: TRUTH_PG_ADMIN_URL (superuser URL, required), TRUTH_PG_ROLE_PASSWORD (default: truth-dev-only)
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { EXIT, KIT_DIR, loadConfig, parseArgs, repoRoot, requireFromRepo } from './lib/common.mjs';

export const ROLE_MIGRATOR = 'truth_migrator';
export const ROLE_APP = 'truth_app';
const EXTENSIONS = ['pgcrypto', 'uuid-ossp', 'citext', 'pg_trgm', 'btree_gin', 'btree_gist', 'unaccent', 'ltree', 'hstore', 'vector'];

function adminUrl() {
  if (process.env.TRUTH_PG_ADMIN_URL) return process.env.TRUTH_PG_ADMIN_URL;
  for (const dir of [process.env.TRUTH_CONFIG_DIR, '/etc/ottili-truth', path.join(os.homedir(), '.ottili-truth')].filter(Boolean)) {
    const file = path.join(dir, 'pg-admin.url');
    if (fs.existsSync(file)) return fs.readFileSync(file, 'utf8').trim();
  }
  throw new Error('TRUTH_PG_ADMIN_URL is not set (superuser URL of the shared development PostgreSQL, e.g. postgres://postgres:***@127.0.0.1:55432/postgres)');
}

function rolePassword() {
  return process.env.TRUTH_PG_ROLE_PASSWORD || 'truth-dev-only';
}

export function databaseName(job, cfg = {}) {
  const code = String(cfg.repoCode || cfg.repo || 'repo').toLowerCase().replace(/[^a-z0-9]+/g, '_');
  const slug = String(job).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  return `truth_${code}_${slug}`.slice(0, 63).replace(/_+$/, '');
}

function urlFor(base, { user, password, database }) {
  const u = new URL(base);
  if (user) u.username = user;
  if (password !== undefined) u.password = password;
  if (database) u.pathname = `/${database}`;
  return u.toString();
}

export function urls(job, cfg) {
  const admin = adminUrl();
  const database = databaseName(job, cfg);
  return {
    database,
    admin: urlFor(admin, { database }),
    migrator: urlFor(admin, { user: ROLE_MIGRATOR, password: rolePassword(), database }),
    app: urlFor(admin, { user: ROLE_APP, password: rolePassword(), database }),
  };
}

function loadPg(root) {
  const pg = requireFromRepo(root, 'pg');
  if (!pg) throw new Error(`the "pg" package is not resolvable from the repository or the kit: run  npm install --prefix ${path.relative(root, KIT_DIR) || '.'} --no-audit --no-fund`);
  return pg.default ?? pg;
}

async function withClient(pg, connectionString, fn) {
  const client = new pg.Client({ connectionString });
  await client.connect();
  try {
    return await fn(client);
  } finally {
    await client.end().catch(() => {});
  }
}

const q = (ident) => `"${String(ident).replace(/"/g, '""')}"`;
const lit = (s) => `'${String(s).replace(/'/g, "''")}'`;

export async function bootstrapRoles(pg) {
  await withClient(pg, urlFor(adminUrl(), { database: 'postgres' }), async (c) => {
    for (const role of [ROLE_MIGRATOR, ROLE_APP]) {
      const exists = await c.query('SELECT 1 FROM pg_roles WHERE rolname = $1', [role]);
      const attrs = 'LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOREPLICATION';
      if (exists.rowCount === 0) {
        try {
          await c.query(`CREATE ROLE ${q(role)} ${attrs} PASSWORD ${lit(rolePassword())}`);
        } catch (err) {
          if (err.code !== '42710') throw err; // duplicate_object: another job created it concurrently
        }
      } else await c.query(`ALTER ROLE ${q(role)} ${attrs} PASSWORD ${lit(rolePassword())}`);
    }
  });
}

export async function createJobDatabase({ root, cfg, job, fresh = false }) {
  const pg = loadPg(root);
  const u = urls(job, cfg);
  await bootstrapRoles(pg);
  let created = false;
  await withClient(pg, urlFor(adminUrl(), { database: 'postgres' }), async (c) => {
    const exists = await c.query('SELECT 1 FROM pg_database WHERE datname = $1', [u.database]);
    if (exists.rowCount > 0 && fresh) {
      await c.query(`DROP DATABASE ${q(u.database)} WITH (FORCE)`);
    }
    const again = await c.query('SELECT 1 FROM pg_database WHERE datname = $1', [u.database]);
    if (again.rowCount === 0) {
      try {
        await c.query(`CREATE DATABASE ${q(u.database)} OWNER ${q(ROLE_MIGRATOR)}`);
        created = true;
      } catch (err) {
        if (err.code !== '42P04') throw err;
      }
      await c.query(`COMMENT ON DATABASE ${q(u.database)} IS ${lit(`truth:${new Date().toISOString()}:${job}`)}`);
    }
    await c.query(`REVOKE ALL ON DATABASE ${q(u.database)} FROM PUBLIC`);
    await c.query(`GRANT CONNECT ON DATABASE ${q(u.database)} TO ${q(ROLE_APP)}, ${q(ROLE_MIGRATOR)}`);
  });
  await withClient(pg, u.admin, async (c) => {
    for (const ext of EXTENSIONS) {
      try {
        await c.query(`CREATE EXTENSION IF NOT EXISTS ${q(ext)}`);
      } catch {
        // extension not installed on this server: migrations that need it will say so explicitly
      }
    }
    await c.query(`ALTER SCHEMA public OWNER TO ${q(ROLE_MIGRATOR)}`);
    await c.query(`GRANT USAGE ON SCHEMA public TO ${q(ROLE_APP)}`);
    await c.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${q(ROLE_MIGRATOR)} IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${q(ROLE_APP)}`);
    await c.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${q(ROLE_MIGRATOR)} IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ${q(ROLE_APP)}`);
    await c.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${q(ROLE_MIGRATOR)} IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO ${q(ROLE_APP)}`);
  });
  return { ...u, created };
}

export async function grantApp({ root, cfg, job }) {
  const pg = loadPg(root);
  const u = urls(job, cfg);
  await withClient(pg, u.admin, async (c) => {
    const schemas = await c.query(`SELECT nspname FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema','pg_toast') AND nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'`);
    for (const { nspname } of schemas.rows) {
      const s = q(nspname);
      await c.query(`GRANT USAGE ON SCHEMA ${s} TO ${q(ROLE_APP)}`);
      await c.query(`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ${s} TO ${q(ROLE_APP)}`);
      await c.query(`GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ${s} TO ${q(ROLE_APP)}`);
      await c.query(`GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ${s} TO ${q(ROLE_APP)}`);
      await c.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${q(ROLE_MIGRATOR)} IN SCHEMA ${s} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${q(ROLE_APP)}`);
      await c.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${q(ROLE_MIGRATOR)} IN SCHEMA ${s} GRANT USAGE, SELECT ON SEQUENCES TO ${q(ROLE_APP)}`);
    }
  });
  return true;
}

export async function dropJobDatabase({ root, cfg, job }) {
  const pg = loadPg(root);
  const u = urls(job, cfg);
  await withClient(pg, urlFor(adminUrl(), { database: 'postgres' }), async (c) => {
    await c.query(`DROP DATABASE IF EXISTS ${q(u.database)} WITH (FORCE)`);
  });
  return u.database;
}

export async function listDatabases({ root, prefix = 'truth_' }) {
  const pg = loadPg(root);
  return withClient(pg, urlFor(adminUrl(), { database: 'postgres' }), async (c) => {
    const r = await c.query(`SELECT d.datname AS name, pg_catalog.shobj_description(d.oid, 'pg_database') AS comment, pg_database_size(d.datname) AS bytes FROM pg_database d WHERE d.datname LIKE $1 ORDER BY d.datname`, [`${prefix}%`]);
    return r.rows.map((row) => {
      const m = /^truth:([^:]+:[^:]+:[^:]+Z):(.*)$/.exec(row.comment ?? '');
      return { name: row.name, createdAt: m ? m[1] : null, job: m ? m[2] : null, bytes: Number(row.bytes) };
    });
  });
}

function parseAge(spec) {
  const m = /^(\d+)\s*(m|h|d)$/.exec(spec ?? '');
  if (!m) throw new Error('--older-than expects e.g. 90m, 24h or 7d');
  return Number(m[1]) * { m: 60e3, h: 3600e3, d: 86400e3 }[m[2]];
}

async function main() {
  const args = parseArgs(process.argv.slice(2), { flags: ['fresh'] });
  const cmd = args._[0];
  if (!cmd) {
    process.stderr.write(`${fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(0, 14).join('\n')}\n`);
    process.exit(EXIT.USAGE);
  }
  const root = repoRoot();
  const cfg = loadConfig(root);
  const need = () => {
    if (!args.job) throw new Error('--job <JOB-ID> is required');
    return args.job;
  };
  if (cmd === 'bootstrap') {
    await bootstrapRoles(loadPg(root));
    process.stdout.write(`${JSON.stringify({ roles: [ROLE_MIGRATOR, ROLE_APP] })}\n`);
  } else if (cmd === 'create') {
    const r = await createJobDatabase({ root, cfg, job: need(), fresh: Boolean(args.fresh) });
    process.stdout.write(`${JSON.stringify(r, null, 2)}\n`);
  } else if (cmd === 'url') {
    const u = urls(need(), cfg);
    process.stdout.write(`${u[args.role ?? 'migrator']}\n`);
  } else if (cmd === 'env') {
    const u = urls(need(), cfg);
    const lines = [
      `export TRUTH_DATABASE_NAME='${u.database}'`,
      `export TRUTH_DATABASE_ADMIN_URL='${u.admin}'`,
      `export TRUTH_DATABASE_URL='${u.migrator}'`,
      `export TRUTH_DATABASE_APP_URL='${u.app}'`,
      `export TRUTH_NAMESPACE='${String(args.job).toLowerCase()}'`,
    ];
    process.stdout.write(`${lines.join('\n')}\n`);
  } else if (cmd === 'grant') {
    await grantApp({ root, cfg, job: need() });
    process.stdout.write('granted\n');
  } else if (cmd === 'drop') {
    process.stdout.write(`dropped ${await dropJobDatabase({ root, cfg, job: need() })}\n`);
  } else if (cmd === 'list') {
    process.stdout.write(`${JSON.stringify(await listDatabases({ root, prefix: args.prefix ?? 'truth_' }), null, 2)}\n`);
  } else if (cmd === 'reap') {
    const maxAge = parseAge(args['older-than']);
    const pg = loadPg(root);
    const dropped = [];
    for (const db of await listDatabases({ root, prefix: args.prefix ?? 'truth_' })) {
      if (!db.createdAt || Date.now() - Date.parse(db.createdAt) < maxAge) continue;
      await withClient(pg, urlFor(adminUrl(), { database: 'postgres' }), (c) => c.query(`DROP DATABASE IF EXISTS ${q(db.name)} WITH (FORCE)`));
      dropped.push(db.name);
    }
    process.stdout.write(`${JSON.stringify({ dropped })}\n`);
  } else if (cmd === 'exec') {
    const pg = loadPg(root);
    const u = urls(need(), cfg);
    const sql = args.sql ?? fs.readFileSync(args.file, 'utf8');
    const out = await withClient(pg, u[args.role ?? 'migrator'], (c) => c.query(sql));
    process.stdout.write(`${JSON.stringify(Array.isArray(out) ? out.map((o) => o.rows) : out.rows, null, 2)}\n`);
  } else {
    throw new Error(`unknown command: ${cmd}`);
  }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  main().catch((err) => {
    process.stderr.write(`db.mjs: ${err.message}\n`);
    process.exit(EXIT.FAIL);
  });
}
