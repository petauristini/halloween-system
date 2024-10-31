from trigger import TriggerHandler
from audioplayer.api import AudioPlayer, AudioPlayerGroup
from flask import Flask
import logging
from wled.api import Wled, WledGroup
from raspigpio.api import GPIOPin, GPIOGroup 

flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.WARNING)
root_logger = logging.getLogger('root')
root_logger.setLevel(logging.WARNING)

app = Flask(__name__)
trigger_handler = TriggerHandler(app)

# Audio Players
audio_player_1 = AudioPlayer('192.168.1.110', 5000)
audio_player_2 = AudioPlayer('192.168.1.111', 5000)
audio_player_3 = AudioPlayer('192.168.1.112', 5000)
all_audio_players = AudioPlayerGroup([audio_player_1, audio_player_2, audio_player_3])

# WLED
wled_1 = Wled('192.168.1.120')
wled_2 = Wled('192.168.1.121')
wled_3 = Wled('192.168.1.122')
all_wleds = WledGroup([wled_1, wled_2, wled_3])

# Smoke Modules
smoke_module_1 = GPIOPin("192.168.1.130", 5000, "smoke")
smoke_module_2 = GPIOPin("192.168.1.131", 5000, "smoke")
smoke_module_3 = GPIOPin("192.168.1.132", 5000, "smoke")
all_smoke_modules = GPIOGroup([smoke_module_1, smoke_module_2, smoke_module_3])

# Triggers
trigger_handler.add('motion_sensor_1')
trigger_handler.add('motion_sensor_2')
trigger_handler.add('motion_sensor_3')
trigger_handler.add('doorbell_sensor')

trigger_handler.add('smoke_module_1', deactivate_cooldown=True)
trigger_handler.add_http_callback('smoke_module_1', 'smoke_module_1_callback', (smoke_module_1.turn_on_for, (5,)))

trigger_handler.add('smoke_module_2', deactivate_cooldown=True)
trigger_handler.add_http_callback('smoke_module_2', 'smoke_module_2_callback', (smoke_module_2.turn_on_for, (5,)))

trigger_handler.add('smoke_module_3', deactivate_cooldown=True)
trigger_handler.add_http_callback('smoke_module_3', 'smoke_module_3_callback', (smoke_module_3.turn_on_for, (5,)))

trigger_handler.add('stop_smoke', deactivate_cooldown=True)
trigger_handler.add_callback('stop_smoke', 'stop_smoke_callback', (all_smoke_modules.turn_off, ()))

trigger_handler.add('stop_audio', deactivate_cooldown=True)
trigger_handler.add_callback('stop_audio', 'stop_audio_callback', (all_audio_players.stop, ()))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=7000)