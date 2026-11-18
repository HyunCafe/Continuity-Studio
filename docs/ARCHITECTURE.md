# Architecture — public preview

```text
Continuity Studio GUI (HTML / CSS / JavaScript)
              |
      Local loopback host (Python standard library)
              |
    [demo-only in this public snapshot]
              |
   Future: existing PowerShell 7 rc9 engines
              |
  DEVELOPMENT-MAP.md / TREE.txt / handoff ZIPs
```

The host keeps the UI assets isolated, validates requests, and controls process execution when deployed in a controlled live build. This public preview refuses production execution; it is **not a standalone install of the rc9 PowerShell backend**.

**Development root target:** one `Continuity Studio.cmd` launcher at root, with GUI and host source stored in a Git repository under `05-Utilities-and-Automation/Continuity-Studio`, while the backend remains in Shared Guides. Keep generated maps, ZIPs and diagnostics out of Git.

**Python/Edge rationale:** Retains the approved web styling in an Edge app window while using only Python's standard library for the host. Desktop taskbar branding and the final packaging/installation model are not yet finalized.
