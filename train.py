from stable_baselines3 import PPO
from env import SpaceCarrierEnv
import os

def train():
    env = SpaceCarrierEnv(render_mode=None)
    model_path = "space_carrier_ppo"
    
    if os.path.exists(model_path + ".zip"):
        print(f"Loading existing model: {model_path}")
        model = PPO.load(model_path, env=env, verbose=1, tensorboard_log="./ppo_carrier_tensorboard/")
    else:
        print("No existing model found. Creating a new one.")
        model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_carrier_tensorboard/")

    print("Training started...")
    model.learn(total_timesteps=1000000, reset_num_timesteps=False) # reset_num_timesteps=False로 설정하여 학습 기록 유지
    
    model.save(model_path)
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
