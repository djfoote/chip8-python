import random
import sys

import pygame

MEMORY_SIZE = 0x1000
PC_START = 0x200
FONT_SPRITE_SIZE = 5
FONT_MEMORY_LOCATION = 0x0


class Chip8CPU(object):
	def __init__(self, screen, input_handler, sound_handler):
		self.memory = []
		self.pc = PC_START
		self.registers = [0x0] * 0x10
		self.address_register = 0x0
		self.stack = []
		self.delay_timer = 0
		self.sound_timer = 0
		self.screen = screen
		self.input_handler = input_handler
		self.sound_handler = sound_handler

		self.memory = [0b0] * MEMORY_SIZE

	def clear_screen(self):
		self.screen.clear()

	def load_rom(self, rom_path, is_font=False):
		with open(rom_path, 'rb') as f:
			code_buffer = f.read()

		program_start = FONT_MEMORY_LOCATION if is_font else PC_START
		for byte_number, byte in enumerate(code_buffer):
			self.memory[program_start + byte_number] = byte

	def load_font(self, rom_path):
		self.load_rom(rom_path, is_font=True)

	def decrement_timers(self):
		if self.delay_timer:
			self.delay_timer -= 1
		if self.sound_timer:
			self.sound_handler.play()
			self.sound_timer -= 1
			if not self.sound_timer:
				self.sound_handler.stop()

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
				relative_address = self.registers[x] * FONT_SPRITE_SIZE
				self.address_register = FONT_MEMORY_LOCATION + relative_address
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
