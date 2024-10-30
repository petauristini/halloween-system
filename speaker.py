from flask import Flask
from audioplayer.server import AudioPlayerServer
from audiostreaming.output import AudioStreamingOutputServer
from raspigpio.server import GPIOHandlerServer


app = Flask(__name__)
audio_player = AudioPlayerServer(app)
streaming_output = AudioStreamingOutputServer(app)
gpio_handler_server = GPIOHandlerServer(app)
gpio_handler_server.add(2)

app.run(debug=True, host='0.0.0.0', port=5001)