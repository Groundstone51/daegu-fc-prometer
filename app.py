import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 순수 베이지안 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 팀명 및 매핑 정보
LOGO_MAP = {
    "수원 삼성 블루윙즈": "suwon_samsung.png",
    "대구 FC": "daegu.png",
    "수원 FC": "suwon_fc.png",
    "서울 이랜드 FC": "seoul.png",
    "화성 FC": "hwasung.png",
    "부산 아이파크": "busan.png",
    "경남 FC": "gyeongnam.png",
    "김포 FC": "gimpo.png",
    "충남 아산 FC": "chungnamasan.png",
    "성남 FC": "seongnam.png",
    "용인 FC": "yongin.png",
    "충북 청주 FC": "chungbukcheongju.png",
    "파주 프런티어 FC": "paju.png",
    "천안 시티 FC": "cheonan.png",
    "안산 그리너스 FC": "ansan.png",
    "전남 드래곤즈": "jeonnam.png",
    "김해 FC 2008": "gimhae.png"
}

VENUE_MAP = {
    "수원 삼성 블루윙즈": "수원월드컵경기장",
    "대구 FC": "DGB대구은행파크",
    "수원 FC": "수원종합운동장",
    "서울 이랜드 FC": "목동종합운동장",
    "화성 FC": "화성종합경기타운",
    "부산 아이파크": "부산아시아드주경기장",
    "경남 FC": "창원축구센터",
    "김포 FC": "솔터축구전용구장",
    "충남 아산 FC": "이순신종합운동장",
    "성남 FC": "탄천종합운동장",
    "용인 FC": "용인미르스타디움",
    "충북 청주 FC": "청주종합경기장",
    "파주 프런티어 FC": "파주스타디움",
    "천안 시티 FC": "천안종합운동장",
    "안산 그리너스 FC": "안산와~스타디움",
    "전남 드래곤즈": "광양축구전용구장",
    "김해 FC 2008": "김해운동장"
}

def get_logo_html(team_name, size=22):
    file_name = LOGO_MAP.get(team_name)
    if file_name:
        possible_paths = [file_name, os.path.join("emblem", file_name)]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    return f'<img src="data:image/png;base64,{encoded}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 6px;">'
                except Exception:
                    pass
    return ""

