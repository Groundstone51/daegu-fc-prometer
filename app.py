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

# 2. 저장소 내 matches.csv 자동 불러오기
@st.cache_data(ttl=600)
def load_matches_csv():
    possible_paths = [
        "matches.csv",
        os.path.join(os.path.dirname(__file__), "matches.csv")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return pd.read_csv(p), "🟢 저장소 내 matches.csv 연동 완료"
    return None, "🔴 matches.csv 파일을 찾을 수 없습니다."

matches_df, status_msg = load_matches_csv()

if matches_df is None:
    st.error(status_msg + " app.py와 동일한 폴더에 matches.csv 파일이 있는지 확인해주세요.")
    st.stop()

# 경기 데이터 분리 (종료 1~26R vs 예정 27~34R)
completed_df = matches_df[matches_df['상태'] == '종료'].copy()
scheduled_df = matches_df[matches_df['상태'] == '예정'].copy()

# 라운드 숫자 정렬
def extract_round_num(r_str):
    return int(str(r_str).replace('라운드', '').strip())

completed_rounds = sorted(completed_df['라운드'].unique(), key=extract_round_num)
scheduled_rounds = sorted(scheduled_df['라운드'].unique(), key=extract_round_num)

# 실경기 데이터 기준 순위표 생성
def build_standings_df(completed):
    teams = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    stats = {t: {'팀': t, '승점': 0, '경기수': 0, '승': 0, '무': 0, '패': 0, '득점': 0, '실점': 0} for t in teams}
    
    for row in completed.itertuples():
        h, a = row.홈팀, row.원정팀
        gh, ga = int(row._4), int(row._5) # 홈 스코어, 원정 스코어
        
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

# 3. NumPy 초고속 벡터화 베이지안 포아송 연산 엔진
@st.cache_data(show_spinner=False)
def run_fast_bayesian_simulation(completed, scheduled, past_user_choices_tuple, future_user_choices_tuple, total_games=34, n_sims=2500):
    past_user_choices = dict(past_user_choices_tuple)
    future_user_choices = dict(future_user_choices_tuple)
    
    teams = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    base_pts = np.zeros(n_teams)
    games_played = np.zeros(n_teams)
    total_gf = np.zeros(n_teams)
    total_ga = np.zeros(n_teams)
    
    # 과거 경기 What-If 반영
    for row in completed.itertuples():
        m_id = f"{row.라운드}_{row.홈팀}_{row.원정팀}"
        h_i, a_i = team_idx[row.홈팀], team_idx[row.원정팀]
        o_h, o_a = int(row._4), int(row._5)
        
        games_played[h_i] += 1; games_played[a_i] += 1
        total_gf[h_i] += o_h; total_ga[h_i] += o_a
        total_gf[a_i] += o_a; total_ga[a_i] += o_h
        
        choice = past_user_choices.get(m_id, "실제 결과")
        if choice == f"🏠 {row.홈팀} 승": base_pts[h_i] += 3
        elif choice == "🔺 무승부": base_pts[h_i] += 1; base_pts[a_i] += 1
        elif choice == f"✈️ {row.원정팀} 승": base_pts[a_i] += 3
        else:
            if o_h > o_a: base_pts[h_i] += 3
            elif o_h == o_a: base_pts[h_i] += 1; base_pts[a_i] += 1
            else: base_pts[a_i] += 3

    # 베이지안 Gamma Prior -> Posterior
    prior_alpha, prior_beta = 10.0, 8.0
    post_shape_att = prior_alpha + total_gf
    post_rate_att = prior_beta + games_played
    post_shape_def = prior_alpha + total_ga
    post_rate_def = prior_beta + games_played
    
    # 시뮬레이션 행렬 일괄 생성
    pts_sim = np.tile(base_pts, (n_sims, 1))
    
    sampled_att = np.random.gamma(post_shape_att, 1.0 / post_rate_att, size=(n_sims, n_teams))
    sampled_def = np.random.gamma(post_shape_def, 1.0 / post_rate_def, size=(n_sims, n_teams))
    
    # 잔여 경기 일괄 병렬 연산
    for row in scheduled.itertuples():
        f_id = f"{row.라운드}_{row.홈팀}_{row.원정팀}"
        h_i, a_i = team_idx[row.홈팀], team_idx[row.원정팀]
        choice = future_user_choices.get(f_id, "🎲 베이지안 자동")
        
        if choice == "🎲 베이지안 자동":
            lambda_h = np.maximum(sampled_att[:, h_i] * sampled_def[:, a_i] * 1.10, 0.05)
            lambda_a = np.maximum(sampled_att[:, a_i] * sampled_def[:, h_i], 0.05)
            
            g_h = np.random.poisson(lambda_h)
            g_a = np.random.poisson(lambda_a)
            
            pts_sim[:, h_i] += np.where(g_h > g_a, 3, np.where(g_h == g_a, 1, 0))
            pts_sim[:, a_i] += np.where(g_a > g_h, 3, np.where(g_h == g_a, 1, 0))
        else:
            if f"🏠 {row.홈팀} 승" in choice: pts_sim[:, h_i] += 3
            elif "🔺 무승부" in choice: pts_sim[:, h_i] += 1; pts_sim[:, a_i] += 1
            elif f"✈️ {row.원정팀} 승" in choice: pts_sim[:, a_i] += 3

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
    st.subheader("⚙️ 승/무/패 조건 직접 선택")
    
    # 💡 드롭박스 대신 직관적인 팀별 체크박스 리스트 적용
    all_teams_list = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    
    with st.expander("🔍 팀별 경기 필터 (클릭해서 열기/닫기)", expanded=False):
        st.caption("보고 싶은 팀만 체크하세요. (모두 체크 해제 시 전체 경기 표시)")
        
        # 전체 선택/해제 편의 버튼
        select_all = st.checkbox("✅ 전체 팀 선택", value=False)
        
        selected_filter_teams = []
        # 3열 구조로 체크박스 배치하여 공간 절약
        cols = st.expander("팀 목록 세부 선택", expanded=True) if False else st.columns(3)
        
        for i, team in enumerate(all_teams_list):
            col_idx = i % 3
            with cols[col_idx]:
                is_checked = st.checkbox(team, value=select_all, key=f"chk_team_{team}")
                if is_checked or select_all:
                    selected_filter_teams.append(team)

    tab_fut, tab_past = st.tabs(["🗓️ 잔여 경기 예측 (27~34R)", "🔄 과거 경기 What-If (1~26R)"])
    
    future_choices = {}
    with tab_fut:
        st.caption("👇 라운드 선택 후 클릭 한 번으로 잔여 경기 승/무/패를 변경하세요.")
        sel_fut_r = st.selectbox("📌 잔여 라운드 선택", options=scheduled_rounds, index=0)
        st.divider()
        
        filtered_fut = scheduled_df[scheduled_df['라운드'] == sel_fut_r]
        
        # 팀 필터 적용
        if selected_filter_teams:
            filtered_fut = filtered_fut[
                filtered_fut['홈팀'].isin(selected_filter_teams) | 
                filtered_fut['원정팀'].isin(selected_filter_teams)
            ]
            
        if filtered_fut.empty:
            st.info("선택한 팀의 해당 라운드 경기가 없습니다.")
        else:
            for _, m in filtered_fut.iterrows():
                f_id = f"{m['라운드']}_{m['홈팀']}_{m['원정팀']}"
                st.markdown(f"**{m['홈팀']} vs {m['원정팀']}** *(📅 {m['날짜']})*")
                choice = st.radio(
                    label=f"fut_radio_{f_id}",
                    options=["🎲 베이지안 자동", f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                    horizontal=True,
                    key=f"fut_{f_id}",
                    label_visibility="collapsed"
                )
                future_choices[f_id] = choice
                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)

    past_choices = {}
    with tab_past:
        st.caption("👇 1~26라운드 실경기 스코어를 확인하고 가상 시나리오를 적용해 보세요.")
        sel_past_r = st.selectbox("📌 과거 라운드 선택", options=completed_rounds, index=len(completed_rounds)-1)
        st.divider()
        
        filtered_past = completed_df[completed_df['라운드'] == sel_past_r]
        
        # 팀 필터 적용
        if selected_filter_teams:
            filtered_past = filtered_past[
                filtered_past['홈팀'].isin(selected_filter_teams) | 
                filtered_past['원정팀'].isin(selected_filter_teams)
            ]
            
        if filtered_past.empty:
            st.info("선택한 팀의 해당 라운드 경기가 없습니다.")
        else:
            for _, m in filtered_past.iterrows():
                m_id = f"{m['라운드']}_{m['홈팀']}_{m['원정팀']}"
                gh, ga = int(m['홈 스코어']), int(m['원정 스코어'])
                st.markdown(f"**{m['홈팀']} {gh} : {ga} {m['원정팀']}** *(📅 {m['날짜']})*")
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
    st.subheader(f"📊 {my_team} 베이지안 승격 예측 리포트")
    sim_count = st.slider("시뮬레이션 회수", 1000, 10000, 2500, step=100)
    
    # 튜플 기반 속도 최적화 캡처
    past_choices_tuple = tuple(sorted(past_choices.items()))
    future_choices_tuple = tuple(sorted(future_choices.items()))
    
    rank_matrix, teams, team_idx = run_fast_bayesian_simulation(
        completed_df, scheduled_df, past_choices_tuple, future_choices_tuple, total_games=34, n_sims=sim_count
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
        title=f"<b>{my_team} 베이지안 최종 순위 분포 ({sim_count:,}회 시뮬레이션)</b>",
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
