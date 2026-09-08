#!/usr/bin/env python3
"""TEMPO — Tempo testnet (Moderato) toolkit, agent-first.

Usage:
  python tempo.py faucet 0xYOURADDR          # top up test stablecoins (1 POST, 4 claims)
  python tempo.py balance 0xYOURADDR         # AlphaUSD / USD0 balances + tx count
  python tempo.py deploy-token KEYFILE "Name" "SYM"   # issue your own TIP-20 (gas >= 8M!)
  python tempo.py mint KEYFILE TOKEN AMOUNT  # grant ISSUER_ROLE to self + mint
  python tempo.py fee-liq KEYFILE TOKEN      # open FeeAMM lane so TOKEN can pay gas
  python tempo.py status                     # chain health: chainId, gas price, fee tokens

Config via env (sane defaults):
  TEMPO_RPC      default https://rpc.moderato.tempo.xyz
  TEMPO_CHAINID  default 42431
Keys: a plain-text hex private key file. NEVER paste keys in chat/repos.
"""
import json, os, sys, subprocess

RPC = os.environ.get("TEMPO_RPC", "https://rpc.moderato.tempo.xyz")
CHAIN_ID = int(os.environ.get("TEMPO_CHAINID", "42431"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"
FAUCET_API = "https://tempo.xyz/developers/api/faucet"
ALPHA = "0x20c0000000000000000000000000000000000001"   # default testnet fee token
USD0  = "0x20c0000000000000000000000000000000000000"
FACTORY  = "0x20fc000000000000000000000000000000000000"
FEEMGR   = "0xfeec000000000000000000000000000000000000"

def rpc(method, params):
    out = subprocess.run(["curl","-s","-m","20","-X","POST",RPC,"-H","Content-Type: application/json",
        "-A",UA,"--data",json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params})],
        capture_output=True, text=True, timeout=30).stdout
    try:
        return json.loads(out)["result"]
    except Exception:
        sys.exit(f"RPC error: {out[:200]}\n(hint: bare curl UAs get 403 — we send a browser UA)")

def tip20_balance(token, addr):
    r = rpc("eth_call", [{"to":token,"data":"0x70a08231"+addr[2:].lower().rjust(64,"0")},"latest"])
    return int(r,16)/1e6 if r and r != "0x" else 0.0

def load_acct(keyfile):
    from eth_account import Account
    try:
        return Account.from_key(open(os.path.expanduser(keyfile)).read().strip())
    except FileNotFoundError:
        sys.exit(f"key file not found: {keyfile}")

def w3():
    from web3 import Web3  # noqa
    return Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout":15,"headers":{"User-Agent":UA}}))

def send_tx(acct, to, data, gas, value=0):
    c = w3()
    tx = {"chainId":CHAIN_ID,"from":acct.address,"to":to if isinstance(to,bytes) else Web3.to_checksum_address(to),
          "data":Web3.to_bytes(hexstr=data) if isinstance(data,str) else data,"value":value,
          "nonce":c.eth.get_transaction_count(acct.address),"gas":gas,"gasPrice":c.eth.gas_price}
    s = acct.sign_transaction(tx)
    h = c.eth.send_raw_transaction(s.raw_transaction)
    rc = c.eth.wait_for_transaction_receipt(h, timeout=90)
    print(f"  tx {h.hex()}  status {'OK ✓' if rc['status']==1 else 'FAIL ✗ (check gas cap — deploys need >= 8M)'}")
    return rc["status"]==1, h.hex()

def cmd_faucet(addr):
    out = subprocess.run(["curl","-s","-m","20","-X","POST",FAUCET_API,"-H","Content-Type: application/json",
        "-A",UA,"--data",json.dumps({"address":addr.lower()})],capture_output=True,text=True,timeout=30).stdout
    d = json.loads(out)
    if d.get("error"): sys.exit(f"faucet error: {d['error']}")
    print(f"fauceted {addr}: {len(d['data'])} tx")
    for t in d["data"]: print(" ", t["hash"])

def cmd_balance(addr):
    n = int(rpc("eth_getTransactionCount",[addr.lower(),"latest"]),16)
    print(f"{addr}")
    print(f"  AlphaUSD : {tip20_balance(ALPHA,addr):,.2f}")
    print(f"  USD0     : {tip20_balance(USD0,addr):,.2f}")
    print(f"  tx count : {n}")

