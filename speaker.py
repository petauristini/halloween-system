from flask import Flask
from audioplayer.server import AudioPlayerServer
from audiostreaming.output import AudioStreamingOutputServer
#from raspigpio.server import GPIOPinServer


app = Flask(__name__)

audio_player = AudioPlayerServer(app)
streaming_output = AudioStreamingOutputServer(app)
#gpio_pin = GPIOPinServer(app, 2, "smoke")

app.run(debug=False, host='0.0.0.0', port=5000)