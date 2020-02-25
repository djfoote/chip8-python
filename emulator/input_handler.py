import sys

import pygame

KEY_MAPPING = {
	0x0: pygame.K_0,
	0x1: pygame.K_1,
	0x2: pygame.K_2,
	0x3: pygame.K_3,
	0x4: pygame.K_4,
	0x5: pygame.K_5,
	0x6: pygame.K_6,
	0x7: pygame.K_7,
	0x8: pygame.K_8,
	0x9: pygame.K_9,
	0xA: pygame.K_a,
	0xB: pygame.K_b,
	0xC: pygame.K_c,
	0xD: pygame.K_d,
	0xE: pygame.K_e,
	0xF: pygame.K_f,
}


class Chip8InputHandler(object):
	def get_pressed_keys(self):
		pressed_keyboard_keys = pygame.key.get_pressed()
		pressed_chip8_keys = set()
		for chip8_key, keyboard_key in KEY_MAPPING.items():
			if pressed_keyboard_keys[keyboard_key]:
				pressed_chip8_keys.add(chip8_key)
		return pressed_chip8_keys

	def wait_for_keypress(self):
		while True:
			event = pygame.event.wait()
			if event.type == pygame.QUIT:
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				for candidate_key in range(0x10):
					if event.key == KEY_MAPPING[candidate_key]:
						return candidate_key
