from trigger import TriggerHandler
from audioplayer.api import AudioPlayer, AudioPlayerGroup
from flask import Flask
import logging
from wled.api import Wled, WledGroup
from raspigpio.api import GPIOPin, GPIOGroup 
from audiostreaming.control import StreamingOutput, StreamingControlServerRoutes

flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.WARNING)
root_logger = logging.getLogger('root')
root_logger.setLevel(logging.WARNING)

app = Flask(__name__)
trigger_handler = TriggerHandler(app)

# Audio Players
audio_player_1 = AudioPlayer('192.168.1.93', 5000)
audio_player_2 = AudioPlayer('192.168.1.90', 5000)
audio_player_3 = AudioPlayer('192.168.1.89', 5000)
all_audio_players = AudioPlayerGroup([audio_player_1, audio_player_2, audio_player_3])

# Audio Streaming
outputs = [{"raspi-speaker-1": StreamingOutput('192.168.1.93', 5000)}]
audio_streaming_control_server = StreamingControlServerRoutes(app, outputs)

# WLED
wled_1 = Wled('192.168.1.78')
wled_2 = Wled('192.168.1.121')
wled_3 = Wled('192.168.1.122')
all_wleds = WledGroup([wled_1, wled_2, wled_3])

# Smoke Modules
# smoke_module_1 = GPIOPin("192.168.1.88", 5000, "smoke")
# smoke_module_2 = GPIOPin("192.168.1.90", 5000, "smoke")
# smoke_module_3 = GPIOPin("192.168.1.89", 5000, "smoke")
# all_smoke_modules = GPIOGroup([smoke_module_1, smoke_module_2, smoke_module_3])

# Triggers
trigger_handler.add('motion_sensor_1')
trigger_handler.add_callback('motion_sensor_1', 'motion_sensor_callback_1', (audio_player_1.play, ("scare",)))
trigger_handler.add('motion_sensor_2')
trigger_handler.add_callback('motion_sensor_2', 'motion_sensor_callback_2', (audio_player_2.play, ("scare",)))
trigger_handler.add('motion_sensor_3')
trigger_handler.add('doorbell_sensor')

# trigger_handler.add('smoke_module_1', deactivate_cooldown=True)
# trigger_handler.add_callback('smoke_module_1', 'smoke_module_1_callback', (smoke_module_1.turn_on_for, (5,)))

# trigger_handler.add('smoke_module_2', deactivate_cooldown=True)
# trigger_handler.add_callback('smoke_module_2', 'smoke_module_2_callback', (smoke_module_2.turn_on_for, (5,)))

# trigger_handler.add('smoke_module_3', deactivate_cooldown=True)
# trigger_handler.add_callback('smoke_module_3', 'smoke_module_3_callback', (smoke_module_3.turn_on_for, (5,)))

trigger_handler.add('audio_player_1_scare', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_1_scare', 'audio_player_callback_1_scare', (audio_player_1.play, ("scare",)))

trigger_handler.add('audio_player_2_scare', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_2_scare', 'audio_player_callback_2_scare', (audio_player_2.play, ("scare",)))

trigger_handler.add('audio_player_3_scare', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_3_scare', 'audio_player_callback_3_scare', (audio_player_3.play, ("scare",)))

trigger_handler.add('stop_audio_scare', deactivate_cooldown=True)
trigger_handler.add_callback('stop_audio_scare', 'stop_audio_callback_scare', (all_audio_players.stop, ("scare",)))

trigger_handler.add('play_audio_theme', deactivate_cooldown=True)
trigger_handler.add_callback('play_audio_theme', 'play_audio_callback_theme', (all_audio_players.play, ("theme", 0.2, -1)))

trigger_handler.add('stop_audio_theme', deactivate_cooldown=True)
trigger_handler.add_callback('stop_audio_theme', 'stop_audio_callback_theme', (all_audio_players.stop, ("theme",)))

trigger_handler.add('audio_player_1_rickroll', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_1_rickroll', 'audio_player_callback_1_rickroll', (audio_player_1.play, ("rickroll",)))

trigger_handler.add('audio_player_1_stop_rickroll', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_1_stop_rickroll', 'audio_player_callback_1_stop_rickroll', (audio_player_1.stop, ("rickroll",)))

trigger_handler.add('audio_player_2_rickroll', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_2_rickroll', 'audio_player_callback_2_rickroll', (audio_player_2.play, ("rickroll",)))

trigger_handler.add('audio_player_2_stop_rickroll', deactivate_cooldown=True)
trigger_handler.add_callback('audio_player_2_stop_rickroll', 'audio_player_callback_2_stop_rickroll', (audio_player_2.stop, ("rickroll",)))
# trigger_handler.add('stop_smoke', deactivate_cooldown=True)
# trigger_handler.add_callback('stop_smoke', 'stop_smoke_callback', (all_smoke_modules.turn_off, ()))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=7000)