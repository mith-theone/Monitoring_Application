# SSH metrics (demo)

## Prerequisites

- Target is a Linux host reachable from the app machine
- Prefer key-based auth: store the **private key path** on the app host (e.g. `/home/jumpuser/.ssh/id_ed25519`)
- Password auth is a demo fallback only

## Host key policy (demo warning)

This demo uses Paramiko `AutoAddPolicy` so first connections work without a pre-seeded `known_hosts`.  
**Do not use this policy for production.** Prefer verifying host keys via `known_hosts`.

## Allowlisted remote commands

Only these fixed commands are run (no user-supplied shell strings):

| Metric | Command |
|--------|---------|
| CPU | `grep '^cpu ' /proc/stat` |
| Memory | `cat /proc/meminfo` |
| Network | `cat /proc/net/dev` |
| Ports | `ss -tulnH` (fallback `netstat -tuln`) |

Private keys and passwords are never logged.
