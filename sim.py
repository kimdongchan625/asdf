import pygame
import numpy as np
import math
import os

# 설정
WIDTH, HEIGHT = 1200, 800
FPS = 60

# 색상 정의
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (100, 100, 100)
RED, CYAN, GREEN, YELLOW = (255, 50, 50), (0, 255, 255), (0, 255, 0), (255, 255, 0)

class Carrier:
    def __init__(self):
        self.reset()
        self.length, self.width = 60, 30
        self.mass = 100.0
        self.thrust_power = 0.8
        self.rcs_power = 0.2
        self.rotation_power = 0.5
        self.fuel_cons_main = 0.05
        self.fuel_cons_rcs = 0.01

    def reset(self):
        self.pos, self.vel = np.array([0.0, 0.0]), np.array([0.0, 0.0])
        self.angle, self.angular_vel = 0.0, 0.0
        self.hull_integrity, self.fuel = 100.0, 100.0
        self.is_alive, self.is_docked = True, False

    def apply_thrust(self, direction_vector, is_main=False):
        if not self.is_alive or self.fuel <= 0: return
        self.vel += direction_vector / self.mass
        self.fuel -= self.fuel_cons_main if is_main else self.fuel_cons_rcs

    def apply_rotation(self, direction):
        if not self.is_alive or self.fuel <= 0: return
        self.angular_vel += (direction * self.rotation_power) / self.mass
        self.fuel -= self.fuel_cons_rcs * 0.2

    def update(self):
        if not self.is_alive or self.is_docked: return
        self.pos += self.vel
        self.angle = (self.angle + self.angular_vel) % 360
        self.angular_vel *= 1.0 

    def draw(self, screen, keys_dict):
        if not self.is_alive: return
        center, rad = (WIDTH // 2, HEIGHT // 2), math.radians(self.angle)
        if self.fuel > 0:
            if keys_dict.get(pygame.K_w):
                p = center - np.array([math.cos(rad), -math.sin(rad)]) * (self.length/2+2)
                pygame.draw.circle(screen, RED, (int(p[0]), int(p[1])), 7)
            if keys_dict.get(pygame.K_s):
                p = center + np.array([math.cos(rad), -math.sin(rad)]) * (self.length/2+2)
                pygame.draw.circle(screen, RED, (int(p[0]), int(p[1])), 3)
            if keys_dict.get(pygame.K_q):
                p = center + np.array([math.cos(rad-math.pi/2), -math.sin(rad-math.pi/2)]) * 12
                pygame.draw.circle(screen, RED, (int(p[0]), int(p[1])), 3)
            if keys_dict.get(pygame.K_e):
                p = center + np.array([math.cos(rad+math.pi/2), -math.sin(rad+math.pi/2)]) * 12
                pygame.draw.circle(screen, RED, (int(p[0]), int(p[1])), 3)
            if keys_dict.get(pygame.K_a):
                p1 = center + np.array([math.cos(rad-0.8), -math.sin(rad-0.8)]) * 20
                p2 = center - np.array([math.cos(rad+0.8), -math.sin(rad+0.8)]) * 20
                pygame.draw.circle(screen, RED, (int(p1[0]), int(p1[1])), 4)
                pygame.draw.circle(screen, RED, (int(p2[0]), int(p2[1])), 4)
            if keys_dict.get(pygame.K_d):
                p1 = center + np.array([math.cos(rad+0.8), -math.sin(rad+0.8)]) * 20
                p2 = center - np.array([math.cos(rad-0.8), -math.sin(rad-0.8)]) * 20
                pygame.draw.circle(screen, RED, (int(p1[0]), int(p1[1])), 4)
                pygame.draw.circle(screen, RED, (int(p2[0]), int(p2[1])), 4)

        points = [(center[0] + math.cos(rad)*self.length/2, center[1] - math.sin(rad)*self.length/2),
                  (center[0] + math.cos(rad+2.5)*self.length/2, center[1] - math.sin(rad+2.5)*self.length/2),
                  (center[0] + math.cos(rad-2.5)*self.length/2, center[1] - math.sin(rad-2.5)*self.length/2)]
        hc = (255, int(2.55 * self.hull_integrity), int(2.55 * self.hull_integrity))
        pygame.draw.polygon(screen, hc, points, 2)
        pygame.draw.circle(screen, CYAN, (int(center[0] + math.cos(rad)*self.length/2), int(center[1] - math.sin(rad)*self.length/2)), 3)

class Station:
    def __init__(self): self.spawn()
    def spawn(self):
        angle, dist = np.random.uniform(0, 2*math.pi), np.random.uniform(2000, 3500)
        self.pos = np.array([math.cos(angle)*dist, math.sin(angle)*dist])
        self.radius = 60
    def draw(self, screen, carrier_pos):
        rel = self.pos - carrier_pos + np.array([WIDTH // 2, HEIGHT // 2])
        if -200 < rel[0] < WIDTH+200 and -200 < rel[1] < HEIGHT+200:
            pts = [(rel[0] + math.cos(i*math.pi/3)*self.radius, rel[1] + math.sin(i*math.pi/3)*self.radius) for i in range(6)]
            pygame.draw.polygon(screen, YELLOW, pts, 3)

class Asteroid:
    def __init__(self): self.spawn(np.array([0, 0]))
    def spawn(self, p_pos):
        angle, dist = np.random.uniform(0, 2*math.pi), np.random.uniform(800, 2000)
        self.pos = p_pos + np.array([math.cos(angle)*dist, math.sin(angle)*dist])
        self.vel, self.radius = np.random.uniform(-1.5, 1.5, 2), np.random.uniform(20, 60)
    def update(self, p_pos):
        self.pos += self.vel
        if np.linalg.norm(self.pos - p_pos) > 2500: self.spawn(p_pos)
    def draw(self, screen, p_pos):
        rel = self.pos - p_pos + np.array([WIDTH // 2, HEIGHT // 2])
        if -100 < rel[0] < WIDTH+100 and -100 < rel[1] < HEIGHT+100: pygame.draw.circle(screen, GRAY, (int(rel[0]), int(rel[1])), int(self.radius), 1)

class Starfield:
    def __init__(self): self.stars = [[np.random.uniform(0, WIDTH), np.random.uniform(0, HEIGHT), np.random.uniform(1, 3)] for _ in range(250)]
    def draw(self, screen, vel):
        for s in self.stars:
            s[0], s[1] = (s[0] - vel[0]*0.4) % WIDTH, (s[1] - vel[1]*0.4) % HEIGHT
            pygame.draw.circle(screen, (180, 180, 180), (int(s[0]), int(s[1])), int(s[2]))

class Radar:
    def __init__(self, carrier, asteroids, station): self.carrier, self.asteroids, self.station, self.range, self.rect = carrier, asteroids, station, 3000, pygame.Rect(WIDTH-220, 20, 200, 200)
    def draw(self, screen):
        pygame.draw.rect(screen, (20, 20, 20), self.rect); pygame.draw.rect(screen, GREEN, self.rect, 2)
        c = np.array([self.rect.centerx, self.rect.centery]); pygame.draw.circle(screen, CYAN, c, 3)
        for ast in self.asteroids:
            rel = ast.pos - self.carrier.pos
            if np.linalg.norm(rel) < self.range:
                p = c + (rel/self.range)*(self.rect.width/2)
                pygame.draw.circle(screen, RED, (int(p[0]), int(p[1])), 2)
        rel_s = self.station.pos - self.carrier.pos
        p_s = c + (rel_s/max(np.linalg.norm(rel_s), self.range))*(self.rect.width/2)
        pygame.draw.rect(screen, YELLOW, (int(p_s[0]-3), int(p_s[1]-3), 6, 6))

def check_collision(carrier, asteroids):
    for ast in asteroids:
        if np.linalg.norm(carrier.pos - ast.pos) < (ast.radius + 15): return ast
    return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Carrier - Record & Learn")
    clock, font = pygame.time.Clock(), pygame.font.SysFont("Arial", 18)
    carrier, asteroids, station, stars = Carrier(), [Asteroid() for _ in range(40)], Station(), Starfield()
    radar = Radar(carrier, asteroids, station)
    
    # AI 및 녹화 관련
    ai_mode, model = False, None
    recording = False
    recorded_obs, recorded_actions = [], []
    
    if os.path.exists("expert_data.npz"):
        try:
            data = np.load("expert_data.npz")
            recorded_obs, recorded_actions = list(data['obs']), list(data['actions'])
            print(f"Loaded existing data: {len(recorded_obs)} steps.")
        except: pass

    flash_timer, running = 0, True
    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    ai_mode = not ai_mode
                    if ai_mode:
                        try:
                            from stable_baselines3 import PPO
                            if os.path.exists("space_carrier_ppo.zip"):
                                model = PPO.load("space_carrier_ppo")
                                print("Latest AI Model Loaded.")
                            else:
                                print("No model found. Run imitate.py first.")
                                ai_mode = False
                        except:
                            print("SB3 not installed.")
                            ai_mode = False
                if event.key == pygame.K_r:
                    if recording:
                        recording = False
                        if len(recorded_obs) > 0:
                            np.savez("expert_data.npz", obs=np.array(recorded_obs), actions=np.array(recorded_actions))
                            print(f"Total data saved: {len(recorded_obs)} steps.")
                    elif not carrier.is_alive or carrier.is_docked:
                        carrier.reset(); station.spawn()
                        for ast in asteroids: ast.spawn(carrier.pos)
                    else:
                        recording = True

        rad = math.radians(carrier.angle)
        rel_s = (station.pos - carrier.pos) / 3500.0
        ast_rel = []
        for ast in asteroids: ast_rel.append((ast.pos - carrier.pos) / 2500.0)
        ast_rel.sort(key=lambda x: np.linalg.norm(x))
        near_asts = ast_rel[:5]
        while len(near_asts) < 5: near_asts.append(np.array([1.0, 1.0]))
        obs = np.array([carrier.vel[0]/10, carrier.vel[1]/10, carrier.angular_vel/5, math.sin(rad), math.cos(rad), carrier.fuel/100, carrier.hull_integrity/100, rel_s[0], rel_s[1]] + [v for s in near_asts for v in s], dtype=np.float32)

        keys = pygame.key.get_pressed()
        if ai_mode and model is not None and carrier.is_alive and not carrier.is_docked:
            action, _ = model.predict(obs, deterministic=True)
            curr_keys = {pygame.K_w: action==1, pygame.K_s: action==2, pygame.K_a: action==3, pygame.K_d: action==4, pygame.K_q: action==5, pygame.K_e: action==6}
        else:
            curr_keys = {k: keys[k] for k in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_q, pygame.K_e]}
            if recording and carrier.is_alive and not carrier.is_docked:
                act = 0
                if keys[pygame.K_w]: act = 1
                elif keys[pygame.K_s]: act = 2
                elif keys[pygame.K_a]: act = 3
                elif keys[pygame.K_d]: act = 4
                elif keys[pygame.K_q]: act = 5
                elif keys[pygame.K_e]: act = 6
                recorded_obs.append(obs); recorded_actions.append(act)

        if carrier.is_alive and not carrier.is_docked:
            rad = math.radians(carrier.angle)
            if curr_keys.get(pygame.K_a): carrier.apply_rotation(1)
            if curr_keys.get(pygame.K_d): carrier.apply_rotation(-1)
            if curr_keys.get(pygame.K_w): carrier.apply_thrust(np.array([math.cos(rad), -math.sin(rad)])*carrier.thrust_power, True)
            if curr_keys.get(pygame.K_s): carrier.apply_thrust(np.array([-math.cos(rad), math.sin(rad)])*carrier.rcs_power)
            if curr_keys.get(pygame.K_q): carrier.apply_thrust(np.array([math.cos(rad+math.pi/2), -math.sin(rad+math.pi/2)])*carrier.rcs_power)
            if curr_keys.get(pygame.K_e): carrier.apply_thrust(np.array([math.cos(rad-math.pi/2), -math.sin(rad-math.pi/2)])*carrier.rcs_power)
            
            carrier.update()
            for ast in asteroids: ast.update(carrier.pos)
            hit = check_collision(carrier, asteroids)
            if hit:
                carrier.hull_integrity -= hit.radius/2.0; flash_timer = 3; carrier.vel *= -0.3; hit.spawn(carrier.pos)
                if carrier.hull_integrity <= 0: carrier.is_alive = False
            if np.linalg.norm(carrier.pos - station.pos) < 70:
                if np.linalg.norm(carrier.vel) < 1.0: carrier.is_docked = True; carrier.vel *= 0
                else: carrier.hull_integrity -= 5; carrier.vel *= -0.5; flash_timer = 3

        if flash_timer > 0: screen.fill((150, 0, 0)); flash_timer -= 1
        stars.draw(screen, carrier.vel); station.draw(screen, carrier.pos)
        for ast in asteroids: ast.draw(screen, carrier.pos)
        carrier.draw(screen, curr_keys); radar.draw(screen)
        
        info = [f"AI: {'ON' if ai_mode else 'OFF'}", f"REC: {'ON' if recording else 'OFF'}", f"Hull: {max(0, carrier.hull_integrity):.1f}%", f"Fuel: {max(0, carrier.fuel):.1f}%"]
        if ai_mode:
            ai_f = pygame.font.SysFont("Arial", 30, bold=True)
            screen.blit(ai_f.render("!!! AI PILOT ACTIVE !!!", True, YELLOW), (WIDTH//2 - 150, 50))
        if recording: info.append(f"Recorded: {len(recorded_obs)}")
        for i, text in enumerate(info): screen.blit(font.render(text, True, YELLOW if "REC" in text and recording else WHITE), (20, 20 + i*25))
        pygame.display.flip(); clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__": main()
