# TDK Master System Sync

Windows mapping script for EXIM / DEMON_CORE / WitnessAI operator inventory.

## Run Default Workspace Scan

```powershell
cd C:\KODEKS
.\scripts\master_system_sync.ps1
```

Default output root:

```text
C:\TDK_SYSTEM
```

Generated files:

- `FULL_SYSTEM_MAP.txt`
- `systeminfo.txt`
- `git_repositories.txt`
- `python_packages.txt`
- `node_global.txt`
- `docker_containers.txt`
- `docker_images.txt`
- `windows_services.txt`
- `startup_apps.txt`
- `desktop_layout.txt`
- `tdk_modules_detected.txt`

## Full Disk Scan

Use only when you intentionally want a broad Windows map:

```powershell
cd C:\KODEKS
.\scripts\master_system_sync.ps1 -FullDiskScan
```

Full disk mode scans `C:\` recursively and may take time.

## Safety Notes

- The script does not export environment variables.
- The script does not read secrets or private file contents.
- It records paths, service metadata, installed package names, Docker metadata, and system inventory.
- Output files are local under `C:\TDK_SYSTEM`.
