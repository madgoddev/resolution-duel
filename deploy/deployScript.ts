import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";

import {
  type CalldataEncodable,
  type DecodedDeployData,
  ExecutionResult,
  type GenLayerChain,
  type GenLayerClient,
  type TransactionHash,
  TransactionHashVariant,
  TransactionStatus,
} from "genlayer-js/types";

const SOURCE_SHA256 = "AC3B1069E97B88772DACDD5AD428946A173C234C649D61F1521299880FBAF9CE";
const STUDIO_CHAIN_ID = "61999";
const BRADBURY_CHAIN_ID = "4221";
const STUDIO_HOST = "studio.genlayer.com";
const BRADBURY_HOST = "rpc-bradbury.genlayer.com";
const DUEL_SCHEMA = "resolutionduel/duel/v1";
const AUDIT_SCHEMA = "resolutionduel/audit/v1";
const FINGERPRINT_SCHEMA = "resolutionduel/fingerprint/v1";

const FIXTURE = {
  marketQuestion: "Did Red Team defeat Blue Team by a final score of three to one?",
  resolutionRules:
    "Settle YES only when the registered official final-result evidence explicitly records Red Team 3 and Blue Team 1. Otherwise settle NO; unsupported commentary does not override the official record.",
  proposalOutcome: "YES",
  proposalEvidence:
    "The registered official tournament result states: Red Team 3, Blue Team 1, match complete and final.",
  challengeOutcome: "NO",
  challengeEvidence:
    "The registered official tournament result states: Red Team 3, Blue Team 1, match complete and final. The challenge nevertheless proposes NO.",
} as const;

type Stage = "studionet" | "bradbury";
type Operation = "deploy-finalized" | "submit-bradbury" | "smoke-studionet" | "smoke-bradbury";
type Receipt = {
  status?: string | number; statusName?: string; status_name?: string;
  result?: string | number; resultName?: string; result_name?: string;
  txExecutionResult?: number; txExecutionResultName?: string; tx_execution_result?: number; tx_execution_result_name?: string;
  data?: { contract_address?: string }; to_address?: string; txDataDecoded?: DecodedDeployData;
  consensus_data?: { leader_receipt?: Array<{ mode?: string; execution_result?: string; genvm_result?: { raw_error?: unknown }; result?: { status?: string } }> };
};

function envStage(): Stage {
  const value = process.env.RESOLUTIONDUEL_DEPLOY_STAGE?.trim().toLowerCase();
  if (value !== "studionet" && value !== "bradbury") throw new Error("RESOLUTIONDUEL_DEPLOY_STAGE must be studionet or bradbury");
  return value;
}

function envOperation(): Operation {
  const value = process.env.RESOLUTIONDUEL_OPERATION?.trim().toLowerCase();
  if (value !== "deploy-finalized" && value !== "submit-bradbury" && value !== "smoke-studionet" && value !== "smoke-bradbury") {
    throw new Error("RESOLUTIONDUEL_OPERATION is invalid");
  }
  return value;
}

function positive(name: string, fallback?: number): number {
  const value = Number(process.env[name]?.trim() || fallback);
  if (!Number.isSafeInteger(value) || value <= 0) throw new Error(`${name} must be a positive integer`);
  return value;
}

function contractAddress(): `0x${string}` {
  const value = process.env.RESOLUTIONDUEL_CONTRACT_ADDRESS?.trim();
  if (!value || !/^0x[0-9a-fA-F]{40}$/.test(value)) throw new Error("RESOLUTIONDUEL_CONTRACT_ADDRESS is invalid");
  return value as `0x${string}`;
}

function canonicalAddress(value: unknown, label: string): string {
  if (typeof value !== "string" || !/^0x[0-9a-fA-F]{40}$/.test(value)) throw new Error(`${label} is not an address`);
  return value.toLowerCase();
}

function txHash(value: unknown): TransactionHash {
  if (typeof value !== "string" || !/^0x[0-9a-fA-F]{64}$/.test(value)) throw new Error("SDK did not return a canonical transaction hash");
  return value as TransactionHash;
}

