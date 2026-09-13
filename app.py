import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 동적 베이지안 승격 시뮬레이터",
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

# 3. 26라운드 실경기 및 구단별 세부 Prior 데이터
@st.cache_data
def get_hardcoded_league_data():
    standings = [
        {"팀": "수원 삼성 블루윙즈", "승점": 56, "경기수": 26, "승": 17, "무": 5, "패": 4, "득점": 44, "실점": 24, "최근5경기승점": 13},
        {"팀": "대구 FC", "승점": 49, "경기수": 26, "승": 15, "무": 4, "패": 7, "득점": 45, "실점": 29, "최근5경기승점": 10},
        {"팀": "화성 FC", "승점": 46, "경기수": 26, "승": 13, "무": 7, "패": 6, "득점": 37, "실점": 21, "최근5경기승점": 10},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 26, "승": 13, "무": 6, "패": 7, "득점": 38, "실점": 25, "최근5경기승점": 8},
        {"팀": "수원 FC", "승점": 45, "경기수": 25, "승": 13, "무": 6, "패": 6, "득점": 41, "실점": 23, "최근5경기승점": 9},
        {"팀": "부산 아이파크", "승점": 41, "경기수": 25, "승": 12, "무": 5, "패": 8, "득점": 33, "실점": 25, "최근5경기승점": 7},
        {"팀": "경남 FC", "승점": 33, "경기수": 25, "승": 9, "무": 6, "패": 10, "득점": 28, "실점": 27, "최근5경기승점": 8},
        {"팀": "김포 FC", "승점": 32, "경기수": 25, "승": 8, "무": 8, "패": 9, "득점": 27, "실점": 29, "최근5경기승점": 6},
        {"팀": "충남 아산 FC", "승점": 31, "경기수": 25, "승": 8, "무": 7, "패": 10, "득점": 28, "실점": 28, "최근5경기승점": 4},
        {"팀": "성남 FC", "승점": 31, "경기수": 25, "승": 8, "무": 7, "패": 10, "득점": 27, "실점": 29, "최근5경기승점": 4},
        {"팀": "충북 청주 FC", "승점": 29, "경기수": 26, "승": 7, "무": 8, "패": 11, "득점": 22, "실점": 32, "최근5경기승점": 5},
        {"팀": "용인 FC", "승점": 26, "경기수": 25, "승": 6, "무": 8, "패": 11, "득점": 26, "실점": 32, "최근5경기승점": 3},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "승": 6, "무": 8, "패": 10, "득점": 22, "실점": 28, "최근5경기승점": 4},
        {"팀": "천안 시티 FC", "승점": 23, "경기수": 25, "승": 5, "무": 8, "패": 12, "득점": 22, "실점": 27, "최근5경기승점": 3},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 26, "승": 5, "무": 7, "패": 14, "득점": 19, "실점": 42, "최근5경기승점": 1},
        {"팀": "전남 드래곤즈", "승점": 21, "경기수": 25, "승": 4, "무": 9, "패": 12, "득점": 24, "실점": 36, "최근5경기승점": 3},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 25, "승": 2, "무": 7, "패": 16, "득점": 14, "실점": 45, "최근5경기승점": 1}
    ]
    
    # 상대 전적 (Home vs Away 우세 지수: 1.0 기준, >1.0 홈팀 우세, <1.0 원정팀 우세)
    h2h_index = {
        ("전남 드래곤즈", "수원 FC"): 0.85,
        ("충남 아산 FC", "천안 시티 FC"): 1.15,
        ("서울 이랜드 FC", "대구 FC"): 0.95,
        ("김포 FC", "부산 아이파크"): 0.90,
        ("수원 삼성 블루윙즈", "경남 FC"): 1.25,
        ("부산 아이파크", "전남 드래곤즈"): 1.10
    }
    
    past_matches = [
        {"id": "r26_1", "R": 26, "날짜": "09.12(토)", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "수원 삼성 블루윙즈", "실제홈득점": 0, "실제원정득점": 1, "실제결과": "원정승", "내용": "⚽ 두비츠카스 9' 결승골"},
        {"id": "r26_2", "R": 26, "날짜": "09.12(토)", "장소": "대구iM뱅크파크", "홈팀": "대구 FC", "원정팀": "용인 FC", "실제홈득점": 3, "실제원정득점": 1, "실제결과": "홈승", "내용": "⚽ 세징야 멀티골"},
        {"id": "r26_5", "R": 26, "날짜": "09.13(일)", "장소": "창원축구센터", "홈팀": "경남 FC", "원정팀": "성남 FC", "실제홈득점": 1, "실제원정득점": 0, "실제결과": "홈승", "내용": "⚽ 경남 FC 1:0 성남 제압"},
        {"id": "r26_8", "R": 26, "날짜": "09.13(일)", "장소": "부산구덕운동장", "홈팀": "부산 아이파크", "원정팀": "김해 FC 2008", "실제홈득점": 2, "실제원정득점": 0, "실제결과": "홈승", "내용": "⚽ 부산 2:0 완승"}
    ]
    
    remaining_matches = [
        {"R": 27, "날짜": "09.19(토) 16:30", "장소": "광양전용구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 FC"},
        {"R": 27, "날짜": "09.19(토) 16:30", "장소": "아산이순신구장", "홈팀": "충남 아산 FC", "원정팀": "천안 시티 FC"},
        {"R": 27, "날짜": "09.19(토) 19:00", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"R": 27, "날짜": "09.19(토) 19:00", "장소": "김포솔터구장", "홈팀": "김포 FC", "원정팀": "부산 아이파크"},
        {"R": 28, "날짜": "10.09(금) 14:00", "장소": "청주종합운동장", "홈팀": "충북 청주 FC", "원정팀": "성남 FC"},
        {"R": 28, "날짜": "10.10(토) 16:30", "장소": "빅버드", "홈팀": "수원 삼성 블루윙즈", "원정팀": "안산 그리너스 FC"},
        {"R": 34, "날짜": "11.29(일) 15:00", "장소": "광양전용구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 삼성 블루윙즈"}
    ]
    return pd.DataFrame(standings), h2h_index, past_matches, remaining_matches

