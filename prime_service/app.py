# filepath: d:\workspace\labs\cloud_computing\project\prime_service\app.py
from flask import Flask, jsonify
import math
import os

app = Flask(__name__)

# Get container ID from environment variable with fallback
app.config['CONTAINER_ID'] = os.environ.get('CONTAINER_ID', 'unknown-container')

def count_primes(n):
    if n < 2:
        return 0
    sieve = [True] * (n+1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.sqrt(n)) + 1):
        if sieve[i]:
            sieve[i*i:n+1:i] = [False]*len(sieve[i*i:n+1:i])
    return sum(sieve)

@app.route('/primes/<int:number>')
def primes(number):
    try:
        result = count_primes(number)
        return jsonify({
            'result': result,
            'container_id': app.config['CONTAINER_ID']
        })
    except Exception as e:
        print(f"Error calculating primes: {e}")
        return jsonify({
            'error': str(e),
            'container_id': app.config['CONTAINER_ID']
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)