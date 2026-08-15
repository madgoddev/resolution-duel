# ResolutionDuel

ResolutionDuel is a standalone, frontend-free GenLayer Intelligent Contract for comparing two competing proposed resolutions of one frozen market question. A creator registers the question, resolution rules, proposal outcome and evidence, and challenger outcome and evidence. GenLayer validators independently adjudicate the same canonical payload and reach exact consensus on a closed decision, settlement outcome, and compact defect masks.

It does **not** run a prediction market, custody stakes, open a live challenge window, or prove that registered evidence is authentic. A market or escrow contract can use the compact `matches_decision(duel_id, independently_precommitted_fingerprint, expected_decision, expected_outcome)` view after finality.

## ABI

Writes: `register_duel(...)`, `adjudicate_duel(duel_id)`.

Views: `build_duel_id`, `get_duel`, `get_duel_count`, `get_duel_id`, `get_audit`, `is_adjudicated`, `matches_decision`, `get_audit_count`, `get_audit_id`, `get_policy`.

Decisions are `PROPOSAL_WINS`, `CHALLENGER_WINS`, `VOID`, or `INDETERMINATE`. Defects and uncertainty use closed bitmasks. The first successful creator-only adjudication is immutable.

## Safe integration

Pin the network, finalized contract address, policy version, and fingerprint computed independently from the intended inputs. Never read the stored fingerprint and echo it back as the expected fingerprint. Use `matches_decision`, not `is_adjudicated`, as the consumer gate. Registered prose is public and untrusted.

## Finalized deployments

- StudioNet: `0xB0f57e58B52e71Fc2F2eEBE875f619a1e31AC08b`.
- Bradbury: `0x92e5D1Fc3A1A401cf44E90D421737ae5F991d28E`.

Both deployment records include finalized deployment, registration, adjudication, exact deployed-source hash, and `LATEST_FINAL` gate readback. See `deployments/` and `AUDIT.md` for the transaction-level evidence and the disclosed non-canonical attempts.

## Local verification

```powershell
python -m pytest -p no:cacheprovider tests/direct
& .\node_modules\.bin\tsc.cmd -p tsconfig.json
```

Five-validator GLSim scenarios live in `tests/integration`. Exact verification evidence is recorded in `AUDIT.md`. Deployment commands and current network status are in `HANDOFF.md`. There is no frontend or application server in this folder.

## License

MIT; see `LICENSE`.
