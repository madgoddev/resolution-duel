"""ResolutionDuel registration and view tests."""

from __future__ import annotations

import pytest

from fixtures.duels import (
    CHALLENGE_EVIDENCE,
    CHALLENGE_OUTCOME,
    DUEL_KEY,
    MARKET_QUESTION,
    POLICY_VERSION,
    PROPOSAL_EVIDENCE,
    PROPOSAL_OUTCOME,
    REGISTRATION_DATETIME,
    RESOLUTION_RULES,
    build_fingerprint,
)
from tests.conftest import CONTRACT_PATH, DIRECT_SDK_VERSION


def register(contract, **overrides):
    values = {
        "duel_key": DUEL_KEY,
        "market_question": MARKET_QUESTION,
        "resolution_rules": RESOLUTION_RULES,
        "proposal_outcome": PROPOSAL_OUTCOME,
        "proposal_evidence": PROPOSAL_EVIDENCE,
        "challenge_outcome": CHALLENGE_OUTCOME,
        "challenge_evidence": CHALLENGE_EVIDENCE,
    }
    values.update(overrides)
    return contract.register_duel(**values)


def test_policy_and_constructor(resolutionduel, direct_alice):
    policy = resolutionduel.get_policy()
    assert policy["owner"].lower() == f"0x{bytes(direct_alice).hex()}"
    assert policy["policy_version"] == POLICY_VERSION
    assert policy["defect_category_count"] == 6
    assert policy["uncertainty_category_count"] == 4
    assert policy["creator_only_adjudication"] is True


def test_zero_policy_rejected(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("invalid_policy_version"):
        direct_deploy(str(CONTRACT_PATH), 0, sdk_version=DIRECT_SDK_VERSION)


def test_registers_and_fingerprints(resolutionduel, direct_alice):
    duel_id = register(resolutionduel)
    duel = resolutionduel.get_duel(duel_id)
    creator = f"0x{bytes(direct_alice).hex()}"
    assert duel_id == f"{creator}:{DUEL_KEY}"
    assert duel["duel_fingerprint"] == build_fingerprint(creator)
    assert duel["registered_at"] == REGISTRATION_DATETIME
    assert resolutionduel.get_duel_count() == 1
    assert resolutionduel.get_duel_id(0) == duel_id
    assert resolutionduel.is_adjudicated(duel_id) is False


def test_duplicate_is_idempotent(resolutionduel):
    first = register(resolutionduel)
    second = register(
        resolutionduel,
        duel_key=f" {DUEL_KEY.lower()} ",
        market_question=f"\r\n{MARKET_QUESTION}\r\n",
    )
    assert second == first
    assert resolutionduel.get_duel_count() == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("market_question", MARKET_QUESTION + " A materially different question."),
        ("resolution_rules", RESOLUTION_RULES + " A later post controls."),
        ("proposal_outcome", "VOID"),
        ("proposal_evidence", PROPOSAL_EVIDENCE + " Additional evidence."),
        ("challenge_outcome", "VOID"),
        ("challenge_evidence", CHALLENGE_EVIDENCE + " Additional evidence."),
    ],
)
def test_same_key_changed_core_rejected(resolutionduel, direct_vm, field, value):
    register(resolutionduel)
    with direct_vm.expect_revert("duel_registration_conflict"):
        register(resolutionduel, **{field: value})


def test_creator_scoped_ids(resolutionduel, direct_vm, direct_bob):
    first = register(resolutionduel)
    direct_vm.sender = direct_bob
    second = register(resolutionduel)
    assert first != second
    assert resolutionduel.get_duel_count() == 2


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"duel_key": ""}, "invalid_duel_key"),
        ({"duel_key": "BAD KEY"}, "invalid_duel_key"),
        ({"duel_key": "K" * 49}, "invalid_duel_key"),
        ({"market_question": "short"}, "invalid_market_question"),
        ({"market_question": "Question with a\ttab that is not accepted."}, "invalid_market_question"),
        ({"resolution_rules": "short"}, "invalid_resolution_rules"),
        ({"proposal_outcome": "BAD OUTCOME"}, "invalid_proposal_outcome"),
        ({"proposal_outcome": CHALLENGE_OUTCOME}, "outcomes_must_differ"),
        ({"proposal_evidence": "short"}, "invalid_proposal_evidence"),
        ({"challenge_evidence": "short"}, "invalid_challenge_evidence"),
        ({"challenge_evidence": "café " * 20}, "invalid_challenge_evidence"),
    ],
)
def test_invalid_registration_rejected(resolutionduel, direct_vm, overrides, message):
    with direct_vm.expect_revert(message):
        register(resolutionduel, **overrides)


def test_index_and_missing_views_fail(resolutionduel, direct_vm):
    with direct_vm.expect_revert("duel_index_out_of_bounds"):
        resolutionduel.get_duel_id(0)
    with direct_vm.expect_revert("duel_not_registered"):
        resolutionduel.get_duel("missing")
