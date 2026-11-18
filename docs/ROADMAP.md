# Continuity Studio — development roadmap

**Original milestone snapshot:** November 18, 2026. The repository is an early public, **demo-only** preview. Completed milestones below refer to the owner's local Windows beta unless otherwise indicated. These are historical milestone claims; their suite-level evidence is separately classified in [TEST-PROVENANCE.md](TEST-PROVENANCE.md).

**Audit status (Nov 18, 2026):** Sections 01 and 02 of 09 are **PASS WITH CONDITIONS** after independent GPT/Qwen reconciliation and owner-run Windows verification. Audit 02 added reviewed, exact-path inclusion of selected Git-ignored text files, accurate omission/readiness warnings, and verified GUI-to-ZIP integration on a disposable fixture. Public Git remains demo-only; private `Backend/` is not published. See [AUDIT-STATUS.md](AUDIT-STATUS.md) and the [findings register](AUDIT-REGISTER.csv).

## Implemented and verified locally

- [x] Three workflows: Structure Map, Organization Audit, Deep Project Handoff.
- [x] Searchable projects, contextual options, light/dark themes, and delayed plain-English hover help.
- [x] Windows preview and layered app icon; public source preview repository.
- [x] Windows host tests and disposable PowerShell v3.1.0-rc9 acceptance scenarios.
- [x] Relocated-backend tests: **40/40** host cases and **7/7** real-engine sandbox scenarios.
- [x] Parallel live integration, reversible root launcher switch, verified engine hashes and Git checkpoint.
- [x] Consolidated local PowerShell engines under `Continuity-Studio/Backend`; archived the previous Shared Guides installation.
- [x] Regenerated real workspace maps and a project handoff, preserving honest coverage warnings.
- [x] Added fictional demo-mode screenshot and short animated walkthrough to the public README.

## Source/publication safety

- [x] Add a tracked `/Backend/` ignore guardrail to reduce accidental staging in fresh clones. **This does not make the private backend safe to publish.**
- [ ] Decide the durable private/public repository boundary and vet public release contents (Audit 08).
- [ ] Reconcile raw Windows engine-suite transcripts against the historic 40/40, 7/7, and rc3 16-assertion documentation (Audits 03/04/09).

## Functional quality improvements

- [x] Narrow, explicitly approved exact-path inclusion of selected Git-ignored text source in Deep Project Handoff; owner-run disposable fixture GUI-to-ZIP verified. No blanket ignored-file inclusion.
- [x] Gate material source omissions and redacted instructions for review and mask recognized private basenames in exported metadata (Audit 02 regression coverage).
- [x] Distinguish export success from `safe_to_resume` / incomplete coverage for tested omission classes; later security audit must challenge broader edge cases.
- [ ] Review accessibility, keyboard behavior, DPI scaling and definitive Windows icon/taskbar identity.

## Public release work

- [ ] Review backend source, sensitive output handling, and redistributability before adding it to public Git.
- [ ] Document reproducible live installation, dependency acquisition, backups and rollback for third parties.
- [ ] Perform an external security and release-readiness review.
- [ ] Add final sanitized real-application screenshots, polished GIF/video demos, and release notes.
- [ ] Decide on a license (currently rights reserved; no open-source license is granted).

Completion of local beta milestones does **not** make the public GitHub checkout a production-ready installer.
