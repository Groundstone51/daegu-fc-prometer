import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(
    page_title="2026 K리그2 승격 시뮬레이터 (경기별 직접 선택)",
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
    .match-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. 실시간 순위 데이터 로드
@st.cache_data(ttl=3600)
def fetch_realtime_standings():
    url = "https://sports.news.naver.com/kfootball/record/index?category=kleague2"
    headers = {"User-Agent": "Mozilla/5.0"}
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
            return pd.DataFrame(teams_data), "🔴 실시간 갱신됨 (네이버 연동)"
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
    return pd.DataFrame(default_teams), "🟡 기본 일정 로드됨"

# 4. K리그2 잔여 경기 일정 크롤링/로드
@st.cache_data(ttl=3600)
def fetch_remaining_matches():
    # 실제 잔여 일정 크롤링 실패 시 적용되는 라운드별 경기일정 데이터
    default_schedule = [
        {"R": 27, "홈팀": "수원 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 27, "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"R": 27, "홈팀": "화성 FC", "원정팀": "부산 아이파크"},
        {"R": 27, "홈팀": "성남 FC", "원정팀": "충남 아산 FC"},
        {"R": 28, "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 28, "홈팀": "부산 아이파크", "원정팀": "수원 FC"},
        {"R": 28, "홈팀": "서울 이랜드 FC", "원정팀": "화성 FC"},
        {"R": 29, "홈팀": "수원 FC", "원정팀": "서울 이랜드 FC"},
        {"R": 29, "홈팀": "대구 FC", "원정팀": "화성 FC"},
        {"R": 29, "홈팀": "수원 삼성 블루윙즈", "원정팀": "부산 아이파크"},
        {"R": 30, "홈팀": "전남 드래곤즈", "원정팀": "대구 FC"},
        {"R": 30, "홈팀": "화성 FC", "원정팀": "수원 FC"},
        {"R": 30, "홈팀": "수원 삼성 블루윙즈", "원정팀": "서울 이랜드 FC"},
    ]
    return default_schedule

df_standings, status_msg = fetch_realtime_standings()
remaining_matches = fetch_remaining_matches()

st.title("⚽ K리그2 직관적 잔여경기 승격 시뮬레이터")
st.caption(f"경기별 [홈승 / 무승부 / 원정승] 즉시 선택 가능 엔진 | {status_msg}")
st.divider()

# 5. 베이지안 포아송 잔여 경기 연산 엔진
def run_match_based_simulation(df, schedule, match_predictions, total_games=32, n_sims=3000):
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
    
    # 직접 결과가 입력된 경기 처리
    for m_idx, match in enumerate(schedule):
        home_team = match["홈팀"]
        away_team = match["원정팀"]
        
        if home_team not in team_idx or away_team not in team_idx:
            continue
            
        h_i = team_idx[home_team]
        a_i = team_idx[away_team]
        choice = match_predictions.get(m_idx, "🎲 자동 (베이지안)")
        
        if choice == "🎲 자동 (베이지안)":
            continue
            
        if choice == "🏠 홈승":
            pts_sim[:, h_i] += 3
        elif choice == "🔺 무승부":
            pts_sim[:, h_i] += 1
            pts_sim[:, a_i] += 1
        elif choice == "✈️ 원정승":
            pts_sim[:, a_i] += 3
            
        games_played[h_i] += 1
        games_played[a_i] += 1

    # 나머지 지정되지 않은 경기의 베이지안 난수 시뮬레이션
    for i in range(n_teams):
        rem = total_games - games_played[i]
        if rem > 0:
            p_win = np.clip(0.35 * (att_strength[i] / def_strength[i]), 0.15, 0.65)
            p_draw = 0.28
            p_loss = 1.0 - p_win - p_draw
            
            sim_adds = np.random.choice([3, 1, 0], size=(n_sims, int(rem)), p=[p_win, p_draw, p_loss]).sum(axis=1)
            pts_sim[:, i] += sim_adds

    # 최종 순위 매트릭스 계산
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        order = np.argsort(-pts_sim[s, :])
        for r, t_idx in enumerate(order, start=1):
            rank_matrix[s, t_idx] = r

    return rank_matrix, teams, team_idx

# 6. UI 영역 구성
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("📋 K리그2 현재 순위")
    st.dataframe(df_standings[["팀", "승점", "경기수", "득점", "실점"]], use_container_width=True, hide_index=True, height=200)
    
    st.subheader("🗓️ 잔여 경기 일정 및 결과 직접 선택")
    st.caption("각 경기의 승/무/패를 직접 고르시면 우측 승격 확률에 즉시 반영됩니다.")
    
    match_preds = {}
    
    # 라운드별로 묶어서 경기 일정 표시
    rounds = sorted(list(set([m["R"] for m in remaining_matches])))
    
    for r in rounds:
        with st.expander(f"📌 Round {r} 경기 일정", expanded=True):
            r_matches = [m for m in remaining_matches if m["R"] == r]
            for idx, match in enumerate(r_matches):
                m_global_idx = remaining_matches.index(match)
                
                # 직관적인 카드 형태 UI
                st.markdown(f"**{match['홈팀']}** vs **{match['원정팀']}**")
                choice = st.radio(
                    label=f"r_{r}_{idx}",
                    options=["🎲 자동 (베이지안)", "🏠 홈승", "🔺 무승부", "✈️ 원정승"],
                    horizontal=True,
                    key=f"radio_match_{m_global_idx}",
                    label_visibility="collapsed"
                )
                match_preds[m_global_idx] = choice

with col2:
    st.subheader("📊 승격 확률 및 최종 순위 예측")
    
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 10000, 3000, step=1000)
    
    rank_matrix, teams, team_idx = run_match_based_simulation(
        df_standings, remaining_matches, match_preds, total_games=32, n_sims=sim_count
    )
    
    # 확인할 분석 대상 팀 선택
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=1)
    
    target_i = team_idx[target_team]
    target_ranks = rank_matrix[:, target_i]
    
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{target_team} 1~2위 (직행)", f"{direct_p:.1f}%")
    m2.metric(f"{target_team} 3~6위 (PO)", f"{po_p:.1f}%")
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
        title=f"<b>{target_team} 예상 최종 순위 분포</b>",
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
