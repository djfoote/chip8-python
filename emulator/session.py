import pygame

from emulator import cpu
from emulator import input_handler
from emulator import screen
from emulator import sound

TIMER_PERIOD = 1000 // 60

FONT_FILENAME = 'font/font.ch8'

TIMER_EVENT = pygame.USEREVENT + 1


class Chip8Session(object):
	def __init__(self, rom_path):
		self.screen = screen.Chip8Screen()
		self.input_handler = input_handler.Chip8InputHandler()
		self.sound_handler = sound.Chip8SoundHandler()

		self.cpu = cpu.Chip8CPU(
				self.screen, self.input_handler, self.sound_handler)
		self.cpu.load_font(FONT_FILENAME)
		self.cpu.load_rom(rom_path)

	def start(self):
		pygame.init()
		pygame.time.set_timer(TIMER_EVENT, TIMER_PERIOD) 

		while True:
			if pygame.event.get(pygame.QUIT):
				break
			if pygame.event.get(TIMER_EVENT):
				self.cpu.decrement_timers()
			pygame.event.pump()

			return_code = self.cpu.execute_instruction()
			if return_code:
				break
