# Delta ERP

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
