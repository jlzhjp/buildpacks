"""Check detection and composite/package consistency without Docker or downloads."""

import pathlib
import subprocess
import tempfile
import tomllib

root = pathlib.Path(__file__).resolve().parents[1]
component = tomllib.loads((root / "pnpm-assets/buildpack.toml").read_text())
composite = tomllib.loads((root / "go-web/buildpack.toml").read_text())
package = tomllib.loads((root / "go-web/package.toml").read_text())
group = composite["order"][0]["group"]
assert group[1]["id"] == component["buildpack"]["id"]
assert group[1]["version"] == component["buildpack"]["version"]
assert package["dependencies"][0]["uri"].endswith("/node-engine-" + group[0]["version"] + ".cnb")
assert package["dependencies"][2]["uri"].endswith("/go-" + group[2]["version"] + ".cnb")

with tempfile.TemporaryDirectory() as directory:
    app = pathlib.Path(directory)
    plan = app / "plan.toml"
    detect = root / "pnpm-assets/bin/detect"
    assert subprocess.run([detect, directory, plan], cwd=app).returncode == 100
    (app / "package.json").write_text("{}")
    assert subprocess.run([detect, directory, plan], cwd=app).returncode == 100
    (app / "pnpm-lock.yaml").touch()
    subprocess.run([detect, directory, plan], cwd=app, check=True)
    requirements = tomllib.loads(plan.read_text())["requires"]
    assert {item["name"] for item in requirements} == {"node", "npm"}
    assert all(item["metadata"] == {"build": True, "launch": False} for item in requirements)

print("Detection and composite/package checks passed")
