#!/usr/bin/env bash

# Phase 5 GPU environment bootstrap for Plato.
# This script installs a pinned Miniforge distribution under the user's home
# directory, creates a dedicated Python 3.11 environment, and installs only
# the historical vision dependencies required for Case 1/Case 3 validation.
#
# It does not modify the system Python, does not require root, and does not
# write credentials.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MINIFORGE_DIR="${HOME}/.local/miniforge3-phenoassistant"
ENV_DIR="${HOME}/.local/envs/phenoassistant-phase5-gpu"
CACHE_DIR="${HOME}/.cache/phenoassistant"
INSTALLER="${CACHE_DIR}/Miniforge3-26.7.2-0-Linux-x86_64.sh"
INSTALLER_URL="https://github.com/conda-forge/miniforge/releases/download/26.7.2-0/Miniforge3-Linux-x86_64.sh"
INSTALLER_SHA256="281b0ac7d550802efc81af633225a5e6116d29ae72f3ab4eae7168c3931a4c05"

mkdir -p "${CACHE_DIR}" "${HOME}/.local/envs"

if [ ! -x "${MINIFORGE_DIR}/bin/conda" ]; then
  echo "Downloading pinned Miniforge installer..."
  python - "${INSTALLER_URL}" "${INSTALLER}" <<'PY'
import pathlib
import sys
import urllib.request

url = sys.argv[1]
target = pathlib.Path(sys.argv[2])
request = urllib.request.Request(url, headers={"User-Agent": "PhenoAssistant-Phase5/1.0"})
with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
    while True:
        chunk = response.read(1024 * 1024)
        if not chunk:
            break
        output.write(chunk)
print(target)
PY

  echo "${INSTALLER_SHA256}  ${INSTALLER}" | sha256sum -c -
  if [ "$?" -ne 0 ]; then
    echo "Miniforge installer checksum verification failed."
    return 1 2>/dev/null || false
  fi

  bash "${INSTALLER}" -b -p "${MINIFORGE_DIR}"
  if [ "$?" -ne 0 ]; then
    echo "Miniforge installation failed."
    return 1 2>/dev/null || false
  fi
fi

CONDA="${MINIFORGE_DIR}/bin/conda"

if [ ! -x "${ENV_DIR}/bin/python" ]; then
  "${CONDA}" create -y -p "${ENV_DIR}" python=3.11 pip
  if [ "$?" -ne 0 ]; then
    echo "Conda environment creation failed."
    return 1 2>/dev/null || false
  fi
fi

PYTHON="${ENV_DIR}/bin/python"

"${PYTHON}" -m pip install --upgrade "pip<27"
if [ "$?" -ne 0 ]; then
  echo "pip upgrade failed."
  return 1 2>/dev/null || false
fi

"${PYTHON}" -m pip install   torch==2.4.1 torchvision==0.19.1   --index-url https://download.pytorch.org/whl/cu121
if [ "$?" -ne 0 ]; then
  echo "PyTorch installation failed."
  return 1 2>/dev/null || false
fi

"${PYTHON}" -m pip install -r "${ROOT}/requirements-phase5-gpu.txt"
if [ "$?" -ne 0 ]; then
  echo "Phase 5 dependency installation failed."
  return 1 2>/dev/null || false
fi

"${PYTHON}" -m pip install   "git+https://github.com/facebookresearch/segment-anything.git"
if [ "$?" -ne 0 ]; then
  echo "segment-anything installation failed."
  return 1 2>/dev/null || false
fi

"${PYTHON}" -m pip check

echo
echo "Phase 5 environment ready:"
echo "  Python: ${PYTHON}"
"${PYTHON}" --version
echo
echo "Activate with:"
echo "  source ${ENV_DIR}/bin/activate"
