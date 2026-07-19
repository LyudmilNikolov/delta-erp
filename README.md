# DeliaERP

## Run locally

Requirements:

- Python 3
- Internet access on the first run

Start the backend and frontend together:

```bash
./run.sh
```

Open `http://127.0.0.1:4200/`. Press `Ctrl+C` in the terminal to stop both
services.

The launcher uses a compatible installed Node.js version when available. If it
cannot find one, it downloads Node.js 22.22.3 into the ignored `.runtime`
directory and reuses it on later runs.

## Build for Windows

The `Build DeliaERP for Windows` GitHub Actions workflow builds and tests a
Windows x64 package on every relevant push. It can also be started manually from
the repository's **Actions** tab.

After the workflow succeeds:

1. Open the workflow run in GitHub.
2. Download the `DeliaERP-Windows-x64` artifact.
3. Extract `DeliaERP-Windows-x64.zip` on the Windows computer.
4. Run `DeliaERP.exe` without moving it away from the accompanying `_internal`
   directory.

The executable opens the application in the default browser and continues to run
in the Windows notification area. Use the DeliaERP tray icon to reopen the app or
exit it cleanly. Generated workbooks and the application log are stored under
`%LOCALAPPDATA%\DeliaERP`.

Windows may show a SmartScreen warning because the demo executable is not code
signed.
