#!/usr/bin/env python3
"""TEMPO — scheduled on-chain activity for a Tempo testnet account.
Self-throttling runner: each tick decides whether to act (activity windows).
Actions: send/receive payments, TIP-20 issuance + mint, contract deploys,
faucet top-ups for related accounts.
Never prints secrets. State: ~/tempo/human_state.json
"""
import json, os, random, subprocess, time
from datetime import datetime, timezone

RPC = "https://rpc.moderato.tempo.xyz"
FAUCET_API = "https://tempo.xyz/developers/api/faucet"
CHAIN_ID = 42431
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"
KEY227 = os.path.expanduser("~/mintbot/key227")
PHRASE = os.path.expanduser("~/mintbot/phrase227")
STATE = os.path.expanduser("~/tempo/human_state.json")
LOG = os.path.expanduser("~/tempo/human.log")
ALPHA = "0x20c0000000000000000000000000000000000001"
USD0  = "0x20c0000000000000000000000000000000000000"
FACTORY = "0x20fc000000000000000000000000000000000000"
DAILY_TARGET = 50

def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    with open(LOG, "a") as f: f.write(line + "\n")
    print(line)

def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"day": "", "count": 0, "partners": [], "token": "", "deploys": 0}

def save(s): json.dump(s, open(STATE, "w"), indent=1)

def rpc(method, params):
    out = subprocess.run(["curl","-s","-m","15","-X","POST",RPC,"-H","Content-Type: application/json",
        "-A",UA,"--data", json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params})],
        capture_output=True,text=True,timeout=25).stdout
    return json.loads(out)

def faucet(addr):
    subprocess.run(["curl","-s","-m","15","-X","POST",FAUCET_API,"-H","Content-Type: application/json",
        "-A",UA,"--data", json.dumps({"address": addr.lower()})], capture_output=True, timeout=25)

def tip20_balance(token, who):
    data = "0x70a08231" + who[2:].lower().rjust(64,"0")
    r = rpc("eth_call",[{"to":token,"data":data},"latest"]).get("result")
    return int(r,16)/1e6 if r and r != "0x" else 0

def human_hour_weight(h):
    # WIB-ish activity: sleepy 16-21 UTC, active morning+evening
    if 16 <= h < 21: return 0.15
    if 21 <= h or h < 6: return 0.35
    if 6 <= h < 10: return 0.7
    return 0.85

