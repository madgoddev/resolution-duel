"""ResolutionDuel audit and fail-closed gate tests."""

from __future__ import annotations

import json

import pytest

from fixtures.duels import PROPOSAL_WINS, build_fingerprint
from tests.direct.test_registration import register

LLM_PATTERN = r"independent prediction-market resolution adjudicator"


def mock(direct_vm, response):
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(response))


def test_proposal_wins_and_gate(resolutionduel, direct_vm):
    duel_id = register(resolutionduel)
    mock(direct_vm, PROPOSAL_WINS)
    resolutionduel.adjudicate_duel(duel_id)
    duel = resolutionduel.get_duel(duel_id)
    audit = resolutionduel.get_audit(duel_id)
    assert audit["decision"] == "PROPOSAL_WINS"
    assert audit["settlement_outcome"] == "YES"
    assert audit["proposal_defect_mask"] == 0
    assert audit["challenge_defect_mask"] == 1
    assert resolutionduel.matches_decision(
        duel_id, duel["duel_fingerprint"], "PROPOSAL_WINS", "YES"
    ) is True
    assert resolutionduel.matches_decision(
        duel_id, duel["duel_fingerprint"], "CHALLENGER_WINS", "NO"
    ) is False


@pytest.mark.parametrize(
    ("code", "mask"),
    [
        ("RULE_MISMATCH", 1),
        ("EVIDENCE_NOT_RELEVANT", 2),
        ("EVIDENCE_INCONSISTENT", 4),
        ("TEMPORAL_DEFECT", 8),
        ("AUTHORITY_DEFECT", 16),
        ("INCOMPLETE_SUPPORT", 32),
    ],
)
def test_each_defect_bit(resolutionduel, direct_vm, code, mask):
    duel_id = register(resolutionduel, duel_key=f"DEFECT-{mask}")
    response = dict(PROPOSAL_WINS)
    response["challenge_defect_codes"] = [code]
    mock(direct_vm, response)
    resolutionduel.adjudicate_duel(duel_id)
    assert resolutionduel.get_audit(duel_id)["challenge_defect_mask"] == mask


def test_challenger_wins(resolutionduel, direct_vm):
    duel_id = register(resolutionduel, duel_key="CHALLENGER-WINS")
    mock(
        direct_vm,
        {
            "decision": "CHALLENGER_WINS",
            "settlement_outcome": "NO",
            "proposal_defect_codes": ["RULE_MISMATCH"],
            "challenge_defect_codes": [],
            "uncertainty_codes": [],
        },
    )
    resolutionduel.adjudicate_duel(duel_id)
    assert resolutionduel.get_audit(duel_id)["decision"] == "CHALLENGER_WINS"


def test_void_and_indeterminate(resolutionduel, direct_vm):
    void_id = register(resolutionduel, duel_key="VOID-BOTH")
    mock(
        direct_vm,
        {
            "decision": "VOID",
            "settlement_outcome": "VOID",
            "proposal_defect_codes": ["RULE_MISMATCH"],
            "challenge_defect_codes": ["INCOMPLETE_SUPPORT"],
            "uncertainty_codes": [],
        },
    )
    resolutionduel.adjudicate_duel(void_id)
    assert resolutionduel.get_audit(void_id)["decision"] == "VOID"

    direct_vm.clear_mocks()
    uncertain_id = register(resolutionduel, duel_key="UNCERTAIN")
    mock(
        direct_vm,
        {
            "decision": "INDETERMINATE",
            "settlement_outcome": "INDETERMINATE",
            "proposal_defect_codes": [],
            "challenge_defect_codes": [],
            "uncertainty_codes": ["CONFLICTING_EVIDENCE"],
        },
    )
    resolutionduel.adjudicate_duel(uncertain_id)
    assert resolutionduel.get_audit(uncertain_id)["uncertainty_mask"] == 2


@pytest.mark.parametrize(
    "response",
    [
        {},
        [],
        {**PROPOSAL_WINS, "extra": 1},
        {**PROPOSAL_WINS, "decision": "UNKNOWN"},
        {**PROPOSAL_WINS, "settlement_outcome": "NO"},
        {**PROPOSAL_WINS, "proposal_defect_codes": ["RULE_MISMATCH"]},
        {**PROPOSAL_WINS, "challenge_defect_codes": []},
        {**PROPOSAL_WINS, "challenge_defect_codes": ["UNKNOWN"]},
        {**PROPOSAL_WINS, "uncertainty_codes": ["AMBIGUOUS_RULE"]},
        {**PROPOSAL_WINS, "challenge_defect_codes": ["AUTHORITY_DEFECT", "AUTHORITY_DEFECT"]},
    ],
)
def test_malformed_output_writes_no_state(resolutionduel, direct_vm, response):
    duel_id = register(resolutionduel)
    mock(direct_vm, response)
    with direct_vm.expect_revert("[LLM_ERROR]"):
        resolutionduel.adjudicate_duel(duel_id)
    assert resolutionduel.is_adjudicated(duel_id) is False
    assert resolutionduel.get_audit_count() == 0


def test_creator_only_and_immutable(resolutionduel, direct_vm, direct_bob):
    duel_id = register(resolutionduel)
    direct_vm.sender = direct_bob
    mock(direct_vm, PROPOSAL_WINS)
    with direct_vm.expect_revert("only_creator_may_adjudicate"):
        resolutionduel.adjudicate_duel(duel_id)
    direct_vm.sender = resolutionduel.owner
    resolutionduel.adjudicate_duel(duel_id)
    with direct_vm.expect_revert("duel_already_adjudicated"):
        resolutionduel.adjudicate_duel(duel_id)


def test_gate_rejects_fingerprint_and_stored_tampering(resolutionduel, direct_vm):
    duel_id = register(resolutionduel)
    mock(direct_vm, PROPOSAL_WINS)
    resolutionduel.adjudicate_duel(duel_id)
    duel = resolutionduel.get_duel(duel_id)
    fingerprint = duel["duel_fingerprint"]
    assert fingerprint == build_fingerprint(duel["creator"])
    altered = fingerprint[:-1] + ("0" if fingerprint[-1] != "0" else "1")
    assert resolutionduel.matches_decision(duel_id, altered, "PROPOSAL_WINS", "YES") is False
    audit = json.loads(resolutionduel.audits[duel_id])
    audit["challenge_defect_mask"] = False
    resolutionduel.audits[duel_id] = json.dumps(audit, sort_keys=True, separators=(",", ":"))
    assert resolutionduel.matches_decision(duel_id, fingerprint, "PROPOSAL_WINS", "YES") is False
