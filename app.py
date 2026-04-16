import requests
import time
import base58
import os
from flask import Flask

app = Flask(__name__)

# ========== ТЕСТОВЫЙ КОШЕЛЁК ==========
PRIVATE_KEY = '2fd79529ed4481bd34542f84df7c220f9da519f1c09dbbe31d0d85c067ff188e'
FROM_ADDRESS = 'TAPCUcxYN6aGGaPHnVp2RWB6CvMGicKDBX'
TO_ADDRESS = 'TVBSzwaKLEwUmdCXUCyaCbZGgsbdBR8LLn'
# ======================================

API_URL = 'https://api.trongrid.io'

def b58_to_hex(addr):
    decoded = base58.b58decode(addr)
    return '41' + decoded[1:-4].hex()

def get_balance():
    try:
        resp = requests.get(f'{API_URL}/v1/accounts/{FROM_ADDRESS}')
        data = resp.json()
        if data.get('data') and len(data['data']) > 0:
            return data['data'][0].get('balance', 0)
        return 0
    except:
        return 0

def send_trx(amount_sun):
    try:
        owner_hex = b58_to_hex(FROM_ADDRESS)
        to_hex = b58_to_hex(TO_ADDRESS)
        
        tx_data = {"owner_address": owner_hex, "to_address": to_hex, "amount": amount_sun}
        create = requests.post(f'{API_URL}/wallet/createtransaction', json=tx_data)
        tx = create.json()
        if 'Error' in tx:
            return False
        
        block = requests.post(f'{API_URL}/wallet/getnowblock').json()
        num = block['block_header']['raw_data']['number']
        ref_block_bytes = hex(num)[2:].zfill(8)[-8:]
        ref_block_hash = block['blockid'][:16]
        
        tx['ref_block_bytes'] = ref_block_bytes
        tx['ref_block_hash'] = ref_block_hash
        tx['timestamp'] = int(time.time() * 1000)
        
        sign_data = {"transaction": tx, "privateKey": PRIVATE_KEY}
        signed = requests.post(f'{API_URL}/wallet/gettransactionsign', json=sign_data).json()
        if 'Error' in signed:
            return False
        
        result = requests.post(f'{API_URL}/wallet/broadcasttransaction', json=signed).json()
        return result.get('result', False)
    except:
        return False

@app.route('/')
def index():
    return 'TRX Sweeper (TEST MODE) is running!'

@app.route('/check')
def check():
    balance = get_balance()
    if balance > 5_000_000:
        amount = balance - 1_500_000
        success = send_trx(amount)
        if success:
            return f'✅ Sent {amount/1_000_000:.2f} TRX'
        else:
            return '❌ Send failed'
    return f'Balance: {balance/1_000_000:.2f} TRX'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
