import pygame
import os
from flask import Flask, request, jsonify
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

class AudioFile:

    def __init__(self, file_path: str):
        if not os.path.isfile(file_path):
            raise ValueError(f"File '{file_path}' not found")
        
        self.sound = pygame.mixer.Sound(file_path)
    
    def is_playing(self) -> bool:
        return self.sound.get_num_channels() > 0
        
    def play(self, volume: float = 1.0):
        if self.is_playing():
            self.stop()
        
        self.sound.set_volume(volume)
        self.sound.play()

    def stop(self):
        if self.is_playing():
            self.sound.stop()


class AudioManager:

    def __init__(self):
        self.audio_files = {}
        pygame.mixer.init()
        self._initialize_audio_files()

    def _initialize_audio_files(self):
        module_dir = Path(__file__).parent
        assets_dir = module_dir / 'assets'
        
        if not assets_dir.exists():
            raise FileNotFoundError(f"The directory '{assets_dir}' does not exist.")
        
        for wav_file in assets_dir.glob('*.wav'):
            file_key = wav_file.stem
            self.audio_files[file_key] = AudioFile(str(wav_file))
        
        logging.info(f"Initialized audio files: {self.audio_files}")

class ServerHandler:
    def __init__(self, port: int=5000):
        self.port = port
        self.audio_manager = AudioManager()
        self.app = Flask(__name__)
        self._setup_routes()

    def _validate_file(self, file: str):
        return file and file in self.audio_manager.audio_files
    
    def _validate_volume(self, volume: str):
        return volume and float(volume) and 0 <= float(volume) <= 1
    
            
    def _setup_routes(self):
        
        @self.app.route('/api/ping', methods=['GET'])
        def ping():
            return "", 200
        
        @self.app.route('/api/play', methods=['GET'])
        def play():
            file = request.args.get('file')
            volume = request.args.get('volume', '1')



            if not self._validate_file:
                return jsonify(error="File not found"), 404

            if not self._validate_volume(volume):
                return jsonify(error="Invalid volume"), 400
            
            try:
                self.audio_manager.audio_files[file].play(float(volume))
                logging.info(f"Playing sound '{file}' with volume {volume}")
                return "", 200
            except Exception as e:
                return jsonify(error=str(e)), 500

        @self.app.route('/api/stop', methods=['GET'])
        def stop():
            file = request.args.get('file')

            if not self._validate_file(file):
                return jsonify(error="File not found"), 404
            
            try:
                self.audio_manager.audio_files[file].stop()
                logging.info(f"Stopping sound '{file}'")
                return "", 200
            except Exception as e:
                return jsonify(error=str(e)), 500

    def start(self):
        self.app.run(host='0.0.0.0', port=self.port)

if __name__ == '__main__':
    app = ServerHandler()
    app.start()
