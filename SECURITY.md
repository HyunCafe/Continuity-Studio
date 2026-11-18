# Security and privacy

- The public preview contains only fictional project names and outcomes. It does not need your development directory.
- The desktop host serves locally on a random `127.0.0.1` port, not on a public network interface.
- Do not expose that port, modify the host's origin/token checks, or run the preview as administrator.
- The public snapshot disables unrestricted live PowerShell execution; real-engine testing must use a separate, explicitly isolated test package.
- Do not upload handoff ZIPs, repository logs, `.git` directories, credentials, local maps, generated reports, or screenshots containing private workspace paths.
- This is an early preview, not a security-audited production release.

For a security report, use the repository owner's GitHub contact or GitHub private vulnerability reporting if enabled. Please avoid opening public issues containing secrets.
