import pygame
import random
import sys
import math

pygame.init()

WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Square Collecting Game")

# Colors
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

# Mod settings
NEUTRAL_STACK_THRESHOLD = 5  # Stacks required to activate mode
NEUTRAL_MODE_DURATION = 5000  # Mode duration in ms
EXTRA_DAMAGE_PER_STACK = 0.25  # Extra damage per stack collected during mode

def get_opposite_color(color):
    if color == RED:
        return BLUE
    elif color == BLUE:
        return RED
    else:
        return ORANGE  # Default color

def circle_circle_collision(pos1, radius1, pos2, radius2):
    dist = pygame.math.Vector2(pos1).distance_to(pos2)
    return dist < radius1 + radius2

def circle_rect_collision(circle_pos, circle_radius, rect):
    circle_distance_x = abs(circle_pos[0] - rect.centerx)
    circle_distance_y = abs(circle_pos[1] - rect.centery)

    if circle_distance_x > (rect.width / 2 + circle_radius):
        return False
    if circle_distance_y > (rect.height / 2 + circle_radius):
        return False

    if circle_distance_x <= (rect.width / 2):
        return True
    if circle_distance_y <= (rect.height / 2):
        return True

    corner_distance_sq = (circle_distance_x - rect.width / 2) ** 2 + (circle_distance_y - rect.height / 2) ** 2

    return corner_distance_sq <= (circle_radius ** 2)

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
        self.stack_count = 0  # Stacks collected to enter mode
        self.mod_stack_count = 0  # Stacks collected during mode
        self.in_neutral_mode = False
        self.neutral_mode_end_time = 0
        self.extra_damage = 0  # Extra damage to deal at mode end
        self.initial_stacked_small_squares = []  # Small squares collected to enter mode
        self.mod_stacked_small_squares = []  # Small squares collected during mode

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
            angle = random.uniform(-20, 20)  # More randomness
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
        # Always draw the stacks collected to enter mode
        stack_spacing = 12  # Spacing between stacks
        start_x = self.rect.centerx - (NEUTRAL_STACK_THRESHOLD * stack_spacing) / 2
        start_y = self.rect.bottom + 5  # Below the big square
        for i in range(len(self.initial_stacked_small_squares)):
            small_rect = pygame.Rect(start_x + i * stack_spacing, start_y, 10, 10)
            pygame.draw.rect(surface, WHITE, small_rect.inflate(2, 2), border_radius=2)
            pygame.draw.rect(surface, self.initial_stacked_small_squares[i]["color"], small_rect, border_radius=2)

        if self.in_neutral_mode:
            # Only white border is visible, inside is transparent
            pygame.draw.ellipse(surface, self.border_color, self.rect, BORDER_THICKNESS)

            # Visualize stacks collected during mode
            start_x = self.rect.centerx - (self.mod_stack_count * stack_spacing) / 2
            start_y = self.rect.bottom + 20  # Below the initial stacks
            for i in range(len(self.mod_stacked_small_squares)):
                small_rect = pygame.Rect(start_x + i * stack_spacing, start_y, 10, 10)
                pygame.draw.rect(surface, WHITE, small_rect.inflate(2, 2), border_radius=2)
                pygame.draw.rect(surface, self.mod_stacked_small_squares[i]["color"], small_rect, border_radius=2)
        else:
            # Normal appearance
            max_radius = self.rect.width // 2
            radius = int(max_radius * (1 - self.health / 100))
            pygame.draw.rect(surface, self.border_color, self.rect, border_radius=radius)
            inner_rect = self.rect.inflate(-BORDER_THICKNESS * 2, -BORDER_THICKNESS * 2)
            pygame.draw.rect(surface, self.color, inner_rect, border_radius=radius)

    def handle_collision(self, other, background_color):
        collision_occurred = False
        if self.in_neutral_mode and other.in_neutral_mode:
            # Both are in mod, use circle-circle collision detection
            pos1 = self.rect.center
            radius1 = self.rect.width / 2
            pos2 = other.rect.center
            radius2 = other.rect.width / 2
            if circle_circle_collision(pos1, radius1, pos2, radius2):
                collision_occurred = True
        elif self.in_neutral_mode and not other.in_neutral_mode:
            # Self is in mod, other is not; use circle-rectangle collision detection
            pos = self.rect.center
            radius = self.rect.width / 2
            if circle_rect_collision(pos, radius, other.rect):
                collision_occurred = True
        elif not self.in_neutral_mode and other.in_neutral_mode:
            # Other is in mod, self is not; use circle-rectangle collision detection
            pos = other.rect.center
            radius = other.rect.width / 2
            if circle_rect_collision(pos, radius, self.rect):
                collision_occurred = True
        else:
            # Both are not in mod, use rectangle collision detection
            if self.rect.colliderect(other.rect):
                collision_occurred = True

        if collision_occurred:
            # Collision response (adjust positions and velocities)
            dx = min(self.rect.right - other.rect.left, other.rect.right - self.rect.left)
            dy = min(self.rect.bottom - other.rect.top, other.rect.bottom - self.rect.top)
            dx = max(dx, 1)
            dy = max(dy, 1)
            if dx < dy:
                if self.rect.centerx < other.rect.centerx:
                    adjustment = max(dx / 2, 1)
                    self.rect.right -= adjustment
                    other.rect.left += adjustment
                    normal = pygame.math.Vector2(-1, 0)
                else:
                    adjustment = max(dx / 2, 1)
                    self.rect.left += adjustment
                    other.rect.right -= adjustment
                    normal = pygame.math.Vector2(1, 0)
            else:
                if self.rect.centery < other.rect.centery:
                    adjustment = max(dy / 2, 1)
                    self.rect.bottom -= adjustment
                    other.rect.top += adjustment
                    normal = pygame.math.Vector2(0, -1)
                else:
                    adjustment = max(dy / 2, 1)
                    self.rect.top += adjustment
                    other.rect.bottom -= adjustment
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

            # Add randomness to velocities
            angle1 = random.uniform(-20, 20)
            angle2 = random.uniform(-20, 20)
            self.velocity = self.velocity.rotate(angle1)
            other.velocity = other.velocity.rotate(angle2)

            # Damage handling
            if self.in_neutral_mode and other.in_neutral_mode:
                # Both are in mod; both deal damage
                damage_self = int(10 + 10 * EXTRA_DAMAGE_PER_STACK * self.mod_stack_count)
                damage_other = int(10 + 10 * EXTRA_DAMAGE_PER_STACK * other.mod_stack_count)
                if self.mod_stack_count > other.mod_stack_count:
                    # Self deals more damage
                    damage_other += self.mod_stack_count - other.mod_stack_count
                elif other.mod_stack_count > self.mod_stack_count:
                    # Other deals more damage
                    damage_self += other.mod_stack_count - self.mod_stack_count
                self.take_damage(damage_self)
                other.take_damage(damage_other)
                if self.health == 0 and self in big_squares:
                    big_squares.remove(self)
                if other.health == 0 and other in big_squares:
                    big_squares.remove(other)
            elif not self.in_neutral_mode and not other.in_neutral_mode:
                # Neither is in mod
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
            else:
                # One is in mod and one is not; no damage applied
                pass

    def take_damage(self, amount):
        self.health = max(self.health - amount, 0)
        self.update_size()

    def recover_health(self, amount):
        self.health = min(self.health + amount, 100)
        self.update_size()

    def collect_small_square(self, small_square):
        if self.in_neutral_mode:
            if small_square["color"] == self.color:
                self.mod_stack_count += 1
                self.mod_stacked_small_squares.append(small_square)
        else:
            if small_square["color"] != self.color:
                self.stack_count += 1
                self.initial_stacked_small_squares.append(small_square)
                if self.stack_count >= NEUTRAL_STACK_THRESHOLD:
                    self.activate_neutral_mode()
        self.collected += 1

    def activate_neutral_mode(self):
        self.in_neutral_mode = True
        self.neutral_mode_end_time = pygame.time.get_ticks() + NEUTRAL_MODE_DURATION
        # Fix background to orange
        global background_color
        background_color = ORANGE
        # Clear stacks collected to enter mode
        self.initial_stacked_small_squares.clear()
        self.stack_count = 0

    def update_neutral_mode(self):
        if self.in_neutral_mode:
            current_time = pygame.time.get_ticks()
            if current_time >= self.neutral_mode_end_time:
                self.deactivate_neutral_mode()

    def deactivate_neutral_mode(self):
        self.in_neutral_mode = False
        # Calculate extra damage (10 + 25% * mod_stack_count)
        self.extra_damage = int(10 + 10 * EXTRA_DAMAGE_PER_STACK * self.mod_stack_count)
        # Apply extra damage
        apply_extra_damage(self.extra_damage, self)
        # Reset mod stack count and visualization
        self.mod_stack_count = 0
        self.mod_stacked_small_squares.clear()

