from flask import Flask
from audioplayer.server import AudioPlayerServer
from audiostreaming.output import AudioStreamingOutputServer


app = Flask(__name__)
audio_player = AudioPlayerServer(app)
streaming_output = AudioStreamingOutputServer(app)
app.run(debug=True, host='0.0.0.0', port=5001)