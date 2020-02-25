import pygame

BEEP_FILENAME = 'sound/beep.wav'


class Chip8SoundHandler(object):
	def __init__(self):
		pygame.mixer.init()
		pygame.mixer.music.load(BEEP_FILENAME)
		self.is_playing = False

	def play(self):
		if not self.is_playing:
			pygame.mixer.music.play(-1)
			self.is_playing = True

	def stop(self):
		if self.is_playing:
			pygame.mixer.music.stop()
			self.is_playing = False
