import pygame
import random
import sys
import math

pygame.init()

WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Square Collecting Game")

RED = (200, 0, 0)
BLUE = (0, 0, 200)
ORANGE = (255, 165, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

LIGHT_RED = (255, 50, 50)
LIGHT_BLUE = (50, 50, 255)

clock = pygame.time.Clock()
FPS = 60
FAST_FPS = FPS * 4
fast_forward = False

SQUARE_SIZE = 50
BORDER_THICKNESS = 4
BASE_SPEED = 3
MAX_SPEED = 6
MIN_SPEED = 1

class BigSquare:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
        self.color = color
        self.border_color = WHITE
        self.health = 100
        self.mass = 1
        self.velocity = pygame.math.Vector2(random.choice([-BASE_SPEED, BASE_SPEED]),
                                            random.choice([-BASE_SPEED, BASE_SPEED]))
        self.current_speed = BASE_SPEED
        self.collected = 0

    def move(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

    def handle_boundary_collision(self):
        collided = False
        if self.rect.left <= BORDER_THICKNESS:
            self.rect.left = BORDER_THICKNESS
            self.velocity.x *= -1
            collided = True
        elif self.rect.right >= WIDTH - BORDER_THICKNESS:
            self.rect.right = WIDTH - BORDER_THICKNESS
            self.velocity.x *= -1
            collided = True
        if self.rect.top <= BORDER_THICKNESS:
            self.rect.top = BORDER_THICKNESS
            self.velocity.y *= -1
            collided = True
        elif self.rect.bottom >= HEIGHT - BORDER_THICKNESS:
            self.rect.bottom = HEIGHT - BORDER_THICKNESS
            self.velocity.y *= -1
            collided = True
        if collided:
            angle = random.uniform(-15, 15)
            self.velocity = self.velocity.rotate(angle)

    def update_speed(self):
        current_size = self.rect.width
        self.current_speed = BASE_SPEED * (SQUARE_SIZE / current_size)
        self.current_speed = min(BASE_SPEED, self.current_speed)
        self.current_speed = max(MIN_SPEED, self.current_speed)
        if self.velocity.length() != 0:
            self.velocity = self.velocity.normalize() * self.current_speed

    def update_size(self):
        size = int(SQUARE_SIZE * self.health / 100)
        size = min(size, SQUARE_SIZE)
        size = max(10, size)
        center = self.rect.center
        self.rect.width = size
        self.rect.height = size
        self.rect.center = center
        self.update_speed()

    def draw(self, surface):
        max_radius = self.rect.width // 2
        radius = int(max_radius * (1 - self.health / 100))
        pygame.draw.rect(surface, self.border_color, self.rect, border_radius=radius)
        inner_rect = self.rect.inflate(-BORDER_THICKNESS * 2, -BORDER_THICKNESS * 2)
        pygame.draw.rect(surface, self.color, inner_rect, border_radius=radius)

    def handle_collision(self, other, background_color):
        if self.rect.colliderect(other.rect):
            dx = min(self.rect.right - other.rect.left, other.rect.right - self.rect.left)
            dy = min(self.rect.bottom - other.rect.top, other.rect.bottom - self.rect.top)
            if dx < dy:
                if self.rect.centerx < other.rect.centerx:
                    self.rect.right -= dx / 2
                    other.rect.left += dx / 2
                    normal = pygame.math.Vector2(-1, 0)
                else:
                    self.rect.left += dx / 2
                    other.rect.right -= dx / 2
                    normal = pygame.math.Vector2(1, 0)
            else:
                if self.rect.centery < other.rect.centery:
                    self.rect.bottom -= dy / 2
                    other.rect.top += dy / 2
                    normal = pygame.math.Vector2(0, -1)
                else:
                    self.rect.top += dy / 2
                    other.rect.bottom -= dy / 2
                    normal = pygame.math.Vector2(0, 1)
            relative_velocity = self.velocity - other.velocity
            vel_along_normal = relative_velocity.dot(normal)
            if vel_along_normal > 0:
                return
            restitution = 1
            impulse = -(1 + restitution) * vel_along_normal
            impulse /= (1 / self.mass + 1 / other.mass)
            impulse_vector = normal * impulse
            self.velocity += impulse_vector / self.mass
            other.velocity -= impulse_vector / other.mass
            angle1 = random.uniform(-10, 10)
            angle2 = random.uniform(-10, 10)
            self.velocity = self.velocity.rotate(angle1)
            other.velocity = other.velocity.rotate(angle2)
            if background_color == other.color and self.color != other.color:
                self.take_damage(10)
                other.recover_health(3)
                if self.health == 0 and self in big_squares:
                    big_squares.remove(self)
            elif background_color == self.color and self.color != other.color:
                other.take_damage(10)
                self.recover_health(3)
                if other.health == 0 and other in big_squares:
                    big_squares.remove(other)

    def take_damage(self, amount):
        self.health = max(self.health - amount, 0)
        self.update_size()

    def recover_health(self, amount):
        self.health = min(self.health + amount, 100)
        self.update_size()

def spawn_small_square():
    x = random.randint(20, WIDTH - 30)
    y = random.randint(20, HEIGHT - 30)
    total_collected = red_square.collected + blue_square.collected
    if total_collected == 0:
        color = random.choice([RED, BLUE])
    else:
        red_advantage = (blue_square.collected - red_square.collected) / total_collected
        if random.random() < 0.5 + red_advantage * 0.5:
            color = RED
        else:
            color = BLUE
    border_color = WHITE
    return {"rect": pygame.Rect(x, y, 10, 10), "color": color, "border": border_color}

red_square = BigSquare(100, 100, RED)
blue_square = BigSquare(450, 450, BLUE)
big_squares = [red_square, blue_square]

small_squares = [spawn_small_square() for _ in range(4)]

background_color = ORANGE
GAME_OVER = False

def respawn_small_square():
    if len(small_squares) < 4:
        small_squares.append(spawn_small_square())

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                fast_forward = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                fast_forward = False
    if not GAME_OVER:
        for square in big_squares:
            square.move()
            square.handle_boundary_collision()
        for i in range(len(big_squares)):
            for j in range(i + 1, len(big_squares)):
                big_squares[i].handle_collision(big_squares[j], background_color)
        for square in big_squares:
            for small_square in small_squares[:]:
                if square.rect.colliderect(small_square["rect"]):
                    if small_square["color"] == square.color:
                        background_color = square.color
                    square.collected += 1
                    small_squares.remove(small_square)
                    respawn_small_square()
        if len(big_squares) <= 1:
            GAME_OVER = True
        elif len(big_squares) == 0:
            print("Draw!")
            GAME_OVER = True
    screen.fill(background_color)
    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), BORDER_THICKNESS)
    for square in big_squares:
        square.draw(screen)
    for small_square in small_squares:
        pygame.draw.rect(screen, small_square["border"], small_square["rect"].inflate(2, 2), border_radius=2)
        pygame.draw.rect(screen, small_square["color"], small_square["rect"], border_radius=2)
    for square in big_squares:
        if square.color == RED:
            pygame.draw.rect(screen, LIGHT_RED, (20, HEIGHT - 40, square.health * 2, 20))
            pygame.draw.rect(screen, WHITE, (20, HEIGHT - 40, 200, 20), 2)
    for square in big_squares:
        if square.color == BLUE:
            pygame.draw.rect(screen, LIGHT_BLUE, (WIDTH - 220, HEIGHT - 40, square.health * 2, 20))
            pygame.draw.rect(screen, WHITE, (WIDTH - 220, HEIGHT - 40, 200, 20), 2)
    if GAME_OVER:
        font = pygame.font.SysFont(None, 48)
        if len(big_squares) == 0:
            text = font.render("Draw!", True, BLACK)
        elif len(big_squares) == 1:
            winner = "Red Square" if big_squares[0].color == RED else "Blue Square"
            text = font.render(f"{winner} Wins!", True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, text_rect)
    pygame.display.flip()
    if fast_forward:
        clock.tick(FAST_FPS)
    else:
        clock.tick(FPS)
pygame.quit()
sys.exit()
