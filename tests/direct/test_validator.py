"""ResolutionDuel independent validator tests."""

from __future__ import annotations

import json

import pytest

from fixtures.duels import PROPOSAL_WINS
from tests.direct.test_registration import register

LLM_PATTERN = r"independent prediction-market resolution adjudicator"


def capture(resolutionduel, direct_vm):
    duel_id = register(resolutionduel)
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(PROPOSAL_WINS))
    resolutionduel.adjudicate_duel(duel_id)
    return direct_vm._captured_validators[-1][0]


def test_validator_repeats_substance(resolutionduel, direct_vm):
    leader = capture(resolutionduel, direct_vm)
    assert direct_vm.run_validator(leader_result=leader) is True
    direct_vm.clear_mocks()
    different = dict(PROPOSAL_WINS)
    different["challenge_defect_codes"] = ["INCOMPLETE_SUPPORT"]
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(different))
    assert direct_vm.run_validator(leader_result=leader) is False


@pytest.mark.parametrize(
    "tampered",
    [
        {},
        {"decision": "PROPOSAL_WINS"},
        {"decision": "PROPOSAL_WINS", "settlement_outcome": "YES", "proposal_defect_mask": 0, "challenge_defect_mask": 16, "uncertainty_mask": 0, "extra": 0},
        {"decision": "PROPOSAL_WINS", "settlement_outcome": "NO", "proposal_defect_mask": 0, "challenge_defect_mask": 16, "uncertainty_mask": 0},
        {"decision": "PROPOSAL_WINS", "settlement_outcome": "YES", "proposal_defect_mask": False, "challenge_defect_mask": 16, "uncertainty_mask": 0},
        {"decision": "PROPOSAL_WINS", "settlement_outcome": "YES", "proposal_defect_mask": 0, "challenge_defect_mask": -1, "uncertainty_mask": 0},
        {"decision": "PROPOSAL_WINS", "settlement_outcome": "YES", "proposal_defect_mask": 0, "challenge_defect_mask": 64, "uncertainty_mask": 0},
        {"decision": "INDETERMINATE", "settlement_outcome": "INDETERMINATE", "proposal_defect_mask": 0, "challenge_defect_mask": 0, "uncertainty_mask": 0},
    ],
)
def test_validator_rejects_tampered_leader(resolutionduel, direct_vm, tampered):
    capture(resolutionduel, direct_vm)
    assert direct_vm.run_validator(leader_result=tampered) is False


def test_validator_rejects_leader_error(resolutionduel, direct_vm):
    capture(resolutionduel, direct_vm)
    assert direct_vm.run_validator(leader_error=RuntimeError("broken")) is False
