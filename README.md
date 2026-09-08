# TEMPO

> @onargudel udah muter-muter di chain-nya Stripe sebelum Stripe-nya ngundang lo. 🧾

Interacting with the Tempo testnet (Moderato) — payments, TIP-20 issuance,
and scheduled on-chain activity. Built as an automation example for
Stripe+Paradigm's payments L1 ($500M raised, $5B valuation, no token yet —
elo tau harus ngapain).

📖 **Full walkthrough: [TUTORIAL.md](TUTORIAL.md)** — dari faucet sampe token lo bisa dipakai bayar gas, pake AI agent, zero SDK.

## Quickstart (git clone ini, 30 detik)

```bash
git clone https://github.com/urelkdubdqwr/TEMPO.git && cd TEMPO
pip install -r requirements.txt

python tempo.py status                                  # chain health
python tempo.py faucet 0xYOURADDR                       # 1M+ test stablecoins, no captcha
python tempo.py balance 0xYOURADDR                      # cek isi
python tempo.py deploy-token ~/my.key "My Name" "SYM"   # issue TIP-20 sendiri (gas 8M!)
python tempo.py mint ~/my.key 0xTOKEN 10000             # grant ISSUER_ROLE + mint
python tempo.py fee-liq ~/my.key 0xTOKEN                # lane FeeAMM: token lo bisa buat bayar gas
```

`~/my.key` = file teks berisi private key (0600). Jangan commit, jangan paste ke chat mana pun termasuk ke agent lo sendiri — kasih path-nya.

## Chain facts (bukan karangan, semua bisa lo verify)

- Testnet "Moderato": chainId **42431** (mainnet 4217), RPC `https://rpc.moderato.tempo.xyz` (browser UA required, node-nya galak sama curl telanjang)
- Gas dibayar pake stablecoin (TIP-20) — default fee token AlphaUSD `0x20c0...0001`. Iya, gas fee pake duit, bukan token native. Waras.
- Faucet API: `POST https://tempo.xyz/developers/api/faucet {"address":"0x..."}` → 4 top-up sekaligus
- TIP-20 Factory `0x20fc...0000` `createToken(6 args)` — butuh gas ≥ 8M (real usage 2.3M, gue pernah mati di 2M, jangan kayak gue)
- Explorer: `https://explore.testnet.tempo.xyz`

## On-chain artifacts

- TIP-20 yang lahir dari project ini: **OnarPay USD (OPAY)** @ `0x20C00000000000000000000016Fb5370A25543EE` — 10k minted, ISSUER_ROLE on-chain, bukan cuma wacana
- Scheduled activity: transfers, mints, deploys across a small set of related accounts — polanya manusia, bukan conveyor belt

## Secrets policy

No keys in this repo, ever. Signer baca path di luar project (0600).
Private key nggak pernah nongol di sini — yang baca cuma bisa ngiler, bukan nyolong.

## Ops

- Runner: `python tempo_daily.py` (idempotent, stateful, self-throttling)
- State: `~/tempo/human_state.json` | log: `~/tempo/human.log`
- Ritme: tick tiap 30 menit, burst acak, cap harian — mesinnya lebih disiplin dari gue bangun subuh

---

*Built by ONAR-77 — @onargudel. berenang di testnet, portofolio di mainnet.* 🐟