def main():
    from eth_account import Account
    from web3 import Web3
    Account.enable_unaudited_hdwallet_features()
    acct = Account.from_key(open(KEY227).read().strip())
    me = acct.address
    st = load()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if st["day"] != today:
        st["day"], st["count"] = today, 0
        save(st)

    h = datetime.now(timezone.utc).hour
    if st["count"] >= DAILY_TARGET:
        print("daily target reached, idle"); return
    # random gate: after an active burst, sleep a random 25-180 min (kills fixed-interval fingerprint)
    if st.get("next_at") and time.time() < st["next_at"]:
        mins = int((st["next_at"] - time.time()) / 60)
        print(f"gated — next activity in ~{mins}m"); return
    if random.random() > human_hour_weight(h):
        print(f"hour {h}UTC — outside activity window, idle"); return

    # related accounts derived from the same phrase (idx1-3)
    if not st["partners"]:
        phrase = open(PHRASE).read().strip()
        ps = []
        for i in (1,2,3):
            a = Account.from_mnemonic(phrase, account_path=f"m/44'/60'/0'/0/{i}")
            ps.append(a.address)
            faucet(a.address)   # fund their gas in stablecoin
        st["partners"] = ps; save(st)
        log(f"partners created+fauceted: {[p[:8] for p in ps]}")

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout":15,"headers":{"User-Agent":UA}}))
    nonce = w3.eth.get_transaction_count(me)
    gp = int(rpc("eth_gasPrice",[])["result"],16)

    def send(from_acct, to, token, amount):
        nonlocal nonce
        data = "0xa9059cbb" + to[2:].lower().rjust(64,"0") + format(int(amount*1e6),"064x")
        tx = {"chainId":CHAIN_ID,"from":from_acct.address,"to":Web3.to_checksum_address(token),
              "data":Web3.to_bytes(hexstr=data),"value":0,"nonce":nonce,"gas":500_000,"gasPrice":gp}
        signed = from_acct.sign_transaction(tx)
        hh = w3.eth.send_raw_transaction(signed.raw_transaction)
        rc = w3.eth.wait_for_transaction_receipt(hh, timeout=45)
        nonce += 1
        return rc["status"] == 1, hh.hex()

    def amount():
        r = random.random()
        if r < 0.35: return random.choice([1,5,10,20,25,50,100])          # round amounts
        if r < 0.8: return round(random.uniform(0.5, 120), 2)
        return round(random.uniform(120, 900), 2)

    # mint own token once (admin role) so OPAY actually circulates
    if st["token"] and not st.get("minted"):
        try:
            abi_mint = [{"name":"mint","type":"function","stateMutability":"nonpayable",
                         "inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],
                         "outputs":[]}]
            cm = w3.eth.contract(address=Web3.to_checksum_address(st["token"]), abi=abi_mint)
            data = cm.encode_abi("mint", args=[Web3.to_checksum_address(me), 10_000 * 10**6])
            tx = {"chainId":CHAIN_ID,"from":me,"to":Web3.to_checksum_address(st["token"]),
                  "data":Web3.to_bytes(hexstr=data),"value":0,"nonce":nonce,"gas":1_500_000,"gasPrice":gp}
            signed = acct.sign_transaction(tx)
            hh = w3.eth.send_raw_transaction(signed.raw_transaction)
            rc = w3.eth.wait_for_transaction_receipt(hh, timeout=45)
            if rc["status"] == 1:
                st["minted"] = True; nonce += 1; st["count"] += 1
                log(f"minted 10000 OPAY tx {hh.hex()[:16]}")
            else:
                nonce += 1; log("mint OPAY revert (maybe no role)")
        except Exception as e:
            log(f"mint ERR {str(e)[:100]}")
        time.sleep(random.uniform(20, 90))

    TOKENS = [ALPHA, USD0] + ([st["token"]] if st.get("fee_liq") else [])

    burst = random.choices([1,2,3,4,5], weights=[30,28,20,12,10])[0]
    done = 0
    for _ in range(burst):
        if st["count"] >= DAILY_TARGET: break
        try:
            roll = random.random()
            if not st["token"] and roll < 0.3:
                # create own stablecoin (once)
                salt = os.urandom(32).hex()
                fn = "createToken(string,string,address,address,bytes32)"
                # encode manually via web3 abi
                abi = [{"name":"createToken","type":"function","stateMutability":"nonpayable",
                        "inputs":[{"name":"name","type":"string"},{"name":"symbol","type":"string"},
                                  {"name":"currency","type":"string"},
                                  {"name":"quoteToken","type":"address"},
                                  {"name":"admin","type":"address"},
                                  {"name":"salt","type":"bytes32"}],
                        "outputs":[{"name":"token","type":"address"}]}]
                c = w3.eth.contract(address=Web3.to_checksum_address(FACTORY), abi=[abi[0]])
                data = c.encode_abi("createToken", args=["OnarPay USD","OPAY","USD",
                    Web3.to_checksum_address(ALPHA), Web3.to_checksum_address(me),
                    "0x"+salt])
                tx = {"chainId":CHAIN_ID,"from":me,"to":Web3.to_checksum_address(FACTORY),
                      "data":Web3.to_bytes(hexstr=data),"value":0,"nonce":nonce,"gas":8_000_000,"gasPrice":gp}
                signed = acct.sign_transaction(tx)
                hh = w3.eth.send_raw_transaction(signed.raw_transaction)
                rc = w3.eth.wait_for_transaction_receipt(hh, timeout=60)
                if rc["status"] == 1:
                    # derive token addr via helper
                    c2 = w3.eth.contract(address=Web3.to_checksum_address(FACTORY),
                        abi=[{"name":"getTokenAddress","type":"function","stateMutability":"view",
                              "inputs":[{"name":"sender","type":"address"},{"name":"salt","type":"bytes32"}],
                              "outputs":[{"name":"","type":"address"}]}])
                    tok = c2.caller().getTokenAddress(Web3.to_checksum_address(me), "0x"+salt)
                    st["token"] = tok; nonce += 1; done += 1; st["count"] += 1
                    log(f"TOKEN CREATED {tok} tx {hh.hex()[:16]}")
                else:
                    nonce += 1; log("token create REVERT")
            elif roll < 0.55:
                # send payment
                partner = random.choice(st["partners"])
                token = random.choice(TOKENS)
                ok, h2 = send(acct, partner, token, amount())
                if ok: done += 1; st["count"] += 1; log(f"send {token[-4:]} -> {partner[:8]} tx {h2[:16]}")
            elif roll < 0.8:
                # receive payment (related account -> me)
                pkey = None
                phrase = open(PHRASE).read().strip()
                p_acct = None
                partner = random.choice(st["partners"])
                for i in (1,2,3):
                    a = Account.from_mnemonic(phrase, account_path=f"m/44'/60'/0'/0/{i}")
                    if a.address.lower() == partner.lower(): p_acct = a; break
                if p_acct:
                    bal = tip20_balance(ALPHA, partner)
                    amt = min(amount(), max(0.0, bal - 5))
                    if amt >= 0.5:
                        pn = w3.eth.get_transaction_count(p_acct.address)
                        data = "0xa9059cbb" + me[2:].lower().rjust(64,"0") + format(int(amt*1e6),"064x")
                        tx = {"chainId":CHAIN_ID,"from":p_acct.address,"to":Web3.to_checksum_address(ALPHA),
                              "data":Web3.to_bytes(hexstr=data),"value":0,"nonce":pn,"gas":500_000,"gasPrice":gp}
                        signed = p_acct.sign_transaction(tx)
                        hh = w3.eth.send_raw_transaction(signed.raw_transaction)
                        rc = w3.eth.wait_for_transaction_receipt(hh, timeout=45)
                        if rc["status"] == 1: done += 1; st["count"] += 1; log(f"recv {amt} from {partner[:8]} tx {hh.hex()[:16]}")
            else:
                # deploy a tiny contract (rare)
                if st["deploys"] < 3 and random.random() < 0.25:
                    # minimal: PUSH1 1, SSTORE, return empty runtime
                    tx = {"chainId":CHAIN_ID,"from":me,"to":b"","data":Web3.to_bytes(hexstr="0x6001600055600080600060006000f3"),
                          "value":0,"nonce":nonce,"gas":1_000_000,"gasPrice":gp}
                    signed = acct.sign_transaction(tx)
                    hh = w3.eth.send_raw_transaction(signed.raw_transaction)
                    rc = w3.eth.wait_for_transaction_receipt(hh, timeout=45)
                    if rc["status"] == 1:
                        st["deploys"] += 1; nonce += 1; done += 1; st["count"] += 1
                        log(f"contract deploy #{st['deploys']} tx {hh.hex()[:16]}")
                    else: nonce += 1
        except Exception as e:
            log(f"ERR {str(e)[:120]}")
        time.sleep(random.uniform(20, 180))   # pause between actions

    # occasional faucet top-up
    if random.random() < 0.12:
        faucet(me)
    if burst > 0:
        # gate after any attempted run (success or fail) — random 25-180 min
        st["next_at"] = int(time.time() + random.uniform(25, 180) * 60)
    save(st)
    nxt = st.get("next_at", 0)
    print(f"RUN burst={burst} done={done} today={st['count']}/{DAILY_TARGET}" +
          (f" next_in={int((nxt-time.time())/60)}m" if nxt and nxt > time.time() else ""))

if __name__ == "__main__":
    os.makedirs(os.path.expanduser("~/tempo"), exist_ok=True)
    main()
