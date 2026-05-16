import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
import pygame
from sim import Carrier, Asteroid, Station, check_collision

class SpaceCarrierEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, render_mode=None):
        super(SpaceCarrierEnv, self).__init__()
        
        self.render_mode = render_mode
        self.carrier = Carrier()
        self.asteroids = [Asteroid() for _ in range(20)]
        self.station = Station()
        
        # Action Space: 0:None, 1:W, 2:S, 3:A, 4:D, 5:Q, 6:E
        self.action_space = spaces.Discrete(7)
        
        # Observation Space (AI가 보는 정보)
        # 1. 속도 (vx, vy)
        # 2. 각속도
        # 3. 각도 (sin, cos)
        # 4. 연료 및 장갑
        # 5. 스테이션 상대 위치 (dx, dy)
        # 6. 가장 가까운 소행성 5개의 상대 위치 (dx, dy)
        low = np.array([-1, -1, -1, -1, -1, 0, 0, -1, -1] + [-1, -1] * 5, dtype=np.float32)
        high = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1] + [1, 1] * 5, dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self.screen = None
        self.clock = None

    def _get_obs(self):
        # 정규화된 관측값 생성
        rad = math.radians(self.carrier.angle)
        rel_station = (self.station.pos - self.carrier.pos) / 3000.0 # 최대 거리로 정규화
        
        # 소행성 거리 순 정렬
        ast_rel_positions = []
        for ast in self.asteroids:
            rel = (ast.pos - self.carrier.pos) / 2000.0
            ast_rel_positions.append(rel)
        ast_rel_positions.sort(key=lambda x: np.linalg.norm(x))
        nearest_asts = ast_rel_positions[:5]
        while len(nearest_asts) < 5:
            nearest_asts.append(np.array([1.0, 1.0])) # 못 찾으면 멀리 있는 것으로 처리

        obs = np.array([
            self.carrier.vel[0] / 10.0,
            self.carrier.vel[1] / 10.0,
            self.carrier.angular_vel / 5.0,
            math.sin(rad),
            math.cos(rad),
            self.carrier.fuel / 100.0,
            self.carrier.hull_integrity / 100.0,
            rel_station[0],
            rel_station[1]
        ] + [val for sub in nearest_asts for val in sub], dtype=np.float32)
        
        return np.clip(obs, -1, 1)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.carrier.reset()
        self.station.spawn()
        for ast in self.asteroids:
            ast.spawn(self.carrier.pos)
        
        return self._get_obs(), {}

    def step(self, action):
        # 1. Action 적용
        rad = math.radians(self.carrier.angle)
        keys = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, 
                pygame.K_d: False, pygame.K_q: False, pygame.K_e: False}
        
        if action == 1: # W
            self.carrier.apply_thrust(np.array([math.cos(rad), -math.sin(rad)]) * self.carrier.thrust_power, is_main=True)
            keys[pygame.K_w] = True
        elif action == 2: # S
            self.carrier.apply_thrust(np.array([-math.cos(rad), math.sin(rad)]) * self.carrier.rcs_power)
            keys[pygame.K_s] = True
        elif action == 3: # A
            self.carrier.angular_vel += self.carrier.rotation_power / self.carrier.mass
            keys[pygame.K_a] = True
        elif action == 4: # D
            self.carrier.angular_vel -= self.carrier.rotation_power / self.carrier.mass
            keys[pygame.K_d] = True
        elif action == 5: # Q
            self.carrier.apply_thrust(np.array([math.cos(rad + math.pi/2), -math.sin(rad + math.pi/2)]) * self.carrier.rcs_power)
            keys[pygame.K_q] = True
        elif action == 6: # E
            self.carrier.apply_thrust(np.array([math.cos(rad - math.pi/2), -math.sin(rad - math.pi/2)]) * self.carrier.rcs_power)
            keys[pygame.K_e] = True

        # 2. 업데이트
        self.carrier.update()
        for ast in self.asteroids:
            ast.update(self.carrier.pos)

        # 3. 보상 및 종료 조건
        reward = -0.01 # 시간 패널티
        terminated = False
        truncated = False
        
        # 거리 보상 (정거장에 가까워지면 보상)
        dist_to_station = np.linalg.norm(self.carrier.pos - self.station.pos)
        reward += (1.0 / (dist_to_station + 100)) * 10 

        # 충돌 패널티
        hit_ast = check_collision(self.carrier, self.asteroids)
        if hit_ast:
            reward -= 5.0
            self.carrier.hull_integrity -= 10
            hit_ast.spawn(self.carrier.pos)
            if self.carrier.hull_integrity <= 0:
                reward -= 50.0
                terminated = True

        # 연료 부족 패널티
        if self.carrier.fuel <= 0:
            reward -= 20.0
            terminated = True

        # 도킹 성공 보상
        speed = np.linalg.norm(self.carrier.vel)
        if dist_to_station < 70:
            if speed < 1.0:
                reward += 200.0
                terminated = True
            else:
                reward -= 5.0 # 너무 빠름

        if self.render_mode == "human":
            self.render(keys)

        return self._get_obs(), reward, terminated, truncated, {}

    def render(self, keys=None):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((1200, 800))
            self.clock = pygame.time.Clock()

        if keys is None:
            keys = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, 
                    pygame.K_d: False, pygame.K_q: False, pygame.K_e: False}

        self.screen.fill((0, 0, 0))
        # sim.py의 로직을 그대로 사용 (시각화)
        # 여기서는 생략하고 핵심만 구현
        self.carrier.draw(self.screen, keys)
        self.station.draw(self.screen, self.carrier.pos)
        for ast in self.asteroids:
            ast.draw(self.screen, self.carrier.pos)
            
        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.screen is not None:
            pygame.quit()