def apply_extra_damage(amount, source_square):
    # Apply extra damage to all squares except the source square
    for square in big_squares[:]:
        if square != source_square and not square.in_neutral_mode:
            square.take_damage(amount)
            if square.health == 0 and square in big_squares:
                big_squares.remove(square)

def spawn_small_square():
    x = random.randint(20, WIDTH - 30)
    y = random.randint(20, HEIGHT - 30)
    total_collected = red_square.collected + blue_square.collected
    if total_collected == 0:
        probability_red = 0.5
    else:
        advantage = (blue_square.collected - red_square.collected) / total_collected
        probability_red = 0.5 + advantage * 0.5
        probability_red = max(0.2, min(0.8, probability_red))
    if random.random() < probability_red:
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

        # Handle collisions between big squares
        for i in range(len(big_squares)):
            for j in range(i + 1, len(big_squares)):
                big_squares[i].handle_collision(big_squares[j], background_color)

        # Handle big squares collecting small squares
        for square in big_squares:
            for small_square in small_squares[:]:
                if square.rect.colliderect(small_square["rect"]):
                    if small_square["color"] == square.color and not square.in_neutral_mode:
                        background_color = square.color
                    square.collect_small_square(small_square)
                    small_squares.remove(small_square)
                    respawn_small_square()

        # Update mod timers
        for square in big_squares:
            square.update_neutral_mode()

        # Check GAME_OVER conditions
        if len(big_squares) <= 1:
            GAME_OVER = True
        elif len(big_squares) == 0:
            print("Draw!")
            GAME_OVER = True

    # Set background
    any_in_neutral = any(square.in_neutral_mode for square in big_squares)
    if any_in_neutral:
        screen.fill(ORANGE)
    else:
        screen.fill(background_color)

    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), BORDER_THICKNESS)
    for square in big_squares:
        square.draw(screen)
    for small_square in small_squares:
        pygame.draw.rect(screen, small_square["border"], small_square["rect"].inflate(2, 2), border_radius=2)
        pygame.draw.rect(screen, small_square["color"], small_square["rect"], border_radius=2)

    # Draw health bars
    for square in big_squares:
        if square.color == RED:
            pygame.draw.rect(screen, LIGHT_RED, (20, HEIGHT - 40, square.health * 2, 20))
            pygame.draw.rect(screen, WHITE, (20, HEIGHT - 40, 200, 20), 2)
    for square in big_squares:
        if square.color == BLUE:
            pygame.draw.rect(screen, LIGHT_BLUE, (WIDTH - 220, HEIGHT - 40, square.health * 2, 20))
            pygame.draw.rect(screen, WHITE, (WIDTH - 220, HEIGHT - 40, 200, 20), 2)

    # Show GAME_OVER message
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
