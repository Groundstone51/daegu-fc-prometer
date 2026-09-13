import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# 1. 페이지 대시보드 기본 설정
st.set_page_config(
    page_title="2026 K리그2 내 팀 승격 확률 예측기",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0085FF !important; font-weight: 800 !important; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border: 2px solid #E2E8F0; padding: 20px;
        border-radius: 14px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
    }
    [data-testid="stMetricLabel"] { color: #475569; font-weight: 700; font-size: 1.05rem; }
    [data-testid="stMetricValue"] { color: #0085FF; font-weight: 900; font-size: 2.2rem; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 2. 크롤링 없이 내장된 리그 스탯 및 과거/잔여 일정 데이터셋
@st.cache_data
def get_league_data():
    standings = [
        {"팀": "수원 삼성 블루윙즈", "승점": 56, "경기수": 26, "승": 17, "무": 5, "패": 4, "득점": 44, "실점": 24},
        {"팀": "대구 FC", "승점": 49, "경기수": 26, "승": 15, "무": 4, "패": 7, "득점": 45, "실점": 29},
        {"팀": "화성 FC", "승점": 46, "경기수": 26, "승": 13, "무": 7, "패": 6, "득점": 37, "실점": 21},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 26, "승": 13, "무": 6, "패": 7, "득점": 38, "실점": 25},
        {"팀": "수원 FC", "승점": 45, "경기수": 25, "승": 13, "무": 6, "패": 6, "득점": 41, "실점": 23},
        {"팀": "부산 아이파크", "승점": 41, "경기수": 25, "승": 12, "무": 5, "패": 8, "득점": 33, "실점": 25},
        {"팀": "경남 FC", "승점": 33, "경기수": 25, "승": 9, "무": 6, "패": 10, "득점": 28, "실점": 27},
        {"팀": "김포 FC", "승점": 32, "경기수": 25, "승": 8, "무": 8, "패": 9, "득점": 27, "실점": 29},
        {"팀": "충남 아산 FC", "승점": 31, "경기수": 25, "승": 8, "무": 7, "패": 10, "득점": 28, "실점": 28},
        {"팀": "성남 FC", "승점": 31, "경기수": 25, "승": 8, "무": 7, "패": 10, "득점": 27, "실점": 29},
        {"팀": "충북 청주 FC", "승점": 29, "경기수": 26, "승": 7, "무": 8, "패": 11, "득점": 22, "실점": 32},
        {"팀": "용인 FC", "승점": 26, "경기수": 25, "승": 6, "무": 8, "패": 11, "득점": 26, "실점": 32},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "승": 6, "무": 8, "패": 10, "득점": 22, "실점": 28},
        {"팀": "천안 시티 FC", "승점": 23, "경기수": 25, "승": 5, "무": 8, "패": 12, "득점": 22, "실점": 27},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 26, "승": 5, "무": 7, "패": 14, "득점": 19, "실점": 42},
        {"팀": "전남 드래곤즈", "승점": 21, "경기수": 25, "승": 4, "무": 9, "패": 12, "득점": 24, "실점": 36},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 25, "승": 2, "무": 7, "패": 16, "득점": 14, "실점": 45}
    ]
    
    past_matches = [
        {"id": "p1", "R": 26, "홈팀": "서울 이랜드 FC", "원정팀": "수원 삼성 블루윙즈", "실제홈득점": 0, "실제원정득점": 1},
        {"id": "p2", "R": 26, "홈팀": "대구 FC", "원정팀": "용인 FC", "실제홈득점": 3, "실제원정득점": 1},
        {"id": "p3", "R": 26, "홈팀": "경남 FC", "원정팀": "성남 FC", "실제홈득점": 1, "실제원정득점": 0},
        {"id": "p4", "R": 26, "홈팀": "부산 아이파크", "원정팀": "김해 FC 2008", "실제홈득점": 2, "실제원정득점": 0}
    ]
    
    remaining_matches = [
        {"id": "f1", "R": 27, "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"id": "f2", "R": 27, "홈팀": "전남 드래곤즈", "원정팀": "수원 FC"},
        {"id": "f3", "R": 27, "홈팀": "충남 아산 FC", "원정팀": "천안 시티 FC"},
        {"id": "f4", "R": 27, "홈팀": "김포 FC", "원정팀": "부산 아이파크"},
        {"id": "f5", "R": 28, "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"id": "f6", "R": 28, "홈팀": "수원 FC", "원정팀": "화성 FC"},
        {"id": "f7", "R": 34, "홈팀": "충남 아산 FC", "원정팀": "대구 FC"}
    ]
    return pd.DataFrame(standings), past_matches, remaining_matches

df_standings, past_matches, remaining_matches = get_league_data()

# 3. 베이지안 포아송 시뮬레이션 엔진
def run_bayesian_simulation(df, past_list, past_choices, future_list, future_choices, total_games=34, n_sims=5000):
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    base_pts = df['승점'].values.astype(np.float64)
    games_played = df['경기수'].values.copy()
    total_gf = df['득점'].values.astype(np.float64)
    total_ga = df['실점'].values.astype(np.float64)
    
    # 지난 경기 What-If 승점 차감 및 사용자 설정 승점 반영
    for m in past_list:
        h_i, a_i = team_idx[m["홈팀"]], team_idx[m["원정팀"]]
        o_h, o_a = m["실제홈득점"], m["실제원정득점"]
        
        if o_h > o_a: base_pts[h_i] -= 3
        elif o_h == o_a: base_pts[h_i] -= 1; base_pts[a_i] -= 1
        else: base_pts[a_i] -= 3
        
        choice = past_choices.get(m["id"], "실제 결과 반영")
        if choice == f"🏠 {m['홈팀']} 승": base_pts[h_i] += 3
        elif choice == "🔺 무승부": base_pts[h_i] += 1; base_pts[a_i] += 1
        elif choice == f"✈️ {m['원정팀']} 승": base_pts[a_i] += 3
        else:
            if o_h > o_a: base_pts[h_i] += 3
            elif o_h == o_a: base_pts[h_i] += 1; base_pts[a_i] += 1
            else: base_pts[a_i] += 3

    # 베이지안 감마 사전 분포(Prior) -> 사후 분포(Posterior) 추정
    prior_alpha, prior_beta = 10.0, 8.0
    post_shape_att = prior_alpha + total_gf
    post_rate_att = prior_beta + games_played
    post_shape_def = prior_alpha + total_ga
    post_rate_def = prior_beta + games_played
    
    pts_sim = np.tile(base_pts, (n_sims, 1))
    
    # 몬테카를로 5,000회 시뮬레이션
    for s in range(n_sims):
        sampled_att = np.random.gamma(post_shape_att, 1.0 / post_rate_att)
        sampled_def = np.random.gamma(post_shape_def, 1.0 / post_rate_def)
        sim_games = games_played.copy()
        
        # 잔여 경기 사용자 조건 반영 및 포아송 시뮬레이션
        for idx, match in enumerate(future_list):
            h_i, a_i = team_idx[match["홈팀"]], team_idx[match["원정팀"]]
            choice = future_choices.get(idx, "🎲 베이지안 자동 시뮬레이션")
            
            if choice == "🎲 베이지안 자동 시뮬레이션":
                lambda_h = sampled_att[h_i] * sampled_def[a_i] * 1.10
                lambda_a = sampled_att[a_i] * sampled_def[h_i]
                g_h = np.random.poisson(max(lambda_h, 0.05))
                g_a = np.random.poisson(max(lambda_a, 0.05))
                
                if g_h > g_a: pts_sim[s, h_i] += 3
                elif g_h == g_a: pts_sim[s, h_i] += 1; pts_sim[s, a_i] += 1
                else: pts_sim[s, a_i] += 3
            else:
                if f"🏠 {match['홈팀']} 승" in choice: pts_sim[s, h_i] += 3
                elif "🔺 무승부" in choice: pts_sim[s, h_i] += 1; pts_sim[s, a_i] += 1
                elif f"✈️ {match['원정팀']} 승" in choice: pts_sim[s, a_i] += 3
                
            sim_games[h_i] += 1
            sim_games[a_i] += 1

        # 남은 리그 경기 추정
        for i in range(n_teams):
            rem = total_games - sim_games[i]
            if rem > 0:
                l_h = sampled_att[i] * 1.10
                l_a = sampled_def[i]
                gh_s = np.random.poisson(max(l_h, 0.05), size=int(rem))
                ga_s = np.random.poisson(max(l_a, 0.05), size=int(rem))
                pts_sim[s, i] += np.where(gh_s > ga_s, 3, np.where(gh_s == ga_s, 1, 0)).sum()

    # 최종 순위 계산
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        scores = [(pts_sim[s, i], total_gf[i], total_gf[i] - total_ga[i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx

# 4. 헤더 및 내 팀 선택 UI
st.title("⚽ K리그2 내 팀 승격 확률 예측 시뮬레이터")
my_team = st.selectbox("🎯 승격 분석 대상 (내 팀) 선택:", options=df_standings["팀"].tolist(), index=1)
st.divider()

col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("⚙️ 조건 직접 설정")
    tab_fut, tab_past = st.tabs(["🗓️ 잔여 경기 결과 직접 선택", "🔄 지난 경기 What-If 조정"])
    
    future_choices = {}
    with tab_fut:
        st.caption("내 팀 및 경쟁 팀의 승/무/패를 직접 고르면 확률에 100% 확정 반영됩니다.")
        for idx, m in enumerate(remaining_matches):
            label = f"R{m['R']} {m['홈팀']} VS {m['원정팀']}"
            choice = st.selectbox(
                label,
                options=["🎲 베이지안 자동 시뮬레이션", f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                key=f"fut_{idx}"
            )
            future_choices[idx] = choice

    past_choices = {}
    with tab_past:
        st.caption("과거 경기 결과를 바꿨을 때 내 팀의 승격 확률 변화를 관찰하세요.")
        for m in past_matches:
            label = f"R{m['R']} {m['홈팀']} ({m['실제홈득점']}:{m['실제원정득점']}) {m['원정팀']}"
            choice = st.selectbox(
                label,
                options=["실제 결과 반영", f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                key=f"past_{m['id']}"
            )
            past_choices[m["id"]] = choice

with col2:
    st.subheader(f"📊 {my_team} 승격 예측 리포트")
    sim_count = st.slider("시뮬레이션 반복 회수", 1000, 10000, 5000, step=1000)
    
    rank_matrix, teams, team_idx = run_bayesian_simulation(
        df_standings, past_matches, past_choices, remaining_matches, future_choices, total_games=34, n_sims=sim_count
    )
    
    target_i = team_idx[my_team]
    target_ranks = rank_matrix[:, target_i]
    
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    total_promotion_p = direct_p + po_p
    
    # 메인 지표 3종 표시
    m1, m2, m3 = st.columns(3)
    m1.metric("🥇 직행 승격 (1~2위)", f"{direct_p:.1f}%")
    m2.metric("🎫 플레이오프 (3~6위)", f"{po_p:.1f}%")
    m3.metric("🔥 총 승격 성공률", f"{total_promotion_p:.1f}%")
    
    # 최종 순위 분포 차트
    rank_df = pd.DataFrame({"예상 최종 순위": target_ranks})
    rank_counts = rank_df["예상 최종 순위"].value_counts().reset_index()
    rank_counts.columns = ["순위", "빈도수"]
    rank_counts = rank_counts.sort_values("순위")
    
    fig = px.bar(
        rank_counts, 
        x="순위", 
        y="빈도수", 
        text="빈도수", 
        title=f"<b>{my_team} 최종 예상 순위 분포 ({sim_count:,}회 분석)</b>",
        color_discrete_sequence=["#0085FF"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickmode='linear', tick0=1, dtick=1),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
