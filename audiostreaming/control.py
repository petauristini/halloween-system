import requests
import logging
from flask import Flask, request, jsonify
import time
import threading

INPUT_TIMEOUT = 5

logging.basicConfig(level=logging.INFO)

class StreamingOutput:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
    def check_connection(self):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/streamingoutput/ping')
            return res.ok
        except Exception as e:
            logging.error(f"Connection error: {e}")
            
    def start(self, server):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/streamingoutput/start?ip={server[0]}&port={server[1]}')
            if not res.ok:
                logging.error(f"Error starting stream client")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def stop(self, server):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/streamingoutput/stop?ip={server[0]}&port={server[1]}', timeout=1)
            if not res.ok:
                logging.error(f"Error stopping stream client")
        except Exception as e:
            logging.error(f"Connection error: {e}")

class StreamingOutputGroup:

    def __init__(self, outputs: list[StreamingOutput]):
        self.outputs = outputs

    def start(self, server):
        for client in self.outputs:
            client.start(server)

    def stop(self, server):
        for client in self.outputs:
            client.stop(server)

    def check_connection(self):
        results = []
        for client in self.outputs:
            result = client.check_connection()
            results.append(result)
        return results
    
class StreamingControlServerRoutes:
    def __init__(self, app: Flask, outputs: dict[StreamingOutput | StreamingOutputGroup]): 
        self.app = app
        self.outputs = outputs
        self.inputs = []
        self._setup_routes()
        thread = threading.Thread(target=self.clean_input_list, daemon=True)
        thread.start()
      
    def _setup_routes(self):
        
        @self.app.route('/api/streamingcontrol/ping', methods=['GET'])
        def ping():
            return "", 200
        
        @self.app.route('/api/streamingcontrol/info/outputs', methods=['GET'])
        def get_outputs():
            return jsonify(list(self.outputs.keys())), 200           
        
        @self.app.route('/api/streamingcontrol/input', methods=['POST'])
        def register():
            current_time = time.time()
            newInputs = request.get_json()  
            for newInput in newInputs:
                existing_input = next((item for item in self.inputs if item[0] == newInput), None)
                input = (newInput, current_time, False)

                if existing_input:
                    self.inputs.remove(existing_input)
                else:
                    print(f'Input {input} connected') 

                self.inputs.append(input)

            return "", 200
        
    def clean_input_list(self):
        while True:
            timedOutInputs = [i for i in self.inputs if time.time() - i[1] > INPUT_TIMEOUT]
            
            for input in timedOutInputs:
                for output in input[0]["outputs"]:
                    try:
                        outputs[output].stop((input[0]["ip"], input[0]["port"]))
                    except Exception as e:
                        print(e)
                self.inputs.remove(input)
                print(f'Client {input} disconnected')

            for i, input in enumerate(self.inputs):
                if not input[2]:
                    try:
                        for output in input[0]["outputs"]:
                            outputs[output].start((input[0]["ip"], input[0]["port"]))
                        self.inputs[i] = (input[0], input[1], True)
                    except Exception as e:
                        print(e)
                    




if __name__ == '__main__':
    outputs = {"localoutput": StreamingOutput("127.0.0.1", 5001), "remioutput": StreamingOutput("192.168.6.240", 5001)}
    app = Flask(__name__)
    server = StreamingControlServerRoutes(app, outputs)
    app.run(debug=False, host='0.0.0.0')