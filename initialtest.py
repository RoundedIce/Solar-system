import pygame
import math

# === PYGAME INIT ===
pygame.init()
WIDTH, HEIGHT = 1000, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simplified Solar System")
clock = pygame.time.Clock()
running = True

# === SCALE AND TIME ===
SCALE = 300  # pixels per AU
dt = 0.5     # days per frame

# === VIEWPORT CONTROL ===
offset_x = WIDTH // 2
offset_y = HEIGHT // 2
camera_target = None
zoom_factor = 1.0

# === COLORS ===
YELLOW = (255, 255, 0)
WHITE = (220, 220, 220)
GRAY = (150, 150, 150)
BLUE = (100, 149, 237)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)

# === KEPLER SOLVER ===
def solve_kepler(M, e, tol=1e-6, max_iter=100):
    E = M if e < 0.8 else math.pi
    for _ in range(max_iter):
        delta = E - e * math.sin(E) - M
        if abs(delta) < tol:
            break
        E -= delta / (1 - e * math.cos(E))
    return E

# === CLASSES ===
class Body:
    def __init__(self, name, a, e, T, omega_deg, color, radius=5):
        self.name = name
        self.a = a
        self.e = e
        self.T = T
        self.omega = math.radians(omega_deg)
        self.color = color
        self.radius = radius
        self.t = 0
        self.trail = []
        self.last_px = 0
        self.last_py = 0

    def compute_position(self, dt):
        self.t += dt
        n = 2 * math.pi / self.T
        M = (n * self.t) % (2 * math.pi)
        E = solve_kepler(M, self.e)
        theta = 2 * math.atan2(math.sqrt(1 + self.e) * math.sin(E / 2),
                               math.sqrt(1 - self.e) * math.cos(E / 2))
        r = self.a * (1 - self.e * math.cos(E))

        x_orb = r * math.cos(theta)
        y_orb = r * math.sin(theta)

        x = x_orb * math.cos(self.omega) - y_orb * math.sin(self.omega)
        y = x_orb * math.sin(self.omega) + y_orb * math.cos(self.omega)

        return x, y

    def update_and_draw(self, cx, cy, dt, screen):
        x, y = self.compute_position(dt)
        px = int(cx + x * SCALE * zoom_factor)
        py = int(cy - y * SCALE * zoom_factor)
        self.last_px = px
        self.last_py = py
        self.trail.append((px, py))
        if len(self.trail) > 500:
            self.trail.pop(0)

        pygame.draw.circle(screen, self.color, (px, py), max(1, int(self.radius * zoom_factor)))
        return px, py

class Planet(Body):
    def __init__(self, name, a, e, T, omega_deg, color, radius=5):
        super().__init__(name, a, e, T, omega_deg, color, radius)
        self.moons = []

    def add_moon(self, name, a, e, T, omega_deg, color, radius=3):
        moon = Moon(name, a, e, T, omega_deg, color, self, radius)
        self.moons.append(moon)

    def update_and_draw_all(self, dt, screen, cx, cy):
        px, py = self.update_and_draw(cx, cy, dt, screen)
        for moon in self.moons:
            moon.update_and_draw(px, py, dt, screen)

class Moon(Body):
    def __init__(self, name, a, e, T, omega_deg, color, host, radius=3):
        super().__init__(name, a, e, T, omega_deg, color, radius)
        self.host = host

# === CREATE PLANETS AND MOONS ===
planet_data = [
    {"name": "Mercury", "a": 0.387, "e": 0.2056, "T": 88, "omega_deg": 29, "color": WHITE, "radius": 4, "moons": []},
    {"name": "Earth", "a": 1.0, "e": 0.0167, "T": 365.25, "omega_deg": 114, "color": BLUE, "radius": 6, "moons": [
        {"name": "Moon", "a": 0.00257, "e": 0.055, "T": 27.3, "omega_deg": 0, "color": GRAY, "radius": 3}
    ]}
]

planets = []
for pdata in planet_data:
    p = Planet(pdata["name"], pdata["a"], pdata["e"], pdata["T"], pdata["omega_deg"], pdata["color"], pdata["radius"])
    for mdata in pdata["moons"]:
        p.add_moon(**mdata)
    planets.append(p)

# === MAIN LOOP ===
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            for p in planets:
                dx = mx - p.last_px
                dy = my - p.last_py
                if dx*dx + dy*dy <= (p.radius * SCALE * zoom_factor)**2:
                    camera_target = p
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_x:
                camera_target = None

    # Controls
    keys = pygame.key.get_pressed()
    if not camera_target:
        if keys[pygame.K_w]: offset_y += 10
        if keys[pygame.K_s]: offset_y -= 10
        if keys[pygame.K_a]: offset_x += 10
        if keys[pygame.K_d]: offset_x -= 10

    if keys[pygame.K_q]: zoom_factor *= 1.02
    if keys[pygame.K_e]: zoom_factor /= 1.02
    if keys[pygame.K_c]: dt *= 1.02
    if keys[pygame.K_z]: dt /= 1.02

    # Center on camera target if exists
    if camera_target:
        offset_x = WIDTH // 2 - camera_target.last_px + offset_x
        offset_y = HEIGHT // 2 - camera_target.last_py + offset_y

    screen.fill(BLACK)
    pygame.draw.circle(screen, YELLOW, (offset_x, offset_y), max(1, int(10 * zoom_factor)))

    for planet in planets:
        planet.update_and_draw_all(dt, screen, offset_x, offset_y)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
