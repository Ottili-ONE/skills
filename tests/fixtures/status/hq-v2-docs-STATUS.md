# STATUS (HQ)

Was nachweislich läuft, was gestubbt ist und was fehlt. Jede Zeile hier ist entweder mit einem
Befehl belegt oder ausdrücklich offen. Neue Abschnitte bitte an das Ende hängen und mit der
Task-ID (`wa-hq-<n>`) überschreiben, damit 40 parallele Agenten sich nicht gegenseitig wegschreiben.

## 1. Umgebung und Freeze (wa-hq-01, 2026-10-01)

| Was | Wert | Beleg |
|---|---|---|
| Host | B, Ubuntu 26.04.1 LTS, Kernel 7.0.0-30, x86_64 | `uname -srm`, `/etc/os-release` |
| Node / npm | v24.19.0 / 11.17.0 | `node -v`, `npm -v` |
| Platform-Freeze | **2.0.0-alpha.3**, Tag `platform-m1-freeze-3`, Commit `24c78171…`, 32 Tarballs in `http://127.0.0.1:18873` (Verdaccio) | `docs/m1/FREEZE_REPORT_3.md`, `git -C ottili-platform tag -l` |
| `@ottili/*` im Repo | `platform-sdk`, `foundation-shell`, `foundation-react`, `foundation-testing` — alle exakt `2.0.0-alpha.3`, nie `^`/`~` | `package-lock.json` |
| Weitere Pakete | `pg` 8.23.1 (neu, Postgres-Treiber), `esbuild` 0.24.2, `react`/`react-dom` 19.0.0 | `package-lock.json` |
| Platform-Instanz dieses Produkts | `http://127.0.0.1:18300` (Produkt-Welt `hq`, `PLATFORM_DEV_PRODUCT=none`), Prodikt-Shell `:18401` | `.env`, `SHELLS_READY.md` |
| Keycloak | `http://127.0.0.1:18180`, Realm `ottili` | `SHELLS_READY.md` |
| Dev-Postgres | Container `ottili-dev-postgres`, `postgres:16-alpine`, `127.0.0.1:18432:5432`, Server **16.15** | `docker ps`, `db:ping` |

## 2. Baseline (wa-hq-01)

Alles auf Host B gegen die eigene Platform-Instanz 18300 ausgeführt, Belege unter
`/mnt/ottili-nvme/ottili/scratch/hq-v2/wa-hq-01/`.

| Schritt | Ergebnis | Beleg |
|---|---|---|
| `npm install` | grün, **mit einer Falle**: `NODE_ENV=production` in der Agent-Umgebung lässt npm die devDependencies weg und entfernt `esbuild` beim Installieren; dann bricht `npm run build`. Abhilfe: `NODE_ENV=development npm install --include=dev`. Danach `npm run build` grün (`dist/app.js`) | `npm-install.log`, Build-Ausgabe |
| `npm test` | **13 bestanden, 0 fehlgeschlagen, 1 übersprungen** (14 gesamt). Übersprungen: `the product database answers when DATABASE_URL is set` — der Test braucht eine Datenbank und läuft nur mit gesetzter `DATABASE_URL`; **mit gesetzter `DATABASE_URL` sind es 9/9 in dieser Datei, ohne Skip** | `npm test`, Testlauf mit injizierter `DATABASE_URL` |
| `npm run journey:shell` | **16 PASS, 0 FAIL, Exit 0** (Hello-Entity, Policy-Deny pro Rolle, Browser-Render, Degraded State, Anmeldung, Dev-Login) | `journey-shell-2.log` (`PASS 16  FAIL 0`, `EXIT=0`) |
| `node scripts/db-ping.mjs` | **DB-PING OK** gegen `hq@127.0.0.1:18432/hq`, PostgreSQL 16.15, Connect 17 ms, Rolle ohne Superuser/CREATEDB | Ausgabe in Abschnitt 4 |

## 3. Package-Skripte (wa-hq-01)

`journey`, `journey:shell`, `proof:login` laden jetzt `--env-file-if-exists=.env` wie `dev` schon
tat. Grund: ohne das laufen sie gegen den Default `http://127.0.0.1:18150`, und **auf Host B gibt
es 18150 nicht** (dort laufen die Instanzen 18300 ff.). Neu: `npm run db:ping`.
*Für den Integrator:* das ist die einzige Änderung an der geteilten `package.json` aus dieser Task.

## 4. Datenbank (wa-hq-01)

`scripts/db-ping.mjs` (`npm run db:ping`, `--json` für Maschinen) beweist die Verbindung, ohne ein
Geheimnis zu berühren: Die URL kommt **nur aus der Prozessumgebung** (`DATABASE_URL`), das Skript
liest keine Datei, druckt die URL nie und führt jedes Ergebnis durch `redact()`._exit 0_ = alles grün,
_1_ = nicht erreichbar (RFC-9457-Problem-Dokument), _2_ = `DATABASE_URL` fehlt.

Geprüft wurde: connect, read, write (TEMP-Tabelle, sessionlokal, ohne Rückstand), Rollenrechte
(kein Superuser, kein CREATEDB), RLS-Fähigkeit. Letzte Ausgabe (ohne Geheimnis, hier abgeschrieben):

```
DB-PING OK  request_id=req_87d6b3db-…  trace_id=trace_7229c944-…
  target   hq@127.0.0.1:18432/hq (ssl=false)
  server   PostgreSQL 16.15 db=hq role=hq
  timing   connect 17.07 ms
  PASS   connect  connected in 17.07 ms
  PASS   read     SELECT current_database(), current_user, version() in 2.48 ms
  PASS   write    TEMP table write+read+drop in 1.27 ms, no residue
  PASS   role     superuser=false createdb=false createrole=false replication=false
  PASS   rls      0 row-level-security policies visible (capability probe, not a product check)
```

