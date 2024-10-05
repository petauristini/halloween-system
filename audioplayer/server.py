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
    
    def _is_playing(self) -> bool:
        return self.sound.get_num_channels() > 0
        
    def play(self, volume: float = 1.0, loops=0):
        if self._is_playing():
            self.stop()
        
        self.sound.set_volume(volume)
        self.sound.play(loops)

    def stop(self):
        if self._is_playing():
            self.sound.stop()


class AudioPlayer:

    def __init__(self):
        self.audio_files = {}
        pygame.mixer.init()
        self.load_audio_files()

    def load_audio_files(self):
        module_dir = Path(__file__).parent
        assets_dir = module_dir / 'assets'
        
        if not assets_dir.exists():
            raise FileNotFoundError(f"The directory '{assets_dir}' does not exist.")
        
        for wav_file in assets_dir.glob('*.wav'):
            file_key = wav_file.stem
            self.audio_files[file_key] = AudioFile(str(wav_file))
        
        logging.info(f"Loaded audio files: {self.audio_files}")


class AudioPlayerServer:
    def __init__(self, app: Flask):
        self.app = app
        self.audio_manager = AudioPlayer()
        self._setup_routes()

    def _validate_file(self, file: str):
        return file and file in self.audio_manager.audio_files
    
    def _validate_volume(self, volume: str):
        return volume and float(volume) and 0 <= float(volume) <= 1
      
    def _setup_routes(self):
        
        @self.app.route('/api/audioplayer/ping', methods=['GET'])
        def ping():
            return "", 200
        
        @self.app.route('/api/audioplayer/update', methods=['GET'])
        def update():
            try:
                self.audio_manager.load_audio_files()
            except Exception as e:
                return jsonify(error=str(e)), 500
            return "", 200
        
        @self.app.route('/api/audioplayer/play', methods=['GET'])
        def play():
            file = request.args.get('file')
            volume = request.args.get('volume', '1')
            loops = request.args.get('loops', '0')

            if not self._validate_file:
                return jsonify(error="File not found"), 404

            if not self._validate_volume(volume):
                return jsonify(error="Invalid volume"), 400
            
            try:
                self.audio_manager.audio_files[file].play(volume=float(volume), loops=int(loops))
                logging.info(f"Playing sound '{file}' with volume {volume}")
                return "", 200
            except Exception as e:
                return jsonify(error=str(e)), 500

        @self.app.route('/api/audioplayer/stop', methods=['GET'])
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

if __name__ == '__main__':
    app = Flask(__name__)
    server = AudioPlayerServer(app)
    app.run(debug=True)
