from stable_baselines3 import PPO
from env import SpaceCarrierEnv
import os

def train():
    # 환경 생성
    env = SpaceCarrierEnv(render_mode=None) # 학습 시에는 렌더링 끔
    
    # 모델 정의 (PPO 알고리즘 사용)
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_carrier_tensorboard/")

    # 학습 시작 (100만 스텝으로 상향)
    print("Training started...")
    model.learn(total_timesteps=1000000)
    
    # 모델 저장
    model.save("space_carrier_ppo")
    print("Training finished and model saved.")

def test():
    # 학습된 모델 불러오기
    env = SpaceCarrierEnv(render_mode="human")
    model = PPO.load("space_carrier_ppo")
    
    obs, info = env.reset()
    for _ in range(1000):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        
        if terminated or truncated:
            obs, info = env.reset()

if __name__ == "__main__":
    # 학습을 원하시면 train(), 테스트를 원하시면 test()를 실행하세요.
    train()
