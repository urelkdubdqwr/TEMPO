# TEMPO

Interacting with the Tempo testnet (Moderato) — payments, TIP-20 issuance,
and scheduled on-chain activity. Built as an automation example for
Stripe+Paradigm's payments L1.

## Chain facts
- Testnet "Moderato": chainId 42431, RPC https://rpc.moderato.tempo.xyz (browser UA required)
- Gas paid in stablecoins (TIP-20); default fee token AlphaUSD 0x20c0...0001
- Faucet API: POST https://tempo.xyz/developers/api/faucet {"address":"0x..."}
- TIP-20 Factory 0x20fc...0000 createToken(6 args) — needs gas >= 8M (uses ~2.3M)
- Explorer: https://explore.testnet.tempo.xyz

## On-chain artifacts
- TIP-20 issued from this project: OnarPay USD (OPAY) @ 0x20C00000000000000000000016Fb5370A25543EE
- Scheduled activity: transfers, mints, deploys across a small set of related accounts

## Secrets policy
No keys in this repo, ever. The signer reads key paths outside the project
(0600 perms). State and logs live locally, gitignored.

## Ops
- Runner: `python tempo_daily.py` (idempotent, stateful, self-throttling)
- State: ~/tempo/human_state.json | log: ~/tempo/human.log
