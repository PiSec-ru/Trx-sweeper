import requests
import time
import base58
import os
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
        return 0

@app.route('/')
def index():
    return 'TRX Sweeper (TEST MODE) is running!'

@app.route('/check')
def check():
    balance = get_balance()
    balance_trx = balance / 1_000_000
    return f'Balance: {balance_trx:.2f} TRX'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
