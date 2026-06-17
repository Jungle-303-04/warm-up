import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(scriptDir, "..");
const nextDir = path.join(appDir, ".next");
const standaloneAppDir = path.join(nextDir, "standalone", "apps", "web");

function copyFresh(from, to) {
  if (!existsSync(from)) return;
  rmSync(to, { recursive: true, force: true });
  mkdirSync(path.dirname(to), { recursive: true });
  cpSync(from, to, { recursive: true });
}

if (!existsSync(standaloneAppDir)) {
  throw new Error(`Next standalone output was not found: ${standaloneAppDir}`);
}

copyFresh(path.join(nextDir, "static"), path.join(standaloneAppDir, ".next", "static"));
copyFresh(path.join(appDir, "public"), path.join(standaloneAppDir, "public"));
