# Architecture — public preview and local Windows beta

Continuity Studio uses a browser-based desktop interface with a small Python localhost host. **The published demo and the owner’s local Windows installation are not functionally equivalent.**

## Public checkout: fictional demo

```text
HTML / CSS / JavaScript UI
           |
Python standard-library loopback host (or standalone HTML preview)
           |
Simulated results for fictional projects
```

The public `Launch Preview.cmd` uses demo mode. It does not include, install or execute the actual PowerShell backend.

## Owner’s local Windows beta: controlled live backend

```text
Development/Continuity Studio.cmd
              |
Continuity-Studio/Support/host.py
              |
HTML/CSS/JavaScript GUI in Edge standalone window
              |
Local authenticated 127.0.0.1 host / process controller
              |
Continuity-Studio/Backend/ (PowerShell 7 rc9 scripts)
      +----------------+----------------+
      |                |                |
 Structure Map    Organization     Deep Project
                  Audit            Handoff
      |                |                |
 Development root  Development root  Backend/Reports/
 maps / handoff ZIP organization map  ZIP + START-HERE + coverage
```

During local integration, the existing **AI Development Continuity v3.1.0-rc9** backend was moved from Shared Guides into `05-Utilities-and-Automation/Continuity-Studio/Backend`. The previous installation was archived for rollback, leaving a single GUI launcher in the Development root. The independent coding-workflow guide remains in Shared Guides.

## Privacy and distribution boundary

- `GUI/`, `Support/`, `Tests/`, `docs/` and the sanitized README visuals are public preview materials.
- `Backend/` is intentionally excluded from **this owner's local Git checkout**; a newly cloned public repository will **not** contain the PowerShell backend.
- Reports, backups, logs, Git metadata and handoff outputs are local operational artifacts, not source files for public commits.
- The screenshots/GIF in `assets/` are captured from fictional preview data, never from real development folders.
- No public installer, security certification, or redistribution permission for the backend is implied.

## Execution, verification and coverage

The localhost host validates incoming requests before delegating controlled work to its PowerShell adapter in the local beta. Coverage interpretation is evidence-based: a process exiting with code 0 does not itself prove a complete result. The GUI distinguishes verified outputs from coverage warnings, unknowns, and failures.

Directory links/junctions are listed but not traversed to avoid loops and duplicated scans. Git metadata can be unavailable. Required README instructions or essential source excluded by Git-ignore rules can make a Deep Handoff unsafe to resume even when a ZIP exists.

The backend relocation passed Windows sandbox acceptance, was installed in parallel, and underwent a reversible launcher cutover. That does not replace a separate public-backend privacy audit, redistribution review, installer design, and security testing.

## Why Python + Edge?

The lightweight Python standard-library host keeps the existing HTML-based interface in a desktop-like window without a larger framework runtime. A distributable Windows installer and definitive taskbar/application identity remain separate release tasks.
