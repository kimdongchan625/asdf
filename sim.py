import pygame
import numpy as np
import math

# 설정
WIDTH, HEIGHT = 1200, 800
FPS = 60

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class Carrier:
    def __init__(self):
        self.reset()
        self.length = 60
        self.width = 30
        
        # 물리 특성
        self.mass = 100.0
        self.thrust_power = 0.8
        self.rcs_power = 0.1
        self.rotation_power = 0.2
        
        # 소모량 설정
        self.fuel_consumption_main = 0.05
        self.fuel_consumption_rcs = 0.01

    def reset(self):
        self.pos = np.array([0.0, 0.0], dtype=float)
        self.vel = np.array([0.0, 0.0], dtype=float)
        self.angle = 0.0
        self.angular_vel = 0.0
        self.hull_integrity = 100.0
        self.fuel = 100.0
        self.is_alive = True
        self.is_docked = False

    def apply_thrust(self, direction_vector, is_main=False):
        if not self.is_alive or self.fuel <= 0: return
        
        # 가속
        acceleration = direction_vector / self.mass
        self.vel += acceleration
        
        # 연료 소모
        if is_main:
            self.fuel -= self.fuel_consumption_main
        else:
            self.fuel -= self.fuel_consumption_rcs

    def update(self):
        if not self.is_alive or self.is_docked: return
        self.pos += self.vel
        self.angle += self.angular_vel
        
        # 자연적인 회전 감쇠
        self.angular_vel *= 0.98

    def draw(self, screen, keys):
        if not self.is_alive: return
        center = (WIDTH // 2, HEIGHT // 2)
        rad = math.radians(self.angle)
        
        if self.fuel > 0:
            # 추진기 불꽃 연출
            if keys[pygame.K_w]:
                ex_x = center[0] - math.cos(rad) * (self.length/2 + 2)
                ex_y = center[1] + math.sin(rad) * (self.length/2 + 2)
                pygame.draw.circle(screen, RED, (int(ex_x), int(ex_y)), 7)
            if keys[pygame.K_s]:
                ex_x = center[0] + math.cos(rad) * (self.length/2 + 2)
                ex_y = center[1] - math.sin(rad) * (self.length/2 + 2)
                pygame.draw.circle(screen, RED, (int(ex_x), int(ex_y)), 3)
            if keys[pygame.K_q]:
                ex_x = center[0] + math.cos(rad - math.pi/2) * 12
                ex_y = center[1] - math.sin(rad - math.pi/2) * 12
                pygame.draw.circle(screen, RED, (int(ex_x), int(ex_y)), 3)
            if keys[pygame.K_e]:
                ex_x = center[0] + math.cos(rad + math.pi/2) * 12
                ex_y = center[1] - math.sin(rad + math.pi/2) * 12
                pygame.draw.circle(screen, RED, (int(ex_x), int(ex_y)), 3)
            if keys[pygame.K_a]:
                ex_x1 = center[0] + math.cos(rad - 0.5) * 20
                ex_y1 = center[1] - math.sin(rad - 0.5) * 20
                pygame.draw.circle(screen, RED, (int(ex_x1), int(ex_y1)), 2)
            if keys[pygame.K_d]:
                ex_x1 = center[0] + math.cos(rad + 0.5) * 20
                ex_y1 = center[1] - math.sin(rad + 0.5) * 20
                pygame.draw.circle(screen, RED, (int(ex_x1), int(ex_y1)), 2)

        # 선체
        points = [
            (center[0] + math.cos(rad) * self.length/2, center[1] - math.sin(rad) * self.length/2),
            (center[0] + math.cos(rad + 2.5) * self.length/2, center[1] - math.sin(rad + 2.5) * self.length/2),
            (center[0] + math.cos(rad - 2.5) * self.length/2, center[1] - math.sin(rad - 2.5) * self.length/2),
        ]
        hull_color = (255, int(2.55 * self.hull_integrity), int(2.55 * self.hull_integrity))
        pygame.draw.polygon(screen, hull_color, points, 2)
        
        front_x = center[0] + math.cos(rad) * (self.length/2)
        front_y = center[1] - math.sin(rad) * (self.length/2)
        pygame.draw.circle(screen, CYAN, (int(front_x), int(front_y)), 3)

class Station:
    def __init__(self):
        self.spawn()

    def spawn(self):
        angle = np.random.uniform(0, 2*math.pi)
        dist = np.random.uniform(2000, 3000)
        self.pos = np.array([math.cos(angle)*dist, math.sin(angle)*dist], dtype=float)
        self.radius = 60

    def draw(self, screen, carrier_pos):
        rel_pos = self.pos - carrier_pos
        screen_pos = rel_pos + np.array([WIDTH // 2, HEIGHT // 2])
        if -200 < screen_pos[0] < WIDTH + 200 and -200 < screen_pos[1] < HEIGHT + 200:
            pts = []
            for i in range(6):
                a = i * (math.pi/3)
                pts.append((screen_pos[0] + math.cos(a)*self.radius, screen_pos[1] + math.sin(a)*self.radius))
            pygame.draw.polygon(screen, YELLOW, pts, 3)
            pygame.draw.circle(screen, YELLOW, (int(screen_pos[0]), int(screen_pos[1])), 10)

class Asteroid:
    def __init__(self):
        self.spawn(np.array([0, 0]))

    def spawn(self, player_pos):
        angle = np.random.uniform(0, 2*math.pi)
        dist = np.random.uniform(600, 1500)
        self.pos = player_pos + np.array([math.cos(angle)*dist, math.sin(angle)*dist], dtype=float)
        self.vel = np.array([np.random.uniform(-1, 1), np.random.uniform(-1, 1)], dtype=float)
        self.radius = np.random.uniform(20, 50)

    def update(self, player_pos):
        self.pos += self.vel
        if np.linalg.norm(self.pos - player_pos) > 2000:
            self.spawn(player_pos)

    def draw(self, screen, carrier_pos):
        rel_pos = self.pos - carrier_pos
        screen_pos = rel_pos + np.array([WIDTH // 2, HEIGHT // 2])
        if -100 < screen_pos[0] < WIDTH + 100 and -100 < screen_pos[1] < HEIGHT + 100:
            pygame.draw.circle(screen, GRAY, (int(screen_pos[0]), int(screen_pos[1])), int(self.radius), 1)

class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(250):
            self.stars.append([np.random.uniform(0, WIDTH), np.random.uniform(0, HEIGHT), np.random.uniform(1, 3)])

    def draw(self, screen, carrier_vel):
        for star in self.stars:
            star[0] -= carrier_vel[0] * 0.4
            star[1] -= carrier_vel[1] * 0.4
            star[0] %= WIDTH
            star[1] %= HEIGHT
            pygame.draw.circle(screen, (180, 180, 180), (int(star[0]), int(star[1])), int(star[2]))

class Radar:
    def __init__(self, carrier, asteroids, station):
        self.carrier = carrier
        self.asteroids = asteroids
        self.station = station
        self.range = 2500
        self.rect = pygame.Rect(WIDTH - 220, 20, 200, 200)

    def draw(self, screen):
        pygame.draw.rect(screen, (20, 20, 20), self.rect)
        pygame.draw.rect(screen, GREEN, self.rect, 2)
        center = np.array([self.rect.centerx, self.rect.centery])
        pygame.draw.circle(screen, CYAN, center, 3)
        for ast in self.asteroids:
            rel_pos = ast.pos - self.carrier.pos
            dist = np.linalg.norm(rel_pos)
            if dist < self.range:
                radar_pos = center + (rel_pos / self.range) * (self.rect.width / 2)
                pygame.draw.circle(screen, RED, (int(radar_pos[0]), int(radar_pos[1])), 2)
        rel_station = self.station.pos - self.carrier.pos
        dist_s = np.linalg.norm(rel_station)
        radar_pos_s = center + (rel_station / self.range) * (self.rect.width / 2)
        if dist_s > self.range:
            radar_pos_s = center + (rel_station / dist_s) * (self.rect.width / 2)
        pygame.draw.rect(screen, YELLOW, (int(radar_pos_s[0]-3), int(radar_pos_s[1]-3), 6, 6))

def check_collision(carrier, asteroids):
    for ast in asteroids:
        dist = np.linalg.norm(carrier.pos - ast.pos)
        if dist < (ast.radius + 15):
            return ast
    return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Carrier Command")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    
    carrier = Carrier()
    asteroids = [Asteroid() for _ in range(40)]
    station = Station()
    stars = Starfield()
    radar = Radar(carrier, asteroids, station)
    
    flash_timer = 0
    running = True
    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if (not carrier.is_alive or carrier.is_docked) and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    carrier.reset()
                    station.spawn()
                    for ast in asteroids: ast.spawn(carrier.pos)

        keys = pygame.key.get_pressed()
        if carrier.is_alive and not carrier.is_docked:
            rad = math.radians(carrier.angle)
            if keys[pygame.K_w]:
                carrier.apply_thrust(np.array([math.cos(rad), -math.sin(rad)]) * carrier.thrust_power, is_main=True)
            if keys[pygame.K_s]:
                carrier.apply_thrust(np.array([-math.cos(rad), math.sin(rad)]) * carrier.rcs_power)
            if keys[pygame.K_a]:
                if carrier.fuel > 0: carrier.angular_vel += carrier.rotation_power / carrier.mass
            if keys[pygame.K_d]:
                if carrier.fuel > 0: carrier.angular_vel -= carrier.rotation_power / carrier.mass
            if keys[pygame.K_q]:
                carrier.apply_thrust(np.array([math.cos(rad + math.pi/2), -math.sin(rad + math.pi/2)]) * carrier.rcs_power)
            if keys[pygame.K_e]:
                carrier.apply_thrust(np.array([math.cos(rad - math.pi/2), -math.sin(rad - math.pi/2)]) * carrier.rcs_power)

            carrier.update()
            for ast in asteroids:
                ast.update(carrier.pos)

            hit_ast = check_collision(carrier, asteroids)
            if hit_ast:
                damage = hit_ast.radius / 2.0
                carrier.hull_integrity -= damage
                flash_timer = 3
                carrier.vel = -carrier.vel * 0.3
                hit_ast.spawn(carrier.pos)
                if carrier.hull_integrity <= 0:
                    carrier.is_alive = False

            dist_to_station = np.linalg.norm(carrier.pos - station.pos)
            speed = np.linalg.norm(carrier.vel)
            if dist_to_station < 70:
                if speed < 1.0:
                    carrier.is_docked = True
                    carrier.vel = np.array([0, 0], dtype=float)
                else:
                    carrier.hull_integrity -= 5.0
                    carrier.vel = -carrier.vel * 0.5
                    flash_timer = 3

        if flash_timer > 0:
            screen.fill((150, 0, 0))
            flash_timer -= 1

        stars.draw(screen, carrier.vel)
        station.draw(screen, carrier.pos)
        for ast in asteroids:
            ast.draw(screen, carrier.pos)
        carrier.draw(screen, keys)
        radar.draw(screen)
        
        speed = np.linalg.norm(carrier.vel)
        dist_to_station = np.linalg.norm(carrier.pos - station.pos)
        info_text = [
            f"Hull Integrity: {max(0, carrier.hull_integrity):.1f}%",
            f"Fuel: {max(0, carrier.fuel):.1f}%",
            f"Speed: {speed:.2f}",
            f"Dist to Station: {dist_to_station:.0f}",
        ]
        if carrier.fuel <= 0: info_text.append("!!! OUT OF FUEL !!!")
        if not carrier.is_alive: info_text.append("!!! SHIP DESTROYED !!!")
        if carrier.is_docked: info_text.append("=== DOCKING SUCCESSFUL ===")
        
        for i, text in enumerate(info_text):
            img = font.render(text, True, WHITE)
            screen.blit(img, (20, 20 + i * 25))

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()
