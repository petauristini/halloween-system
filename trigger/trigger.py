import logging
from typing import Callable, Dict, Tuple
import time
from flask import Flask, render_template, jsonify
import os

logging.basicConfig(level=logging.INFO)
LAST_TRIGGERED_DISPLAY_TIME = 5

class CallbackNotFoundError(Exception):
    """Exception raised when a callback is not found in a Trigger."""
    pass

class TriggerNotFoundError(Exception):
    """Exception raised when a Trigger is not found in the TriggerHandler."""
    pass

class Trigger:
    def __init__(self, triggerId: str):
        """
        Initialize a Trigger with a unique ID.

        :param triggerId: The ID of the trigger.
        """
        self.triggerId = triggerId
        self.callbacks: Dict[str, Tuple[Callable, Tuple]] = {}
        self.last_triggered = None

    def callback_exists(self, callbackId: str) -> bool:
        """Check if a callback exists in the trigger."""
        return callbackId in self.callbacks
    
    def add_callback(self, callbackId: str, callback: Tuple[Callable, Tuple]):
        """Add a callback to the trigger."""
        if not self.callback_exists(callbackId):
            self.callbacks[callbackId] = callback
            logging.debug(f"Callback {callbackId} added to trigger {self.triggerId}")
        else:
            logging.debug(f"Callback {callbackId} already exists in trigger {self.triggerId}")

    def remove_callback(self, callbackId: str):
        """Remove a callback from the trigger."""
        if self.callback_exists(callbackId):
            del self.callbacks[callbackId]
            logging.debug(f"Callback {callbackId} removed from trigger {self.triggerId}")
        else:
            logging.error(f"Callback {callbackId} not found in trigger {self.triggerId}")
            raise CallbackNotFoundError(f"Callback {callbackId} not found in trigger {self.triggerId}")

    def clear_callbacks(self):
        """Clear all callbacks from the trigger."""
        self.callbacks.clear()

    def trigger(self):
        """Trigger all callbacks associated with this trigger."""
        logging.info(f"Trigger {self.triggerId} executing callbacks")
        for callback, args in self.callbacks.values():
            logging.debug(f"Trigger {self.triggerId} calling callback {callback} with args {args}")
            try:
                callback(*args)
            except Exception as e:
                logging.error(f"Error executing callback {callback} with args {args}: {e}")

        self.last_triggered = time.time()

class TriggerHandler:
    def __init__(self, app: Flask):
        """Initialize the TriggerHandler with an empty dictionary of triggers."""
        self.triggers: Dict[str, Trigger] = {}
        self.app = app
        self._setup_routes()

    def _setup_routes(self):
        """Set up the Flask routes for the TriggerHandler."""
        @self.app.route('/trigger/')
        def dashboard():
            return render_template('dashboard.html')

        @self.app.route('/trigger/api/get_triggers')
        def get_triggers():
            current_time = time.time()
            trigger_data = {}
            for trigger_id in self.triggers.keys():
                last_triggered = self.triggers[trigger_id].last_triggered
                if last_triggered:
                    time_since_trigger = current_time - last_triggered
                    status = 'red' if time_since_trigger <= LAST_TRIGGERED_DISPLAY_TIME else 'green'
                else:
                    status = 'green'
                trigger_data[trigger_id] = {
                    'last_triggered': last_triggered,
                    'status': status
                }
            return jsonify(trigger_data)
        
        self.app.route("/trigger/<triggerId>")(self.trigger)
        
    def trigger_exists(self, triggerId: str) -> bool:
        """Check if a trigger exists in the handler."""
        return triggerId in self.triggers
    
    def get_trigger(self, triggerId: str) -> Trigger:
        """Retrieve a trigger by its ID."""
        if not self.trigger_exists(triggerId):
            logging.error(f"Trigger with ID '{triggerId}' not found")
            raise TriggerNotFoundError(f"Trigger with ID '{triggerId}' not found")
        return self.triggers[triggerId]

    def add(self, triggerId: str):
        """Create a new trigger with the specified ID."""
        if self.trigger_exists(triggerId):  
            logging.warning(f"Trigger with ID {triggerId} already exists")
            return
        self.triggers[triggerId] = Trigger(triggerId)
        logging.info(f"Trigger {triggerId} created")

    def remove(self, triggerId: str):
        """Delete a trigger by its ID."""
        trigger = self.get_trigger(triggerId)  # This will raise TriggerNotFoundError if not found
        del self.triggers[triggerId]
        logging.info(f"Trigger {triggerId} deleted")
        
    def get_callbacks(self, triggerId: str) -> Dict[str, Tuple[Callable, Tuple]]:
        """Get all callbacks associated with a trigger."""
        return self.get_trigger(triggerId).callbacks
        
    def clear_callbacks(self, triggerId: str):
        """Clear all callbacks from a specific trigger."""
        self.get_trigger(triggerId).clear_callbacks()
        logging.info(f"Callbacks cleared for trigger {triggerId}")
        
    def add_callback(self, triggerId: str, callbackId: str, callback: Tuple[Callable, Tuple]):
        """Add a callback to a specific trigger."""
        self.get_trigger(triggerId).add_callback(callbackId, callback)
        logging.debug(f"Callback {callbackId} added to trigger {triggerId}")
        
    def remove_callback(self, triggerId: str, callbackId: str):
        """Remove a callback from a specific trigger."""
        self.get_trigger(triggerId).remove_callback(callbackId)
        logging.debug(f"Callback {callbackId} removed from trigger {triggerId}")
        
    def trigger(self, triggerId: str):
        """Execute all callbacks associated with a specific trigger."""
        try:
            self.get_trigger(triggerId).trigger()
            return "", 200
        except Exception as e:
            logging.error(f"Error executing callbacks for trigger {triggerId}: {e}")
            return "", 500

if __name__ == '__main__':
    app = Flask(__name__)
    handler = TriggerHandler(app)
    handler.add('test')
    app.run(debug=True)