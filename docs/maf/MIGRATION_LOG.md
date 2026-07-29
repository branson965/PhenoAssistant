# PhenoAssistant MAF Linux Migration Log

## 2026-07-29

### Phase
Phase 0 and Phase 1 — Preservation and clean migration branch

### Objective
Preserve the previous MAF proof of concept and establish a clean branch from the upstream `maf` branch for the real Linux-first migration.

### Completed
- Created a local Stage 2A backup archive.
- Recorded its SHA-256 checksum.
- Created and pushed `backup/maf-stage2a-poc`.
- Preserved the offline prototype in commit `48a7709`.
- Fetched `upstream/maf`.
- Created `feature/maf-linux-migration` from `upstream/maf@aff8551`.
- Pushed the migration branch to the fork.

### Evidence
- Backup archive: `PhenoAssistant-stage2a-backup-20260728-145741.tar.gz`
- Backup SHA-256: `b88f382a90de381bbeea2ed28d0bfbd4a5346744d8bef84a5376c2713c3c4c3c`
- Backup branch: `backup/maf-stage2a-poc`
- Backup commit: `48a7709`
- Migration branch: `feature/maf-linux-migration`
- Migration baseline: `aff8551`

### Blocked
- Nottingham GPU/cluster account not yet available.
- Canonical scientific fixture not yet approved.
- Final OpenRouter model not yet selected.
- Vincent's authoritative MCP interface not yet confirmed.

### Next
- Add local environments and generated Python files to `.gitignore`.
- Commit the master execution plan and this log.
- Create a dedicated Ubuntu VM in VirtualBox.
- Clone the migration branch inside Linux.
- Record Linux runtime evidence.

### Overall completion
30%
