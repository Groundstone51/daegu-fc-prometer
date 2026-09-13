import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(
    page_title="2026 K리그2 주요 팀 승격 시뮬레이터 (Bayesian)",
    page_icon="⚽",
    layout="wide"
)

# 2. CSS 스타일링
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

# 3. 실시간 순위 데이터 로드
@st.cache_data(ttl=3600)
def fetch_realtime_standings():
    url = "https://sports.news.naver.com/kfootball/record/index?category=kleague2"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    try:
        response = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("#regularGroup_table tr")
        teams_data = []
        for row in rows:
            name = row.select_one(".name").text.strip()
            pts = int(row.select_one(".pts").text.strip())
            games = int(row.select_one(".num").text.strip())
            gf = int(row.select_one(".gf").text.strip())
            ga = int(row.select_one(".ga").text.strip())
            teams_data.append({"팀": name, "승점": pts, "경기수": games, "득점": gf, "실점": ga})
        if teams_data:
            return pd.DataFrame(teams_data), "🔴 실시간 갱신됨 (네이버 스포츠 연동)"
    except Exception:
        pass
        
    default_teams = [
        {"팀": "수원 삼성 블루윙즈", "승점": 53, "경기수": 25, "득점": 43, "실점": 24},
        {"팀": "대구 FC", "승점": 46, "경기수": 25, "득점": 42, "실점": 28},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 25, "득점": 38, "실점": 24},
        {"팀": "수원 FC", "승점": 44, "경기수": 24, "득점": 40, "실점": 22},
        {"팀": "화성 FC", "승점": 43, "경기수": 25, "득점": 35, "실점": 21},
        {"팀": "부산 아이파크", "승점": 38, "경기수": 24, "득점": 31, "실점": 25},
        {"팀": "충남 아산 FC", "승점": 31, "경기수": 24, "득점": 28, "실점": 27},
        {"팀": "성남 FC", "승점": 31, "경기수": 24, "득점": 27, "실점": 28},
        {"팀": "김포 FC", "승점": 31, "경기수": 24, "득점": 25, "실점": 27},
        {"팀": "경남 FC", "승점": 30, "경기수": 24, "득점": 27, "실점": 27},
        {"팀": "용인 FC", "승점": 26, "경기수": 24, "득점": 25, "실점": 29},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "득점": 22, "실점": 28},
        {"팀": "충북 청주 FC", "승점": 26, "경기수": 25, "득점": 21, "실점": 32},
        {"팀": "천안 시티 FC", "승점": 22, "경기수": 24, "득점": 21, "실점": 26},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 25, "득점": 19, "실점": 40},
        {"팀": "전남 드래곤즈", "승점": 20, "경기수": 24, "득점": 22, "실점": 34},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 24, "득점": 14, "실점": 43}
    ]
    return pd.DataFrame(default_teams), "🟡 기준 데이터 로드됨"

df_standings, status_msg = fetch_realtime_standings()

st.title("⚽ 2026 K리그2 승격 가능성 시뮬레이터 (Bayesian Model)")
st.caption(f"다중 팀 직접 결과 제어 및 포아송 연산 엔진 | {status_msg}")
st.divider()

# 팀별 잔여 경기 일정 데이터베이스
team_schedules = {
    "대구 FC": [
        {"R": 27, "상대팀": "서울 이랜드 FC", "장소": "원정"},
        {"R": 28, "상대팀": "수원 삼성 블루윙즈", "장소": "홈"},
        {"R": 29, "상대팀": "화성 FC", "장소": "홈"},
        {"R": 30, "상대팀": "전남 드래곤즈", "장소": "원정"},
        {"R": 31, "상대팀": "수원 FC", "장소": "원정"},
        {"R": 32, "상대팀": "경남 FC", "장소": "홈"},
    ],
    "수원 FC": [
        {"R": 27, "상대팀": "수원 삼성 블루윙즈", "장소": "홈"},
        {"R": 28, "상대팀": "부산 아이파크", "장소": "원정"},
        {"R": 29, "상대팀": "서울 이랜드 FC", "장소": "홈"},
        {"R": 30, "상대팀": "화성 FC", "장소": "원정"},
        {"R": 31, "상대팀": "대구 FC", "장소": "홈"},
        {"R": 32, "상대팀": "성남 FC", "장소": "원정"},
    ],
    "수원 삼성 블루윙즈": [
        {"R": 27, "상대팀": "수원 FC", "장소": "원정"},
        {"R": 28, "상대팀": "대구 FC", "장소": "원정"},
        {"R": 29, "상대팀": "부산 아이파크", "장소": "홈"},
        {"R": 30, "상대팀": "서울 이랜드 FC", "장소": "홈"},
    ],
    "서울 이랜드 FC": [
        {"R": 27, "상대팀": "대구 FC", "장소": "홈"},
        {"R": 28, "상대팀": "화성 FC", "장소": "원정"},
        {"R": 29, "상대팀": "수원 FC", "장소": "원정"},
        {"R": 30, "상대팀": "수원 삼성 블루윙즈", "장소": "원정"},
    ],
    "화성 FC": [
        {"R": 27, "상대팀": "부산 아이파크", "장소": "홈"},
        {"R": 28, "상대팀": "서울 이랜드 FC", "장소": "홈"},
        {"R": 29, "상대팀": "대구 FC", "장소": "원정"},
        {"R": 30, "상대팀": "수원 FC", "장소": "홈"},
    ],
    "부산 아이파크": [
        {"R": 27, "상대팀": "화성 FC", "장소": "원정"},
        {"R": 28, "상대팀": "수원 FC", "장소": "홈"},
        {"R": 29, "상대팀": "수원 삼성 블루윙즈", "장소": "원정"},
        {"R": 30, "상대팀": "충남 아산 FC", "장소": "홈"},
    ]
}

