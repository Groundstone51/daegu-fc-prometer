import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import re

# 1. 페이지 설정
st.set_page_config(
    page_title="2026 K리그2 승격 시뮬레이터 (정밀 연동형)",
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

# 3. matches.csv 데이터 로드 (인코딩 및 공백 오류 완벽 방지)
@st.cache_data(ttl=3600)
def load_match_data():
    try:
        # BOM 문자 및 한글 인코딩 대응
        try:
            df = pd.read_csv('matches.csv', encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv('matches.csv', encoding='cp949')
            
        # 모든 열 이름의 앞뒤 공백 및 줄바꿈 제거 (KeyError 원인 제거)
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        st.error(f"matches.csv 파일을 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

df_matches = load_match_data()

if df_matches.empty:
    st.stop()

# 열 이름 정상 인식 여부 검증
if '경기상태' not in df_matches.columns:
    st.error("데이터 파일에 '경기상태' 열이 인식되지 않습니다.")
    st.write("현재 인식된 열 목록:", df_matches.columns.tolist())
    st.stop()

# 경기 상태에 따른 분리 (종료 vs 예정) - 값의 공백도 제거하여 매칭
df_matches['경기상태'] = df_matches['경기상태'].astype(str).str.strip()
df_finished = df_matches[df_matches['경기상태'] == '종료']
df_remaining = df_matches[df_matches['경기상태'] == '예정'].reset_index(drop=True)

# 4. 완료된 경기 기반 실시간 순위 산출 함수
def calculate_standings(finished_df, all_matches_df):
    # 팀명 앞뒤 공백 제거 통일
    teams = sorted(list(set(all_matches_df['홈팀'].astype(str).str.strip()).union(set(all_matches_df['원정팀'].astype(str).str.strip()))))
    standings = {t: {'팀': t, '승점': 0, '경기수': 0, '승': 0, '무': 0, '패': 0, '득점': 0, '실점': 0} for t in teams}
    
    for _, row in finished_df.iterrows():
        h = str(row['홈팀']).strip()
        a = str(row['원정팀']).strip()
        
        # 엑셀에서 넘어온 "2.0" 등 실수형태의 점수를 정수로 안전하게 변환
        try:
            hs = int(float(row['홈팀 점수']))
            as_ = int(float(row['원정팀 점수']))
        except (ValueError, TypeError):
            continue  # 점수가 숫자가 아니면 계산 스킵
        
        standings[h]['경기수'] += 1
        standings[a]['경기수'] += 1
        standings[h]['득점'] += hs
        standings[h]['실점'] += as_
        standings[a]['득점'] += as_
        standings[a]['실점'] += hs
        
        if hs > as_:
            standings[h]['승'] += 1
            standings[h]['승점'] += 3
            standings[a]['패'] += 1
        elif hs < as_:
            standings[a]['승'] += 1
            standings[a]['승점'] += 3
            standings[h]['패'] += 1
        else:
            standings[h]['무'] += 1
            standings[h]['승점'] += 1
            standings[a]['무'] += 1
            standings[a]['승점'] += 1
            
    df_calc = pd.DataFrame(list(standings.values()))
    df_calc['득실차'] = df_calc['득점'] - df_calc['실점']
    # 순위 산정 로직: 1.승점 -> 2.득실차 -> 3.다득점
    df_calc = df_calc.sort_values(by=['승점', '득실차', '득점'], ascending=[False, False, False]).reset_index(drop=True)
    df_calc.index = df_calc.index + 1
    df_calc.insert(0, '순위', df_calc.index)
    return df_calc

df_standings = calculate_standings(df_finished, df_matches)

st.title("⚽ 2026 K리그2 정밀 승격 시뮬레이터")
st.caption(f"총 {len(df_matches)}경기 중 **{len(df_finished)}경기 완료** (실제 결과 반영) | 잔여 **{len(df_remaining)}경기** 시뮬레이션")
st.divider()

# 5. 베이지안 포아송 시뮬레이션 엔진
def run_simulation(standings_df, finished_df, remaining_df, match_predictions, n_sims=3000):
    # 팀당 예정된 총 경기 수 자동 파악 (대체로 36경기)
    team_total_games = df_matches['홈팀'].astype(str).str.strip().value_counts() + df_matches['원정팀'].astype(str).str.strip().value_counts()
    total_games = int(team_total_games.max()) if not team_total_games.empty else 36
        
    teams = standings_df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    # 득실점 기반 공격/수비 전력 지수 산출
    avg_gf = np.where(standings_df['경기수'] > 0, standings_df['득점'] / standings_df['경기수'], 1.0).values
    avg_ga = np.where(standings_df['경기수'] > 0, standings_df['실점'] / standings_df['경기수'], 1.0).values
    league_avg_gf = max(avg_gf.mean(), 0.1)
    
    att_strength = avg_gf / league_avg_gf
    def_strength = avg_ga / league_avg_gf
    
    base_pts = standings_df['승점'].values.astype(np.float64)
    games_played = standings_df['경기수'].values.copy()
    pts_sim = np.tile(base_pts, (n_sims, 1))
    
    # 사용자 잔여 경기 예측 반영
    for m_idx, match in remaining_df.iterrows():
        home_team = str(match["홈팀"]).strip()
        away_team = str(match["원정팀"]).strip()
        
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
        rem = int(total_games - games_played[i])
        if rem > 0:
            # 득점력/실점력을 고려한 홈/어웨이 가중 확률 배분
            p_win = np.clip(0.35 * (att_strength[i] / max(def_strength[i], 0.1)), 0.15, 0.65)
            p_draw = 0.28
            p_loss = 1.0 - p_win - p_draw
            
            sim_adds = np.random.choice([3, 1, 0], size=(n_sims, rem), p=[p_win, p_draw, p_loss]).sum(axis=1)
            pts_sim[:, i] += sim_adds

    # 최종 순위 매트릭스 계산
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        order = np.argsort(-pts_sim[s, :]) # 승점이 높은 순으로 정렬
        for r, t_idx in enumerate(order, start=1):
            rank_matrix[s, t_idx] = r

    return rank_matrix, teams, team_idx

# 6. UI 구성
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("📋 실시간 공식 순위표 (완료 경기 반영)")
    st.dataframe(df_standings[["순위", "팀", "승점", "경기수", "승", "무", "패", "득실차"]], use_container_width=True, hide_index=True, height=280)
    
    st.subheader("🗓️ 잔여 경기 승패 직접 예측")
    st.caption("잔여 경기의 승/무/패를 직접 선택해 시뮬레이션 결과를 변화시켜 보세요.")
    
    match_preds = {}
    
    # "27라운드", "27R" 등 문자열을 27 같은 숫자로 파싱하여 라운드 순으로 정렬
    def parse_round(r_str):
        numbers = re.findall(r'\d+', str(r_str))
        return int(numbers[0]) if numbers else 0
        
    rounds = sorted(list(set(df_remaining['라운드'])), key=parse_round)
    
    for r in rounds:
        with st.expander(f"📌 {r} 잔여 경기", expanded=False):
            r_matches = df_remaining[df_remaining['라운드'] == r]
            for idx, match in r_matches.iterrows():
                home = str(match['홈팀']).strip()
                away = str(match['원정팀']).strip()
                st.markdown(f"**{home}** vs **{away}**")
                choice = st.radio(
                    label=f"match_{idx}",
                    options=["🎲 자동 (베이지안)", "🏠 홈승", "🔺 무승부", "✈️ 원정승"],
                    horizontal=True,
                    key=f"radio_match_{idx}",
                    label_visibility="collapsed"
                )
                match_preds[idx] = choice

with col2:
    st.subheader("📊 승격 확률 및 최종 순위 예측")
    
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 10000, 3000, step=1000)
    
    rank_matrix, teams, team_idx = run_simulation(
        df_standings, df_finished, df_remaining, match_preds, n_sims=sim_count
    )
    
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=0)
    
    target_i = team_idx[target_team]
    target_ranks = rank_matrix[:, target_i]
    
    # K리그2 승격 규정 통상 (1~2위 직행/자동, 3~6위 플옵)
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 5)) / sim_count) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{target_team} 1~2위 (직행권)", f"{direct_p:.1f}%")
    m2.metric(f"{target_team} 3~5위 (PO권)", f"{po_p:.1f}%")
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
        xaxis=dict(showgrid=False, tickmode='linear', dtick=1),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
