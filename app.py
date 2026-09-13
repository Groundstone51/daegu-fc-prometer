import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 베이지안 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 팀 엠블럼 매핑
LOGO_MAP = {
    "수원 삼성 블루윙즈": "suwon_samsung.png", "대구 FC": "daegu.png", "서울 이랜드 FC": "seoul.png",
    "수원 FC": "suwon_fc.png", "화성 FC": "hwasung.png", "부산 아이파크": "busan.png",
    "충남 아산 FC": "chungnamasan.png", "성남 FC": "seongnam.png", "김포 FC": "gimpo.png",
    "경남 FC": "gyeongnam.png", "용인 FC": "yongin.png", "파주 프런티어 FC": "paju.png",
    "충북 청주 FC": "chungbukcheongju.png", "천안 시티 FC": "cheonan.png",
    "안산 그리너스 FC": "ansan.png", "전남 드래곤즈": "jeonnam.png", "김해 FC 2008": "gimhae.png"
}

def get_logo_html(team_name, size=22):
    file_name = LOGO_MAP.get(team_name)
    if file_name:
        for path in [file_name, os.path.join("emblem", file_name)]:
            if os.path.exists(path):
                encoded = base64.b64encode(open(path, "rb").read()).decode()
                return f'<img src="data:image/png;base64,{encoded}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 6px;">'
    return ""

