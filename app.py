import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 및 레이아웃
st.set_page_config(
    page_title="2026 대구 FC 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 커스텀 CSS (대구 FC 하늘색 테마)
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

# 3. 실시간 K리그2 순위 크롤링 (1시간 캐싱)
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
    return pd.DataFrame(default_teams), "🟡 기준 데이터 로드됨 (네이버 접속 불가시 백업용)"

df_standings, status_msg = fetch_realtime_standings()

st.title("⚽ 2026 대구 FC 승격 가능성 시뮬레이터")
st.caption(f"K리그2 17개 구단 체제 반영 | {status_msg}")
st.divider()

daegu_schedule = [
    {"R": 27, "상대팀": "서울 이랜드 FC", "장소": "원정"},
    {"R": 28, "상대팀": "수원 삼성 블루윙즈", "장소": "홈"},
    {"R": 29, "상대팀": "화성 FC", "장소": "홈"},
    {"R": 30, "상대팀": "전남 드래곤즈", "장소": "원정"},
    {"R": 31, "상대팀": "수원 FC", "장소": "원정"},
    {"R": 32, "상대팀": "경남 FC", "장소": "홈"},
    {"R": 33, "상대팀": "성남 FC", "장소": "홈"},
    {"R": 34, "상대팀": "충남 아산 FC", "장소": "원정"}
]

# 4. 연산 최적화 시뮬레이션 로직
def run_fast_simulation(df, schedule, user_predictions, total_games=32, n_sims=3000):
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    daegu_i = team_idx.get("대구 FC", 1)
    
    base_pts = df['승점'].values.astype(np.float64)
    base_gf = df['득점'].values.astype(np.float64)
    base_ga = df['실점'].values.astype(np.float64)
    games_played = df['경기수'].values.copy()
    
    # 3000번 시뮬레이션용 배열 미리 확보
    pts_sim = np.tile(base_pts, (n_sims, 1))
    
    # 대구 FC 잔여 경기 고정/확률 계산
    for idx, match in enumerate(schedule):
        opp_i = team_idx.get(match["상대팀"])
        choice = user_predictions[idx]
        
        if choice == "승리 ⭕":
            res = np.full(n_sims, 3)
        elif choice == "무승부 🔺":
            res = np.full(n_sims, 1)
        elif choice == "패배 ❌":
            res = np.full(n_sims, 0)
        else:
            p_win = 0.42 if match["장소"] == "홈" else 0.32
            res = np.random.choice([3, 1, 0], size=n_sims, p=[p_win, 0.28, 1.0 - p_win - 0.28])
            
        pts_sim[:, daegu_i] += res
        games_played[daegu_i] += 1
        
        if opp_i is not None:
            opp_res = np.where(res == 3, 0, np.where(res == 1, 1, 3))
            pts_sim[:, opp_i] += opp_res
            games_played[opp_i] += 1

    # 타 구단 잔여 경기 일괄 벡터 연산
    for i in range(n_teams):
        if i == daegu_i: continue
        rem = total_games - games_played[i]
        if rem > 0:
            sim_adds = np.random.choice([3, 1, 0], size=(n_sims, rem), p=[0.35, 0.28, 0.37]).sum(axis=1)
            pts_sim[:, i] += sim_adds

    # 최종 순위 일괄 구하기
    daegu_pts = pts_sim[:, daegu_i]
    # 타 팀 승점 비교
    ranks = (pts_sim > daegu_pts[:, None]).sum(axis=1) + 1
    
    direct_cnt = np.sum(ranks <= 2)
    po_cnt = np.sum((ranks >= 3) & (ranks <= 6))
    
    return (direct_cnt / n_sims) * 100, (po_cnt / n_sims) * 100, ranks.tolist()

# 5. UI 및 레이아웃
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 2026 K리그2 순위표")
    st.dataframe(df_standings[["팀", "승점", "경기수", "득점", "실점"]], use_container_width=True, hide_index=True, height=280)
    
    st.subheader("🗓️ 대구 FC 잔여 경기 승부 직접 입력")
    st.caption("결과를 변경하면 오른쪽 그래프가 즉시 업데이트됩니다.")
    user_preds = []
    for idx, match in enumerate(daegu_schedule):
        label = f"R{match['R']} vs {match['상대팀']} ({match['장소']})"
        choice = st.selectbox(label, options=["자동 계산 (확률적 반영)", "승리 ⭕", "무승부 🔺", "패배 ❌"], key=f"match_{idx}")
        user_preds.append(choice)

with col2:
    st.subheader("📊 시뮬레이션 결과 및 확률")
    sim_count = st.slider("시뮬레이션 반복 횟수 설정", 1000, 10000, 3000, step=1000)
    
    direct_p, po_p, ranks = run_fast_simulation(df_standings, daegu_schedule, user_preds, total_games=32, n_sims=sim_count)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("자동 승격 (1~2위)", f"{direct_p:.1f}%")
    m2.metric("PO 진출 (3~6위)", f"{po_p:.1f}%")
    m3.metric("총 승격 가시권 확률", f"{direct_p + po_p:.1f}%")
    
    rank_df = pd.DataFrame({"예상 최종 순위": ranks})
    rank_counts = rank_df["예상 최종 순위"].value_counts().reset_index()
    rank_counts.columns = ["순위", "빈도수"]
    rank_counts = rank_counts.sort_values("순위")
    
    fig = px.bar(
        rank_counts, 
        x="순위", 
        y="빈도수", 
        text="빈도수", 
        title="<b>대구 FC 최종 순위 분포 (몬테카를로 분석)</b>",
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