# 3. CSS 스타일링
st.markdown("""
    <style>
    .main { background-color: #F4F7FA; }
    h1 { color: #0085FF !important; font-weight: 800 !important; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stMetricLabel"] { color: #64748B; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #0085FF; font-weight: 800; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 4. 실시간 순위표 데이터 (최신 반영)
@st.cache_data(ttl=300)
def fetch_official_standings():
    data = [
        {"팀": "수원 삼성 블루윙즈", "경기수": 25, "승점": 53, "승": 16, "무": 5, "패": 4, "득점": 39, "실점": 20},
        {"팀": "수원 FC", "경기수": 25, "승점": 48, "승": 13, "무": 9, "패": 3, "득점": 50, "실점": 29},
        {"팀": "서울 이랜드 FC", "경기수": 26, "승점": 48, "승": 14, "무": 6, "패": 6, "득점": 45, "실점": 30},
        {"팀": "대구 FC", "경기수": 26, "승점": 46, "승": 13, "무": 7, "패": 6, "득점": 48, "실점": 35},
        {"팀": "화성 FC", "경기수": 25, "승점": 43, "승": 12, "무": 7, "패": 6, "득점": 39, "실점": 25},
        {"팀": "부산 아이파크", "경기수": 26, "승점": 41, "승": 12, "무": 5, "패": 9, "득점": 41, "실점": 34},
        {"팀": "김포 FC", "경기수": 25, "승점": 35, "승": 8, "무": 11, "패": 6, "득점": 31, "실점": 30},
        {"팀": "충남 아산 FC", "경기수": 25, "승점": 34, "승": 9, "무": 7, "패": 9, "득점": 34, "실점": 31},
        {"팀": "경남 FC", "경기수": 24, "승점": 33, "승": 8, "무": 9, "패": 7, "득점": 31, "실점": 30},
        {"팀": "성남 FC", "경기수": 24, "승점": 30, "승": 7, "무": 9, "패": 8, "득점": 26, "실점": 28},
        {"팀": "용인 FC", "경기수": 24, "승점": 26, "승": 5, "무": 11, "패": 8, "득점": 31, "실점": 35},
        {"팀": "충북 청주 FC", "경기수": 25, "승점": 26, "승": 4, "무": 14, "패": 7, "득점": 28, "실점": 39},
        {"팀": "파주 프런티어 FC", "경기수": 24, "승점": 26, "승": 7, "무": 5, "패": 12, "득점": 22, "실점": 28},
        {"팀": "천안 시티 FC", "경기수": 26, "승점": 23, "승": 4, "무": 11, "패": 11, "득점": 30, "실점": 37},
        {"팀": "안산 그리너스 FC", "경기수": 25, "승점": 22, "승": 6, "무": 4, "패": 15, "득점": 25, "실점": 46},
        {"팀": "전남 드래곤즈", "경기수": 25, "승점": 21, "승": 4, "무": 9, "패": 12, "득점": 28, "실점": 43},
        {"팀": "김해 FC 2008", "경기수": 24, "승점": 13, "승": 2, "무": 7, "패": 15, "득점": 19, "실점": 47}
    ]
    df = pd.DataFrame(data)
    df["득실차"] = df["득점"] - df["실점"]
    return df

# 5. 27R~34R 전체 잔여 일정 (최신 수정)
@st.cache_data(ttl=300)
def fetch_remaining_schedule():
    return [
        # 27R (9.20 진행 예정 경기)
        {"R": 27, "날짜": "09.20(일) 16:30", "장소": "안산와~스타디움", "홈팀": "안산 그리너스 FC", "원정팀": "충북 청주 FC"},
        {"R": 27, "날짜": "09.20(일) 16:30", "장소": "용인미르스타디움", "홈팀": "용인 FC", "원정팀": "경남 FC"},
        {"R": 27, "날짜": "09.20(일) 19:00", "장소": "탄천종합운동장", "홈팀": "성남 FC", "원정팀": "화성 FC"},
        {"R": 27, "날짜": "09.20(일) 19:00", "장소": "김해운동장", "홈팀": "김해 FC 2008", "원정팀": "파주 프런티어 FC"},
        
        # 28R
        {"R": 28, "날짜": "10.09(금) 14:00", "장소": "수원종합운동장", "홈팀": "수원 FC", "원정팀": "화성 FC"},
        {"R": 28, "날짜": "10.09(금) 16:30", "장소": "솔터축구전용구장", "홈팀": "김포 FC", "원정팀": "서울 이랜드 FC"},
        {"R": 28, "날짜": "10.09(금) 16:30", "장소": "청주종합경기장", "홈팀": "충북 청주 FC", "원정팀": "성남 FC"},
        {"R": 28, "날짜": "10.10(토) 14:00", "장소": "광양축구전용구장", "홈팀": "전남 드래곤즈", "원정팀": "용인 FC"},
        {"R": 28, "날짜": "10.10(토) 14:00", "장소": "파주스타디움", "홈팀": "파주 프런티어 FC", "원정팀": "부산 아이파크"},
        {"R": 28, "날짜": "10.10(토) 16:30", "장소": "천안종합운동장", "홈팀": "천안 시티 FC", "원정팀": "경남 FC"},
        {"R": 28, "날짜": "10.10(토) 16:30", "장소": "김해운동장", "홈팀": "김해 FC 2008", "원정팀": "충남 아산 FC"},
        {"R": 28, "날짜": "10.11(일) 14:00", "장소": "수원월드컵경기장", "홈팀": "수원 삼성 블루윙즈", "원정팀": "안산 그리너스 FC"},
        
        # 29R
        {"R": 29, "날짜": "10.17(토) 14:00", "장소": "DGB대구은행파크", "홈팀": "대구 FC", "원정팀": "충북 청주 FC"},
        {"R": 29, "날짜": "10.17(토) 14:00", "장소": "탄천종합운동장", "홈팀": "성남 FC", "원정팀": "수원 FC"},
        {"R": 29, "날짜": "10.17(토) 16:30", "장소": "창원축구센터", "홈팀": "경남 FC", "원정팀": "충남 아산 FC"},
        {"R": 29, "날짜": "10.17(토) 16:30", "장소": "솔터축구전용구장", "홈팀": "김포 FC", "원정팀": "파주 프런티어 FC"},
        {"R": 29, "날짜": "10.17(토) 16:30", "장소": "용인미르스타디움", "홈팀": "용인 FC", "원정팀": "안산 그리너스 FC"},
        {"R": 29, "날짜": "10.18(일) 14:00", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "김해 FC 2008"},
        {"R": 29, "날짜": "10.18(일) 14:00", "장소": "수원월드컵경기장", "홈팀": "수원 삼성 블루윙즈", "원정팀": "화성 FC"},
        {"R": 29, "날짜": "10.18(일) 16:30", "장소": "부산아시아드", "홈팀": "부산 아이파크", "원정팀": "전남 드래곤즈"},
        
        # 30R
        {"R": 30, "날짜": "10.24(토) 14:00", "장소": "광양축구전용구장", "홈팀": "전남 드래곤즈", "원정팀": "대구 FC"},
        {"R": 30, "날짜": "10.24(토) 16:30", "장소": "솔터축구전용구장", "홈팀": "김포 FC", "원정팀": "김해 FC 2008"},
        {"R": 30, "날짜": "10.24(토) 14:00", "장소": "부산아시아드", "홈팀": "부산 아이파크", "원정팀": "경남 FC"},
        {"R": 30, "날짜": "10.24(토) 14:00", "장소": "탄천종합운동장", "홈팀": "성남 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 30, "날짜": "10.24(토) 14:00", "장소": "수원종합운동장", "홈팀": "수원 FC", "원정팀": "충남 아산 FC"},
        {"R": 30, "날짜": "10.25(일) 16:30", "장소": "천안종합운동장", "홈팀": "천안 시티 FC", "원정팀": "안산 그리너스 FC"},
        {"R": 30, "날짜": "10.25(일) 16:30", "장소": "청주종합경기장", "홈팀": "충북 청주 FC", "원정팀": "용인 FC"},
        {"R": 30, "날짜": "10.25(일) 16:30", "장소": "파주스타디움", "홈팀": "파주 프런티어 FC", "원정팀": "화성 FC"},
        
        # 31R
        {"R": 31, "날짜": "10.31(토) 14:00", "장소": "창원축구센터", "홈팀": "경남 FC", "원정팀": "화성 FC"},
        {"R": 31, "날짜": "10.31(토) 14:00", "장소": "용인미르스타디움", "홈팀": "용인 FC", "원정팀": "서울 이랜드 FC"},
        {"R": 31, "날짜": "10.31(토) 16:30", "장소": "DGB대구은행파크", "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 31, "날짜": "10.31(토) 16:30", "장소": "이순신종합운동장", "홈팀": "충남 아산 FC", "원정팀": "김포 FC"},
        {"R": 31, "날짜": "10.31(토) 14:00", "장소": "수원종합운동장", "홈팀": "수원 FC", "원정팀": "안산 그리너스 FC"},
        {"R": 31, "날짜": "10.31(토) 14:00", "장소": "광양축구전용구장", "홈팀": "전남 드래곤즈", "원정팀": "성남 FC"},
        {"R": 31, "날짜": "11.01(일) 16:30", "장소": "김해운동장", "홈팀": "김해 FC 2008", "원정팀": "천안 시티 FC"},
        {"R": 31, "날짜": "11.01(일) 16:30", "장소": "청주종합경기장", "홈팀": "충북 청주 FC", "원정팀": "파주 프런티어 FC"},
        
        # 32R
        {"R": 32, "날짜": "11.07(토) 14:00", "장소": "탄천종합운동장", "홈팀": "성남 FC", "원정팀": "대구 FC"},
        {"R": 32, "날짜": "11.07(토) 14:00", "장소": "수원종합운동장", "홈팀": "수원 FC", "원정팀": "경남 FC"},
        {"R": 32, "날짜": "11.07(토) 16:30", "장소": "솔터축구전용구장", "홈팀": "김포 FC", "원정팀": "안산 그리너스 FC"},
        {"R": 32, "날짜": "11.07(토) 16:30", "장소": "김해운동장", "홈팀": "김해 FC 2008", "원정팀": "화성 FC"},
        {"R": 32, "날짜": "11.07(토) 16:30", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "전남 드래곤즈"},
        {"R": 32, "날짜": "11.08(일) 14:00", "장소": "수원월드컵경기장", "홈팀": "수원 삼성 블루윙즈", "원정팀": "용인 FC"},
        {"R": 32, "날짜": "11.08(일) 14:00", "장소": "천안종합운동장", "홈팀": "천안 시티 FC", "원정팀": "부산 아이파크"},
        {"R": 32, "날짜": "11.08(일) 16:30", "장소": "파주스타디움", "홈팀": "파주 프런티어 FC", "원정팀": "충남 아산 FC"},
        
        # 33R
        {"R": 33, "날짜": "11.21(토) 14:00", "장소": "부산아시아드", "홈팀": "부산 아이파크", "원정팀": "충북 청주 FC"},
        {"R": 33, "날짜": "11.21(토) 14:00", "장소": "수원월드컵경기장", "홈팀": "수원 삼성 블루윙즈", "원정팀": "경남 FC"},
        {"R": 33, "날짜": "11.21(토) 16:30", "장소": "솔터축구전용구장", "홈팀": "김포 FC", "원정팀": "수원 FC"},
        {"R": 33, "날짜": "11.21(토) 16:30", "장소": "탄천종합운동장", "홈팀": "성남 FC", "원정팀": "용인 FC"},
        {"R": 33, "날짜": "11.22(일) 14:00", "장소": "DGB대구은행파크", "홈팀": "대구 FC", "원정팀": "김해 FC 2008"},
        {"R": 33, "날짜": "11.22(일) 14:00", "장소": "광양축구전용구장", "홈팀": "전남 드래곤즈", "원정팀": "안산 그리너스 FC"},
        {"R": 33, "날짜": "11.22(일) 16:30", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "충남 아산 FC"},
        {"R": 33, "날짜": "11.22(일) 16:30", "장소": "파주스타디움", "홈팀": "파주 프런티어 FC", "원정팀": "천안 시티 FC"},
        
        # 34R (최종전 동시 개킥)
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "창원축구센터", "홈팀": "경남 FC", "원정팀": "서울 이랜드 FC"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "솔터축구전용구장", "홈팀": "김포 FC", "원정팀": "화성 FC"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "김해운동장", "홈팀": "김해 FC 2008", "원정팀": "성남 FC"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "수원종합운동장", "홈팀": "수원 FC", "원정팀": "충북 청주 FC"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "용인미르스타디움", "홈팀": "용인 FC", "원정팀": "파주 프런티어 FC"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "광양축구전용구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "천안종합운동장", "홈팀": "천안 시티 FC", "원정팀": "대구 FC"},
        {"R": 34, "날짜": "11.28(토) 16:00", "장소": "이순신종합운동장", "홈팀": "충남 아산 FC", "원정팀": "부산 아이파크"}
    ]

df_standings = fetch_official_standings()
remaining_matches = fetch_remaining_schedule()

st.title("⚽ K리그2 순수 베이지안 승격 시뮬레이터")
st.caption("🔮 감마-포아송 베이지안 추론 기반 몬테카를로 시뮬레이션")
st.divider()

# 6. 베이지안 시뮬레이션 엔진
def run_bayesian_simulation(df_base, future_schedule, future_preds, total_games=32, n_sims=5000):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    base_pts = df['승점'].values.astype(np.float64)
    games_played = df['경기수'].values.copy()
    
    prior_alpha, prior_beta = 2.0, 1.5
    
    post_alpha_att = prior_alpha + df['득점'].values
    post_beta_att = prior_beta + games_played
    post_alpha_def = prior_alpha + df['실점'].values
    post_beta_def = prior_beta + games_played

    lambda_att = np.random.gamma(post_alpha_att, 1.0 / post_beta_att, size=(n_sims, n_teams))
    lambda_def = np.random.gamma(post_alpha_def, 1.0 / post_beta_def, size=(n_sims, n_teams))

    pts_sim = np.tile(base_pts, (n_sims, 1))
    gf_sim = np.tile(df['득점'].values.astype(np.float64), (n_sims, 1))
    ga_sim = np.tile(df['실점'].values.astype(np.float64), (n_sims, 1))

    # 선택된 경기 결과 반영
    for m_idx, match in enumerate(future_schedule):
        home_team = match["홈팀"]
        away_team = match["원정팀"]
        if home_team not in team_idx or away_team not in team_idx:
            continue
            
        h_i = team_idx[home_team]
        a_i = team_idx[away_team]
        choice = future_preds.get(m_idx, "🎲 베이지안 추론")
        
        if choice == "🎲 베이지안 추론":
            exp_h = lambda_att[:, h_i] * lambda_def[:, a_i]
            exp_a = lambda_att[:, a_i] * lambda_def[:, h_i]
            
            sim_h = np.random.poisson(exp_h)
            sim_a = np.random.poisson(exp_a)
            
            pts_sim[:, h_i] += np.where(sim_h > sim_a, 3, np.where(sim_h == sim_a, 1, 0))
            pts_sim[:, a_i] += np.where(sim_a > sim_h, 3, np.where(sim_h == sim_a, 1, 0))
            gf_sim[:, h_i] += sim_h
            ga_sim[:, h_i] += sim_a
            gf_sim[:, a_i] += sim_a
            ga_sim[:, a_i] += sim_h
        else:
            if f"🏠 {home_team} 승" in choice:
                pts_sim[:, h_i] += 3
            elif "🔺 무승부" in choice:
                pts_sim[:, h_i] += 1
                pts_sim[:, a_i] += 1
            elif f"✈️ {away_team} 승" in choice:
                pts_sim[:, a_i] += 3

        games_played[h_i] += 1
        games_played[a_i] += 1

    # 미지정 잔여 대진 32경기 완주 시뮬레이션
    for i in range(n_teams):
        rem_n = int(total_games - games_played[i])
        if rem_n > 0:
            opponents = np.random.choice([j for j in range(n_teams) if j != i], size=(rem_n, n_sims))
            exp_i = lambda_att[:, i] * lambda_def[np.arange(n_sims), opponents]
            exp_opp = lambda_att[np.arange(n_sims), opponents] * lambda_def[:, i]
            
            goals_i = np.random.poisson(exp_i)
            goals_opp = np.random.poisson(exp_opp)
            
            pts_gained = np.where(goals_i > goals_opp, 3, np.where(goals_i == goals_opp, 1, 0)).sum(axis=0)
            gf_gained = goals_i.sum(axis=0)
            ga_gained = goals_opp.sum(axis=0)
            
            pts_sim[:, i] += pts_gained
            gf_sim[:, i] += gf_gained
            ga_sim[:, i] += ga_gained

    gd_sim = gf_sim - ga_sim
    rank_matrix = np.zeros((n_sims, n_teams))
    
    for s in range(n_sims):
        scores = [(pts_sim[s, i], gf_sim[s, i], gd_sim[s, i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx, base_pts

# 7. UI 구성 및 필터링 기능
col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.subheader("🗓️ 잔여 경기 예측 필터")
    
    # 경기 표시 필터 옵션
    top_6_teams = df_standings.head(6)["팀"].tolist()
    filter_option = st.selectbox(
        "🔍 경기 목록 보기 필터",
        ["전체 경기 보기", "🔥 상위 6개 팀 관련 경기만 보기", "🎯 특정 팀 핵심 경기만 보기"]
    )
    
    selected_filter_team = None
    if filter_option == "🎯 특정 팀 핵심 경기만 보기":
        selected_filter_team = st.selectbox("팀 선택", options=df_standings["팀"].tolist(), index=0)

    # 필터 조건에 맞춰 잔여 경기 리스트 필터링
    filtered_matches = []
    for m in remaining_matches:
        h, a = m["홈팀"], m["원정팀"]
        if filter_option == "전체 경기 보기":
            filtered_matches.append(m)
        elif filter_option == "🔥 상위 6개 팀 관련 경기만 보기":
            if h in top_6_teams or a in top_6_teams:
                filtered_matches.append(m)
        elif filter_option == "🎯 특정 팀 핵심 경기만 보기":
            # 선택 팀 경기 중 상위 6개 팀과의 맞대결
            if (h == selected_filter_team and a in top_6_teams) or (a == selected_filter_team and h in top_6_teams):
                filtered_matches.append(m)

    future_preds = {}
    if not filtered_matches:
        st.info("조건에 일치하는 잔여 경기가 없습니다.")
    else:
        fut_rounds = sorted(list(set([m["R"] for m in filtered_matches])))
        for r in fut_rounds:
            with st.expander(f"📌 Round {r} 잔여 경기", expanded=(r==27)):
                r_matches = [m for m in filtered_matches if m["R"] == r]
                for idx, match in enumerate(r_matches):
                    m_global_idx = remaining_matches.index(match)
                    h_team, a_team = match['홈팀'], match['원정팀']
                    m_date, m_venue = match.get('날짜', ''), match.get('장소', '')
                    
                    st.caption(f"📅 일시: {m_date} | 📍 장소: {m_venue}")
                    
                    match_header_html = f"""
                    <div style="font-size: 1.05rem; font-weight: bold; margin-bottom: 6px;">
                        {get_logo_html(h_team, size=22)}{h_team}
                        <span style="color:#94A3B8; margin: 0 8px;">VS</span> 
                        {get_logo_html(a_team, size=22)}{a_team}
                    </div>
                    """
                    st.markdown(match_header_html, unsafe_allow_html=True)
                    
                    opt_home = f"🏠 {h_team} 승"
                    opt_draw = "🔺 무승부"
                    opt_away = f"✈️ {a_team} 승"
                    
                    choice = st.radio(
                        label=f"r_fut_{r}_{idx}",
                        options=["🎲 베이지안 추론", opt_home, opt_draw, opt_away],
                        horizontal=True,
                        key=f"radio_fut_r{r}_idx{idx}_g{m_global_idx}_{h_team}_vs_{a_team}",
                        label_visibility="collapsed"
                    )
                    future_preds[m_global_idx] = choice
                    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

with col2:
    st.subheader("📊 베이지안 승격 확률 및 순위 예측")
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx, base_pts = run_bayesian_simulation(
        df_standings, remaining_matches, future_preds, total_games=32, n_sims=sim_count
    )
    
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=0)
    target_i = team_idx[target_team]
    target_ranks = rank_matrix[:, target_i]
    
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    total_promotion_p = direct_p + po_p
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{target_team} 1~2위 (직행)", f"{direct_p:.1f}%")
    m2.metric(f"{target_team} 3~6위 (PO)", f"{po_p:.1f}%")
    m3.metric("총 승격 가시권 (1~6위)", f"{total_promotion_p:.1f}%")
    
    rank_df = pd.DataFrame({"예상 최종 순위": target_ranks})
    rank_counts = rank_df["예상 최종 순위"].value_counts().reset_index()
    rank_counts.columns = ["순위", "빈도수"]
    rank_counts = rank_counts.sort_values("순위")
    
    fig = px.bar(
        rank_counts, 
        x="순위", 
        y="빈도수", 
        text="빈도수", 
        title=f"<b>{target_team} 베이지안 사후 최종 순위 분포 ({sim_count:,}회)</b>",
        color_discrete_sequence=["#0085FF"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