st.markdown("""
    <style>
    .main { background-color: #F4F7FA; }
    h1 { color: #0085FF !important; font-weight: 800 !important; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 18px;
        border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
    }
    .tooltip {
        position: relative; display: block; cursor: pointer; width: 100%;
        padding: 10px 14px; background-color: #FFFFFF; border-radius: 8px;
        border: 1px solid #E2E8F0; border-left: 4px solid #0085FF; margin-bottom: 8px; font-size: 0.95rem;
    }
    .tooltip .tooltiptext {
        visibility: hidden; width: 320px; background-color: #1E293B; color: #FFFFFF;
        text-align: left; border-radius: 8px; padding: 12px; position: absolute; z-index: 99;
        bottom: 125%; left: 50%; margin-left: -160px; opacity: 0;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. 2026 K리그2 하드코딩 기초 데이터셋
@st.cache_data
def get_hardcoded_league_data():
    standings = [
        {"팀": "수원 삼성 블루윙즈", "승점": 53, "경기수": 25, "승": 16, "무": 5, "패": 4, "득점": 43, "실점": 24},
        {"팀": "대구 FC", "승점": 46, "경기수": 25, "승": 14, "무": 4, "패": 7, "득점": 42, "실점": 28},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 25, "승": 13, "무": 6, "패": 6, "득점": 38, "실점": 24},
        {"팀": "수원 FC", "승점": 44, "경기수": 24, "승": 13, "무": 5, "패": 6, "득점": 40, "실점": 22},
        {"팀": "화성 FC", "승점": 43, "경기수": 25, "승": 12, "무": 7, "패": 6, "득점": 35, "실점": 21},
        {"팀": "부산 아이파크", "승점": 38, "경기수": 24, "승": 11, "무": 5, "패": 8, "득점": 31, "실점": 25},
        {"팀": "충남 아산 FC", "승점": 31, "경기수": 24, "승": 8, "무": 7, "패": 9, "득점": 28, "실점": 27},
        {"팀": "성남 FC", "승점": 31, "경기수": 24, "승": 8, "무": 7, "패": 9, "득점": 27, "실점": 28},
        {"팀": "김포 FC", "승점": 31, "경기수": 24, "승": 8, "무": 7, "패": 9, "득점": 25, "실점": 27},
        {"팀": "경남 FC", "승점": 30, "경기수": 24, "승": 8, "무": 6, "패": 10, "득점": 27, "실점": 27},
        {"팀": "용인 FC", "승점": 26, "경기수": 24, "승": 6, "무": 8, "패": 10, "득점": 25, "실점": 29},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "승": 6, "무": 8, "패": 10, "득점": 22, "실점": 28},
        {"팀": "충북 청주 FC", "승점": 26, "경기수": 25, "승": 6, "무": 8, "패": 11, "득점": 21, "실점": 32},
        {"팀": "천안 시티 FC", "승점": 22, "경기수": 24, "승": 5, "무": 7, "패": 12, "득점": 21, "실점": 26},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 25, "승": 5, "무": 7, "패": 13, "득점": 19, "실점": 40},
        {"팀": "전남 드래곤즈", "승점": 20, "경기수": 24, "승": 4, "무": 8, "패": 12, "득점": 22, "실점": 34},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 24, "승": 2, "무": 7, "패": 15, "득점": 14, "실점": 43}
    ]
    
    past_matches = [
        {"id": "r1_1", "R": 1, "날짜": "03.01(일)", "장소": "대구파크", "홈팀": "대구 FC", "원정팀": "화성 FC", "실제홈득점": 1, "실제원정득점": 0, "실제결과": "홈승", "내용": "박대훈 결승골 (12,005명 관중)"},
        {"id": "r1_2", "R": 1, "날짜": "03.01(일)", "장소": "목동구장", "홈팀": "서울 이랜드 FC", "원정팀": "부산 아이파크", "실제홈득점": 1, "실제원정득점": 0, "실제결과": "홈승", "내용": "이준석 54' 결승골"},
        {"id": "r1_3", "R": 1, "날짜": "03.01(일)", "장소": "수원종합", "홈팀": "수원 FC", "원정팀": "경남 FC", "실제홈득점": 1, "실제원정득점": 1, "실제결과": "무승부", "내용": "싸박 31' / 원기종 78'"},
        {"id": "r25_1", "R": 25, "날짜": "09.06(일)", "장소": "빅버드", "홈팀": "수원 삼성 블루윙즈", "원정팀": "충남 아산 FC", "실제홈득점": 2, "실제원정득점": 0, "실제결과": "홈승", "내용": "뮬리치, 이기제 득점"},
        {"id": "r26_1", "R": 26, "날짜": "09.12(토)", "장소": "목동구장", "홈팀": "서울 이랜드 FC", "원정팀": "수원 삼성 블루윙즈", "실제홈득점": 0, "실제원정득점": 1, "실제결과": "원정승", "내용": "카즈키 40' 결승골"},
        {"id": "r26_2", "R": 26, "날짜": "09.12(토)", "장소": "대구파크", "홈팀": "대구 FC", "원정팀": "용인 FC", "실제홈득점": 3, "실제원정득점": 1, "실제결과": "홈승", "내용": "세징야 멀티골, 에드가 득점"}
    ]
    
    remaining_matches = [
        {"R": 27, "날짜": "09.19(토) 16:30", "장소": "광양전용구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 FC"},
        {"R": 27, "날짜": "09.19(토) 16:30", "장소": "아산이순신구장", "홈팀": "충남 아산 FC", "원정팀": "천안 시티 FC"},
        {"R": 27, "날짜": "09.19(토) 19:00", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"R": 27, "날짜": "09.19(토) 19:00", "장소": "김포솔터축구장", "홈팀": "김포 FC", "원정팀": "부산 아이파크"},
        {"R": 27, "날짜": "09.20(일) 16:30", "장소": "안산와~스타디움", "홈팀": "안산 그리너스 FC", "원정팀": "충북 청주 FC"},
        {"R": 27, "날짜": "09.20(일) 16:30", "장소": "용인미르스타디움", "홈팀": "용인 FC", "원정팀": "경남 FC"},
        {"R": 27, "날짜": "09.20(일) 19:00", "장소": "김해종합운동장", "홈팀": "김해 FC 2008", "원정팀": "파주 프런티어 FC"},
        {"R": 27, "날짜": "09.20(일) 19:00", "장소": "탄천종합운동장", "홈팀": "성남 FC", "원정팀": "화성 FC"},
        {"R": 28, "날짜": "09.26(토) 16:30", "장소": "대구iM뱅크파크", "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 28, "날짜": "09.26(토) 19:00", "장소": "부산아시아드", "홈팀": "부산 아이파크", "원정팀": "수원 FC"},
        {"R": 28, "날짜": "09.27(일) 19:00", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "화성 FC"}
    ]
    return pd.DataFrame(standings), past_matches, remaining_matches

df_standings, past_matches, remaining_matches = get_hardcoded_league_data()

# 4. 베이지안 포아송 시뮬레이션 엔진
def run_bayesian_simulation(df_base, past_list, past_preds, future_schedule, future_preds, home_adv, total_games=36, n_sims=5000):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    # 1. Past Match What-If 승점 및 골 스탯 재계산
    pts_mod = np.zeros(n_teams)
    gf_mod = np.zeros(n_teams)
    ga_mod = np.zeros(n_teams)
    
    for m in past_list:
        if m["홈팀"] not in team_idx or m["원정팀"] not in team_idx: continue
        h_i, a_i = team_idx[m["홈팀"]], team_idx[m["원정팀"]]
        o_h, o_a = int(m["실제홈득점"]), int(m["실제원정득점"])
        
        # 실제 결과 차감
        if o_h > o_a: pts_mod[h_i] -= 3
        elif o_h == o_a: pts_mod[h_i] -= 1; pts_mod[a_i] -= 1
        else: pts_mod[a_i] -= 3
        gf_mod[h_i] -= o_h; ga_mod[h_i] -= o_a
        gf_mod[a_i] -= o_a; ga_mod[a_i] -= o_h
        
        # What-If 선택 결과 가산
        p_choice = past_preds.get(m["id"], f"🏠 {m['홈팀']} 승")
        if f"🏠 {m['홈팀']} 승" in p_choice:
            pts_mod[h_i] += 3; gf_mod[h_i] += 2; ga_mod[h_i] += 0; gf_mod[a_i] += 0; ga_mod[a_i] += 2
        elif "🔺 무승부" in p_choice:
            pts_mod[h_i] += 1; pts_mod[a_i] += 1; gf_mod[h_i] += 1; ga_mod[h_i] += 1; gf_mod[a_i] += 1; ga_mod[a_i] += 1
        elif f"✈️ {m['원정팀']} 승" in p_choice:
            pts_mod[a_i] += 3; gf_mod[a_i] += 2; ga_mod[a_i] += 0; gf_mod[h_i] += 0; ga_mod[h_i] += 2

    # 베이지안 모형 사전 분포(Prior) 설정 (Gamma Prior: shape=10, rate=8 -> Prior Mean 1.25골)
    prior_shape = 10.0
    prior_rate = 8.0
    
    current_pts = df['승점'].values.astype(np.float64) + pts_mod
    games_played = df['경기수'].values.copy()
    total_gf = df['득점'].values.astype(np.float64) + gf_mod
    total_ga = df['실점'].values.astype(np.float64) + ga_mod
    
    # 2. 사후 분포(Posterior Parameters: Gamma Distribution)
    post_shape_att = prior_shape + total_gf
    post_rate_att = prior_rate + games_played
    
    post_shape_def = prior_shape + total_ga
    post_rate_def = prior_rate + games_played
    
    pts_sim = np.tile(current_pts, (n_sims, 1))
    
    # 몬테카를로 베이지안 샘플링
    for s in range(n_sims):
        # Posterior 샘플링: 각 팀의 득점력 및 수비 불안도 파라미터 추출
        sampled_att = np.random.gamma(post_shape_att, 1.0 / post_rate_att)
        sampled_def = np.random.gamma(post_shape_def, 1.0 / post_rate_def)
        
        sim_games_count = games_played.copy()
        
        # 사용자 선택 잔여 경기 (Future What-If)
        for m_idx, match in enumerate(future_schedule):
            h_t, a_t = match["홈팀"], match["원정팀"]
            if h_t not in team_idx or a_t not in team_idx: continue
            h_i, a_i = team_idx[h_t], team_idx[a_t]
            choice = future_preds.get(m_idx, "🎲 베이지안 자동 시뮬레이션")
            
            if choice == "🎲 베이지안 자동 시뮬레이션":
                lambda_h = sampled_att[h_i] * sampled_def[a_i] * (1 + home_adv)
                lambda_a = sampled_att[a_i] * sampled_def[h_i]
                
                g_h = np.random.poisson(max(lambda_h, 0.05))
                g_a = np.random.poisson(max(lambda_a, 0.05))
                
                if g_h > g_a: pts_sim[s, h_i] += 3
                elif g_h == g_a: pts_sim[s, h_i] += 1; pts_sim[s, a_i] += 1
                else: pts_sim[s, a_i] += 3
            else:
                if f"🏠 {h_t} 승" in choice: pts_sim[s, h_i] += 3
                elif "🔺 무승부" in choice: pts_sim[s, h_i] += 1; pts_sim[s, a_i] += 1
                elif f"✈️ {a_t} 승" in choice: pts_sim[s, a_i] += 3
                    
            sim_games_count[h_i] += 1
            sim_games_count[a_i] += 1

        # 남은 미정 경기 베이지안 포아송 추정
        for i in range(n_teams):
            rem = total_games - sim_games_count[i]
            if rem > 0:
                l_h = sampled_att[i] * 1.0 * (1 + home_adv * 0.5)
                l_a = 1.0 * sampled_def[i]
                g_h_sim = np.random.poisson(max(l_h, 0.05), size=int(rem))
                g_a_sim = np.random.poisson(max(l_a, 0.05), size=int(rem))
                
                pts_adds = np.where(g_h_sim > g_a_sim, 3, np.where(g_h_sim == g_a_sim, 1, 0)).sum()
                pts_sim[s, i] += pts_adds

    # 최종 순위 매트릭스 생성
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        scores = [(pts_sim[s, i], total_gf[i], total_gf[i] - total_ga[i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx

# --- UI 레이아웃 ---
st.title("⚽ K리그2 승격 시뮬레이터 (Bayesian Model)")
st.info("베이지안 포아송 추론 모델 기반! past/future 경기 결과 What-If 시나리오를 설정하세요.")
st.divider()

col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.markdown("### ⚙️ 시뮬레이션 환경 설정")
    home_adv = st.slider("홈 경기 이점 가중치", 0.0, 0.3, 0.1, step=0.05)
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측 (What-If)", "🔄 지난 경기 기록 변경 (What-If)"])
    
    future_preds = {}
    with tab_future:
        st.caption("잔여 경기의 승/무/패를 직접 지정하면 해당 결과가 100% 반영됩니다.")
        fut_rounds = sorted(list(set([m["R"] for m in remaining_matches])))
        for r in fut_rounds:
            with st.expander(f"📌 Round {r} 잔여 경기", expanded=(r == fut_rounds[0])):
                r_matches = [m for m in remaining_matches if m["R"] == r]
                for idx, match in enumerate(r_matches):
                    m_global_idx = remaining_matches.index(match)
                    h_team, a_team = match['홈팀'], match['원정팀']
                    st.caption(f"📅 {match['날짜']} | 📍 {match['장소']}")
                    st.markdown(f"**{get_logo_html(h_team)}{h_team} VS {get_logo_html(a_team)}{a_team}**", unsafe_allow_html=True)
                    choice = st.radio(
                        label=f"r_fut_{r}_{idx}",
                        options=["🎲 베이지안 자동 시뮬레이션", f"🏠 {h_team} 승", "🔺 무승부", f"✈️ {a_team} 승"],
                        horizontal=True, key=f"radio_fut_{m_global_idx}", label_visibility="collapsed"
                    )
                    future_preds[m_global_idx] = choice

    past_preds = {}
    with tab_past:
        st.caption("지난 경기의 실제 결과를 만약(What-If) 다른 결과로 바꿨을 때 승격 확률 변화를 연산합니다.")
        past_rounds = sorted(list(set([m["R"] for m in past_matches])))
        if past_rounds:
            selected_round = st.selectbox("🔍 조회할 라운드 선택", options=past_rounds, index=len(past_rounds)-1)
            r_matches = [m for m in past_matches if m["R"] == selected_round]
            for idx, m in enumerate(r_matches):
                st.caption(f"📅 {m['날짜']} | 📍 {m['장소']}")
                st.markdown(f"<div class='tooltip'><b>{get_logo_html(m['홈팀'])}{m['홈팀']} <span style='color:#0085FF'>{m['실제홈득점']} : {m['실제원정득점']}</span> {get_logo_html(m['원정팀'])}{m['원정팀']}</b><span class='tooltiptext'>{m['내용']}</span></div>", unsafe_allow_html=True)
                default_idx = 0 if m['실제결과'] == "홈승" else (1 if m['실제결과'] == "무승부" else 2)
                p_choice = st.radio(
                    label=f"r_past_{m['R']}_{idx}",
                    options=[f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                    index=default_idx, horizontal=True, key=f"radio_past_{m['id']}", label_visibility="collapsed"
                )
                past_preds[m["id"]] = p_choice

with col2:
    st.subheader("📊 베이지안 승격 확률 및 순위 분포")
    sim_count = st.slider("몬테카를로 시뮬레이션 횟수", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx = run_bayesian_simulation(
        df_standings, past_matches, past_preds, remaining_matches, future_preds, home_adv, total_games=36, n_sims=sim_count
    )
    
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=0)
    
    if target_team in team_idx:
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
            rank_counts, x="순위", y="빈도수", text="빈도수",
            title=f"<b>{target_team} 베이지안 시뮬레이션 최종 순위 분포 ({sim_count:,}회)</b>",
            color_discrete_sequence=["#0085FF"]
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickmode='linear', tick0=1, dtick=1),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
