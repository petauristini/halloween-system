from trigger import TriggerHandler
from audioplayer.api import AudioServer, AudioServerGroup
from flask import Flask
import logging
from wled.api import Wled, WledGroup

flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.WARNING)

root_logger = logging.getLogger('root')
root_logger.setLevel(logging.WARNING)

app = Flask(__name__)
handler = TriggerHandler(app)
server = AudioServer('localhost', 5001)
server2 = AudioServer('192.168.6.240', 5000)
all_servers = AudioServerGroup ([server, server2])
wled = Wled('192.168.6.182')
handler.add('trigger1')
handler.add_callback('trigger1', 'callback1', (all_servers.play, ('joghurt')))
handler.add('stopall', deactivate_cooldown=True)
handler.add_callback('stopall', 'stopall_callback', (all_servers.stop, ('joghurt')))
handler.add('httptest')
handler.add_http_callback("httptest", "httptest_callback", "http://192.168.6.151/trigger/trigger1")
handler.add('wled_on', deactivate_cooldown=True)
handler.add_callback('wled_on', 'wled_callback', (wled.on, ()))
handler.add('wled_off', deactivate_cooldown=True)
handler.add_callback('wled_off', 'wled_callback', (wled.off, ()))
app.run(debug=False, host='0.0.0.0')