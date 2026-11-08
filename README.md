# Shared buildpacks

Two reusable Cloud Native Buildpacks for Go applications that embed frontend assets:

- `shared/pnpm-assets`: installs Corepack separately and uses it to select pnpm from `package.json`, installs locked dependencies including build tools, runs a package script, and removes `node_modules`. Corepack, its package-manager downloads, and dependency layers are cached, with `launch = false`.
- `shared/go-web`: composes Paketo Node Engine, pnpm-assets, and Paketo Go. Node and pnpm stay build-only; Paketo selects and launches the Go binary.

## Build and use locally

Requires pack, Docker, and just. Python 3.11+ is used by `just check`.

```sh
just check
just package
```

In an application’s `project.toml`:

```toml
[_]
schema-version = "0.2"

[io.buildpacks]
builder = "paketobuildpacks/ubuntu-resolute-builder-buildpackless"
exclude = [".git", "node_modules", "static", "dist"]

[[io.buildpacks.group]]
uri = "docker://shared/go-web:0.1.2"

[[io.buildpacks.build.env]]
name = "BP_NODE_VERSION"
value = "24.*"

[[io.buildpacks.build.env]]
name = "BP_GO_BUILD_FLAGS"
value = "-tags=release -trimpath"
```

Declare an exact package manager in `package.json`, for example `"packageManager": "pnpm@12.18.0"`, and a `scripts.build` command. Commit the matching `pnpm-lock.yaml`. Run `pack build my-app --pull-policy if-not-present` to use locally packaged images. Rootless Docker may require `--docker-host unix:///run/user/1000/docker.sock`.

## Configuration

| Setting | Purpose |
| --- | --- |
| `packageManager` | Exact pnpm version; required. Corepack integrity suffixes are accepted. |
| `BP_PNPM_BUILD_SCRIPT` | Package script to run; defaults to `build`. |
| `BP_NODE_VERSION` | Node version constraint understood by Paketo Node Engine. |
| `BP_GO_BUILD_FLAGS` | Go compiler flags, such as the application's embedding build tag. |
| `BP_GO_TARGETS` | Go package targets; handled by Paketo Go. |

Asset paths and embedding are owned by the application. Generated output remains in the shared workspace for Go compilation. The frontend build runs before the Go toolchain is installed; generate templ or other Go-based source before invoking pack, and include it in the build context. The component works at the application root, including pnpm workspaces. Only the build script's outputs should be needed after `node_modules` is removed.

## Distribution

Replace the `shared/` buildpack IDs with your organization namespace before the first public release. Keep composite references synchronized. The OCI registry namespace can differ from the buildpack ID.

```sh
docker login ghcr.io
just publish ghcr.io/your-org
```

Applications then reference `docker://ghcr.io/your-org/go-web:0.1.2`. Publishing the component separately also lets other pipelines reuse it with a Node provider. Publishing requires registry authorization; the recipes do not create repositories or credentials.

After building an application image, run `just check-image my-app` to verify the Go runtime layer is exported and Node/pnpm layers are absent. Smoke-test the application's own endpoints separately.

Dependency versions are pinned in `go-web/buildpack.toml` and `go-web/package.toml`. Update both together, test the resulting application image, and publish a new version. The builder is selected separately by each application.

## GitHub Actions releases

The workflow in `.github/workflows/publish.yml` checks pull requests and pushes to `main`. Pushing a Git tag starting with `v` triggers packaging and publishing. Each image tag comes directly from its own `buildpack.toml` version, independently of the Git tag:

- `ghcr.io/<owner>/<repository>/pnpm-assets:0.1.2`
- `ghcr.io/<owner>/<repository>/go-web:0.1.2`

The owner/repository is derived automatically and lowercased. Authentication uses the repository's `GITHUB_TOKEN` with `packages: write`; no personal access token is needed. OCI source labels link the packages to the repository.

Update component versions and composite references together before the next release. The Git tag must match both buildpack versions. Consumers reference `docker://ghcr.io/<owner>/<repository>/go-web:0.1.2`. Set GHCR package visibility to public if consumers should pull without registry authentication.

## Node workspace applications

`shared/node-app` selects a package using `BP_PNPM_FILTER`, installs its workspace dependency closure, and builds it. Define `buildpack:main` and optional `buildpack:<name>` scripts as direct `node <path>` commands relative to the workspace root. The main process is the default. Include Paketo Node Engine before this buildpack. Node and required system libraries must be available at launch.
