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
