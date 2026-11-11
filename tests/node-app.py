"""Exercise node-app runtime preparation without a builder or network."""
import json
import pathlib
import subprocess
import tempfile
import tomllib

script = pathlib.Path(__file__).resolve().parents[1] / 'node-app/lib/prepare-runtime.cjs'

with tempfile.TemporaryDirectory() as directory:
    base = pathlib.Path(directory)
    app = base / 'app'
    app.mkdir()
    package = app / 'apps/example'
    (package / 'dist').mkdir(parents=True)
    (package / 'dist/main.mjs').write_text('')
    (package / 'dist/migrate.mjs').write_text('')
    (app / 'src').mkdir()
    (app / 'src/private').write_text('source')
    (app / 'node_modules').mkdir()
    (app / 'node_modules/dev').write_text('dev dependency')
    (package / 'dist/node_modules').mkdir()
    (package / 'dist/node_modules/runtime').write_text('runtime dependency')
    metadata = {
        'scripts': {
            'buildpack:main': 'node apps/example/dist/main.mjs',
            'buildpack:migrate': 'node apps/example/dist/migrate.mjs',
        },
        'buildpack': {'include': ['apps/example/dist']},
    }
    (package / 'package.json').write_text(json.dumps(metadata))
    selected = base / 'selected.json'
    selected.write_text(json.dumps([{'path': str(package)}]))
    launch = base / 'launch.toml'

    def run():
        return subprocess.run(['node', script, launch, selected], cwd=app, capture_output=True, text=True)

    metadata['buildpack']['include'] = ['../outside']
    (package / 'package.json').write_text(json.dumps(metadata))
    assert run().returncode != 0
    assert (app / 'src/private').exists(), 'invalid configuration must not remove source'
    metadata['buildpack']['include'] = ['apps/example/dist']
    (package / 'package.json').write_text(json.dumps(metadata))
    result = run()
    assert result.returncode == 0, result.stderr
    processes = tomllib.loads(launch.read_text())['processes']
    assert [(p['type'], p['default']) for p in processes] == [('main', True), ('migrate', False)]
    assert processes[1]['command'] == ['node', 'apps/example/dist/migrate.mjs']
    assert (package / 'dist/node_modules/runtime').exists()
    assert not (app / 'src').exists()
    assert not (app / 'node_modules').exists()
    assert not (package / 'package.json').exists()

print('Node application runtime checks passed')
