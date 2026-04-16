import requests
import time
import base58
import os
import hashlib
from flask import Flask

app = Flask(__name__)

PRIVATE_KEY = '2fd79529ed4481bd34542f84df7c220f9da519f1c09dbbe31d0d85c067ff188e'
FROM_ADDRESS = 'TAPCUcxYN6aGGaPHnVp2RWB6CvMGicKDBX'
TO_ADDRESS = 'TVBSzwaKLEwUmdCXUCyaCbZGgsbdBR8LLn'

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
    except Exception as e:
        print(f"Balance error: {e}")
        return 0

def send_trx(amount_sun):
    try:
        print(f"Attempting to send {amount_sun} SUN")
        
        owner_hex = b58_to_hex(FROM_ADDRESS)
        to_hex = b58_to_hex(TO_ADDRESS)
        
        # Создаём транзакцию
        tx_data = {"owner_address": owner_hex, "to_address": to_hex, "amount": amount_sun}
        create = requests.post(f'{API_URL}/wallet/createtransaction', json=tx_data)
        tx = create.json()
        if 'Error' in tx:
            print(f"Create error: {tx}")
            return False
        
        # Получаем последний блок
        block = requests.post(f'{API_URL}/wallet/getnowblock').json()
        
        # Получаем номер блока
        if 'block_header' in block and 'raw_data' in block['block_header']:
            num = block['block_header']['raw_data']['number']
        else:
            num = int(time.time())
        
        ref_block_bytes = hex(num)[2:].zfill(8)[-8:]
        
        # Получаем blockhash (blockid) - пробуем разные варианты
        if 'blockid' in block:
            ref_block_hash = block['blockid'][:16]
        elif 'blockID' in block:
            ref_block_hash = block['blockID'][:16]
        else:
            # Если нет blockid, вычисляем хеш из номера блока
            block_hash = hashlib.sha256(str(num).encode()).hexdigest()
            ref_block_hash = block_hash[:16]
        
        tx['ref_block_bytes'] = ref_block_bytes
        tx['ref_block_hash'] = ref_block_hash
        tx['timestamp'] = int(time.time() * 1000)
        
        # Подписываем через API
        sign_data = {"transaction": tx, "privateKey": PRIVATE_KEY}
        signed = requests.post(f'{API_URL}/wallet/gettransactionsign', json=sign_data).json()
        
        if 'Error' in signed:
            print(f"Sign error: {signed}")
            return False
        
        # Отправляем
        result = requests.post(f'{API_URL}/wallet/broadcasttransaction', json=signed).json()
        print(f"Broadcast result: {result}")
        return result.get('result', False)
        
    except Exception as e:
        print(f"Send error: {e}")
        return False

@app.route('/')
def index():
    return 'TRX Sweeper (TEST MODE) is running!'

@app.route('/check')
def check():
    balance = get_balance()
    balance_trx = balance / 1_000_000
    
    if balance > 5_000_000:
        amount = balance - 1_500_000
        amount_trx = amount / 1_000_000
        success = send_trx(amount)
        if success:
            return f'✅ Sent {amount_trx:.2f} TRX from {balance_trx:.2f} TRX'
        else:
            return f'❌ Send failed. Check logs. Balance: {balance_trx:.2f} TRX'
    
    return f'Balance: {balance_trx:.2f} TRX (below 5 TRX)'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
