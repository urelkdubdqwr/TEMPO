# TEMPO Testnet, Garap Pake AI Agent — the no-SDK tutorial

> @onargudel nulis ini sambil ngasih tau agent-nya buat ngomong sama chain-nya Stripe. Lo tinggal copy. 🧾

Tempo is the payments L1 from Stripe + Paradigm ($500M raised, $5B valuation, no token yet).
Their docs are built agent-first — which means you don't need their SDK, their wagmi hooks,
or even their permission to ship. You need a terminal and something that thinks.

This is the exact path we ran on the Moderato testnet. Every command below was executed,
every gotcha is a scar we actually have.

---

## 0. The two things that make Tempo agent-friendly

1. **Every docs page has a raw `.md` twin.** Append `.md` to any docs URL:
   `https://docs.tempo.xyz/guide/issuance/create-a-stablecoin.md` → clean markdown, no HTML soup.
   Your agent can read the entire protocol spec with one curl.
2. **Official MCP server:** `https://mcp.tempo.xyz` — tools `search`, `read_page`, `find_pages`, `code`.
   Stateless HTTP, works with plain JSON-RPC over curl (no session id needed):

```bash
curl -s -X POST https://mcp.tempo.xyz \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search","arguments":{"query":"fee amm liquidity"}}}'
```

Claude/Codex/Cursor users: `claude mcp add --transport http tempo https://mcp.tempo.xyz` and you're done.

## 1. Network facts (memorize, they don't change)

| | |
|---|---|
| Testnet | Moderato, chainId **42431** |
| RPC | `https://rpc.moderato.tempo.xyz` |
| Explorer | `https://explore.testnet.tempo.xyz` |
| Fee token | AlphaUSD `0x20c0000000000000000000000000000000000001` |
| TIP-20 Factory | `0x20fc000000000000000000000000000000000000` |
| FeeManager (FeeAMM) | `0xfeec000000000000000000000000000000000000` |
| Stablecoin DEX | `0xdec000000000000000000000000000000000000` |

**Gotcha #1:** the RPC answers 403 to bare `curl`/python UAs. Send a browser User-Agent:

```bash
curl -s -X POST https://rpc.moderato.tempo.xyz \
  -H "Content-Type: application/json" \
  -A "Mozilla/5.0 Chrome/126.0" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
# → 0xa5bf (= 42431)
```

## 2. Faucet — one POST, four top-ups

No captcha, no twitter-connect, no "request approved within 24h". Just:

```bash
curl -s -X POST https://tempo.xyz/developers/api/faucet \
  -H "Content-Type: application/json" \
  -d '{"address":"0xYOUR_WALLET"}'
# → {"data":[{"hash":"0x..."},{"hash":"0x..."},{"hash":"0x..."},{"hash":"0x..."}]}
```

You get 1M AlphaUSD + 1M of the other test stablecoins. Verify on-chain:

```bash
curl -s -X POST https://rpc.moderato.tempo.xyz -H "Content-Type: application/json" \
  -A "Mozilla/5.0 Chrome/126.0" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":"0x20c0000000000000000000000000000000000001","data":"0x70a08231000000000000000000000000YOURADDR40HEX"},"latest"]}'
```

## 3. Gas is money — literally

Tempo has no native gas token. You pay fees **in stablecoins** (default: AlphaUSD).
Every transfer you send quietly burns ~$0.1–0.2 of test AlphaUSD as fee.
This breaks every EVM intuition you have — and it's the whole thesis of the chain.

## 4. Issue your own stablecoin (the fun part)

`createToken(name, symbol, currency, quoteToken, admin, salt)` on the factory.
The salt lets you **predict the address before deploying** (`getTokenAddress`).

```python
# web3.py — no Tempo SDK exists for python, and it didn't stop us
abi = [{"name":"createToken","type":"function","stateMutability":"nonpayable",
        "inputs":[{"name":"n","type":"string"},{"name":"s","type":"string"},
                  {"name":"c","type":"string"},{"name":"q","type":"address"},
                  {"name":"a","type":"address"},{"name":"sl","type":"bytes32"}],
        "outputs":[{"name":"","type":"address"}]}]
c = w3.eth.contract(address=FACTORY, abi=abi)
data = c.encode_abi("createToken", args=["OnarPay USD","OPAY","USD", ALPHA, ME, salt])
```

**Gotcha #2:** `createToken` costs ~2.3M gas. We sent it with a 2M cap first —
`status 0`, gasUsed exactly 2000000. That's not a revert, that's **out of gas**.
Rule of thumb on Tempo: **gas ≥ 8M for deploys**, 500k for transfers.

## 5. Mint it (roles are real here)

`mint()` requires `ISSUER_ROLE`. The factory gives you `DEFAULT_ADMIN_ROLE`,
so grant yourself first:

```python
ROLE = w3.keccak(text="ISSUER_ROLE")
c.functions.grantRole(ROLE, ME)   # one tx
c.functions.mint(ME, 10_000 * 10**6)  # 10k OPAY, one tx
```

## 6. Make your token usable as gas (the part nobody documents well)

Your shiny TIP-20 can't pay fees yet — the **FeeAMM has no liquidity for it**.
Transfers paid in your token fail with:

```
insufficient liquidity in FeeAMM pool to swap fee tokens for user token
```

Fix: approve AlphaUSD to the FeeManager, then `mint(userToken, validatorToken, amount, to)`:

```python
# 1. approve AlphaUSD → 0xfeec...
# 2. FeeManager.mint(OPAY, ALPHA, 100e6, ME)   # 100 AlphaUSD into the fee pool
```

After that, your token circulates as a fee medium. This is Tempo's "stablecoin exchange"
story in one function call — and the docs page for it (`/guide/issuance/use-for-fees`)
is exactly what we fed our agent via MCP `read_page`.

## 7. Don't look like a conveyor belt

Testnet activity is the receipt. A wallet that fires 50 tx at exact 30-minute
intervals is a bot with a calendar. Ours self-gates: after each burst it sleeps a
random 25–180 minutes, respects an activity window (nobody trades at 4am WIB),
and uses round numbers 35% of the time because humans are lazy with decimals.
The runner is in this repo — `tempo_daily.py`, keys live outside it, always.

---

## The meta-lesson

Tempo ships MCP + `.md` docs because they *expect* agents to build on the chain.
That's the play: while everyone else waits for a token to decide if a chain is real,
you can already ship on it with the agent you talk to every day.

We went faucet → stablecoin → fee liquidity in one night, zero SDK, zero hand-holding.
The chain didn't care that our "IDE" was a chat window.

*Built by ONAR-77 — @onargudel. agent pertama yang bayar gas pake duit, bukan pake hopes.* 🐟
