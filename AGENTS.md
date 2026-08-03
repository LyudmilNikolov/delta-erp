# Agent Instructions

These instructions apply to the entire repository.

## Communication and language

- Conduct every chat, progress update, review, and handoff in English, even when
  the project data is Bulgarian.
- Keep technical prose, code comments, commit descriptions, and new developer
  documentation in English.
- Bulgarian is appropriate when quoting or adding DeliaERP UI text, menu names,
  workbook headers, product names, domain terms, validation messages, and test
  examples. Preserve Bulgarian text verbatim when it is part of a contract.
- The product UI and customer-facing backend errors are currently Bulgarian.
  Keep that convention unless the task explicitly introduces localization.
- Preserve UTF-8 text and the existing `bg-BG` formatting behavior.

## What this project does

DeliaERP is a local Excel-processing application for Microinvest exports. A user
uploads one `.xls` or `.xlsx` workbook, the Python service normalizes quantities
to kilograms and builds summaries, and the Angular UI displays the result and
offers the generated workbook for download. In development the two services run
separately; the Windows package serves the compiled UI and API from one local
FastAPI process with a notification-area icon.

The main flow is:

1. `POST /process` receives one multipart field named `file` and an optional
   `sheet_name`.
2. `backend/excel_processing.py` reads and normalizes the workbook, creates the
   summary tables, and writes the result workbook.
3. `backend/main.py` returns JSON plus a relative `/download/...` URL.
4. The Angular app stores that response in memory and navigates to `/table`.
5. The UI can instead load `/mock/example_output.json` through
   **Използвай демо данни**, without a backend.

## Repository map and sources of truth

- `backend/excel_processing.py`: workbook parsing, domain rules, warnings,
  pivots, and output workbook generation. Treat this as the business-logic
  source of truth.
- `backend/main.py`: FastAPI endpoints, response shape, CORS, output retention,
  filename safety, and compiled-SPA serving.
- `backend/desktop.py`: local port selection, browser startup, tray lifecycle,
  logging, and clean desktop shutdown.
- `backend/tests/`: the real pytest suite. `backend/test.py` and
  `backend/testing_json.py` are old interactive experiments, are not collected
  by pytest, and should not be used as production references.
- `frontend/src/modules/file-upload/`: upload and demo-data workflow.
- `frontend/src/modules/table/`: API interfaces, response-to-view adapters,
  filters, pagination, selection, and the four result views.
- `frontend/public/mock/example_output.json`: the demo payload actually loaded
  by the UI. `backend/data/example_output.json` is a separate legacy copy and is
  not guaranteed to match it.
- `run.sh`: supported development launcher for both services.
- `delia-erp.spec`: PyInstaller definition. It requires a production frontend
  at `frontend/dist/delia-erp/browser` before packaging.
- `.github/workflows/build-windows.yml`: authoritative Windows x64 build,
  backend test, packaged-app smoke test, and artifact workflow.

## Domain and API invariants

- Accepted uploads are exactly one `.xls` or `.xlsx` file. Validate this on the
  backend even though the frontend also validates it.
- `.xls` uses `xlrd`; `.xlsx` uses `openpyxl`.
- When no sheet is requested, prefer a sheet named `Microinvest`, then try the
  remaining sheets. Headers may be within the first six rows.
- Required Microinvest columns are exactly `Дата`, `Код`, `Стока`, `Група`,
  `Партида`, `Количество`, and `Мярка`. Optional source fields are mapped in
  `normalize_microinvest()`.
- Kilogram quantities pass through. Quantities in `бр`/`бр.` depend on a package
  weight parsed from `Стока`; unknown quantities, weights, dates, and units
  produce structured warnings rather than silently inventing values.
- Product type, `стока`/`произв`, and seasoned-or-ground classification are
  domain rules. Keep their Bulgarian spelling and add focused regression tests
  whenever changing `PHRASE_TO_TYPE`, `GROUNDED_MEAT_TERMS`, `SEASONED_TERMS`,
  weight parsing, or group classification.
- Processing failures return `{ "error": "..." }` with Bulgarian user-facing
  text. Unexpected exceptions must not expose paths, stack traces, or workbook
  contents to the client.
- The successful response deliberately mixes normalized snake_case detail rows
  with Bulgarian workbook-style summary keys such as `Дата`, `Код`, `Стока`,
  `Партида`, and `вид`. Do not casually rename these fields.
- If the API response changes, update all of the following together:
  `backend/tests/test_api.py`, `frontend/src/modules/table/table.models.ts`, the
  adapters in `frontend/src/modules/table/table.ts`, and
  `frontend/public/mock/example_output.json`.
- Generated workbooks contain `Sheet1`, `Sheet2`, `Sheet3`, and `Details`; add
  `Warnings` only when warnings exist. Treat sheet names and columns as an
  external contract unless a task says otherwise.
- Keep download URLs relative so development proxying and the packaged
  same-origin application both work.
- Preserve upload cleanup, basename sanitization, download traversal checks,
  output TTL cleanup, and localhost-only desktop binding.

## Backend conventions

- CI targets Python 3.12. Keep code compatible with 3.12 even if a local
  environment uses a newer Python.