# 4. 베이지안 포아송 다중 팀 시뮬레이션 엔진
def run_bayesian_simulation_multi(df, schedules, all_predictions, total_games=32, n_sims=3000):
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    avg_gf = (df['득점'] / df['경기수']).values
    avg_ga = (df['실점'] / df['경기수']).values
    league_avg_gf = avg_gf.mean()
    
    att_strength = avg_gf / league_avg_gf
    def_strength = avg_ga / league_avg_gf
    
    base_pts = df['승점'].values.astype(np.float64)
    games_played = df['경기수'].values.copy()
    pts_sim = np.tile(base_pts, (n_sims, 1))
    
    # 선택된 모든 주요 팀의 경기 결과 적용
    for team_name, match_preds in all_predictions.items():
        if team_name not in team_idx or team_name not in schedules:
            continue
        t_i = team_idx[team_name]
        
        for idx, match in enumerate(schedules[team_name]):
            opp_i = team_idx.get(match["상대팀"])
            choice = match_preds[idx]
            
            if choice == "자동 계산 (베이지안 확률)":
                continue  # 자동 계산은 하단 난수 시뮬레이션에서 일괄 처리
                
            if choice == "승리 ⭕":
                res = np.full(n_sims, 3)
            elif choice == "무승부 🔺":
                res = np.full(n_sims, 1)
            elif choice == "패배 ❌":
                res = np.full(n_sims, 0)
                
            pts_sim[:, t_i] += res
            games_played[t_i] += 1
            
            if opp_i is not None:
                opp_res = np.where(res == 3, 0, np.where(res == 1, 1, 3))
                pts_sim[:, opp_i] += opp_res
                games_played[opp_i] += 1

    # 나머지 지정되지 않은 경기들의 베이지안 시뮬레이션
    for i in range(n_teams):
        rem = total_games - games_played[i]
        if rem > 0:
            p_win = np.clip(0.35 * (att_strength[i] / def_strength[i]), 0.15, 0.65)
            p_draw = 0.28
            p_loss = 1.0 - p_win - p_draw
            
            sim_adds = np.random.choice([3, 1, 0], size=(n_sims, int(rem)), p=[p_win, p_draw, p_loss]).sum(axis=1)
            pts_sim[:, i] += sim_adds

    # 전 구단 최종 순위 확률 계산
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        # 승점 내림차순 순위 산출
        order = np.argsort(-pts_sim[s, :])
        for r, t_idx in enumerate(order, start=1):
            rank_matrix[s, t_idx] = r

    return rank_matrix, teams, team_idx

# 5. UI 출력
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 K리그2 현재 순위표")
    st.dataframe(df_standings[["팀", "승점", "경기수", "득점", "실점"]], use_container_width=True, hide_index=True, height=220)
    
    st.subheader("🗓️ 팀별 잔여 경기 직접 선택")
    
    # 탭을 통해 대구 FC 외 수원 FC, 수원 삼성 등 여러 팀의 결과를 선택 가능
    selected_teams = ["대구 FC", "수원 FC", "수원 삼성 블루윙즈", "서울 이랜드 FC", "화성 FC", "부산 아이파크"]
    tabs = st.tabs(selected_teams)
    
    all_user_preds = {}
    
    for team_name, tab in zip(selected_teams, tabs):
        with tab:
            st.caption(f"**{team_name}**의 승/무/패를 선택하세요.")
            team_preds = []
            if team_name in team_schedules:
                for idx, match in enumerate(team_schedules[team_name]):
                    label = f"R{match['R']} vs {match['상대팀']} ({match['장소']})"
                    choice = st.selectbox(
                        label, 
                        options=["자동 계산 (베이지안 확률)", "승리 ⭕", "무승부 🔺", "패배 ❌"], 
                        key=f"match_{team_name}_{idx}"
                    )
                    team_preds.append(choice)
            all_user_preds[team_name] = team_preds

with col2:
    st.subheader("📊 시뮬레이션 결과 및 확률")
    
    sim_count = st.slider("시뮬레이션 반복 횟수 설정", 1000, 10000, 3000, step=1000)
    
    rank_matrix, teams, team_idx = run_bayesian_simulation_multi(
        df_standings, team_schedules, all_user_preds, total_games=32, n_sims=sim_count
    )
    
    # 분석 대상 팀 선택
    target_team = st.selectbox("확률을 확인할 분석 대상 팀 선택", options=selected_teams, index=0)
    
    target_i = team_idx[target_team]
    target_ranks = rank_matrix[:, target_i]
    
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{target_team} 자동 승격 (1~2위)", f"{direct_p:.1f}%")
    m2.metric(f"{target_team} PO 진출 (3~6위)", f"{po_p:.1f}%")
    m3.metric("총 승격 가시권 확률", f"{direct_p + po_p:.1f}%")
    
    rank_df = pd.DataFrame({"예상 최종 순위": target_ranks})
    rank_counts = rank_df["예상 최종 순위"].value_counts().reset_index()
    rank_counts.columns = ["순위", "빈도수"]
    rank_counts = rank_counts.sort_values("순위")
    
    fig = px.bar(
        rank_counts, 
        x="순위", 
        y="빈도수", 
        text="빈도수", 
        title=f"<b>{target_team} 최종 순위 분포 (베이지안 분석)</b>",
        color_discrete_sequence=["#0085FF"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
