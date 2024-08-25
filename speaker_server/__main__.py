import os
from flask import Flask, request
import json
import lib.AudioStream as AudioStream
import lib.AudioFile as AudioFile

module_dir = os.path.dirname(__file__)

assets_dir = os.path.join(module_dir, 'assets')

with open(os.path.join(module_dir, 'config.json')) as configFile:
    config = json.load(configFile)

app = Flask(__name__)       

audioFileHandler = AudioFile.AudioFileHandler()
audioStreamHandler = AudioStream.StreamClientHandler()

@app.route('/play')
def play_file():
    id = request.args.get('id')
    file = request.args.get('file')
    volume = request.args.get('volume', '1')

    path = os.path.join(assets_dir, f"{file}.wav")

    if not audioFileHandler.id_exists(id):
        try:
            audioFileHandler.add(id, path, float(volume))
        except Exception as e:
            return f"Error: {e}", 500
    
    audioFileHandler.play(id)
    return "Sound playing", 200
    

@app.route('/stop')
def stop_file():
    id = request.args.get('id')

    if not audioFileHandler.id_exists(id):
        return "Please provide a valid id", 400

    audioFileHandler.stop(id)
    return f"Sound '{id}' stopped", 200

@app.route('/streaming/create')
def create_stream():
    id = request.args.get('id')

    if audioStreamHandler.id_exists(id):
        return f'Stream with id: {id} already exists', 400
    try:
        audioStreamHandler.add(id, server=(config["server"]["ip"], config["server"]["port"]), outputDevice=config["outputDevice"])
        return f"Successfully created Stream with id {id}", 200
    except Exception as e:
        return f"Error: {e}", 500
       
@app.route('/streaming/start')
def start_streaming():
    id = request.args.get('id')

    if not audioStreamHandler.id_exists(id):
        return f'Stream with id: {id} does not exist', 400

    audioStreamHandler.start(id)

    return f"Successfully started Stream with id {id}", 200
    
@app.route('/streaming/stop')
def stop_streaming():
    id = request.args.get('id')

    if audioStreamHandler.id_exists(id):
        audioStreamHandler.stop(id)
        return f"Stream '{id}' stopped", 200
    
    return f"No stream with id: {id}", 400

if __name__ == '__main__':
    app.run(debug=True)
