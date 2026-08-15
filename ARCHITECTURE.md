# Architecture

`register_duel` normalizes bounded ASCII inputs, derives a creator-scoped ID, hashes a canonical semantic core, and stores one immutable record. Idempotent identical registration returns the existing ID; changed content under the same key fails.

`adjudicate_duel` validates and recomputes stored identity/fingerprint before nondeterminism. The leader and every validator independently evaluate only the semantic projection. Strict JSON is normalized to decision/outcome plus three masks; malformed, unknown, or substantively different output fails consensus. A successful creator-only write stores a closed audit exactly once.

`matches_decision` revalidates both stored records, schemas, ID, policy, and fingerprint before comparing the expected decision and outcome. Enumeration and status views are informational only.
