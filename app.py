import streamlit as st
import random
from collections import defaultdict

# 페이지 제목 설정
st.title("⚽ K리그2 승격 확률 시뮬레이터")

# 1. 팀별 현재 전적 데이터
team_records = {
    "Daegu FC":        {"W": 14, "D": 9,  "L": 7,  "gf": 48, "ga": 36, "remaining": 6},
    "Suwon FC":        {"W": 15, "D": 7,  "L": 8,  "gf": 52, "ga": 38, "remaining": 6},
    "Suwon Samsung":   {"W": 13, "D": 10, "L": 7,  "gf": 44, "ga": 35, "remaining": 6},
    "Seoul E-Land":    {"W": 14, "D": 6,  "L": 10, "gf": 49, "ga": 41, "remaining": 6},
    "Hwaseong FC":     {"W": 11, "D": 11, "L": 8,  "gf": 38, "ga": 34, "remaining": 6},
    "Busan IPark":     {"W": 12, "D": 8,  "L": 10, "gf": 43, "ga": 39, "remaining": 6},
}

# 2. 팀별 수동 개입 결과 지정
manual_overrides = {
    "Daegu FC":        [("W", 2, 0), ("W", 3, 1), ("D", 1, 1)],
    "Suwon FC":        [("W", 1, 0), ("D", 2, 2), ("L", 0, 1)],
    "Suwon Samsung":   ["W", "W", "D"],
    "Seoul E-Land":    ["W", "D", "L"],
    "Hwaseong FC":     ["D", "W", "W"],
    "Busan IPark":     ["W", "W", "D"],
}

def get_team_probabilities(record):
    total_games = record["W"] + record["D"] + record["L"]
    if total_games == 0:
        return [0.333, 0.333, 0.334]
    return [record["W"] / total_games, record["D"] / total_games, record["L"] / total_games]

def simulate_match_stats_by_avg(outcome, avg_gf, avg_ga):
    if outcome == 3:
        gf = max(1, round(random.gauss(avg_gf + 0.5, 0.8)))
        ga = random.randint(0, gf - 1)
    elif outcome == 1:
        gf = max(0, round(random.gauss(avg_gf, 0.7)))
        ga = gf
    else:
        ga = max(1, round(random.gauss(avg_ga + 0.5, 0.8)))
        gf = random.randint(0, ga - 1)
    return gf, ga

# 실행 버튼 추가 (웹 인터페이스)
if st.button("🚀 시뮬레이션 돌리기"):
    with st.spinner("10,000회 모의 시뮬레이션 계산 중..."):
        num_simulations = 10000
        target_rank = 1
        success_counts = defaultdict(int)
        
        for _ in range(num_simulations):
            simulated_data = {}
            for team, rec in team_records.items():
                pts = (rec["W"] * 3) + (rec["D"] * 1)
                gf = rec["gf"]
                gd = rec["gf"] - rec["ga"]
                wins = rec["W"]
                remaining_games = rec["remaining"]
                
                played = rec["W"] + rec["D"] + rec["L"]
                avg_gf = rec["gf"] / played if played > 0 else 1.2
                avg_ga = rec["ga"] / played if played > 0 else 1.2
                
                # 수동 입력
                if team in manual_overrides:
                    for match in manual_overrides[team]:
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
                    remaining_games = max(0, remaining_games - len(manual_overrides[team]))
                
                # 전적 기반 확률 시뮬레이션
                win_p, draw_p, loss_p = get_team_probabilities(rec)
                for _ in range(remaining_games):
                    outcome = random.choices([3, 1, 0], weights=[win_p, draw_p, loss_p])[0]
                    m_gf, m_ga = simulate_match_stats_by_avg(outcome, avg_gf, avg_ga)
                    pts += outcome
                    if outcome == 3:
                        wins += 1
                    gf += m_gf
                    gd += (m_gf - m_ga)
                    
                simulated_data[team] = {"points": pts, "goals_for": gf, "goal_diff": gd, "wins": wins}
                
            # K리그 동률 규정 정렬
            sorted_teams = sorted(
                simulated_data.items(),
                key=lambda x: (x[1]["points"], x[1]["goals_for"], x[1]["goal_diff"], x[1]["wins"]),
                reverse=True
            )
            
            for rank, (team, _) in enumerate(sorted_teams, start=1):
                if rank <= target_rank:
                    success_counts[team] += 1

        # Streamlit 화면에 결과 출력
        st.subheader("📊 1위(직행 승격) 확률 결과")
        for team, rec in team_records.items():
            prob = (success_counts[team] / num_simulations) * 100
            st.metric(label=team, value=f"{prob:.2f}%")
