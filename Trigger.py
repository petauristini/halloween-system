import logging
from typing import Callable, Dict, Tuple

logging.basicConfig(level=logging.INFO)

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

class TriggerHandler:
    def __init__(self):
        """Initialize the TriggerHandler with an empty dictionary of triggers."""
        self.triggers: Dict[str, Trigger] = {}

    def trigger_exists(self, triggerId: str) -> bool:
        """Check if a trigger exists in the handler."""
        return triggerId in self.triggers
    
    def get_trigger(self, triggerId: str) -> Trigger:
        """Retrieve a trigger by its ID."""
        if not self.trigger_exists(triggerId):
            logging.error(f"Trigger with ID '{triggerId}' not found")
            raise TriggerNotFoundError(f"Trigger with ID '{triggerId}' not found")
        return self.triggers[triggerId]

    def create(self, triggerId: str):
        """Create a new trigger with the specified ID."""
        if self.trigger_exists(triggerId):
            print("I WILL KILL YOU")
            logging.warning(f"Trigger with ID {triggerId} already exists")
            return
        self.triggers[triggerId] = Trigger(triggerId)
        logging.info(f"Trigger {triggerId} created")

    def delete(self, triggerId: str):
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
        logging.info(f"Trigger {triggerId} is executing callbacks")
        self.get_trigger(triggerId).trigger()
