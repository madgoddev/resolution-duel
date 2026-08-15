"""Canonical ResolutionDuel fixtures and independent fingerprint helper."""

from __future__ import annotations

import hashlib
import json


POLICY_VERSION = 1
REGISTRATION_DATETIME = "2026-08-12T10:00:00Z"
DUEL_KEY = "RED-BLUE-FINAL"
MARKET_QUESTION = "Did Red Team defeat Blue Team by a final score of three to one?"
RESOLUTION_RULES = (
    "Settle YES only when the registered official final-result evidence explicitly "
    "records Red Team 3 and Blue Team 1. Otherwise settle NO; unsupported commentary "
    "does not override the official record."
)
PROPOSAL_OUTCOME = "YES"
PROPOSAL_EVIDENCE = (
    "The registered official tournament result states: Red Team 3, Blue Team 1, "
    "match complete and final."
)
CHALLENGE_OUTCOME = "NO"
CHALLENGE_EVIDENCE = (
    "The registered official tournament result states: Red Team 3, Blue Team 1, "
    "match complete and final. The challenge nevertheless proposes NO."
)

PROPOSAL_WINS = {
    "decision": "PROPOSAL_WINS",
    "settlement_outcome": "YES",
    "proposal_defect_codes": [],
    "challenge_defect_codes": ["RULE_MISMATCH"],
    "uncertainty_codes": [],
}


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def build_fingerprint(
    creator: str,
    *,
    policy_version: int = POLICY_VERSION,
    duel_key: str = DUEL_KEY,
    market_question: str = MARKET_QUESTION,
    resolution_rules: str = RESOLUTION_RULES,
    proposal_outcome: str = PROPOSAL_OUTCOME,
    proposal_evidence: str = PROPOSAL_EVIDENCE,
    challenge_outcome: str = CHALLENGE_OUTCOME,
    challenge_evidence: str = CHALLENGE_EVIDENCE,
) -> str:
    key = duel_key.strip().upper()
    binding = {
        "schema": "resolutionduel/fingerprint/v1",
        "policy_version": policy_version,
        "duel_id": f"{creator.lower()}:{key}",
        "creator": creator.lower(),
        "duel_key": key,
        "market_question": market_question.strip(),
        "resolution_rules": resolution_rules.strip(),
        "proposal_outcome": proposal_outcome.strip().upper(),
        "proposal_evidence": proposal_evidence.strip(),
        "challenge_outcome": challenge_outcome.strip().upper(),
        "challenge_evidence": challenge_evidence.strip(),
    }
    return "sha256:" + hashlib.sha256(canonical_json(binding).encode("ascii")).hexdigest()
