# Continuity Studio — Audit 01 Final Reconciliation

**Scope:** Architecture, Source & Baseline Integrity (section 01 of 09)
**Decision:** **PASS WITH CONDITIONS** for *Audit 01 only*; **NOT** a public-production-release approval.
**Inputs:** User-supplied full `Continuity-Studio.rar`, November 18 pause checkpoint, produced structure and Deep Handoff outputs, GPT primary Audit 01 report, and Qwen4-Max independent Audit 01 response.
**Methods:** Read-only local inspection, source-to-manifest comparison and reconciliation. No source modifications, Git commits, installation, or Windows execution.

## 1. Established baseline

- Public repository baseline: `HyunCafe/Continuity-Studio`, `main`, SHA `e1118564738f5518df41e052bfcbdf8278ca0621`, as verified by the primary reviewer against GitHub and the extracted project Git state. Public checkout is explicitly **fictional/demo-only**.
- The installed local beta has a **private, Git-ignored PowerShell backend** under `Backend/`, with a local launcher and the public-tracked Python/HTML/JS host/GUI. The full user-supplied RAR contains the actual backend source, test engines, and manifests; the public Git tree does not.
- Rechecked during this reconciliation: all **11/11** `Backend/.LIVE-MANIFEST.json` engine SHA-256 values match the corresponding files in the RAR; `Backend/Run-Live.py` also matches the launcher SHA-256. The primary reviewer separately reported 25/25 pause-checkpoint hashes, 33/33 Linux host unit tests, successful Python compilation, and JS parsing. These are **not Windows backend integration certifications**.
- The historical deployment manifest records source commit `a3a6b61f8bde8315c6713261d186e20ee118f67c`; the later public HEAD is `e111856...`. Deployment receipts describe the historical cutover and are not automatically freshness checks.
- The observed Deep Handoff records 38 inventoried, 14 copied, 24 not copied, and `safe_to_resume=false`. Its exclusion of ignored backend implementation is an **observed functional limitation**, correctly reported by the application.

## 2. Finding-by-finding reconciliation

| Qwen finding | Reconciliation | Severity and confidence | Ownership / next gate |
|---|---|---|---|
| **Q01-001** — Private backend inside public worktree, per-clone ignore | **Accepted; extends A01-F01.** `.git/info/exclude` locally hides `Backend/`; tracked `.gitignore` lacks `Backend/`. The cause is the private-backend relocation into the public checkout. No actual disclosure demonstrated. A tracked ignore is only a guardrail; separation is stronger. | **High release-process risk; verified mechanism** | Audit 08. Until a reviewed publication design is authorized, keep backend private and do not `git add -f` or publish it. Owner's permanent boundary choice remains OPEN. |
| **Q01-002** — Deep Handoff not self-contained | **Accepted; confirms A01-F02.** Essential ignored code absent, while the current output correctly says unsafe. | **High handoff limitation; verified** | Audit 02. Design a reviewed narrow inclusion facility, not global ignore disablement. |
| **Q01-003** — False-safe possibility for ignored source | **Accepted with calibrated confidence.** The actual run shows ignored ordinary source causes no blockers; the two omitted instruction READMEs cause the reported blockers. `safe_to_resume` explicitly tests blocker count, not an essential-source manifest. **A false `true` verdict is not yet reproduced**, and the GUI adds a material-unknown gate. | **Medium; observed omission mechanism verified, exploitable layout a strong inference** | Audit 02. Synthetic ignored-source/no-instruction-doc fixture; evaluate both backend `safe_to_resume` and GUI `complete` status. |
| **Q01-004** — Windows testing provenance | **Accepted with qualification.** The Organization README says its *integrated rc3 16-assertion suite* was not executed on Windows; top-level README/ROADMAP assert *40/40 relocated-host* and *7/7 sandbox* tests. These can be different suites rather than contradictory statements. No complete dated suite execution ledger or raw Windows test transcript is present. | **Medium documentation/evidence gap; wording verified, actual status unresolved** | Audit 01 carry-forward, Audits 03–04/09. Reconcile dates, suite names, revisions, counts and log provenance; correct stale docs only after verification. |
| **Q01-005** — Stale demo-only JS header | **Accepted.** `GUI/app.js:1–3,452` contradicts the actual live adapter in the same file (`:222–334,449`). Public preview mode remains a legitimate mode; comments alone are stale. | **Low; verified** | Audit 07 or targeted documentation cleanup. |
| **Q01-006** — Split backend path authority | **Accepted as transitional debt.** Public `Support/host.py:31` defaults to the legacy Shared-Guides path; private `Backend/Run-Live.py:17,58–62` overrides `host.TOOL_REL` at runtime. Not an observed failure of the verified launcher. | **Low; verified architecture, future-impact inference** | Audits 05/08. Explicit configurable backend path only if migration or release scope warrants. |
| **Q01-007** — Manifest omits executing host bridge | **Accepted as a limited integrity-boundary gap.** `Run-Live.py` hashes 11 engine entries and itself, but only existence/link-checks `Support/host.py` (`:29–45`). Git integrity could be the intentional separate trust boundary; no unexpected host change established. | **Low; verified omission, significance policy-dependent** | Audits 05/08. Document division of responsibility or extend attestation, avoid duplicate verification without need. |
| **Q01-008** — Git-ignore reason mislabelled | **Accepted; same as A01-F04.** Deep engine uses `--exclude-standard` but says `.gitignore` in its exclusion reason (`Deep/...ps1:903`). The actual `Backend/` rule is `.git/info/exclude`. | **Low; verified** | Audit 02. Minimal wording change: “Excluded by Git ignore policy.” |
| **Q01-009** — Public checkout cannot run live engines | **Agreed but intentional, not a defect.** Public docs explicitly identify demo-only scope; public release cannot be certified as live distributable. | **Release gate; verified** | Audit 08/09. |
| **Q01-010** — No open-source license | **Accepted as owner policy pending, not a coding defect.** Publicly viewable and rights-reserved are compatible; no license grant. | **Release-policy gate; verified** | Audit 08 before open-source/reuse claims. |
| **Q01-011** — Historical receipts vs current HEAD | **Accepted; source specificity improved.** Qwen lacked raw manifests, but the supplied RAR confirms both `.LIVE-MANIFEST.json:source_git_head` and `.ROOT-LAUNCHER-CUTOVER.json:git_head` contain `a3a6b61...`. Current source SHA is separately verified. | **Informational/low; verified, no defect** | No corrective edit needed. Record separate source vs deployment provenance. |
| **Q01-012** — Last-Selection reuse lacks picker revalidation | **Downgraded to informational; no defect evidenced.** The menu passes the stored string, but its downstream Structure Map scanner checks development-root containment, existence, and reparse-point ancestors (`New-Development-Structure.ps1:51–67`). This is not equivalent to unguarded filesystem traversal. | **Informational; verified downstream safeguards** | No Audit 01 blocker; targeted tests only if Audit 04 finds an actual bypass. |

