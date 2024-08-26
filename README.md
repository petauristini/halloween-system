# halloween-system

### Example usage for smoke functionality:
    # initialise a smoke module on pin 17
    smoke_module = SmokeModule(17)
    # (permanently) turn on the smoke module
    smoke_module.turn_on()
    # wait for three seconds
    time.sleep(3)
    # (permanently) turn off the smoke module
    smoke_module.turn_off()
    # wait for two seconds
    time.sleep(2)
    # turn on the smoke module for 5 seconds
    smoke_module.turn_on_for(5)

### Example usage for led functionality:
