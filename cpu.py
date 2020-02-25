import curses
import itertools
import random
import sys

import pygame

import disassembler

MEMORY_SIZE = 0x1000
PC_START = 0x200
SPRITE_WIDTH = 8
TIMER_PERIOD = 1000 // 60
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
PIXEL_SIZE = 10
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

TIMER_EVENT = pygame.USEREVENT + 1


class Chip8CPU(object):
	def __init__(self, screen, input_handler):
		self.memory = []
		self.pc = 0x0
		self.registers = [0x0] * 0x10
		self.address_register = 0x0
		self.stack = []
		self.delay_timer = 0
		self.sound_timer = 0
		self.screen = screen
		self.input_handler = input_handler

	def clear_screen(self):
		self.screen.clear()

	def load_rom(self, rom_path):
		with open(rom_path, 'rb') as f:
			code_buffer = f.read()

		self.pc = PC_START
		self.memory = [0b0] * MEMORY_SIZE
		for byte_number, byte in enumerate(code_buffer):
			self.memory[self.pc + byte_number] = byte

	def decrement_timers(self):
		if self.delay_timer:
			self.delay_timer -= 1
		if self.sound_timer:
			self.sound_timer -= 1

	def execute_instruction(self):
		if self.pc >= MEMORY_SIZE - 1:
			return 1

		opcode = (self.memory[self.pc] << 8) + self.memory[self.pc + 1]

		first_nibble = opcode >> 12
		x = (opcode >> 8) & 0xF
		y = (opcode >> 4) & 0xF
		nnn = opcode & 0x0FFF
		nn = opcode & 0x00FF
		n = opcode & 0x000F

		self.pc += 2

		if first_nibble == 0x0:
			if opcode == 0x00E0:
				self.clear_screen()
				self.screen.flush()
			elif opcode == 0x00EE:
				self.pc = self.stack.pop()
			else:
				raise ValueError('Invalid instruction ' + format(opcode, '04x'))

		elif first_nibble == 0x1:
			self.pc = nnn

		elif first_nibble == 0x2:
			self.stack.append(self.pc)
			self.pc = nnn

		elif first_nibble == 0x3:
			if self.registers[x] == nn:
				self.pc += 2

		elif first_nibble == 0x4:
			if self.registers[x] != nn:
				self.pc += 2

		elif first_nibble == 0x5:
			if self.registers[x] == self.registers[y]:
				self.pc += 2

		elif first_nibble == 0x6:
			self.registers[x] = nn

		elif first_nibble == 0x7:
			self.registers[x] += nn
			self.registers[x] &= 0xFF

		elif first_nibble == 0x8:
			if n == 0x0:
				self.registers[x] = self.registers[y]
			elif n == 0x1:
				self.registers[x] |= self.registers[y]
			elif n == 0x2:
				self.registers[x] &= self.registers[y]
			elif n == 0x3:
				self.registers[x] ^= self.registers[y]
			elif n == 0x4:
				self.registers[x] += self.registers[y]
				self.registers[0xF] = int(self.registers[x] > 0xFF)
				self.registers[x] &= 0xFF
			elif n == 0x5:
				self.registers[0xF] = int(self.registers[x] >= self.registers[y])
				self.registers[x] -= self.registers[y]
				self.registers[x] &= 0xFF
			elif n == 0x6:
				self.registers[0xF] = self.registers[x] & 0x1
				self.registers[x] >>= 1
			elif n == 0x7:
				self.registers[0xF] = int(self.registers[y] >= self.registers[x])
				self.registers[x] = self.registers[y] - self.registers[x]
				self.registers[x] &= 0xFF
			elif n == 0xE:
				self.registers[0xF] = (self.registers[x] & 0x80) >> 7
				self.registers[x] <<= 1
				self.registers[x] &= 0xFF
			else:
				raise ValueError('Invalid instruction ' + format(opcode, '04x'))

		elif first_nibble == 0x9:
			if self.registers[x] != self.registers[y]:
				self.pc += 2

		elif first_nibble == 0xA:
			self.address_register = nnn

		elif first_nibble == 0xB:
			self.pc = self.registers[0] + nnn

		elif first_nibble == 0xC:
			self.registers[x] = random.randint(0, 0xFF) & nn

		elif first_nibble == 0xD:
			row_anchor = self.registers[y]
			col_anchor = self.registers[x]
			sprite = self.memory[self.address_register : self.address_register + n]
			collision = self.screen.draw_sprite(col_anchor, row_anchor, sprite)
			self.registers[0xF] = int(collision)
			self.screen.flush()

		elif first_nibble == 0xE:
			if nn == 0x9E:
				if self.registers[x] in self.input_handler.get_pressed_keys():
					self.pc += 2
			elif nn == 0xA1:
				if self.registers[x] not in self.input_handler.get_pressed_keys():
					self.pc += 2
			else:
				raise ValueError('Invalid instruction ' + format(opcode, '04x'))

		elif first_nibble == 0xF:
			if nn == 0x07:
				self.registers[x] = self.delay_timer
			elif nn == 0x0A:
				self.registers[x] = self.input_handler.wait_for_keypress()
			elif nn == 0x15:
				self.delay_timer = self.registers[x]
			elif nn == 0x18:
				self.sound_timer = self.registers[x]
			elif nn == 0x1E:
				self.address_register += self.registers[x]
				self.registers[0xF] = int(self.address_register > 0xFFF)
				self.address_register &= 0xFFF
			elif nn == 0x29:
				# TODO: handle fonts (I = sprite_address[V{x}])
				self.address_register = 0x000
			elif nn == 0x33:
				number = self.registers[x]
				self.memory[self.address_register] = (number // 100) % 10
				self.memory[self.address_register] = (number // 10) % 10
				self.memory[self.address_register] = number % 10
			elif nn == 0x55:
				for i in range(x + 1):
					self.memory[self.address_register + i] = self.registers[i]
			elif nn == 0x65:
				for i in range(x + 1):
					self.registers[i] = self.memory[self.address_register + i]
			else:
				raise ValueError('Invalid instruction ' + format(opcode, '04x'))

		else:
			raise ValueError('Memory is not a list of bytes.')

		return 0


class Chip8Screen(object):
	def __init__(self):
		self.screen = pygame.display.set_mode((SCREEN_WIDTH * PIXEL_SIZE,
		                                       SCREEN_HEIGHT * PIXEL_SIZE))
		self.clear()

	def flush(self):
		pygame.display.flip()

	def clear(self):
		self.bitmap = [[False] * SCREEN_HEIGHT for _ in range(SCREEN_WIDTH)]
		self.screen.fill(BLACK)

	def get_pixel(self, x, y):
		return self.bitmap[x][y]

	def toggle_pixel(self, x, y):
		self.bitmap[x][y] ^= 1
		color = WHITE if self.bitmap[x][y] else BLACK
		pygame.draw.rect(self.screen, color,
		                 pygame.Rect(x * PIXEL_SIZE, y * PIXEL_SIZE,
		                             PIXEL_SIZE, PIXEL_SIZE))

	def draw_sprite(self, x_anchor, y_anchor, sprite):
		collision = False
		for y_offset in range(len(sprite)):
			for x_offset in range(SPRITE_WIDTH):
				complement = SPRITE_WIDTH - x_offset - 1
				sprite_pixel = (sprite[y_offset] & (1 << complement)) >> complement
				x, y = x_anchor + x_offset, y_anchor + y_offset
				if sprite_pixel and is_on_screen(x, y):
					prev_pixel = self.get_pixel(x, y)
					self.toggle_pixel(x, y)
					collision |= prev_pixel & sprite_pixel
		return collision


def is_on_screen(x, y):
	return x >= 0 and x < SCREEN_WIDTH and y >= 0 and y < SCREEN_HEIGHT


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
	def __init__(self):
		pass

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


class Chip8Session(object):
	def __init__(self, rom_path):
		self.screen = Chip8Screen()
		self.input_handler = Chip8InputHandler()

		self.cpu = Chip8CPU(self.screen, self.input_handler)
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


if __name__ == '__main__':
	rom_path = sys.argv[1]

	session = Chip8Session(rom_path)
	session.start()
