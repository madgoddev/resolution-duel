# Handoff

Status: local build/audit, StudioNet deployment/smoke, and Bradbury deployment/smoke are complete and finalized. StudioNet is `0xB0f57e58B52e71Fc2F2eEBE875f619a1e31AC08b`; Bradbury is `0x92e5D1Fc3A1A401cf44E90D421737ae5F991d28E`. Exact network evidence is in `deployments/` and `AUDIT.md`.

Use the project-local CLI only. Set and verify the network immediately before every operation. `deploy-finalized` is StudioNet-only; `submit-bradbury` reports ACCEPTED then returns so read-only monitoring can continue. The recorded deployments must not be resubmitted.

```powershell
$env:RESOLUTIONDUEL_DEPLOY_STAGE='studionet'
$env:RESOLUTIONDUEL_OPERATION='deploy-finalized'
$env:RESOLUTIONDUEL_POLICY_VERSION='1'
pnpm run deploy
```

For a new deployment smoke, set `RESOLUTIONDUEL_CONTRACT_ADDRESS` and select `smoke-studionet` or `smoke-bradbury`. Do not persist wallet passwords. `RESOLUTIONDUEL_SMOKE_RESUME=1` is a Bradbury-only recovery mode: use it only after independently proving that the pinned registration is finalized and exact; it skips duplicate registration and submits an adjudication only if final state is absent. It is not a general shortcut.
