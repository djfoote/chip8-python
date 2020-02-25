import sys


def disassemble_rom(rom):
	with open(rom, 'rb') as f:
		code_buffer = f.read()

	pc = 0x200
	memory = [0x00] * pc + list(code_buffer)
	if len(memory) % 2 == 1:
		memory.append(0b0)

	while pc < len(memory):
		print(get_disassembled_line(memory, pc))
		pc += 2


def get_disassembled_line(memory, pc):
	pc_string = format(pc, '04x')
	opcode_string = format(memory[pc], '02x') + format(memory[pc+1], '02x')
	disassembled_string = disassemble_op(memory, pc)
	return f'{pc_string} {opcode_string} {disassembled_string}'


def disassemble_op(memory, pc):
	opcode = (memory[pc] << 8) + memory[pc + 1]

	first_nibble = opcode >> 12
	x = format((opcode >> 8) & 0xF, 'x')
	y = format((opcode >> 4) & 0xF, 'x')
	nnn = format(opcode & 0x0FFF, '03x')
	nn = format(opcode & 0x00FF, '02x')
	n = format(opcode & 0xF, 'x')

	if first_nibble == 0x0:
		if opcode == 0x00E0:
			return 'clear screen'
		elif opcode == 0x00EE:
			return 'return'
		else:
			return f'Call RCA 1802 program at address {nnn}'

	elif first_nibble == 0x1:
		return f'goto {nnn}'

	elif first_nibble == 0x2:
		return f'call subroutine at {nnn}'

	elif first_nibble == 0x3:
		return f'if (V{x} == {nn}) PC+=2'

	elif first_nibble == 0x4:
		return f'if (V{x} != {nn}) PC+=2'

	elif first_nibble == 0x5:
		return f'if (V{x} == V{y}) PC+=2'

	elif first_nibble == 0x6:
		return f'V{x} = {nn}'

	elif first_nibble == 0x7:
		return f'V{x} += {nn}'

	elif first_nibble == 0x8:
		if int(n, 16) == 0x0:
			return f'V{x} = V{y}'
		elif int(n, 16) == 0x1:
			return f'V{x} |= V{y}'
		elif int(n, 16) == 0x2:
			return f'V{x} &= V{y}'
		elif int(n, 16) == 0x3:
			return f'V{x} ^= V{y}'
		elif int(n, 16) == 0x4:
			return f'V{x} += V{y}'
		elif int(n, 16) == 0x5:
			return f'V{x} -= V{y}'
		elif int(n, 16) == 0x6:
			return f'V{x} >>= 1'
		elif int(n, 16) == 0x7:
			return f'V{x} = V{y} - V{x}'
		elif int(n, 16) == 0xE:
			return f'V{x} <<= 1'
		else:
			return 'unrecognized opcode'

	elif first_nibble == 0x9:
		return f'if (V{x} != V{y}) PC+=2'

	elif first_nibble == 0xA:
		return f'I = {nnn}'

	elif first_nibble == 0xB:
		return f'PC=V0 + {nnn}'

	elif first_nibble == 0xC:
		return f'V{x} = rand() & {nn}'

	elif first_nibble == 0xD:
		return f'draw(V{x}, V{y}, {n})'

	elif first_nibble == 0xE:
		if int(nn, 16) == 0x9E:
			return f'if (V{x} in pressed_keys()) PC += 2'
		elif int(nn, 16) == 0xA1:
			return f'if (V{x} not in pressed_keys()) PC += 2'
		else:
			return 'unrecognized opcode'

	elif first_nibble == 0xF:
		if int(nn, 16) == 0x07:
			return f'V{x} = get_delay()'
		elif int(nn, 16) == 0x0A:
			return f'V{x} = get_key()'
		elif int(nn, 16) == 0x15:
			return f'set_delay_timer(V{x})'
		elif int(nn, 16) == 0x18:
			return f'set_sound_timer(V{x})'
		elif int(nn, 16) == 0x1E:
			return f'I += V{x}'
		elif int(nn, 16) == 0x29:
			return f'I = sprite_address[V{x}]'
		elif int(nn, 16) == 0x33:
			return f'set_BCD(V{x})'
		elif int(nn, 16) == 0x55:
			return f'dump_registers({x}, I)'
		elif int(nn, 16) == 0x65:
			return f'load_registers({x}, I)'
		else:
			return 'unrecognized opcode'

	else:
		raise ValueError('Memory is not a list of bytes.')


def main():
	disassemble_rom(sys.argv[1])


if __name__ == '__main__':
	main()