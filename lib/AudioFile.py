import pygame
import os

class AudioFile:
    def __init__(self, filePath, id, volume=1):
        self.filePath = filePath
        self.id = id 
        self.volume = volume
        self.playing = False

        if not os.path.isfile(self.filePath):
            raise ValueError("File not found")
        
        self.sound = pygame.mixer.Sound(self.filePath)
        self.sound.set_volume(self.volume)
        
    def play(self):
        self.sound.play()
        self.playing = True

    def stop(self):
        self.sound.stop()
        self.playing = False

class AudioFileHandler:
    def __init__(self):
        self.audioFiles = {}
        pygame.mixer.init()

    def add(self, id, filePath,volume: float=1.0):
        if id is None:
            raise ValueError("ID cannot be None")
        elif id in self.audioFiles:
            raise ValueError("ID already in use")
        
        audioFile = AudioFile(filePath, id, volume)

        self.audioFiles[audioFile.id] = audioFile
    
    def play(self, id):
        if id not in self.audioFiles:
            raise ValueError("ID not found")
        
        if not self.audioFiles[id].playing:
            self.audioFiles[id].play()
    
    def stop(self, id):
        if id not in self.audioFiles:
            return ValueError("ID not found")
        
        if self.audioFiles[id].playing:
            self.audioFiles[id].stop()

    def delete(self, id):
        if self.id_exists(id):
            del self.audioFiles[id]

    def id_exists(self, id):
        return id in self.audioFiles

if __name__ == '__main__':
    audioFileHandler = AudioFileHandler()
    audioFileHandler.add(1, "audio_files/rickroll.wav", 0.5)
    audioFileHandler.play(1)
    while True:
        pass