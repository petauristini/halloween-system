import AudioStream

audioStreamServerHandler = AudioStream.StreamServerHandler()
audioStreamServerHandler.add(id=1, port=7000)
audioStreamServerHandler.start(1)