def cmd_deploy_token(keyfile, name, symbol):
    from web3 import Web3
    acct = load_acct(keyfile)
    import secrets
    c = w3()
    abi = [{"name":"createToken","type":"function","stateMutability":"nonpayable",
            "inputs":[{"name":"n","type":"string"},{"name":"s","type":"string"},{"name":"c","type":"string"},
                      {"name":"q","type":"address"},{"name":"a","type":"address"},{"name":"sl","type":"bytes32"}],
            "outputs":[{"name":"token","type":"address"}]},
           {"name":"getTokenAddress","type":"function","stateMutability":"view",
            "inputs":[{"name":"sender","type":"address"},{"name":"salt","type":"bytes32"}],
            "outputs":[{"name":"","type":"address"}]}]
    ct = c.eth.contract(address=Web3.to_checksum_address(FACTORY), abi=abi)
    salt = "0x"+secrets.token_hex(32)
    predicted = ct.caller().getTokenAddress(Web3.to_checksum_address(acct.address), salt)
    print(f"deploying '{name}' ({symbol}) → will live at {predicted}")
    data = ct.encode_abi("createToken", args=[name, symbol, "USD",
        Web3.to_checksum_address(ALPHA), Web3.to_checksum_address(acct.address), salt])
    ok,_ = send_tx(acct, FACTORY, data, 8_000_000)
    if ok: print(f"token address: {predicted}")

def cmd_mint(keyfile, token, amount):
    from web3 import Web3
    acct = load_acct(keyfile)
    c = w3()
    abi = [{"name":"grantRole","type":"function","stateMutability":"nonpayable",
            "inputs":[{"name":"role","type":"bytes32"},{"name":"account","type":"address"}],"outputs":[]},
           {"name":"mint","type":"function","stateMutability":"nonpayable",
            "inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[]}]
    ct = c.eth.contract(address=Web3.to_checksum_address(token), abi=abi)
    role = c.keccak(text="ISSUER_ROLE")
    print("granting ISSUER_ROLE to self...")
    send_tx(acct, token, ct.encode_abi("grantRole", args=[role, Web3.to_checksum_address(acct.address)]), 1_000_000)
    print(f"minting {amount} {token[:10]}...")
    send_tx(acct, token, ct.encode_abi("mint", args=[Web3.to_checksum_address(acct.address), int(float(amount)*10**6)]), 1_500_000)

def cmd_fee_liq(keyfile, token, amount="100"):
    from web3 import Web3
    acct = load_acct(keyfile)
    c = w3()
    print(f"approving {amount} AlphaUSD → FeeManager...")
    appr = "0x095ea7b3"+FEEMGR[2:].lower().rjust(64,"0")+format(int(float(amount)*10**6),"064x")
    if not send_tx(acct, ALPHA, appr, 500_000)[0]: return
    abi = [{"name":"mint","type":"function","stateMutability":"nonpayable",
            "inputs":[{"name":"userToken","type":"address"},{"name":"validatorToken","type":"address"},
                      {"name":"validatorTokenAmount","type":"uint256"},{"name":"to","type":"address"}],"outputs":[]}]
    ct = c.eth.contract(address=Web3.to_checksum_address(FEEMGR), abi=abi)
    print("opening FeeAMM lane (your token can now pay gas)...")
    send_tx(acct, FEEMGR, ct.encode_abi("mint", args=[
        Web3.to_checksum_address(token), Web3.to_checksum_address(ALPHA),
        int(float(amount)*10**6), Web3.to_checksum_address(acct.address)]), 3_000_000)

def cmd_status():
    cid = rpc("eth_chainId",[])
    gp = int(rpc("eth_gasPrice",[]),16)
    blk = int(rpc("eth_blockNumber",[]),16)
    print(f"RPC      : {RPC}")
    print(f"chainId  : {int(cid,16)} {'✓ Moderato' if int(cid,16)==CHAIN_ID else '✗ NOT '+str(CHAIN_ID)}")
    print(f"block    : {blk:,}")
    print(f"gasPrice : {gp/1e9:,.2f} gwei (paid in stablecoins, not native)")

if __name__ == "__main__":
    args = sys.argv[1:]
    cmds = {"faucet":(2,cmd_faucet),"balance":(2,cmd_balance),"deploy-token":(4,cmd_deploy_token),
            "mint":(4,cmd_mint),"fee-liq":(3,cmd_fee_liq),"status":(1,cmd_status)}
    if not args or args[0] not in cmds:
        print(__doc__); sys.exit(0)
    name = args[0]
    if len(args) < cmds[name][0]:
        sys.exit(f"'{name}' needs {cmds[name][0]-1} arg(s) — see: python tempo.py --help")
    cmds[name][1](*args[1:])
