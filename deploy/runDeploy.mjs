import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const deployDirectory = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(deployDirectory, "..");
const require = createRequire(import.meta.url);
const { transformSync } = require(
  path.join(projectRoot, "node_modules", ".pnpm", "node_modules", "esbuild"),
);
const compiledArtifact = path.join(deployDirectory, "deployScript.compiled.js");
const runtimeSource = path.join(deployDirectory, "runtime.ts");
const runtimeArtifact = path.join(deployDirectory, "runtime.js");
const cli = path.join(projectRoot, "node_modules", "genlayer", "dist", "index.js");

rmSync(compiledArtifact, { force: true });
rmSync(runtimeArtifact, { force: true });
try {
  if (existsSync(runtimeSource)) {
    const transpiled = transformSync(readFileSync(runtimeSource, "utf8"), {
      loader: "ts",
      format: "esm",
      target: "es2022",
      sourcefile: runtimeSource,
    });
    writeFileSync(runtimeArtifact, transpiled.code, { encoding: "utf8", flag: "wx" });
  }
  const result = spawnSync(process.execPath, [cli, "deploy"], {
    cwd: projectRoot,
    env: process.env,
    stdio: "inherit",
  });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
} finally {
  rmSync(compiledArtifact, { force: true });
  rmSync(runtimeArtifact, { force: true });
}