function record(value: unknown, label: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label} did not return an object`);
  return value as Record<string, unknown>;
}

function uint(value: unknown, label: string): number {
  if (typeof value === "number" && Number.isSafeInteger(value) && value >= 0) return value;
  if (typeof value === "bigint" && value >= 0n && value <= BigInt(Number.MAX_SAFE_INTEGER)) return Number(value);
  if (typeof value === "string" && /^(0|[1-9][0-9]*)$/.test(value) && BigInt(value) <= BigInt(Number.MAX_SAFE_INTEGER)) return Number(value);
  throw new Error(`${label} is not a safe unsigned integer`);
}

function stableJson(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (typeof value === "object") {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(",")}}`;
  }
  throw new Error("unsupported fingerprint value");
}

function expectedFingerprint(policyVersion: number, creator: string, key: string): string {
  const normalizedCreator = canonicalAddress(creator, "creator");
  const binding = {
    schema: FINGERPRINT_SCHEMA,
    policy_version: policyVersion,
    duel_id: `${normalizedCreator}:${key}`,
    creator: normalizedCreator,
    duel_key: key,
    market_question: FIXTURE.marketQuestion,
    resolution_rules: FIXTURE.resolutionRules,
    proposal_outcome: FIXTURE.proposalOutcome,
    proposal_evidence: FIXTURE.proposalEvidence,
    challenge_outcome: FIXTURE.challengeOutcome,
    challenge_evidence: FIXTURE.challengeEvidence,
  };
  return `sha256:${createHash("sha256").update(stableJson(binding), "ascii").digest("hex")}`;
}

function alter(fingerprint: string): string { return `${fingerprint.slice(0, -1)}${fingerprint.endsWith("0") ? "1" : "0"}`; }

function localSource(): { code: Uint8Array; hash: string } {
  const code = new Uint8Array(readFileSync(path.resolve(process.cwd(), "contracts/resolution_duel.py")));
  const hash = createHash("sha256").update(code).digest("hex").toUpperCase();
  if (hash !== SOURCE_SHA256) throw new Error(`Refusing unaudited source ${hash}`);
  return { code, hash };
}

async function deployedSource(client: GenLayerClient<GenLayerChain>, target: `0x${string}`): Promise<string> {
  const code = await client.getContractCode(target);
  if (typeof code !== "string" || code.length === 0) throw new Error("deployed source was unavailable");
  const hash = createHash("sha256").update(code, "utf8").digest("hex").toUpperCase();
  if (hash !== SOURCE_SHA256) throw new Error(`deployed source mismatch ${hash}`);
  return hash;
}

