"""Five-validator GLSim tests for ResolutionDuel."""

from __future__ import annotations

import json
from pathlib import Path

from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_failed, tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address

from fixtures.duels import (
    CHALLENGE_EVIDENCE,
    CHALLENGE_OUTCOME,
    DUEL_KEY,
    MARKET_QUESTION,
    POLICY_VERSION,
    PROPOSAL_EVIDENCE,
    PROPOSAL_OUTCOME,
    PROPOSAL_WINS,
    REGISTRATION_DATETIME,
    RESOLUTION_RULES,
)

PROMPT_KEY = "independent prediction-market resolution adjudicator"


def context(response):
    validators = get_validator_factory().batch_create_mock_validators(
        5, mock_llm_response={"nondet_exec_prompt": {PROMPT_KEY: json.dumps(response)}}
    )
    return {
        "validators": [validator.to_dict() for validator in validators],
        "genvm_datetime": REGISTRATION_DATETIME,
    }


def deploy():
    path = Path(__file__).resolve().parents[2] / "contracts" / "resolution_duel.py"
    factory = get_contract_factory(contract_file_path=path)
    receipt = factory.deploy_contract_tx(
        args=[POLICY_VERSION], wait_transaction_status=TransactionStatus.FINALIZED
    )
    assert tx_execution_succeeded(receipt)
    return factory.build_contract(extract_contract_address(receipt))


def register(contract, key=DUEL_KEY):
    receipt = contract.register_duel(
        args=[
            key,
            MARKET_QUESTION,
            RESOLUTION_RULES,
            PROPOSAL_OUTCOME,
            PROPOSAL_EVIDENCE,
            CHALLENGE_OUTCOME,
            CHALLENGE_EVIDENCE,
        ]
    ).transact(wait_transaction_status=TransactionStatus.FINALIZED)
    assert tx_execution_succeeded(receipt)
    return contract.get_duel_id(args=[0]).call()


def adjudicate(contract, duel_id, response):
    return contract.adjudicate_duel(args=[duel_id]).transact(
        transaction_context=context(response),
        wait_transaction_status=TransactionStatus.FINALIZED,
    )


def test_glsim_proposal_wins_and_gate():
    contract = deploy()
    duel_id = register(contract)
    receipt = adjudicate(contract, duel_id, PROPOSAL_WINS)
    assert tx_execution_succeeded(receipt)
    duel = contract.get_duel(args=[duel_id]).call()
    audit = contract.get_audit(args=[duel_id]).call()
    assert audit["decision"] == "PROPOSAL_WINS"
    assert contract.matches_decision(
        args=[duel_id, duel["duel_fingerprint"], "PROPOSAL_WINS", "YES"]
    ).call() is True


def test_glsim_challenger_and_indeterminate():
    contract = deploy()
    duel_id = register(contract, "CHALLENGER")
    response = {
        "decision": "CHALLENGER_WINS",
        "settlement_outcome": "NO",
        "proposal_defect_codes": ["RULE_MISMATCH"],
        "challenge_defect_codes": [],
        "uncertainty_codes": [],
    }
    assert tx_execution_succeeded(adjudicate(contract, duel_id, response))
    assert contract.get_audit(args=[duel_id]).call()["decision"] == "CHALLENGER_WINS"


def test_glsim_malformed_fails_without_state():
    contract = deploy()
    duel_id = register(contract)
    receipt = adjudicate(contract, duel_id, {**PROPOSAL_WINS, "extra": True})
    assert tx_execution_failed(receipt)
    assert contract.is_adjudicated(args=[duel_id]).call() is False


def test_glsim_immutable_second_audit_fails():
    contract = deploy()
    duel_id = register(contract)
    assert tx_execution_succeeded(adjudicate(contract, duel_id, PROPOSAL_WINS))
    assert tx_execution_failed(adjudicate(contract, duel_id, PROPOSAL_WINS))
