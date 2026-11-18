# Continuity Studio

A compact Windows desktop interface for managing AI development handoffs and workspace maps. This is an **early public preview**, shared to document the design and development of the utility.

The interface provides three workflows:

- **Structure Map** — an orientation map of an entire development workspace or one project.
- **Organization Audit** — a readable directory hierarchy with technical clutter collapsed.
- **Deep Project Handoff** — source, context, and Git state prepared for continuing work in another AI session.

It includes searchable project selection, dark/light themes, contextual settings, plain-English hover help, and explicit complete / needs-review / unknown / failure states.

## Project status

**Preview / work in progress.** The public source tree runs in a **demo-only** mode, with fictional projects and example outcomes. No real files are collected by the preview. The optional live adapter is intentionally restricted in this published snapshot; a production integration release has **not** been enabled.

The Windows integration was separately validated against a disposable workspace using the existing **AI Development Continuity v3.1.0-rc9** PowerShell engines. That backend is not bundled in this repository. A public, distributable backend and one-click live installer are future milestones.

## Try the preview

On Windows 11, double-click **`Launch Preview.cmd`**, or open **`GUI/index.html`** in a browser for an interface-only preview.

The standalone window launcher needs Python 3.10+ and Microsoft Edge. There are no additional Python packages for the host. The interface has no external fonts, scripts or runtime CDN requirements.

## Test the source

Run **`Run Tests.cmd`** on Windows to exercise the standard-library synthetic host tests. Browser tests using Playwright are optional and require separate browser tooling.

The tests do not need the real PowerShell engine or your own projects.

## Intended local layout

The eventual local Windows installation will add **one file to the Development root**: `Continuity Studio.cmd`. The application source lives in a separate `05-Utilities-and-Automation/Continuity-Studio` repository folder; the existing PowerShell backend remains in `00-Shared-Guides/AI-Development-Continuity`. Workspace maps and reports continue to go to their established output locations.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Screenshots and demonstrations

Polished screenshots and short workflow GIFs will be added after the initial public preview. Current interface images are intentionally omitted to avoid publishing local paths or test evidence from personal workspaces.

## Licensing

**No open-source license has been granted in this initial public preview.** This repository is public for viewing and evaluation. Unless a license is added, ordinary copyright protections apply; public visibility by itself is not permission to reuse or redistribute the code. A license decision is pending.

Copyright © 2026 HyunCafe. All rights reserved at this stage.
