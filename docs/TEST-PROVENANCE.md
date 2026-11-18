# Test provenance — baseline and outstanding Windows evidence

**Purpose:** prevent historical success claims from being confused with tests independently run against a later revision. Audit 01's architectural review did not rerun the Windows PowerShell suites. Source baselines and observations must be tied to date, environment, revision and log where available.

| Claim / activity | Source of claim or observation | Audit 01 evidence level | Outstanding requirement |
| --- | --- | --- | --- |
| 40/40 relocated-host Windows cases | `README.md`, `docs/ROADMAP.md` (Nov 18 milestone) | Historical local assertion; raw dated Windows transcript not supplied | Confirm suite identifier, revision, date, command and transcript |
| 7/7 Windows real-engine sandbox scenarios | Same | Historical local assertion; no raw dated suite transcript supplied | Confirm exact scenario list and relation to subsystem suites |
| Organization standalone v1.0.1: 10 isolated Windows assertions | `Backend/Organization/README.md` | Attributed user-reported historical result | Identify archive, date and logs if available |
| Organization integrated rc3: 16 assertions | `Backend/Organization/README.md` | README explicitly says integrated rc3 suite not yet Windows-executed **at the time of that document**; not proven current | Run/check full five-phase isolated suite on Windows before certifying |
| Linux host regression, 33/33 | Primary Audit 01 run against supplied source | Executed in inspection environment; **not Windows** | Rerun relevant tests on target Windows environment after updates |
| Checkpoint source hashes, 25/25 | Primary Audit 01 checkpoint inspection | Independently checked during primary audit; static identity only | Retest if source snapshot changes |
| Backend engines 11/11 + live launcher hash | Audit 01 full-RAR manifest comparison | Static SHA-256 match on captured files | Validate again against the installed Windows backend before behavioral claims |
| Frontend JS parsing | Audit 01 `node --check` | Parse-only, no browser acceptance | Targeted GUI behavior in Audit 07/09 |

**No conflict is established merely by different counts.** The 40 host tests, 7 sandbox scenarios, and 16 Organization assertions may belong to different suites. Audit 01 verified that their documentation lacks a single reconciled execution ledger, not that any suite failed.

**Required execution ledger format for future tests:** UTC date/time; environment and PowerShell/Python versions; command or runner name; code version and file hashes; number of assertions; pass/fail/skip; raw result log location; scope limitations. Avoid posting logs containing private paths or tokens.

**Current update verification:** recorded separately in the Audit 01 update package's `VERIFICATION.md`. The update changes no PowerShell engine or live host Python behavior; it must not be treated as a Windows integration retest.

## Audit 02 — November 18, 2026 verified Windows runs

These are *owner-executed* and reported in the conversation; the results are tied to successive private update phases rather than to the older historical `40/40` and `7/7` claims. Raw log excerpts were uploaded as `Pasted text(20261118-185447).txt`; full local console archives, if any, were not independently preserved in this repository.

| Check | Evidence / result | Scope and limitation |
| --- | --- | --- |
| Deep relocated harness Phase 1 | **96 passed, 0 failed** | Windows PowerShell 7; repaired fixture paths, unmodified production guard |
| Deep Phase 2 readiness/privacy corrections | **106 passed, 0 failed** | Windows synthetic PowerShell tests; backend behavior changed |
| Deep Phase 2.1 linked-worktree exception | **108 passed, 0 failed** | `.git` worktree pointer excluded without false material-source warning |
| Deep Phase 3A reviewed ignored-file inclusion | **119 passed, 0 failed** | Windows synthetic fixtures; digest approval, path and change rejection; backend hash attestation PASS |
| Python host Phase 3B | **45 tests, 0 failed, 5.231 s** | Owner's Windows environment, after GUI/host update |
| Live backend launcher | **PASS: all 11 relocated engine hashes** | Owner's Windows environment after Phase 3A; no claim about Git publication |
| JavaScript syntax / Git diff validation | PASS after removing two trailing spaces from GUI/app.js | Parsing and whitespace only, not full accessibility or interaction testing |
| Browser interaction integration | **5/5 reported by primary auditor** | Separate Chromium inspection environment, not verified as user-run Windows browser cases |
| Real GUI→host→PowerShell→ZIP fixture | **PASS (single disposable project)** | Four expected files including explicitly approved ignored `src/ignored_helper.py`; COVERAGE `safe_to_resume=true`, 0 blockers |
| Uploaded fixture ZIP integrity | **17/17 SHA-256 checksum lines matched**; four source hashes match manifest | Read-only archive inspection; does not prove universal coverage or secret-detection completeness |

**Next checkpoint:** Audit 03 Structure Map will need its own Windows test runs, separate from the verified Audit 02 Deep tests. Preserve the current private backend SHA manifest and the newly published public Git commit as distinct reference points.
