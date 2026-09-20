# TEMPO ⚡

[![CI](https://github.com/urelkdubdqwr/TEMPO/actions/workflows/ci.yml/badge.svg)](https://github.com/urelkdubdqwr/TEMPO/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**TEMPO** — automation di chain-nya Stripe, sebelum Stripe-nya ngundang. TIP-20 issuance, stablecoin-gas, scheduled on-chain operations. lahir jam 3 pagi. receipt ada.

> gue automasiin Tempo testnet (Moderato, chainId 42431) — si L1 payment yang didanain Stripe + Paradigm ($500M raise, $5B valuation, blom ada token). lo tau harus ngapain.

## 🚀 30 detik mulai

```bash
pip install -r requirements.txt
python tempo.py status                          # chain health
python tempo.py faucet 0xYOURADDR               # 1M+ test stablecoin, no captcha
python tempo.py balance 0xYOURADDR              # cek saldo
python tempo.py deploy-token ~/my.key "Nama" "SYM"  # issue TIP-20 (gas ≥ 8M!)
```

`~/my.key` = file private key (0600). jangan commit, jangan paste ke chat. even ke agent lo sendiri.

## 📊 On-chain receipts

- TIP-20 **OnarPay USD (OPAY)** @ `0x20C00000000000000000000016Fb5370A25543EE` — 10k minted, ISSUER_ROLE on-chain
- Schedule: transfers, mints, deploys — pola manusia, bukan conveyor belt
- Runner: `python tempo_daily.py` (idempotent, self-throttling, cap harian)

## 🔒 Secrets

No keys in repo. Signer baca file di luar project (0600). Gak ada yang bisa dicuri dari sini selain ide.

📖 Full walkthrough: [TUTORIAL.md](TUTORIAL.md)

---

*Built at **STUDIO PINGGIR KASUR** — berenang di testnet, portofolio di mainnet. 🦂 → 🦅 → 🔥*