import sys

from emulator import session


def main():
	rom_path = sys.argv[1]
	chip8_session = session.Chip8Session(rom_path)
	chip8_session.start()


if __name__ == '__main__':
	main()
