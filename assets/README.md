# Assets

This folder contains shared resources used by the build system and the
generated applications.

## `icons/`

Place ICO / PNG / SVG icons here. The build system picks up:

| File                   | Used by                                                  |
|------------------------|----------------------------------------------------------|
| `master.ico`           | `AIClusterRuntime.exe --mode master`                                    |
| `worker.ico`           | `AIClusterRuntime.exe --mode worker`                                    |
| `master-control.ico`   | `MasterControlCenter.exe` (Tauri)                        |
| `worker-control.ico`   | `WorkerControlCenter.exe` (Tauri)                        |
| `studio.ico`           | `AIClusterStudio.exe` (Tauri)                            |
| `cli.ico`              | `aicluster.exe`                                          |
| `default.ico`          | Fallback for every executable                            |

Tauri apps additionally expect a set of PNG variants in their
`src-tauri/icons/` folder; the build system will copy any matching
asset from here. When an icon is missing, the build still succeeds and
the Windows default icon is embedded.

## `manifest.json`

A small JSON file (`product_name`, `version`, `company`, `copyright`,
`description`) consumed by the CLI at runtime. Updated automatically
on every build.
