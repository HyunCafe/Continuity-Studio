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
- `Backend/` remains **private operational source** and is excluded from public commits. The tracked root `.gitignore` now contains `/Backend/` as a portable **accidental-staging guardrail**, in addition to this owner's local `.git/info/exclude`. Ignore rules are **not security boundaries**: `git add -f` and other publication workflows can bypass them. Audit 08 must decide whether a structural private/public separation is needed. A fresh public clone does **not** contain the PowerShell backend.
- Reports, backups, logs, Git metadata and handoff outputs are local operational artifacts, not source files for public commits.
- The screenshots/GIF in `assets/` are captured from fictional preview data, never from real development folders.
- No public installer, security certification, or redistribution permission for the backend is implied.

## Execution, verification and coverage

The localhost host validates incoming requests before delegating controlled work to its PowerShell adapter in the local beta. Coverage interpretation is evidence-based: a process exiting with code 0 does not itself prove a complete result. The GUI distinguishes verified outputs from coverage warnings, unknowns, and failures.

Directory links/junctions are listed but not traversed to avoid loops and duplicated scans. Git metadata can be unavailable. The observed Deep Handoff excluded essential ignored backend source and reported `safe_to_resume: false`, with two ignored instruction READMEs accounting for its blockers. Plain ignored source may not independently trigger a blocker; a synthetic false-safe regression is required in Audit 02. Until fixed and tested, **do not treat `safe_to_resume: true` as proof that all essential ignored source was captured**.

The backend relocation is documented as having passed Windows sandbox acceptance, having been installed in parallel, and having undergone a reversible launcher cutover. Audit 01 verified supplied source and hash manifests but did not independently rerun the historical Windows backend suites. See [test provenance](TEST-PROVENANCE.md) for the evidence boundary. These earlier milestones do not replace a separate public-backend privacy audit, redistribution review, installer design, or security testing.

The live integrity manifest hashes the private engine files and `Backend/Run-Live.py`. Its trust in the public-tracked `Support/host.py` currently comes from source/Git provenance rather than the same live manifest. The significance of that split is reserved for Audits 05/08.

## Why Python + Edge?

The lightweight Python standard-library host keeps the existing HTML-based interface in a desktop-like window without a larger framework runtime. A distributable Windows installer and definitive taskbar/application identity remain separate release tasks.