### Additional full-source clarifications unavailable to Qwen

- Qwen had only excerpts of the 1,533-line Deep engine. The full source and the Structure/Organization engines are now available in the user's complete RAR. The request to *obtain* them for Audits 02–04 has already been met; their runtime correctness has **not** been established.
- The task-note `240` UI counter vs `2,000` host validation is deliberate-compatible layering: `GUI/index.html:84` contains `maxlength="240"`; `Support/host.py:369` allows up to 2,000 characters through its broader API. This is not an independently confirmed bug, though desired API/UI policy can be reviewed in Audit 07.
- The Organization output signature is produced by the engine (`Organization/New-Organization-Audit.ps1:25`) and checked by the host (`Support/host.py:159`); the Deep engine prints `ZIP:` (`Deep/New-Project-Deep-Handoff.ps1:1523`) and the host reads that marker (`Support/host.py:171`). These cross-component text contracts are **static-source corroborated** but not freshly Windows end-to-end tested here.
- The Qwen package was evidence-limited by its five-file constraint. Its claim that source was *unseen by Qwen* is true, but that is not a limitation of the independent full-RAR inspection performed in this conversation.

## 3. Release/section separation

**Audit 01 closure:** PASS WITH CONDITIONS. Sufficient authoritative baseline and architecture boundaries are established to start focused Audit 02. Qwen's useful additional findings are accepted without treating predictions as reproduced defects.

**Current Deep Handoff for the studio project:** NOT SAFE TO RESUME as a self-contained coding package. The generated application correctly labels this state. Do not use its ZIP as an authoritative substitute for the complete source during audits.

**Public production release:** BLOCKED separately by absent live distribution/install path, publication-boundary design, license decision and uncompleted later security/integration gates.

## 4. Decisions, open conditions, and carry-forward

1. **Preserve existing behavior.** No structural move, tracked ignore change, Git mutation, backend inclusion, or license change is authorized by this audit. Maintain local/private use only under the current documented boundary.
2. **Owner decision outstanding:** Before public live publication, choose whether `Backend/` stays outside the public working tree, is separated into a private repo, or is protected through an audited distribution layout. An interim tracked ignore is not a substitute for deciding whether source may be shared.
3. **Provenance ledger outstanding:** Obtain or reconstruct suite-level Windows evidence for 40/40 host, 7/7 real-engine sandbox, and 16-assertion Organization rc3. Absence of raw logs prevents a fresh independent historical test certification; it does not automatically refute existing claims.
4. **Audit 02 must address:** essential ignored source, explicit per-file inclusion review, privacy checks, complete manifest/hash coverage, fail-closed safety status, and clean synthetic regression proving/disproving Q01-003. This is a dedicated Deep Handoff audit, not a code-edit authorization.
5. **Later sections:** Audit 05 handles path authority and trust attestation; 07 handles stale UI comments and accessibility; 08 handles publication, licensing, installation; 09 synthesizes full release certification.

## 5. Evidence standard for later Qwen reviews

Supply Qwen the complete section-relevant source (split across multiple batches of at most five files if needed) or explicitly mark any excerpts. Do **not** claim a complete independent code audit from a summary-only packet. Preserve original path and line identifiers, known hashes, and test provenance; never include private credential or unrelated archive content.

**Disposition:** Audit 01 reconciled and closed conditionally. Section 02 is next, with no source changes performed as part of this reconciliation.
