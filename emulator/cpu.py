import random
import sys

import pygame

MEMORY_SIZE = 0x1000
PC_START = 0x200
FONT_SPRITE_SIZE = 5
FONT_MEMORY_LOCATION = 0x0


class Chip8CPU(object):

	# ==============
	# INITIALIZATION
	# ==============

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

		self.opcode_dispatch_dict = {
			0x0: self.handle_0_instructions,
			0x1: self.goto,
			0x2: self.call_subroutine,
			0x3: self.skip_if_equal,
			0x4: self.skip_if_not_equal,
			0x5: self.skip_if_reg_equal,
			0x6: self.assign_constant,
			0x7: self.add_constant,
			0x8: self.dispatch_arithmetic_op,
			0x9: self.skip_if_reg_not_equal,
			0xA: self.set_address_register,
			0xB: self.jump_relative,
			0xC: self.get_random_number,
			0xD: self.draw_sprite,
			0xE: self.handle_keypress_op,
			0xF: self.dispatch_io_op,
		}

		self.arithmetic_op_dispatch_dict = {
			0x0: self.assign,
			0x1: self.assign_or,
			0x2: self.assign_and,
			0x3: self.assign_xor,
			0x4: self.assign_add,
			0x5: self.assign_subtract,
			0x6: self.assign_right_shift,
			0x7: self.assign_subtract_reversed,
			0xE: self.assign_left_shift,
		}

		self.io_op_dispatch_dict = {
			0x07: self.get_delay,
			0x0A: self.wait_for_keypress,
			0x15: self.set_delay,
			0x18: self.set_sound_timer,
			0x1E: self.add_to_address_register,
			0x29: self.get_font_sprite_address,
			0x33: self.set_binary_coded_decimal,
			0x55: self.dump_registers,
			0x65: self.load_registers,
		}

	# ==================
	# CORE FUNCTIONALITY
	# ==================

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
		self.pc += 2
		self.dispatch_opcode(opcode)
		return 0

	def dispatch_opcode(self, opcode):
		first_nibble = opcode >> 12
		try:
			self.opcode_dispatch_dict[first_nibble](opcode)
		except KeyError:
			raise ValueError('Invalid instruction ' + format(opcode, '04x'))		

	# ===============
	# CORE OPERATIONS
	# ===============

	def handle_0_instructions(self, opcode):
		if opcode == 0x00E0:
			self.clear_screen()
			self.screen.flush()
		elif opcode == 0x00EE:
			self.pc = self.stack.pop()
		else:
			raise ValueError('Invalid instruction ' + format(opcode, '04x'))

	def goto(self, opcode):
		nnn = opcode & 0x0FFF
		self.pc = nnn

	def call_subroutine(self, opcode):
		nnn = opcode & 0x0FFF
		self.stack.append(self.pc)
		self.pc = nnn

	def skip_if_equal(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		if self.registers[x] == nn:
			self.pc += 2

	def skip_if_not_equal(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		if self.registers[x] != nn:
			self.pc += 2

	def skip_if_reg_equal(self, opcode):
		x = (opcode >> 8) & 0xF
		y = (opcode >> 4) & 0xF
		if self.registers[x] == self.registers[y]:
			self.pc += 2

	def assign_constant(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		self.registers[x] = nn

	def add_constant(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		self.registers[x] += nn
		self.registers[x] &= 0xFF

	def dispatch_arithmetic_op(self, opcode):
		x = (opcode >> 8) & 0xF
		y = (opcode >> 4) & 0xF
		n = opcode & 0x000F
		try:
			self.arithmetic_op_dispatch_dict[n](x, y)
		except KeyError:
			raise ValueError('Invalid instruction ' + format(opcode, '04x'))

	def skip_if_reg_not_equal(self, opcode):
		x = (opcode >> 8) & 0xF
		y = (opcode >> 4) & 0xF
		if self.registers[x] != self.registers[y]:
			self.pc += 2

	def set_address_register(self, opcode):
		nnn = opcode & 0x0FFF
		self.address_register = nnn

	def jump_relative(self, opcode):
		nnn = opcode & 0x0FFF
		self.pc = self.registers[0] + nnn

	def get_random_number(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		self.registers[x] = random.randint(0, 0xFF) & nn

	def draw_sprite(self, opcode):
		x = (opcode >> 8) & 0xF
		y = (opcode >> 4) & 0xF
		n = opcode & 0x000F
		row_anchor = self.registers[y]
		col_anchor = self.registers[x]
		sprite = self.memory[self.address_register : self.address_register + n]
		collision = self.screen.draw_sprite(col_anchor, row_anchor, sprite)
		self.registers[0xF] = int(collision)
		self.screen.flush()

	def handle_keypress_op(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		if nn == 0x9E:
			if self.registers[x] in self.input_handler.get_pressed_keys():
				self.pc += 2
		elif nn == 0xA1:
			if self.registers[x] not in self.input_handler.get_pressed_keys():
				self.pc += 2
		else:
			raise ValueError('Invalid instruction ' + format(opcode, '04x'))

	def dispatch_io_op(self, opcode):
		x = (opcode >> 8) & 0xF
		nn = opcode & 0x00FF
		try:
			self.io_op_dispatch_dict[nn](x)
		except KeyError:
			raise ValueError('Invalid instruction ' + format(opcode, '04x'))

	# =====================
	# ARITHMETIC OPERATIONS
	# =====================

	def assign(self, x, y):
		self.registers[x] = self.registers[y]

	def assign_or(self, x, y):
		self.registers[x] |= self.registers[y]

	def assign_and(self, x, y):
		self.registers[x] &= self.registers[y]

	def assign_xor(self, x, y):
		self.registers[x] ^= self.registers[y]

	def assign_add(self, x, y):
		self.registers[x] += self.registers[y]
		self.registers[0xF] = int(self.registers[x] > 0xFF)
		self.registers[x] &= 0xFF

	def assign_subtract(self, x, y):
		self.registers[0xF] = int(self.registers[x] >= self.registers[y])
		self.registers[x] -= self.registers[y]
		self.registers[x] &= 0xFF

	def assign_right_shift(self, x, y):
		self.registers[0xF] = self.registers[x] & 0x1
		self.registers[x] >>= 1

	def assign_subtract_reversed(self, x, y):
		self.registers[0xF] = int(self.registers[y] >= self.registers[x])
		self.registers[x] = self.registers[y] - self.registers[x]
		self.registers[x] &= 0xFF

	def assign_left_shift(self, x, y):
		self.registers[0xF] = (self.registers[x] & 0x80) >> 7
		self.registers[x] <<= 1
		self.registers[x] &= 0xFF

	# =============
	# IO OPERATIONS
	# =============

	def get_delay(self, x):
		self.registers[x] = self.delay_timer

	def wait_for_keypress(self, x):
		self.registers[x] = self.input_handler.wait_for_keypress()

	def set_delay(self, x):
		self.delay_timer = self.registers[x]

	def set_sound_timer(self, x):
		self.sound_timer = self.registers[x]

	def add_to_address_register(self, x):
		self.address_register += self.registers[x]
		self.registers[0xF] = int(self.address_register > 0xFFF)
		self.address_register &= 0xFFF

	def get_font_sprite_address(self, x):
		relative_address = self.registers[x] * FONT_SPRITE_SIZE
		self.address_register = FONT_MEMORY_LOCATION + relative_address

	def set_binary_coded_decimal(self, x):
		number = self.registers[x]
		self.memory[self.address_register] = (number // 100) % 10
		self.memory[self.address_register] = (number // 10) % 10
		self.memory[self.address_register] = number % 10

	def dump_registers(self, x):
		for i in range(x + 1):
			self.memory[self.address_register + i] = self.registers[i]

	def load_registers(self, x):
		for i in range(x + 1):
			self.registers[i] = self.memory[self.address_register + i]
