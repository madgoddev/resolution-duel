# Security and limitations

- This is semantic adjudication, not formal proof. Common-mode LLM error and prompt injection remain possible; registered text is repeatedly delimited as untrusted data.
- Exact normalized validator agreement is fail-closed but can reduce liveness on ambiguous evidence.
- Live testing demonstrated that limitation: one Bradbury adjudication reached no majority and stored no state; the unchanged-source retry finalized only after validator rotations. Consumers should distinguish liveness failure from an accepted verdict and require finalized state.
- Evidence authenticity, source ownership, completeness, market custody, and stake/bond rules are outside v1.
- The creator controls the first audit trigger; accepted false results are immutable. Supersede with a new key or policy deployment.
- Consumers must pin chain, address, finalized state, policy, and an independently precommitted fingerprint; never fetch-and-echo it.
- Public storage contains no secrets. ASCII and size bounds reduce confusable and resource risks.
- SHA-256 collision resistance and the pinned GenVM runner are trust assumptions.

The contract returns a bounded comparison, not an instruction to transfer funds. A downstream market defines its own settlement authority and appeals.
