"""Shared ResolutionDuel direct-mode fixtures."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fixtures.duels import POLICY_VERSION, REGISTRATION_DATETIME
from tests.gltest_windows_compat import install_windows_direct_compatibility

CONTRACT_PATH = PROJECT_ROOT / "contracts" / "resolution_duel.py"
DIRECT_SDK_VERSION = "v0.2.16"

install_windows_direct_compatibility()


@pytest.fixture
def resolutionduel(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.warp(REGISTRATION_DATETIME)
    return direct_deploy(
        str(CONTRACT_PATH), POLICY_VERSION, sdk_version=DIRECT_SDK_VERSION
    )
