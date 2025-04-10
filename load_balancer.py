from flask import Flask, request
import requests
import threading
from collections import defaultdict

app = Flask(__name__)
container_usage = defaultdict(int)  # {container_url: active_requests}
lock = threading.Lock()

def get_least_used():
    print("container_usage ::: ",container_usage)
    with lock:
        return min(container_usage.items(), key=lambda x: x[1], default=(None, None))[0]

@app.route('/primes/<int:number>')
def handle_request(number):
    container = get_least_used()
    print("least used container ::: ",container)
    if not container:
        return "No available containers", 503
    
    try:
        with lock:
            container_usage[container] += 1
        response = requests.get(f"{container}/primes/{number}", timeout=100)
        return response.json()
    except Exception as e:
        return str(e), 500
    finally:
        with lock:
            container_usage[container] -= 1

@app.route('/update_containers', methods=['POST'])
def update_containers():
    new_containers = request.json
    with lock:
        container_usage.clear()
        for c in new_containers:
            container_usage[c] = 0
    return "Updated", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

# http://localhost/primes/100000000