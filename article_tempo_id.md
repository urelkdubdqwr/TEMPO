# Chain-nya Stripe Digarap Semaleman — No Token, No SDK, No Izin

Tempo. Nama yang mungkin masih asing di TL lo.

Payments L1 dari Stripe + Paradigm. $500M raised, valuasi $5B, investor selevel Sequoia, Ribbit, Thrive. Mainnet udah live Maret kemarin.

Token? Belum ada.

Dan justru itu yang bikin interesting: orang lain skip karena "gak ada token", gue gas karena "belum ada token". Beda kerjaan, beda hasil.

## Malemnya

Tempo itu aneh (dalam arti jenius): docs mereka punya twin `.md` di setiap halaman, plus MCP server resmi di `mcp.tempo.xyz`. They built the chain for agents to build on it. Bukan gimmick — literally ada command `claude mcp add` di halaman utama docs mereka.

Jadi semalem gue garapnya lewat chat window. Bukan IDE. Dan ini yang terjadi, berurutan:

## 1. Faucet tanpa drama

Satu POST. Nggak ada captcha, nggak ada "follow + retweet + join Discord", nggak ada approval 24 jam.

```
curl -X POST tempo.xyz/developers/api/faucet -d '{"address":"0x..."}'
```

→ 4 tx hash. Langsung 2 juta stablecoin testnet di wallet. Gue ngerasa dihina sama mudahnya, tapi ya udah gue ambil.

## 2. Gas pake duit. Beneran duit.

Tempo nggak punya native token. Fee transaksi dipotong dari saldo stablecoin lo. Lo transfer USDC, fee-nya USDC.

Bagian ini yang bikin EVM intuisi lo mati mendadak: tiap tx senyap nabik saldo "duit", bukan "gas token" yang lo topup terpisah. Konsep kecil yang nendang banget kalau lo pikirin: buat user biasa, "harus beli ETH dulu buat transfer USDC" itu Tembok Berlin. Tempo robohkin diam-diam.

## 3. Issue stablecoin sendiri

Factory call, 6 argumen, selesai. Nama terserah, symbol terserah.

Lahir: **OnarPay USD (OPAY)** — nongol di explorer testnet dengan alamat yang bisa gue prediksi SEBELUM deploy (salt deterministic — nice touch).

Di sini gue nemu scar termahal semalem: deploy pertama gue mati, `status 0`, gasUsed mentok PERSIS di angka yang gue kirim. Itu bukan revert logic — itu out of gas. createToken makan ~2.3M gas; kap alokasi lo di bawah itu, chain-nya cuma geleng-geleng.

Rule: deploy ≥ 8M, transfer 500k. Catet, hemat semalem.

## 4. Mint — dan role system yang beneran jalan

`mint()` minta `ISSUER_ROLE`. Lo dapet `DEFAULT_ADMIN_ROLE` pas create. Grant diri sendiri, mint, done. 10.000 OPAY berseliweran.

## 5. Bug yang bikin 99% orang nyerah

Gue transfer OPAY → gagal:

```
insufficient liquidity in FeeAMM pool to swap fee tokens for user token
```

Hening. Error apa itu?

Ternyata ini inti arsitektur mereka: karena gas dibayar pake stablecoin, tiap token baru butuh **lane likuiditas** di FeeAMM — pool yang nge-swap token lo ke fee token validator. Token lo nganggur sebagai fee medium SAMPAI lo sendiri yang provision likuiditasnya.

Fix-nya 2 tx: approve AlphaUSD ke FeeManager, mint liquidity ke pool OPAY.

Hasilnya: transfer yang semalem mati, `status 1`. Token gue sekarang literally bisa dipakai bayar gas di network-nya Stripe.

Itu bukan feature demo. Itu lo jadi **infrastruktur** di chain orang.

## 6. Jangan jadi conveyor belt

Semua aktivitas testnet itu receipt — dan orang-orang sizing activity pakai tool. Wallet yang fire 50 tx interval 30 menit PERSIS itu bukan farmer, itu bot yang males bikin alibi.

Runner gue self-gate: burst → tidur random 25–180 menit → burst lagi, plus window jam aktivitas (gak ada manusia normal trading jam 4 pagi). Angka bulat muncul 35% waktu, karena manusia itu males ngasih desimal.

## Meta-lesson-nya

Tempo ngundang agent secara resmi — docs machine-readable, MCP server, faucet satu request. Mereka nge-build buat cara kerja baru: manusia + AI agent, satu tim, semalem kelar.

Sementara TL masih nungguin "apanih tempo airdrop" — yang nggak akan pernah dijawab sama siapa pun yang udah kerja di atasnya.

Reponya udah bisa lo klon. CLI 6 command — faucet, balance, deploy token, mint, fee liquidity. Gotcha-nya nempel di error message, jadi lo bayar pelajaran pake rasa malu, bukan pake gas:

`github.com/urelkdubdqwr/TEMPO`

4 command, satu stablecoin live yang bisa bayar gas. Nggak nunggu izin, nggak nunggu token.

Token mereka belum ada. Chain-nya nggak nungguin lo siap. 🐟

---

## Tweet pemancing (buat yang males baca article)

```
bikin stablecoin di chain-nya Stripe dalam 4 command.
bisa dipakai bayar gas. live on-chain. tanpa SDK, tanpa nunggu token.
malem ini bisa lo ulang: github.com/urelkdubdqwr/TEMPO
```
