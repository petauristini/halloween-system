from flask import Flask, request
import logging
import time
from lib.Trigger import Trigger

app = Flask(__name__)
INPUT_TIMEOUT = 5
# Disable the default Flask/Werkzeug logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Set to ERROR to suppress normal requests logging

inputs = []
outputs = set()

@app.route('/register/input', methods=['POST'])
def register_input():
    current_time = time.time()
    newInputs = request.get_json()
    for newInput in newInputs:
        existing_input = next((item for item in inputs if item[0] == newInput), None)
        input = (newInput, current_time)

        if existing_input:
            inputs.remove(existing_input)
        else:
            print(f'Input {input} connected') 

        inputs.append(input)

    #Remove Timed Out Clients
    timedOutInputs = [i for i in inputs if time.time() - i[1] > INPUT_TIMEOUT]
    for input in timedOutInputs:
        inputs.remove(input)
        print(f'Client {input} disconnected')
    print(inputs)
    return "", 200

@app.route('/register/output')
def register_output():
    pass

if __name__ == '__main__':
    app.run(debug=False)