df_standings, h2h_index, past_matches, remaining_matches = get_hardcoded_league_data()

# 4. 동적 베이지안 포아송 시뮬레이션 엔진
def run_dynamic_bayesian_simulation(
    df_base, h2h_dict, past_list, past_preds, future_schedule, future_preds, 
    form_weight, h2h_weight, home_adv, total_games=34, n_sims=5000
):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    # 1. Past Match What-If 보정
    pts_mod = np.zeros(n_teams)
    gf_mod = np.zeros(n_teams)
    ga_mod = np.zeros(n_teams)
    
    for m in past_list:
        if m["홈팀"] not in team_idx or m["원정팀"] not in team_idx: continue
        h_i, a_i = team_idx[m["홈팀"]], team_idx[m["원정팀"]]
        o_h, o_a = int(m["실제홈득점"]), int(m["실제원정득점"])
        
        if o_h > o_a: pts_mod[h_i] -= 3
        elif o_h == o_a: pts_mod[h_i] -= 1; pts_mod[a_i] -= 1
        else: pts_mod[a_i] -= 3
        gf_mod[h_i] -= o_h; ga_mod[h_i] -= o_a
        gf_mod[a_i] -= o_a; ga_mod[a_i] -= o_h
        
        p_choice = past_preds.get(m["id"], f"🏠 {m['홈팀']} 승")
        if f"🏠 {m['홈팀']} 승" in p_choice:
            pts_mod[h_i] += 3; gf_mod[h_i] += 2; ga_mod[a_i] += 2
        elif "🔺 무승부" in p_choice:
            pts_mod[h_i] += 1; pts_mod[a_i] += 1; gf_mod[h_i] += 1; ga_mod[h_i] += 1; gf_mod[a_i] += 1; ga_mod[a_i] += 1
        elif f"✈️ {m['원정팀']} 승" in p_choice:
            pts_mod[a_i] += 3; gf_mod[a_i] += 2; ga_mod[h_i] += 2

    # 2. 기초 베이지안 사전 분포(Prior) 파라미터 갱신 (공격/수비 득실 반영)
    prior_shape = 10.0
    prior_rate = 8.0
    
    current_pts = df['승점'].values.astype(np.float64) + pts_mod
    games_played = df['경기수'].values.copy()
    total_gf = df['득점'].values.astype(np.float64) + gf_mod
    total_ga = df['실점'].values.astype(np.float64) + ga_mod
    recent_5_pts = df['최근5경기승점'].values.astype(np.float64)
    
    # 사후 분포 (Gamma Posterior)
    post_shape_att = prior_shape + total_gf
    post_rate_att = prior_rate + games_played
    post_shape_def = prior_shape + total_ga
    post_rate_def = prior_rate + games_played
    
    pts_sim = np.tile(current_pts, (n_sims, 1))
    
    # 최근 5경기 기세(Form) 가중치 벡터 계산: F_i = 1 + form_weight * (Recent5Pts / 15 - 0.5)
    form_factor = 1.0 + form_weight * ((recent_5_pts / 15.0) - 0.5)
    
    for s in range(n_sims):
        # 몬테카를로 파라미터 샘플링
        sampled_att = np.random.gamma(post_shape_att, 1.0 / post_rate_att)
        sampled_def = np.random.gamma(post_shape_def, 1.0 / post_rate_def)
        
        sim_games_count = games_played.copy()
        
        # 3. 잔여 경기 시뮬레이션 (상대전적 + 최근기세 + 홈이점 + 공수득실 베이지안 결합)
        for m_idx, match in enumerate(future_schedule):
            h_t, a_t = match["홈팀"], match["원정팀"]
            if h_t not in team_idx or a_t not in team_idx: continue
            h_i, a_i = team_idx[h_t], team_idx[a_t]
            choice = future_preds.get(m_idx, "🎲 동적 베이지안 자동 시뮬레이션")
            
            if choice == "🎲 동적 베이지안 자동 시뮬레이션":
                # 상대 전적 지수 산출 (H2H Prior Factor)
                h2h_val = h2h_dict.get((h_t, a_t), 1.0)
                h2h_h_factor = 1.0 + h2h_weight * (h2h_val - 1.0)
                h2h_a_factor = 1.0 - h2h_weight * (h2h_val - 1.0)
                
                # 최종 동적 람다($\lambda$) 연산
                lambda_h = (sampled_att[h_i] * sampled_def[a_i]) * form_factor[h_i] * h2h_h_factor * (1 + home_adv)
                lambda_a = (sampled_att[a_i] * sampled_def[h_i]) * form_factor[a_i] * h2h_a_factor
                
                # 포아송 확률 샘플링 ($g \sim \text{Poisson}(\lambda)$)
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

        # 미정 리그 경기 처리
        for i in range(n_teams):
            rem = total_games - sim_games_count[i]
            if rem > 0:
                l_h = sampled_att[i] * form_factor[i] * (1 + home_adv * 0.5)
                l_a = sampled_def[i]
                g_h_sim = np.random.poisson(max(l_h, 0.05), size=int(rem))
                g_a_sim = np.random.poisson(max(l_a, 0.05), size=int(rem))
                
                pts_adds = np.where(g_h_sim > g_a_sim, 3, np.where(g_h_sim == g_a_sim, 1, 0)).sum()
                pts_sim[s, i] += pts_adds

    # 최종 순위 매트릭스 산출
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        scores = [(pts_sim[s, i], total_gf[i], total_gf[i] - total_ga[i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx

# --- UI 레이아웃 ---
st.title("⚽ K리그2 동적 베이지안 승격 시뮬레이터")
st.info("사전 분포(Prior): 공격/수비 득실차 + 최근 5경기 기세 + 홈/원정 상대 전적이 실시간 승률에 통합 적용됩니다.")
st.divider()

col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.markdown("### ⚙️ 동적 베이지안 Prior 가중치 조절")
    form_w = st.slider("🔥 최근 5경기 기세(Form) 반영 비중", 0.0, 0.5, 0.25, step=0.05)
    h2h_w = st.slider("⚔️ 홈/원정 상대 전적(H2H) 반영 비중", 0.0, 0.5, 0.20, step=0.05)
    home_adv = st.slider("🏟️ 홈 경기 이점 가중치", 0.0, 0.3, 0.10, step=0.05)
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측 (27R~)", "🔄 경기 기록 & What-If"])
    
    future_preds = {}
    with tab_future:
        st.caption("자동 선택 시 설정한 3대 Prior 기반 베이지안 모델로 승패 확률이 계산됩니다.")
        fut_rounds = sorted(list(set([m["R"] for m in remaining_matches])))
        for r in fut_rounds:
            with st.expander(f"📌 Round {r} 잔여 경기", expanded=(r == fut_rounds[0])):
                r_matches = [m for m in remaining_matches if m["R"] == r]
                for idx, match in enumerate(r_matches):
                    m_global_idx = remaining_matches.index(match)
                    h_team, a_team = match['홈팀'], match['원정팀']
                    h2h_val = h2h_index.get((h_team, a_team), 1.0)
                    h2h_txt = f" (상대전적 지수: {h2h_val:.2f})" if h2h_val != 1.0 else ""
                    
                    st.caption(f"📅 {match['날짜']} | 📍 {match['장소']}{h2h_txt}")
                    st.markdown(f"**{get_logo_html(h_team)}{h_team} VS {get_logo_html(a_team)}{a_team}**", unsafe_allow_html=True)
                    choice = st.radio(
                        label=f"r_fut_{r}_{idx}",
                        options=["🎲 동적 베이지안 자동 시뮬레이션", f"🏠 {h_team} 승", "🔺 무승부", f"✈️ {a_team} 승"],
                        horizontal=True, key=f"radio_fut_{m_global_idx}", label_visibility="collapsed"
                    )
                    future_preds[m_global_idx] = choice

    past_preds = {}
    with tab_past:
        st.caption("과거 경기 스코어 수정 시 팀의 공수 득실차 Prior 데이터가 함께 재계산됩니다.")
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
    st.subheader("📊 3대 Prior 반영 최종 순위 예측")
    sim_count = st.slider("몬테카를로 시뮬레이션 횟수", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx = run_dynamic_bayesian_simulation(
        df_standings, h2h_index, past_matches, past_preds, remaining_matches, future_preds, 
        form_w, h2h_w, home_adv, total_games=34, n_sims=sim_count
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
            title=f"<b>{target_team} 동적 베이지안 순위 분포 ({sim_count:,}회)</b>",
            color_discrete_sequence=["#0085FF"]
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickmode='linear', tick0=1, dtick=1),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