- Follow the existing style: four spaces, type hints for public and non-obvious
  internal APIs, `pathlib.Path` for path-oriented logic where practical, and
  `ProcessingError` for expected user-correctable workbook failures.
- Keep Pandas-to-JSON conversion in `dataframe_to_records()` so timestamps,
  NumPy scalars, and missing values remain JSON-safe.
- Use synthetic DataFrames or workbooks in `tmp_path` for tests. Cover both the
  calculated values and warnings/errors; do not rely solely on status codes.
- Configuration is read from `CORS_ALLOWED_ORIGINS`, `OUTPUT_TTL_SECONDS`,
  `DELIA_ERP_DATA_DIR`, and `DELIA_ERP_WEB_DIR`. The desktop wrapper also uses
  `DELIA_ERP_PORT` and `DELIA_ERP_NO_BROWSER`. Several derived globals are set at
  import time, so isolate or monkeypatch them in tests as the existing suite
  does.
- API routes must remain ahead of the catch-all SPA route in `backend/main.py`.

## Frontend conventions

- The frontend uses Angular 22, Angular Material, strict TypeScript, standalone
  components, zoneless change detection, signals/computed state, and the modern
  `@if`/`@for` template syntax. Follow those patterns instead of introducing
  NgModules or Zone-dependent behavior.
- Use two-space indentation and single quotes in TypeScript. Run the configured
  ESLint and production build; strict template checking is part of the build.
- Keep API calls on relative `/process` and `/download` paths. The development
  proxy targets `127.0.0.1:8000`, while the packaged app serves both surfaces.
- Result state is intentionally in memory. Direct access to `/table` without a
  processed response redirects to `/file-upload`.
- Preserve accessibility labels, keyboard-usable Material controls, Bulgarian
  paginator labels, and locale-aware number/date formatting when changing UI.
- There are currently no frontend `*.spec.ts` files. For frontend-only changes,
  lint plus a production build are the minimum checks; add focused tests when a
  task introduces logic that warrants them.

## Setup and verification

Run commands from the repository root unless a command starts with `cd`.

For the complete development application:

```bash
./run.sh
```

This is a long-running command. It checks ports 8000 and 4200, creates
`backend/venv` if needed, installs missing dependencies, and may download the
pinned Node runtime on first use. Use it for manual integration checks, not as a
substitute for targeted verification.

Backend setup and tests:

```bash
python3 -m venv backend/venv
backend/venv/bin/python -m pip install -r backend/requirements.txt
backend/venv/bin/python -m pytest backend/tests -q
```

Frontend setup and checks require Node `>=22.22.3 <23` and the checked-in Yarn
4.15.0 release:

```bash
cd frontend
node .yarn/releases/yarn-4.15.0.cjs install --immutable
node .yarn/releases/yarn-4.15.0.cjs lint
node .yarn/releases/yarn-4.15.0.cjs build --configuration production --progress=false
```

If the system Node is incompatible, `run.sh` provisions the pinned runtime under
the ignored `.runtime/` directory. The current production build can complete
with a non-fatal initial-bundle budget warning; report it and avoid increasing
the bundle without a reason.

Choose checks proportionally:

- Processing, API, storage, or desktop changes: run the backend suite.
- TypeScript, HTML, SCSS, routing, or model changes: run frontend lint and the
  production build.
- API-contract changes: run both sets of checks and exercise demo-data mode.
- Packaging changes: build the frontend first, run backend tests, then follow
  `delia-erp.spec`; the Windows GitHub workflow is the definitive package and
  tray smoke test.

## Data safety and worktree hygiene

- Inspect `git status` before editing and preserve unrelated tracked and
  untracked work.
- Treat example and reference files as evidence, not as an exhaustive business
  specification. Never hardcode fixture-specific filenames, row values, product
  or document IDs, code aliases, partners, or one-off exceptions merely to make
  an example match. Prefer schema-, metadata-, or format-driven behavior that
  generalizes to unseen files, and cover it with examples using different
  values. If a mismatch appears to require a business-specific exception that
  cannot be derived generally, stop and ask the user before implementing it.
- Treat all workbooks and exports as potentially sensitive operational data.
  Do not paste their contents into chats, logs, snapshots, or new fixtures.
- Do not modify, replace, or delete files under `backend/data/`,
  `backend/outputs/`, `backend/data/new/`, or root-level Excel/Numbers files
  unless the task explicitly targets those artifacts. Some generated-looking
  binary files are tracked, while local additions may be untracked.
- Tests must redirect output to temporary directories. Do not let verification
  overwrite checked-in workbooks or populate `backend/outputs/`.
- Do not commit build products, virtual environments, `node_modules`, caches,
  logs, or `.runtime/` downloads.
- Avoid dependency changes unless they are required. When they are required,
  update the appropriate requirements file or `frontend/yarn.lock` and verify
  the immutable install path.

## Completion checklist

- Keep the change focused and preserve unrelated user work.
- Add or update regression coverage for changed behavior.
- Synchronize backend payloads, TypeScript models/adapters, demo JSON, and docs
  when a contract changes.
- Confirm new user-visible copy is Bulgarian and agent-facing documentation is
  English.
- Run the relevant checks above and report exactly what passed, what warned, and
  what was not run.
