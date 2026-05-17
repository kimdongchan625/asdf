import numpy as np
import torch as th
import torch.nn as nn
import torch.optim as optim
from stable_baselines3 import PPO
from env import SpaceCarrierEnv
import os

def behavior_cloning():
    # 1. 데이터 불러오기
    if not os.path.exists("expert_data.npz"):
        print("Error: expert_data.npz not found!")
        return

    data = np.load("expert_data.npz")
    expert_obs = th.tensor(data['obs'], dtype=th.float32)
    expert_actions = th.tensor(data['actions'], dtype=th.long)
    print(f"Loaded {len(expert_obs)} steps of expert data.")

    # 2. 모델 생성 (또는 기존 모델 불러오기)
    env = SpaceCarrierEnv()
    model_path = "space_carrier_ppo"
    
    if os.path.exists(model_path + ".zip"):
        print("Updating existing model with imitation learning...")
        model = PPO.load(model_path, env=env)
    else:
        print("Creating new model for imitation learning...")
        model = PPO("MlpPolicy", env, verbose=1)

    # 3. 모델의 신경망 추출 및 학습 설정
    # PPO의 policy(두뇌) 부분을 직접 학습시킵니다.
    policy = model.policy
    optimizer = optim.Adam(policy.parameters(), lr=1e-4)
    loss_fn = nn.CrossEntropyLoss()

    # 4. 학습 시작 (Behavior Cloning)
    print("Imitation Learning (Behavior Cloning) started...")
    epochs = 100 # 반복 횟수
    batch_size = 64
    
    for epoch in range(epochs):
        # 무작위 셔플링
        indices = th.randperm(len(expert_obs))
        total_loss = 0
        
        for i in range(0, len(expert_obs), batch_size):
            batch_indices = indices[i:i+batch_size]
            obs_batch = expert_obs[batch_indices]
            act_batch = expert_actions[batch_indices]
            
            # AI의 예측값
            dist = policy.get_distribution(obs_batch)
            log_probs = dist.log_prob(act_batch)
            
            # [수정] SB3 v2 API에 맞게 신경망 출력값(Logits) 추출
            features = policy.extract_features(obs_batch)
            latent_pi, _ = policy.mlp_extractor(features)
            logits = policy.action_net(latent_pi)
            
            loss = loss_fn(logits, act_batch)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/(len(expert_obs)/batch_size):.4f}")

    # 5. 저장
    model.save(model_path)
    print(f"Imitation learning finished. Model saved as {model_path}.zip")

if __name__ == "__main__":
    behavior_cloning()
