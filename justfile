default:
    @just --list

check:
    bash -n pnpm-assets/bin/detect pnpm-assets/bin/build
    python3 tests/check.py

check-image image:
    python3 tests/image.py {{quote(image)}}

package:
    pack buildpack package shared/pnpm-assets:0.1.1 --config pnpm-assets/package.toml
    pack buildpack package shared/go-web:0.1.1 --config go-web/package.toml

publish registry:
    pack buildpack package {{quote(registry + "/pnpm-assets:0.1.1")}} --config pnpm-assets/package.toml --publish
    pack buildpack package {{quote(registry + "/go-web:0.1.1")}} --config go-web/package.toml --publish
