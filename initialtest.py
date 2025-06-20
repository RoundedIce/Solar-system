import pygame
import math
import random

# === WINDOW SETTINGS ===
WIDTH, HEIGHT = 1200, 1000
CENTER = (WIDTH // 2, HEIGHT // 2 + 100)
SCALE = 350  # pixels per AU

# === PLANETARY DATA ===
# (name, semi-major axis (AU), eccentricity, period (days), color, radius px)
PLANETS = [
    ("Mercury", 0.387098, 0.20563, 87.9691, (200, 200, 200), 2439.7),
    ("Venus",   0.723332, 0.006772, 224.701, (255, 200, 100), 6051.8),
    ("Earth",   1, 0.0167086, 365.256363004, (100, 180, 255), 6371.0),
    ("Mars",    1.52368055, 0.0934, 686.98, (255, 100, 100), 3389.5),
]

# (name, parent_planet_index, semi-major axis (AU), eccentricity, period (days), color, radius px)
MOONS = [
    ("Moon", 2, 0.00256954861, 0.0549, 27.321661, (220, 220, 220), 1737.4),  # Earth's moon
    # Add more moons here easily
]

omega_deg = 29.0  # argument of periapsis in degrees (same for all for simplicity)
omega = math.radians(omega_deg)

# === TIME SETTINGS ===
t = 0
dt = 0.5  # simulation time step (days per frame)
camera_speed = 1.0  # multiplier for dt
tau = 0  # time of perihelion

# === PYGAME INIT ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Beautiful Solar System Simulation")
font = pygame.font.SysFont(None, 28)
clock = pygame.time.Clock()
running = True

# === COLORS ===
BLACK = (10, 10, 30)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 100)
SUN_GLOW = (255, 255, 180, 40)

# === STAR BACKGROUND ===
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 2)) for _ in range(200)]

cam_x, cam_y = 0.0, 0.0  # Camera offset in AU
zoom = 1.0  # Camera zoom

def solve_kepler(M, e, tol=1e-6, max_iter=100):
    E = M if e < 0.8 else math.pi
    for _ in range(max_iter):
        delta = E - e * math.sin(E) - M
        if abs(delta) < tol:
            break
        E -= delta / (1 - e * math.cos(E))
    return E

def get_position(a, e, T, t):
    n = 2 * math.pi / T  # mean motion
    M = n * (t - tau)  # mean anomaly
    M = M % (2 * math.pi)  # keep M in [0, 2pi]
    E = solve_kepler(M, e)
    theta = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2),
                           math.sqrt(1 - e) * math.cos(E / 2))
    r = a * (1 - e * math.cos(E))
    # Polar to Cartesian in orbit frame
    x_orbit = r * math.cos(theta)
    y_orbit = r * math.sin(theta)
    # Rotate by omega (argument of periapsis)
    x = x_orbit * math.cos(omega) - y_orbit * math.sin(omega)
    y = x_orbit * math.sin(omega) + y_orbit * math.cos(omega)
    return x, y

def to_screen(x_au, y_au):
    x_px = CENTER[0] + int(((x_au - cam_x) * SCALE * zoom))
    y_px = CENTER[1] - int(((y_au - cam_y) * SCALE * zoom))
    return x_px, y_px

def draw_sun():
    # Draw the Sun at the solar system center, offset by camera
    sun_x, sun_y = to_screen(0, 0)
    pygame.draw.circle(screen, YELLOW, (sun_x, sun_y), int(24 * zoom))

def draw_orbit(a, e, color):
    points = []
    for deg in range(0, 360, 2):
        theta = math.radians(deg)
        r = a * (1 - e**2) / (1 + e * math.cos(theta))
        x_orbit = r * math.cos(theta)
        y_orbit = r * math.sin(theta)
        x = x_orbit * math.cos(omega) - y_orbit * math.sin(omega)
        y = x_orbit * math.sin(omega) + y_orbit * math.cos(omega)
        x_px, y_px = to_screen(x, y)
        points.append((x_px, y_px))
    pygame.draw.aalines(screen, color, True, points, 1)

def draw_stars():
    for x, y, r in stars:
        pygame.draw.circle(screen, WHITE, (x, y), r)

# === TRAILS ===
trails = [[] for _ in PLANETS]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                cam_y += 0.1 / zoom  # Pan up
            if event.key == pygame.K_s:
                cam_y -= 0.1 / zoom  # Pan down
            if event.key == pygame.K_a:
                cam_x -= 0.1 / zoom  # Pan left
            if event.key == pygame.K_d:
                cam_x += 0.1 / zoom  # Pan right
            if event.key == pygame.K_q:
                zoom = max(0.2, zoom * 0.8)  # Zoom out
            if event.key == pygame.K_e:
                zoom = min(5.0, zoom * 1.25)  # Zoom in
            if event.key == pygame.K_z:
                dt = max(0.01, dt * 0.5)  # Slow down
            if event.key == pygame.K_c:
                dt = min(10.0, dt * 2)    # Speed up

    t += dt

    # Draw background
    screen.fill((20, 20, 30))  # light black
   
    draw_sun()
    # Show speed and zoom
    speed_text = font.render(f"Speed: {dt:.2f} days/frame", True, (200, 200, 200))
    zoom_text = font.render(f"Zoom: {zoom:.2f}x", True, (200, 200, 200))
    screen.blit(speed_text, (20, 20))
    screen.blit(zoom_text, (20, 50))

    # Draw orbits and planets
    planet_positions = []
    for i, (name, a, e, T, color, radius) in enumerate(PLANETS):
        draw_orbit(a, e, color)
        x_au, y_au = get_position(a, e, T, t)
        x_px, y_px = to_screen(x_au, y_au)
        planet_positions.append((x_au, y_au, x_px, y_px, color, radius, name))
        trails[i].append((x_px, y_px))
        if len(trails[i]) > 800:
            trails[i].pop(0)
        
        # Draw planet
        pygame.draw.circle(screen, color, (x_px, y_px), max(2, int(radius * zoom)))
        text = font.render(name, True, color)
        screen.blit(text, (x_px + 12, y_px - 12))

    # Draw moons
    for moon in MOONS:
        m_name, parent_idx, m_a, m_e, m_T, m_color, m_radius = moon
        parent_x_au, parent_y_au, _, _, _, _, _ = planet_positions[parent_idx]
        # Moon's position relative to its planet
        m_x_rel, m_y_rel = get_position(m_a, m_e, m_T, t)
        m_x_au = parent_x_au + m_x_rel
        m_y_au = parent_y_au + m_y_rel
        m_x_px, m_y_px = to_screen(m_x_au, m_y_au)
        pygame.draw.circle(screen, m_color, (m_x_px, m_y_px), max(2, int(m_radius * zoom)))
        m_text = font.render(m_name, True, m_color)
        screen.blit(m_text, (m_x_px + 10, m_y_px - 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
