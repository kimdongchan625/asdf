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
        
        # [초등학교 모드] 현실적인 물리로 복귀
        self.carrier.rotation_power = 1.0 # 약간 묵직하게 유지
        self.carrier.rcs_power = 0.2
        
        # 소행성 5개 도입 (장애물 연습)
        self.asteroids = [Asteroid() for _ in range(5)] 
        self.station = Station()
        
        self.max_steps = 1500 # 좀 더 긴 시간 제공
        self.current_step = 0
        
        self.action_space = spaces.Discrete(7)
        low = np.array([-1, -1, -1, -1, -1, 0, 0, -1, -1] + [-1, -1] * 5, dtype=np.float32)
        high = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1] + [1, 1] * 5, dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self.screen = None
        self.clock = None
        self.prev_dist = 0.0

    def _get_obs(self):
        rad = math.radians(self.carrier.angle)
        rel_station = (self.station.pos - self.carrier.pos) / 3500.0
        
        # 소행성 데이터 복구
        ast_rel_positions = []
        for ast in self.asteroids:
            rel = (ast.pos - self.carrier.pos) / 2500.0
            ast_rel_positions.append(rel)
        ast_rel_positions.sort(key=lambda x: np.linalg.norm(x))
        nearest_asts = ast_rel_positions[:5]
        while len(nearest_asts) < 5:
            nearest_asts.append(np.array([1.0, 1.0]))

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
        self.current_step = 0
        self.station.spawn()
        for ast in self.asteroids:
            ast.spawn(self.carrier.pos)
        
        self.prev_dist = np.linalg.norm(self.carrier.pos - self.station.pos)
        return self._get_obs(), {}

    def step(self, action):
        self.current_step += 1
        # [초등학교 모드] 관성 강화 (이제 스스로 멈춰야 함)
        self.carrier.angular_vel *= 1.0 
        
        rad = math.radians(self.carrier.angle)
        # 연료 소모 실제 적용
        if action == 1: self.carrier.apply_thrust(np.array([math.cos(rad), -math.sin(rad)]) * self.carrier.thrust_power, True)
        elif action == 2: self.carrier.apply_thrust(np.array([-math.cos(rad), math.sin(rad)]) * self.carrier.rcs_power)
        elif action == 3: self.carrier.apply_rotation(1)
        elif action == 4: self.carrier.apply_rotation(-1)
        elif action == 5: self.carrier.apply_thrust(np.array([math.cos(rad+math.pi/2), -math.sin(rad+math.pi/2)]) * self.carrier.rcs_power)
        elif action == 6: self.carrier.apply_thrust(np.array([math.cos(rad-math.pi/2), -math.sin(rad-math.pi/2)]) * self.carrier.rcs_power)

        self.carrier.update()
        for ast in self.asteroids:
            ast.update(self.carrier.pos)

        # 보상 계산
        reward = -0.01 # 기본 생존 패널티
        terminated = False
        truncated = False

        # [수정] 행동 패널티 제거 (AI가 일단 움직이게 함)
        # if action != 0: reward -= 0.05 

        dist_to_station = np.linalg.norm(self.carrier.pos - self.station.pos)
        # [상향] 전진 보상 (0.2 -> 0.5): 정거장으로 가는 동기 대폭 강화
        reward += (self.prev_dist - dist_to_station) * 0.5 
        self.prev_dist = dist_to_station

        # 충돌 검사
        hit_ast = check_collision(self.carrier, self.asteroids)
        if hit_ast:
            reward -= 10.0 # 벌점 완화 (너무 무서워하지 않게)
            self.carrier.hull_integrity -= 10.0
            if self.carrier.hull_integrity <= 0:
                reward -= 50.0
                terminated = True

        # 연료 고갈 패널티 (150 -> 50)
        if self.carrier.fuel <= 0:
            reward -= 50.0
            terminated = True


        # 도킹 판정
        if dist_to_station < 70:
            speed = np.linalg.norm(self.carrier.vel)
            if speed < 1.0:
                reward += 1000.0
                # 남은 연료만큼 보너스 (연료 아끼기 유도)
                reward += self.carrier.fuel * 2.0 
                terminated = True
            else:
                reward -= 2.0

        if self.current_step >= self.max_steps:
            truncated = True

        keys = {pygame.K_w: action==1, pygame.K_s: action==2, pygame.K_a: action==3, 
                pygame.K_d: action==4, pygame.K_q: action==5, pygame.K_e: action==6}
        if self.render_mode == "human":
            self.render(keys)

        return self._get_obs(), reward, terminated, truncated, {}

    def render(self, keys=None):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((1200, 800))
            self.clock = pygame.time.Clock()
        self.screen.fill((0, 0, 0))
        self.carrier.draw(self.screen, keys if keys else {})
        self.station.draw(self.screen, self.carrier.pos)
        for ast in self.asteroids:
            ast.draw(self.screen, self.carrier.pos)
        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.screen is not None:
            pygame.quit()
