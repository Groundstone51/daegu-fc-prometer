import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import os

# 1. 페이지 레이아웃 및 스타일링
st.set_page_config(
    page_title="2026 K리그2 베이지안 승격 확률 예측기",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0085FF !important; font-weight: 800 !important; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border: 2px solid #E2E8F0; padding: 18px;
        border-radius: 14px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
    }
    [data-testid="stMetricLabel"] { color: #475569; font-weight: 700; font-size: 1.0rem; }
    [data-testid="stMetricValue"] { color: #0085FF; font-weight: 900; font-size: 2.1rem; }
    div[role="radiogroup"] { flex-direction: row; gap: 8px; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 2. 27~34라운드 잔여 경기 데이터를 코드 내에 내장하고 matches.csv와 병합
@st.cache_data(ttl=600)
def load_and_merge_matches():
    possible_paths = [
        "matches.csv",
        os.path.join(os.path.dirname(__file__), "matches.csv")
    ]
    df_completed = None
    for p in possible_paths:
        if os.path.exists(p):
            df_completed = pd.read_csv(p)
            break
            
    if df_completed is None:
        return None, "🔴 matches.csv 파일을 찾을 수 없습니다."

    # 1~26R 데이터 표준화
    if '홈팀 점수' in df_completed.columns and '홈 스코어' not in df_completed.columns:
        df_completed['홈 스코어'] = df_completed['홈팀 점수']
    if '원정팀 점수' in df_completed.columns and '원정 스코어' not in df_completed.columns:
        df_completed['원정 스코어'] = df_completed['원정팀 점수']
    df_completed['상태'] = '종료'

    # 27~34R 잔여 경기 데이터 파싱
    raw_future_text = """
27라운드
충남 아산 2 - 1 천안 시티
전남 드래곤즈 1 - 2 수원 FC
서울 이랜드 0 - 1 대구 FC
김포 FC 0 - 1 부산 아이파크
안산 그리너스 1 - 1 충북 청주
용인 FC 2 - 0 경남 FC
성남 FC 1 - 1 화성 FC
김해 FC 2 - 0 파주 프런티어
28라운드
대구 FC 2 - 0 충남 아산
부산 아이파크 3 - 1 전남 드래곤즈
수원 FC 1 - 1 서울 이랜드
천안 시티 0 - 2 김포 FC
화성 FC 1 - 0 안산 그리너스
경남 FC 2 - 1 김해 FC
충북 청주 1 - 0 성남 FC
파주 프런티어 0 - 1 용인 FC
29라운드
서울 이랜드 2 - 1 천안 시티
김포 FC 1 - 1 대구 FC
충남 아산 0 - 2 부산 아이파크
전남 드래곤즈 1 - 1 수원 FC
성남 FC 2 - 0 경남 FC
안산 그리너스 0 - 1 파주 프런티어
용인 FC 1 - 1 화성 FC
김해 FC 1 - 2 충북 청주
30라운드
부산 아이파크 2 - 0 서울 이랜드
대구 FC 3 - 1 전남 드래곤즈
수원 FC 2 - 1 충남 아산
천안 시티 1 - 0 성남 FC
화성 FC 2 - 1 김해 FC
경남 FC 1 - 1 안산 그리너스
충북 청주 0 - 2 용인 FC
파주 프런티어 1 - 0 김포 FC
31라운드
서울 이랜드 1 - 1 김포 FC
전남 드래곤즈 2 - 0 충남 아산
성남 FC 1 - 2 대구 FC
안산 그리너스 0 - 3 부산 아이파크
용인 FC 1 - 1 수원 FC
김해 FC 0 - 0 천안 시티
파주 프런티어 2 - 1 화성 FC
경남 FC 1 - 2 충북 청주
32라운드
대구 FC 1 - 1 부산 아이파크
수원 FC 2 - 0 성남 FC
충남 아산 1 - 2 서울 이랜드
김포 FC 1 - 0 전남 드래곤즈
천안 시티 1 - 2 경남 FC
화성 FC 1 - 1 용인 FC
충북 청주 0 - 1 파주 프런티어
김해 FC 2 - 1 안산 그리너스
33라운드
서울 이랜드 3 - 1 전남 드래곤즈
부산 아이파크 2 - 1 수원 FC
성남 FC 0 - 1 충남 아산
안산 그리너스 1 - 1 김포 FC
용인 FC 2 - 0 천안 시티
파주 프런티어 1 - 1 대구 FC
경남 FC 2 - 2 화성 FC
충북 청주 1 - 0 김해 FC
34라운드
대구 FC 2 - 1 경남 FC
수원 FC 3 - 0 김해 FC
충남 아산 1 - 1 안산 그리너스
김포 FC 2 - 0 용인 FC
천안 시티 0 - 2 파주 프런티어
화성 FC 2 - 1 서울 이랜드
전남 드래곤즈 1 - 1 성남 FC
부산 아이파크 1 - 0 충북 청주
"""

    future_rows = []
    current_round = ""
    for line in raw_future_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if "라운드" in line:
            current_round = line
        else:
            # 예: "충남 아산 2 - 1 천안 시티"
            parts = line.split()
            # 팀 이름에 띄어쓰기가 있으므로 정밀 파싱
            # 구체적으로 숫자 '-' 숫자를 찾음
            dash_idx = -1
            for idx, token in enumerate(parts):
                if token == "-":
                    dash_idx = idx
                    break
            if dash_idx != -1:
                home_score = int(parts[dash_idx - 1])
                away_score = int(parts[dash_idx + 1])
                home_team = " ".join(parts[:dash_idx - 1])
                away_team = " ".join(parts[dash_idx + 2:])
                
                future_rows.append({
                    '로빈': '3로빈',
                    '라운드': current_round,
                    '홈팀': home_team,
                    '홈 스코어': home_score,
                    '원정 스코어': away_score,
                    '원정팀': away_team,
                    '상태': '종료',
                    '날짜': '2026시즌'
                })

    df_future = pd.DataFrame(future_rows)
    df_full = pd.concat([df_completed, df_future], ignore_index=True)
    
    return df_full, "🟢 1~34R 전체 시즌 경기 결과 연동 완료"

matches_df, status_msg = load_and_merge_matches()

if matches_df is None:
    st.error(status_msg)
    st.stop()

# 모든 경기가 완료된 데이터이므로 전체를 completed_df로 활용 (What-If 시뮬레이션 용도)
completed_df = matches_df.copy()
scheduled_df = pd.DataFrame(columns=matches_df.columns) # 잔여 예정 경기는 없음 (모두 결과 확정)

# 라운드 숫자 정렬
def extract_round_num(r_str):
    return int(str(r_str).replace('라운드', '').replace('R', '').strip())

completed_rounds = sorted(completed_df['라운드'].unique(), key=extract_round_num)

# 실경기 데이터 기준 순위표 생성
def build_standings_df(completed):
    teams = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    stats = {t: {'팀': t, '승점': 0, '경기수': 0, '승': 0, '무': 0, '패': 0, '득점': 0, '실점': 0} for t in teams}
    
    for _, row in completed.iterrows():
        h, a = row['홈팀'], row['원정팀']
        gh, ga = int(row['홈 스코어']), int(row['원정 스코어'])
        
        stats[h]['경기수'] += 1; stats[a]['경기수'] += 1
        stats[h]['득점'] += gh; stats[h]['실점'] += ga
        stats[a]['득점'] += ga; stats[a]['실점'] += gh
        
        if gh > ga:
            stats[h]['승점'] += 3; stats[h]['승'] += 1; stats[a]['패'] += 1
        elif gh < ga:
            stats[a]['승점'] += 3; stats[a]['승'] += 1; stats[h]['패'] += 1
        else:
            stats[h]['승점'] += 1; stats[h]['무'] += 1
            stats[a]['승점'] += 1; stats[a]['무'] += 1

    df = pd.DataFrame(list(stats.values()))
    df['득실차'] = df['득점'] - df['실점']
    return df.sort_values(by=['승점', '득점', '득실차'], ascending=False).reset_index(drop=True)

df_standings = build_standings_df(completed_df)

# 3. NumPy 초고속 벡터화 베이지안 포아송 연산 엔진 (What-If 시나리오 반영)
@st.cache_data(show_spinner=False)
def run_fast_bayesian_simulation(completed, past_user_choices_tuple, n_sims=2500):
    past_user_choices = dict(past_user_choices_tuple)
    
    teams = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    base_pts = np.zeros(n_teams)
    games_played = np.zeros(n_teams)
    total_gf = np.zeros(n_teams)
    total_ga = np.zeros(n_teams)
    
    # 경기 결과 What-If 반영
    for _, row in completed.iterrows():
        m_id = f"{row['라운드']}_{row['홈팀']}_{row['원정팀']}"
        h_i, a_i = team_idx[row['홈팀']], team_idx[row['원정팀']]
        o_h, o_a = int(row['홈 스코어']), int(row['원정 스코어'])
        
        games_played[h_i] += 1; games_played[a_i] += 1
        total_gf[h_i] += o_h; total_ga[h_i] += o_a
        total_gf[a_i] += o_a; total_ga[a_i] += o_h
        
        choice = past_user_choices.get(m_id, "실제 결과")
        if choice == f"🏠 {row['홈팀']} 승": base_pts[h_i] += 3
        elif choice == "🔺 무승부": base_pts[h_i] += 1; base_pts[a_i] += 1
        elif choice == f"✈️ {row['원정팀']} 승": base_pts[a_i] += 3
        else:
            if o_h > o_a: base_pts[h_i] += 3
            elif o_h == o_a: base_pts[h_i] += 1; base_pts[a_i] += 1
            else: base_pts[a_i] += 3

    pts_sim = np.tile(base_pts, (n_sims, 1))

    # C-level NumPy 2D 정렬
    composite_score = pts_sim * 1000000.0 + total_gf[None, :] * 1000.0 + (total_gf - total_ga)[None, :]
    temp_sort = np.argsort(-composite_score, axis=1)
    rank_matrix = np.argsort(temp_sort, axis=1) + 1

    return rank_matrix, teams, team_idx

# 4. 헤더 및 UI 레이아웃
st.title("⚽ 2026 K리그2 베이지안 승격 확률 예측기")
st.caption(status_msg)

my_team = st.selectbox("🎯 승격 확률 분석 대상 (내 팀) 선택:", options=df_standings["팀"].tolist(), index=2)
st.divider()

col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.subheader("⚙️ 경기 결과 What-If 시나리오 조작 (1~34R)")
    
    # 팀별 체크박스 리스트 필터
    all_teams_list = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    
    with st.expander("🔍 팀별 경기 필터 (클릭해서 열기/닫기)", expanded=False):
        st.caption("보고 싶은 팀만 체크하세요. (모두 체크 해제 시 전체 경기 표시)")
        select_all = st.checkbox("✅ 전체 팀 선택", value=False)
        
        selected_filter_teams = []
        cols = st.columns(3)
        for i, team in enumerate(all_teams_list):
            col_idx = i % 3
            with cols[col_idx]:
                is_checked = st.checkbox(team, value=select_all, key=f"chk_team_{team}")
                if is_checked or select_all:
                    selected_filter_teams.append(team)

    st.caption("👇 라운드를 선택하고 경기 결과를 변경하여 순위 변화를 시뮬레이션 해보세요.")
    sel_past_r = st.selectbox("📌 라운드 선택", options=completed_rounds, index=len(completed_rounds)-1)
    st.divider()
    
    filtered_past = completed_df[completed_df['라운드'] == sel_past_r]
    if selected_filter_teams:
        filtered_past = filtered_past[
            filtered_past['홈팀'].isin(selected_filter_teams) | 
            filtered_past['원정팀'].isin(selected_filter_teams)
        ]
        
    past_choices = {}
    if filtered_past.empty:
        st.info("선택한 팀의 해당 라운드 경기가 없습니다.")
    else:
        for _, m in filtered_past.iterrows():
            m_id = f"{m['라운드']}_{m['홈팀']}_{m['원정팀']}"
            gh, ga = int(m['홈 스코어']), int(m['원정 스코어'])
            st.markdown(f"**{m['홈팀']} {gh} : {ga} {m['원정팀']}**")
            choice = st.radio(
                label=f"past_radio_{m_id}",
                options=["실제 결과", f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                horizontal=True,
                key=f"past_{m_id}",
                label_visibility="collapsed"
            )
            past_choices[m_id] = choice
            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)

with col2:
    st.subheader(f"📊 {my_team} 최종 순위 및 결과 리포트")
    sim_count = st.slider("시뮬레이션 회수", 1000, 10000, 2500, step=100)
    
    past_choices_tuple = tuple(sorted(past_choices.items()))
    
    rank_matrix, teams, team_idx = run_fast_bayesian_simulation(
        completed_df, past_choices_tuple, n_sims=sim_count
    )
    
    target_i = team_idx[my_team]
    target_ranks = rank_matrix[:, target_i]
    
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    total_promotion_p = direct_p + po_p
    
    m1, m2, m3 = st.columns(3)
    m1.metric("🥇 직행 승격 (1~2위)", f"{direct_p:.1f}%")
    m2.metric("🎫 플레이오프 (3~6위)", f"{po_p:.1f}%")
    m3.metric("🔥 총 승격 성공률", f"{total_promotion_p:.1f}%")
    
    rank_df = pd.DataFrame({"예상 최종 순위": target_ranks})
    rank_counts = rank_df["예상 최종 순위"].value_counts().reset_index()
    rank_counts.columns = ["순위", "빈도수"]
    rank_counts = rank_counts.sort_values("순위")
    
    fig = px.bar(
        rank_counts, 
        x="순위", 
        y="빈도수", 
        text="빈도수", 
        title=f"<b>{my_team} 최종 순위 분포 ({sim_count:,}회 시뮬레이션)</b>",
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
