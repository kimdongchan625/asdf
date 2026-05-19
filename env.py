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

        # 보상 계산 (단계별 목표 지향 학습 - Reward Shaping)
        reward = -0.01 # 기본 생존 패널티
        terminated = False
        truncated = False

        dist_to_station = np.linalg.norm(self.carrier.pos - self.station.pos)
        speed = np.linalg.norm(self.carrier.vel)

        # 1. 목표를 향해 기수를 돌리는 것에 대한 보상 (Alignment)
        if dist_to_station > 0:
            target_vec = (self.station.pos - self.carrier.pos) / dist_to_station
            # 우주선의 현재 기수 방향 벡터
            heading_vec = np.array([math.cos(rad), -math.sin(rad)])
            # 두 벡터의 내적 (1에 가까울수록 정면, -1이면 반대)
            alignment = np.dot(target_vec, heading_vec)
            reward += alignment * 0.1 # 올바른 방향을 볼 때 지속적인 소량의 보상

        # 2. 목표를 향해 전진하는 보상
        reward += (self.prev_dist - dist_to_station) * 0.5 
        self.prev_dist = dist_to_station

        # 2-1. 정거장 근처(500px 이내)에 오면 속도를 줄이도록 유도
        if dist_to_station < 500:
            # 거리가 가까울수록 허용되는 안전 속도가 낮아짐
            safe_speed = max(1.0, dist_to_station / 100.0) 
            if speed > safe_speed:
                reward -= (speed - safe_speed) * 0.1 # 과속 감점

        # 3. 소행성 회피 및 충돌 패널티
        hit_ast = check_collision(self.carrier, self.asteroids)
        if hit_ast:
            reward -= 20.0 # 강한 감점 복구
            self.carrier.hull_integrity -= 10.0
            if self.carrier.hull_integrity <= 0:
                reward -= 50.0
                terminated = True

        # 소행성에 너무 가까이 가면 미세한 경고 감점 (회피 유도)
        for ast in self.asteroids:
            if np.linalg.norm(self.carrier.pos - ast.pos) < ast.radius + 100:
                reward -= 0.1

        # 연료 고갈 패널티
        if self.carrier.fuel <= 0:
            reward -= 50.0
            terminated = True

        # 도킹 판정
        if dist_to_station < 70:
            if speed < 1.5: # 약간 넉넉한 도킹 속도
                reward += 1000.0
                reward += self.carrier.fuel * 2.0 
                terminated = True
            else:
                reward -= 10.0 # 충돌 처리

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
