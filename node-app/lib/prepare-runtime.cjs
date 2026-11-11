const fs = require('node:fs');
const path = require('node:path');

const [launchFile, selectedFile] = process.argv.slice(2);
const root = process.cwd();
const packages = JSON.parse(fs.readFileSync(selectedFile, 'utf8'));
if (packages.length !== 1) throw new Error('BP_PNPM_FILTER must select exactly one package');
const pkg = JSON.parse(fs.readFileSync(path.join(packages[0].path, 'package.json'), 'utf8'));
const entries = Object.entries(pkg.scripts || {}).filter(([name]) => name.startsWith('buildpack:'));
if (!entries.some(([name]) => name === 'buildpack:main')) throw new Error('Missing buildpack:main script');
const processes = entries.map(([name, script]) => {
  const type = name.slice('buildpack:'.length);
  if (!/^[a-z][a-z0-9-]*$/.test(type) || typeof script !== 'string' || !/^node [a-zA-Z0-9_./-]+$/.test(script)) {
    throw new Error(`Invalid direct process: ${name}=${script}`);
  }
  const args = script.split(' ');
  return `[[processes]]\ntype = ${JSON.stringify(type)}\ncommand = [${args.map(JSON.stringify).join(', ')}]\ndefault = ${type === 'main'}\n`;
});

const includes = pkg.buildpack?.include;
if (!Array.isArray(includes) || includes.length === 0) throw new Error('buildpack.include must contain runtime paths');
const retained = includes.map((entry) => {
  if (typeof entry !== 'string' || !entry || path.isAbsolute(entry)) throw new Error(`Invalid runtime path: ${entry}`);
  const relative = path.normalize(entry);
  if (relative === '.' || relative === '..' || relative.startsWith(`..${path.sep}`)) throw new Error(`Invalid runtime path: ${entry}`);
  let current = root;
  for (const part of relative.split(path.sep)) {
    current = path.join(current, part);
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink()) throw new Error(`Runtime path must not traverse a symlink: ${entry}`);
  }
  return relative;
});
for (const [name, script] of entries) {
  const entry = path.normalize(script.slice(5));
  if (!retained.some((item) => entry === item || entry.startsWith(`${item}${path.sep}`))) {
    throw new Error(`Process ${name} is not included in buildpack.include`);
  }
  if (!fs.statSync(path.join(root, entry)).isFile()) throw new Error(`Process ${name} entrypoint is not a file`);
}
fs.writeFileSync(launchFile, processes.join('\n'));

function clean(dir, relative = '') {
  for (const name of fs.readdirSync(dir)) {
    const child = path.join(relative, name);
    if (retained.some((item) => child === item || child.startsWith(`${item}${path.sep}`))) continue;
    const full = path.join(dir, name);
    if (retained.some((item) => item.startsWith(`${child}${path.sep}`))) clean(full, child);
    else fs.rmSync(full, { recursive: true, force: true });
  }
}
clean(root);
