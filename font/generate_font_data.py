FONT_MAPS_FILE = 'font/font_maps.txt'
FONT_BYTES_FILE = 'font/font.ch8'

with open(FONT_MAPS_FILE, 'r') as f:
	lines = f.readlines()

font_bytes = []

for line in lines:
	line = line.strip('\n')
	if line:
		binary = line.replace('.', '1').replace(' ', '0').ljust(4, '0')
		assert len(binary) == 4
		font_bytes.append(int(binary, 2) << 4)

with open(FONT_BYTES_FILE, 'wb') as f:
	f.write(bytes(font_bytes))
