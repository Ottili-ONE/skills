// Allocate a free TCP port for a job's dev server / test server without colliding with the other jobs on the machine.
// Usage: node scripts/truth/port.mjs [--job ID] [--count N]      prints one port per line
//        node scripts/truth/port.mjs release PORT [PORT...]
// Range: TRUTH_PORT_MIN..TRUTH_PORT_MAX (default 52000..59999). Reservations live in TRUTH_LOCK_DIR and expire after 6 hours.
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { lockDir, parseArgs } from './lib/common.mjs';

const MIN = Number(process.env.TRUTH_PORT_MIN || 52000);
const MAX = Number(process.env.TRUTH_PORT_MAX || 59999);
const TTL_MS = 6 * 3600 * 1000;

function reservationFile(port) {
  return path.join(lockDir(), `port.${port}`);
}

function reservedAndFresh(port) {
  try {
    const st = fs.statSync(reservationFile(port));
    return Date.now() - st.mtimeMs < TTL_MS;
  } catch {
    return false;
  }
}

function canBind(port) {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.once('error', () => resolve(false));
    srv.listen({ port, host: '127.0.0.1', exclusive: true }, () => srv.close(() => resolve(true)));
  });
}

export async function allocatePort(job = '') {
  for (let attempt = 0; attempt < 200; attempt += 1) {
    const port = MIN + Math.floor(Math.random() * (MAX - MIN + 1));
    if (reservedAndFresh(port)) continue;
    if (!(await canBind(port))) continue;
    try {
      fs.writeFileSync(reservationFile(port), `${new Date().toISOString()} job=${job}\n`, { flag: 'wx', mode: 0o666 });
    } catch {
      continue; // another process reserved it between the check and the write
    }
    return port;
  }
  throw new Error(`no free port in ${MIN}-${MAX}`);
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const args = parseArgs(process.argv.slice(2));
  if (args._[0] === 'release') {
    for (const p of args._.slice(1)) fs.rmSync(reservationFile(p), { force: true });
  } else {
    const count = Number(args.count || 1);
    for (let i = 0; i < count; i += 1) process.stdout.write(`${await allocatePort(args.job ?? '')}\n`);
  }
}
