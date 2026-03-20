# Lit Agent Guide

This repository is a small Flask application for extracting articles, generating EPUB files, and sending them to Kindle devices via email.

## Read Order

1. This file
2. `README.md`
3. `QUICKSTART.md`
4. The most relevant implementation files for the task (`app.py`, `extractor.py`, `epub_generator.py`, `image_processor.py`, `mailer.py`)

## Project Layout

- `app.py` wires the Flask routes and request handling.
- `extractor.py` handles article extraction and paywall fallback logic.
- `image_processor.py` downloads and normalizes article images.
- `epub_generator.py` assembles single-article and digest EPUB outputs.
- `mailer.py` sends finished EPUBs through SMTP to Kindle.
- `templates/` contains the Flask HTML templates.
- `test_installation.py` is the lightweight environment and dependency check included by the upstream repo.
- `flake.nix` exports the repo as the `art-domain` package and NixOS module for NAS hosting.

## Working Rules

- Keep changes minimal and consistent with the existing single-file module layout.
- Prefer updating the relevant Python module directly instead of introducing new abstractions unless the task clearly needs them.
- Treat environment-specific secrets and `.env` values as local-only; never hardcode credentials.
- If setup or runtime behavior changes, update `README.md` or `QUICKSTART.md` in the same task.

## Nix Hosting Contract

- `flake.nix` is the hosting contract for this repo when served from `nix-dotfiles`.
- Keep the exported package and NixOS module name as `art-domain` even if the application branding or repo name changes.
- Keep `packages.default` aligned with `packages.art-domain` unless there is a strong reason to split them.
- Keep `nixosModules.default` aligned with `services.art-domain` so NAS can continue importing the repo with a stable interface.
- Preserve the app source layout expected by the flake install step: `app.py`, the helper modules, and `templates/`.
- If runtime dependencies change, update both the Python package set in `flake.nix` and the human-facing setup docs in the same change.
- If Playwright/browser execution changes, keep the service compatible with a system Chromium path provided through `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`.
- If the hosted app eventually grows multiple sub-apps or path mounts, extend the module interface carefully without breaking the existing `art.bepis.lol -> services.art-domain` deployment path.

## Verification

- For dependency and environment validation, run `python test_installation.py` inside the configured virtualenv.
- For manual app checks, activate the repo virtualenv and run `./run.sh`.
- If browser-based extraction behavior changes, ensure Playwright Chromium is installed before retesting.
- For Nix packaging changes, run `nix flake check` and a targeted package build such as `nix build .#art-domain`.
