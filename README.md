# tempo-farm — Tempo testnet human-like activity (wallet 227)

Tempo = Stripe+Paradigm L1 for payments ($500M raised, $5B valuation, no token yet).
Airdrop-farming repo. Cron every 30m runs `tempo_human.py` → ~50 tx/day, human pattern.

## Chain facts
- Testnet "Moderato": chainId 42431, RPC https://rpc.moderato.tempo.xyz (needs browser UA)
- Gas paid in stablecoins (TIP-20), default fee token AlphaUSD 0x20c0...0001
- Faucet API: POST https://tempo.xyz/developers/api/faucet {"address":"0x..."} → 4 top-ups
- TIP-20 Factory 0x20fc...0000 createToken(6 args) — needs gas ≥ 8M (uses ~2.3M)
- Explorer: https://explore.testnet.tempo.xyz

## What's done on-chain (wallet 0xeb27...4227)
- faucet claims, AlphaUSD 2M
- send/receive payments across 3 sub-accounts (HD idx1-3, same phrase)
- own stablecoin: OnarPay USD (OPAY) @ 0x20C00000000000000000000016Fb5370A25543EE

## Secrets policy
NEVER commit keys. Signer reads ~/mintbot/key227 (0600, outside repo).
Phrase at ~/mintbot/phrase227. Both excluded via .gitignore + live outside dir.

## Ops
- state: ~/tempo/human_state.json | log: ~/tempo/human.log
- cron job id: b60e7cb9a570 (every 30m, deliver local)
- daily cap 50 tx, hour-weighted idle (mimics WIB sleep 16-21 UTC)

## Disclaimer
Testnet only. No real funds, no private keys in this repo (signer reads paths outside it).
Educational automation example — human-pattern activity on a permissionless testnet.