async function readFinal(client: GenLayerClient<GenLayerChain>, address: `0x${string}`, functionName: string, args: CalldataEncodable[] = []): Promise<unknown> {
  return client.readContract({ address, functionName, args, transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
}

function agreed(receipt: Receipt): boolean {
  const name = receipt.resultName ?? receipt.result_name;
  return name !== undefined ? name === "AGREE" || name === "MAJORITY_AGREE" : Number(receipt.result) === 1 || Number(receipt.result) === 6;
}

function succeeded(receipt: Receipt): boolean {
  const name = receipt.txExecutionResultName ?? receipt.tx_execution_result_name;
  if (name !== undefined) return name === ExecutionResult.FINISHED_WITH_RETURN;
  const number = receipt.txExecutionResult ?? receipt.tx_execution_result;
  if (number !== undefined) return Number(number) === 1;
  const leader = receipt.consensus_data?.leader_receipt?.find((item) => item.mode === "leader");
  return leader?.execution_result === "SUCCESS" && leader.genvm_result?.raw_error == null && leader.result?.status === "return";
}

function status(receipt: Receipt, wanted: "FINALIZED" | "ACCEPTED"): boolean {
  const code = wanted === "FINALIZED" ? 7 : 5;
  const name = wanted === "FINALIZED" ? TransactionStatus.FINALIZED : TransactionStatus.ACCEPTED;
  return receipt.statusName === name || receipt.status_name === name || receipt.status === name || Number(receipt.status) === code;
}

async function waitReceipt(client: GenLayerClient<GenLayerChain>, hash: TransactionHash, wanted: "FINALIZED" | "ACCEPTED", retries: number, interval: number): Promise<Receipt> {
  const receipt = await client.waitForTransactionReceipt({ hash, status: wanted === "FINALIZED" ? TransactionStatus.FINALIZED : TransactionStatus.ACCEPTED, retries, interval }) as unknown as Receipt;
  if (!status(receipt, wanted) || !agreed(receipt) || !succeeded(receipt)) throw new Error(`${wanted} receipt did not agree and finish with return`);
  return receipt;
}

function receiptAddress(receipt: Receipt): `0x${string}` {
  const value = receipt.data?.contract_address ?? receipt.txDataDecoded?.contractAddress ?? receipt.to_address;
  canonicalAddress(value, "receipt contract address");
  return value as `0x${string}`;
}

async function verifyPolicy(client: GenLayerClient<GenLayerChain>, target: `0x${string}`, policyVersion: number, signer: string): Promise<void> {
  const value = record(await readFinal(client, target, "get_policy"), "policy");
  if (canonicalAddress(value.owner, "policy owner") !== canonicalAddress(signer, "signer") ||
      uint(value.policy_version, "policy version") !== policyVersion || value.purpose !== "BOUNDED_COMPETING_MARKET_RESOLUTION_ADJUDICATION" ||
      value.duel_schema !== DUEL_SCHEMA || value.audit_schema !== AUDIT_SCHEMA || value.fingerprint_schema !== FINGERPRINT_SCHEMA ||
      value.creator_only_adjudication !== true || value.first_successful_audit_immutable !== true || value.external_evidence_authenticity_verified !== false) {
    throw new Error("policy read-back failed");
  }
}

async function smoke(client: GenLayerClient<GenLayerChain>, stage: Stage, policyVersion: number, retries: number, interval: number) {
  const target = contractAddress();
  const signer = canonicalAddress(client.account?.address, "active signer");
  localSource();
  const sourceHash = await deployedSource(client, target);
  await verifyPolicy(client, target, policyVersion, signer);
  const key = stage === "studionet" ? "STUDIO-RULE-DUEL-20260812" : "BRADBURY-RULE-DUEL-20260812";
  const duelId = `${signer}:${key}`;
  const fingerprint = expectedFingerprint(policyVersion, signer, key);
  const resume = process.env.RESOLUTIONDUEL_SMOKE_RESUME === "1";
  if (resume && stage !== "bradbury") throw new Error("smoke resume is restricted to Bradbury recovery");
  let registration: TransactionHash | undefined;
  if (!resume) {
    registration = txHash(await client.writeContract({ address: target, functionName: "register_duel", args: [key, FIXTURE.marketQuestion, FIXTURE.resolutionRules, FIXTURE.proposalOutcome, FIXTURE.proposalEvidence, FIXTURE.challengeOutcome, FIXTURE.challengeEvidence], value: 0n }));
    console.log(`Smoke registration transaction: ${registration}`);
    await waitReceipt(client, registration, "FINALIZED", retries, interval);
  } else {
    console.log("Smoke registration: RESUME_EXISTING_FINALIZED");
  }
  const stored = record(await readFinal(client, target, "get_duel", [duelId]), "duel");
  if (stored.schema !== DUEL_SCHEMA || stored.duel_id !== duelId || stored.duel_fingerprint !== fingerprint || stored.duel_key !== key || canonicalAddress(stored.creator, "stored creator") !== signer) throw new Error("registration read-back failed");
  let audit: TransactionHash | undefined;
  if (await readFinal(client, target, "is_adjudicated", [duelId]) !== true) {
    audit = txHash(await client.writeContract({ address: target, functionName: "adjudicate_duel", args: [duelId], value: 0n }));
    console.log(`Smoke audit transaction: ${audit}`);
    await waitReceipt(client, audit, "FINALIZED", retries, interval);
  }
  const result = record(await readFinal(client, target, "get_audit", [duelId]), "audit");
  const exact = await readFinal(client, target, "matches_decision", [duelId, fingerprint, "PROPOSAL_WINS", "YES"]);
  const changed = await readFinal(client, target, "matches_decision", [duelId, alter(fingerprint), "PROPOSAL_WINS", "YES"]);
  if (result.schema !== AUDIT_SCHEMA || result.duel_fingerprint !== fingerprint || result.decision !== "PROPOSAL_WINS" || result.settlement_outcome !== "YES" ||
      uint(result.proposal_defect_mask, "proposal defect mask") !== 0 || uint(result.challenge_defect_mask, "challenge defect mask") !== 1 || uint(result.uncertainty_mask, "uncertainty mask") !== 0 || exact !== true || changed !== false) {
    throw new Error("audit verdict/mask/gate read-back failed");
  }
  console.log(`Smoke ID: ${duelId}`);
  console.log(`Smoke fingerprint: ${fingerprint}`);
  console.log("Smoke decision: PROPOSAL_WINS / YES");
  console.log("Exact gate: true; altered gate: false");
  return { target, sourceHash, registration, audit, duelId, fingerprint, decision: result.decision, exact, changed };
}

export default async function main(client: GenLayerClient<GenLayerChain>) {
  const stage = envStage();
  const operation = envOperation();
  if ((operation === "deploy-finalized" || operation === "smoke-studionet") !== (stage === "studionet")) {
    if (operation !== "submit-bradbury" && operation !== "smoke-bradbury") throw new Error("operation/stage mismatch");
  }
  if ((operation === "submit-bradbury" || operation === "smoke-bradbury") && stage !== "bradbury") throw new Error("operation/stage mismatch");
  const expectedChain = stage === "studionet" ? STUDIO_CHAIN_ID : BRADBURY_CHAIN_ID;
  const expectedHost = stage === "studionet" ? STUDIO_HOST : BRADBURY_HOST;
  const chainId = String((client.chain as GenLayerChain).id);
  const rpc = (client.chain as GenLayerChain).rpcUrls.default.http[0] ?? "";
  const host = new URL(rpc).hostname.toLowerCase();
  if (chainId !== expectedChain || host !== expectedHost) throw new Error(`network guard failed: ${chainId}/${host}`);
  const policyVersion = positive("RESOLUTIONDUEL_POLICY_VERSION");
  const retries = positive("RESOLUTIONDUEL_RECEIPT_RETRIES", 1440);
  const interval = positive("RESOLUTIONDUEL_RECEIPT_INTERVAL_MS", 5000);
  if (retries > 10000 || interval < 1000 || interval > 60000) throw new Error("receipt settings outside guarded limits");
  if (operation.startsWith("smoke-")) return smoke(client, stage, policyVersion, retries, interval);
  const { code, hash: sourceHash } = localSource();
  const hash = txHash(await client.deployContract({ code, args: [policyVersion] }));
  console.log(`Canonical GenLayer transaction: ${hash}`);
  console.log(`Source SHA-256: ${sourceHash}`);
  if (operation === "submit-bradbury") {
    const receipt = await waitReceipt(client, hash, "ACCEPTED", retries, interval);
    const target = receiptAddress(receipt);
    console.log(`Provisional contract address: ${target}`);
    console.log("Finality: WAITING");
    return { hash, target, sourceHash, finality: "WAITING" };
  }
  const receipt = await waitReceipt(client, hash, "FINALIZED", retries, interval);
  const target = receiptAddress(receipt);
  const deployedSourceHash = await deployedSource(client, target);
  await verifyPolicy(client, target, policyVersion, client.account?.address ?? "");
  console.log(`ResolutionDuel deployed at ${target}`);
  console.log("Finality: FINALIZED");
  return { hash, target, sourceHash, deployedSourceHash, policyVersion, finality: "FINALIZED" };
}
