import random
from collections import defaultdict

# 1. 팀별 현재 시즌 전적 데이터 (승, 무, 패, 총 득점, 총 실점, 남은 경기 수)
# ※ 실제 전적 기록을 입력하면 자동으로 승/무/패 확률이 계산됩니다.
team_records = {
    "Daegu FC":        {"W": 12, "D": 8,  "L": 10, "gf": 45, "ga": 40, "remaining": 8},
    "Suwon FC":        {"W": 13, "D": 6,  "L": 11, "gf": 48, "ga": 40, "remaining": 8},
    "Suwon Samsung":   {"W": 14, "D": 5,  "L": 11, "gf": 46, "ga": 40, "remaining": 8},
    "Seoul E-Land":    {"W": 15, "D": 4,  "L": 11, "gf": 50, "ga": 40, "remaining": 8},
    "Hwaseong FC":     {"W": 10, "D": 10, "L": 10, "gf": 39, "ga": 38, "remaining": 8},
    "Busan IPark":     {"W": 11, "D": 9,  "L": 10, "gf": 42, "ga": 39, "remaining": 8},
}

# 2. 직접 지정할 경기 결과 (승무패 및 상세 스코어)
# 지정하지 않은 경기나 팀은 전적 기반 승률 시뮬레이션이 적용됩니다.
manual_overrides = {
    "Daegu FC":        [("W", 2, 0), ("W", 3, 1), ("D", 1, 1), ("W", 2, 1)],
    "Suwon FC":        [("W", 1, 0), ("D", 2, 2), ("L", 0, 2), ("W", 3, 1)],
    "Suwon Samsung":   ["W", "W", "W", "D"],
    "Seoul E-Land":    ["W", "D", "W", "L"],
    "Hwaseong FC":     ["D", "W", "W", "W"],
    "Busan IPark":     ["W", "W", "D", "W"],
}

def get_team_probabilities(record):
    """지나온 경기 전적(W, D, L)을 기반으로 승/무/패 발생 확률을 계산합니다."""
    total_games = record["W"] + record["D"] + record["L"]
    if total_games == 0:
        return [0.333, 0.333, 0.334]
    
    p_win = record["W"] / total_games
    p_draw = record["D"] / total_games
    p_loss = record["L"] / total_games
    return [p_win, p_draw, p_loss]

def simulate_match_stats(outcome):
    """경기 결과에 맞춘 무작위 득점/실점 생성기"""
    if outcome == 3:    # 승
        gf = random.choice([1, 2, 3, 4])
        ga = random.randint(0, gf - 1)
    elif outcome == 1:  # 무
        gf = random.choice([0, 1, 2, 3])
        ga = gf
    else:              # 패
        ga = random.choice([1, 2, 3, 4])
        gf = random.randint(0, ga - 1)
    return gf, ga

def simulate_season_with_record_weights(records, overrides, target_rank=1, num_simulations=10000):
    success_counts = defaultdict(int)
    
    for _ in range(num_simulations):
        simulated_data = {}
        
        for team, rec in records.items():
            # 전적 바탕 초기 승점, 골득실, 승수 산출
            pts = (rec["W"] * 3) + (rec["D"] * 1)
            gf = rec["gf"]
            gd = rec["gf"] - rec["ga"]
            wins = rec["W"]
            remaining_games = rec["remaining"]
            
            # 1) 수동 입력 경기 반영
            if team in overrides:
                for match in overrides[team]:
                    if isinstance(match, tuple):
                        res, m_gf, m_ga = match
                    else:
                        res = match
                        m_gf, m_ga = (2, 0) if res == "W" else ((1, 1) if res == "D" else (0, 2))
                    
                    if res == "W":
                        pts += 3
                        wins += 1
                    elif res == "D":
                        pts += 1
                    
                    gf += m_gf
                    gd += (m_gf - m_ga)
                
                remaining_games = max(0, remaining_games - len(overrides[team]))
            
            # 2) 전적 기반 승/무/패 확률 산출 후 남은 경기 시뮬레이션
            win_p, draw_p, loss_p = get_team_probabilities(rec)
            
            for _ in range(remaining_games):
                # 전적 기반 가중치로 승(3점), 무(1점), 패(0점) 추첨
                outcome = random.choices([3, 1, 0], weights=[win_p, draw_p, loss_p])[0]
                m_gf, m_ga = simulate_match_stats(outcome)
                
                pts += outcome
                if outcome == 3:
                    wins += 1
                gf += m_gf
                gd += (m_gf - m_ga)
                
            simulated_data[team] = {
                "points": pts,
                "goals_for": gf,
                "goal_diff": gd,
                "wins": wins
            }
            
        # 3) K리그 동률 순위 결정 (승점 -> 다득점 -> 골득실 -> 다승)
        sorted_teams = sorted(
            simulated_data.items(),
            key=lambda x: (
                x[1]["points"],
                x[1]["goals_for"],
                x[1]["goal_diff"],
                x[1]["wins"]
            ),
            reverse=True
        )
        
        for rank, (team, _) in enumerate(sorted_teams, start=1):
            if rank <= target_rank:
                success_counts[team] += 1
                
    # 결과 출력
    print(f"=== 전적 기반 승률 반영 시뮬레이션 ({num_simulations:,}회 실행 / 목표: {target_rank}위 이내) ===")
    for team, rec in records.items():
        total = rec["W"] + rec["D"] + rec["L"]
        win_rate = (rec["W"] / total * 100) if total > 0 else 0
        prob = (success_counts[team] / num_simulations) * 100
        print(f"- {team:<15} (기존승률: {win_rate:.1f}%): {prob:.2f}%")

# 시뮬레이션 실행 (target_rank=1 : 1위 직행)
simulate_season_with_record_weights(team_records, manual_overrides, target_rank=1, num_simulations=10000)
