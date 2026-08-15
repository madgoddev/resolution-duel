# Audit receipt

Frozen local candidate: 33,067 bytes; SHA-256 `AC3B1069E97B88772DACDD5AD428946A173C234C649D61F1521299880FBAF9CE`.

- GenVM lint/semantic validation: pass, 12 methods (10 view/2 write), one constructor.
- Strict typecheck: zero diagnostics.
- Direct mode: 54/54 passed.
- Five-validator GLSim: 4/4 passed.
- Deploy-helper TypeScript: zero diagnostics.
- Production dependency audit: no known pnpm vulnerabilities; Python dependency check passed.

The matrix covers canonical/idempotent registration, changed-core rejection, fixed fingerprint binding, exact decision/mask derivation, malformed output/no state, independent validator disagreement/error, state corruption, and exact/altered fingerprint gates.

## StudioNet live evidence

- Contract `0xB0f57e58B52e71Fc2F2eEBE875f619a1e31AC08b`; deployment `0xf93e5e69a012777a91ba4130b4153872b70213b0939da85ec0a8248ebf03481d`, FINALIZED/AGREE/FINISHED_WITH_RETURN.
- Independently fetched code is byte-identical to the 33,067-byte frozen source and hash above.
- Canonical smoke registration `0x8e87b3c48a5628c9267d52b86c65c731c17b5bb024bf0bfdd29ebe1c1110051d` and adjudication `0xed429fd61cb9874adc024d1c00362b86e0d4df57e15d9c46a95e98a69253c412` finalized successfully.
- Final state: `PROPOSAL_WINS`, settlement `YES`, masks `0/1/0`, fingerprint `sha256:c8f4445464e0bf95515460cdf113b494ca708b753ec8842342869419ede8cca5`; exact gate true and altered gate false.
- A prior deliberately harder smoke (`0x734107999f2089f42cbd8e3f388bf6475bcd2f2f6d5f3c7853145f97a0fc288f` / `0x00fee7159b59a0341c0186c0fb388dd3e57abf1b485d2041f736384c5de83d4a`) reached `MAJORITY_DISAGREE` because validators chose overlapping defect labels differently. It stored no audit and is not canonical release evidence. This is retained as a liveness limitation, not hidden.

## Bradbury live evidence

- Contract `0x92e5D1Fc3A1A401cf44E90D421737ae5F991d28E`; deployment `0x4cc6a9ac2f01621a8af31a25910e01441ac86e7f1a8e9c06424194855abbd696`, FINALIZED/AGREE/FINISHED_WITH_RETURN.
- An independent `gen_getContractCode` read returned exactly 33,067 UTF-8 bytes with SHA-256 `AC3B1069E97B88772DACDD5AD428946A173C234C649D61F1521299880FBAF9CE`, byte-identical to the frozen local source.
- Canonical registration `0x66b8c9d23fdf2a54a6ecd4f1ba6631fb7d874f1a5397d20a07b66b433ddbaa4b` is FINALIZED/AGREE/FINISHED_WITH_RETURN.
- Before that registration, EVM transaction `0x0c5aadf84f577cfa97700c3a16a4a0ec097c2880e5ea2884dbd38d2e4b1d7adf` reverted with receipt status `0x0`. It produced no canonical GenLayer transaction or contract state and is not release evidence.
- First adjudication `0x0908860c02765903b0e116faed796f1fc7dc90b1e5f039fa96a6473b84965de1` ended UNDETERMINED/NO_MAJORITY/FINISHED_WITH_RETURN after validators produced inconsistent normalizations. It stored no audit and is not canonical release evidence.
- Unchanged-source retry `0x7aa4b61ea3d3223421a0e1f105bebfddeddf851fa1bd705f46a30578afdc9c7b` is FINALIZED/AGREE/FINISHED_WITH_RETURN. The retry required rotations before the final agreeing round; this is retained as liveness evidence rather than hidden.
- `LATEST_FINAL` readback: `PROPOSAL_WINS`, settlement `YES`, masks `0/1/0`, fingerprint `sha256:2151bbb3dbf02286cd29c0f10060491eefedfb9456708d1df1390b68d27c8d6b`; exact gate true and altered gate false.
