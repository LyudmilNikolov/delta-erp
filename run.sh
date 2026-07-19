#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
YARN_CLI="$FRONTEND_DIR/.yarn/releases/yarn-4.15.0.cjs"
PINNED_NODE_VERSION="22.22.3"
RUNTIME_DIR="$ROOT_DIR/.runtime"
BACKEND_PID=""

export NG_CLI_ANALYTICS=false
export PYTHONDONTWRITEBYTECODE=1

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo
    echo "Stopping Delta ERP backend..."
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM

port_in_use() {
  local port=$1

  if command -v lsof >/dev/null 2>&1; then
    lsof -n -P -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return
  fi

  (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
}

node_is_supported() {
  local node_bin=$1
  local version major minor patch

  [[ -n "$node_bin" && -x "$node_bin" ]] || return 1
  version="$($node_bin -p 'process.versions.node' 2>/dev/null)" || return 1
  IFS=. read -r major minor patch <<< "$version"

  [[ "$major" =~ ^[0-9]+$ && "$minor" =~ ^[0-9]+$ && "$patch" =~ ^[0-9]+$ ]] \
    || return 1
  (( major == 22 && (minor > 22 || (minor == 22 && patch >= 3)) ))
}

detect_node_os() {
  case "$(uname -s)" in
    Darwin) echo "darwin" ;;
    Linux) echo "linux" ;;
    *) return 1 ;;
  esac
}

detect_node_arch() {
  case "$(uname -m)" in
    arm64 | aarch64) echo "arm64" ;;
    x86_64 | amd64) echo "x64" ;;
    *) return 1 ;;
  esac
}

install_local_node() {
  local os=$1
  local arch=$2
  local archive archive_path checksums expected actual

  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to download the local Node.js runtime."
    exit 1
  fi

  archive="node-v${PINNED_NODE_VERSION}-${os}-${arch}.tar.gz"
  archive_path="$RUNTIME_DIR/$archive"
  checksums="$RUNTIME_DIR/SHASUMS256.txt"
  mkdir -p "$RUNTIME_DIR"

  echo "Downloading Node.js $PINNED_NODE_VERSION..."
  curl --fail --location --retry 3 --silent --show-error \
    "https://nodejs.org/dist/v${PINNED_NODE_VERSION}/$archive" \
    --output "$archive_path"
  curl --fail --location --retry 3 --silent --show-error \
    "https://nodejs.org/dist/v${PINNED_NODE_VERSION}/SHASUMS256.txt" \
    --output "$checksums"

  expected="$(awk -v name="$archive" '$2 == name { print $1 }' "$checksums")"
  if command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$archive_path" | awk '{ print $1 }')"
  elif command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$archive_path" | awk '{ print $1 }')"
  else
    echo "A SHA-256 checksum tool is required (shasum or sha256sum)."
    exit 1
  fi

  if [[ -z "$expected" || "$actual" != "$expected" ]]; then
    echo "The downloaded Node.js archive failed checksum verification."
    rm -f "$archive_path" "$checksums"
    exit 1
  fi

  tar -xzf "$archive_path" -C "$RUNTIME_DIR"
  rm -f "$archive_path" "$checksums"
}

if port_in_use 8000; then
  echo "Port 8000 is already in use. Stop the existing backend and run this script again."
  exit 1
fi

if port_in_use 4200; then
  echo "Port 4200 is already in use. Stop the existing frontend and run this script again."
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
  if [[ -z "$PYTHON_BIN" ]]; then
    echo "Python 3 is required but was not found."
    exit 1
  fi

  echo "Creating backend virtual environment..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c \
  'import fastapi, uvicorn, pandas, openpyxl, xlrd, multipart' \
  >/dev/null 2>&1; then
  echo "Installing backend dependencies..."
  "$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

NODE_BIN="${NODE_BIN:-$(command -v node || true)}"
if ! node_is_supported "$NODE_BIN"; then
  if ! NODE_OS="$(detect_node_os)" || ! NODE_ARCH="$(detect_node_arch)"; then
    echo "Automatic Node.js setup supports macOS and Linux on arm64 or x64."
    echo "Install Node.js >=22.22.3 <23, then run ./run.sh again."
    exit 1
  fi

  NODE_BIN="$RUNTIME_DIR/node-v${PINNED_NODE_VERSION}-${NODE_OS}-${NODE_ARCH}/bin/node"

  if ! node_is_supported "$NODE_BIN"; then
    install_local_node "$NODE_OS" "$NODE_ARCH"
  fi
fi

if [[ ! -f "$YARN_CLI" ]]; then
  echo "The project Yarn release is missing: $YARN_CLI"
  exit 1
fi

export PATH="$(dirname "$NODE_BIN"):$PATH"

echo "Checking frontend dependencies..."
(
  cd "$FRONTEND_DIR"
  "$NODE_BIN" "$YARN_CLI" install --immutable
)

echo "Starting Delta ERP backend..."
(
  cd "$BACKEND_DIR"
  "$VENV_DIR/bin/uvicorn" main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

BACKEND_READY=false
for _ in {1..40}; do
  if "$VENV_DIR/bin/python" -c \
    'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/docs")' \
    >/dev/null 2>&1; then
    BACKEND_READY=true
    break
  fi

  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID"
    exit 1
  fi

  sleep 0.25
done

if [[ "$BACKEND_READY" != true ]]; then
  echo "The backend did not become ready within 10 seconds."
  exit 1
fi

echo
echo "Delta ERP is running:"
echo "  App:     http://127.0.0.1:4200/"
echo "  Backend: http://127.0.0.1:8000/"
echo "Press Ctrl+C to stop both services."
echo

cd "$FRONTEND_DIR"
"$NODE_BIN" "$YARN_CLI" start --host 127.0.0.1 --port 4200
