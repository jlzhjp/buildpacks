"""Assert the composite image exports Go, without Node or pnpm runtime layers."""

import json
import subprocess
import sys

image = sys.argv[1]
details = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
metadata = json.loads(details["Config"]["Labels"]["io.buildpacks.lifecycle.metadata"])
buildpacks = {item["key"]: item for item in metadata["buildpacks"]}
for name in ["paketo-buildpacks/node-engine", "shared/pnpm-assets"]:
    assert name in buildpacks, f"Missing buildpack: {name}"
    for layer in buildpacks[name].get("layers", {}).values():
        assert not layer.get("launch", False), f"Unexpected runtime layer from {name}"
assert buildpacks["paketo-buildpacks/go-build"]["layers"]["targets"]["launch"]
subprocess.run(
    [
        "docker", "run", "--rm", "--entrypoint", "/bin/sh", image, "-c",
        "test ! -d /layers/paketo-buildpacks_node-engine/node && "
        "test ! -d /layers/shared_pnpm-assets/corepack",
    ],
    check=True,
)
print("Go runtime layer present; Node and pnpm runtime layers absent")
