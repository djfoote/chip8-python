import pygame

SPRITE_WIDTH = 8
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
PIXEL_SIZE = 10
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


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
