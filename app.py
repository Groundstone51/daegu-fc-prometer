import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# 1. 페이지 및 레이아웃 설정
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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. 실시간 K리그2 순위 크롤링 함수 (1시간 간격 자동 갱신)
@st.cache_data(ttl=3600)
def fetch_realtime_standings():
    url = "https://sports.news.naver.com/kfootball/record/index?category=kleague2"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 스포츠 순위 테이블 파싱 (가상 구조 대응)
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
        
    # 크롤링 실패 시 기본 데이터 반환 (Fallback)
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

# 4. 데이터 로드
df_standings, status_msg = fetch_realtime_standings()

# 메인 상단 헤더
st.title("⚽ 2026 대구 FC 승격 가능성 시뮬레이터")
st.caption(f"K리그2 17개 구단 체제 반영 | {status_msg}")

st.divider()

# 대구 FC 잔여 일정
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

# 5. 시뮬레이션 로직
def run_simulation(df, schedule, total_games=32, n_sims=3000):
    direct_cnt, po_cnt, final_ranks = 0, 0, []
    df['득실차'] = df['득점'] - df['실점']
    
    for _ in range(n_sims):
        sim_teams = df.set_index("팀").to_dict('index')
        
        for match in schedule:
            opp = match["상대팀"]
            is_home = (match["장소"] == "홈")
            base_win_p = 0.42 if is_home else 0.32
            res = np.random.choice([3, 1, 0], p=[base_win_p, 0.28, 1.0 - base_win_p - 0.28])
            
            if "대구 FC" in sim_teams:
                sim_teams["대구 FC"]["승점"] += res
                sim_teams["대구 FC"]["경기수"] += 1
            
            opp_pts = 0 if res == 3 else (1 if res == 1 else 3)
            if opp in sim_teams:
                sim_teams[opp]["승점"] += opp_pts
                sim_teams[opp]["경기수"] += 1

        for team, info in sim_teams.items():
            if team == "대구 FC": continue
            rem = total_games - info['경기수']
            if rem > 0:
                outcomes = np.random.choice([3, 1, 0], size=rem, p=[0.35, 0.28, 0.37])
                sim_teams[team]["승점"] += sum(outcomes)
                
        sorted_teams = sorted(sim_teams.items(), key=lambda x: (x[1]['승점'], x[1]['득점'], x[1]['득실차']), reverse=True)
        rankings = [t[0] for t in sorted_teams]
        
        r = rankings.index("대구 FC") + 1 if "대구 FC" in rankings else 2
        final_ranks.append(r)
        if r <= 2: direct_cnt += 1
        elif 3 <= r <= 6: po_cnt += 1
            
    return (direct_cnt / n_sims) * 100, (po_cnt / n_sims) * 100, final_ranks

# 6. 화면 분할 출력
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 2026 K리그2 순위표")
    st.dataframe(
        df_standings[["팀", "승점", "경기수", "득점", "실점"]],
        use_container_width=True,
        hide_index=True,
        height=380
    )
    
    st.subheader("🗓️ 대구 FC 잔여 대진표")
    st.dataframe(pd.DataFrame(daegu_schedule), use_container_width=True, hide_index=True, height=260)

with col2:
    st.subheader("📊 시뮬레이션 결과 및 확률")
    sim_count = st.slider("시뮬레이션 반복 횟수 설정", 1000, 10000, 3000, step=1000)
    
    direct_p, po_p, ranks = run_simulation(df_standings, daegu_schedule, total_games=32, n_sims=sim_count)
    
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
