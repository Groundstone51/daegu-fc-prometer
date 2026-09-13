import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 팀 엠블럼 매핑
LOGO_MAP = {
    "안산 그리너스 FC": "ansan.png", "부산 아이파크": "busan.png", "천안 시티 FC": "cheonan.png",
    "충북 청주 FC": "chungbukcheongju.png", "충남 아산 FC": "chungnamasan.png", "대구 FC": "daegu.png",
    "김해 FC 2008": "gimhae.png", "김포 FC": "gimpo.png", "경남 FC": "gyeongnam.png",
    "화성 FC": "hwasung.png", "전남 드래곤즈": "jeonnam.png", "파주 프런티어 FC": "paju.png",
    "성남 FC": "seongnam.png", "서울 이랜드 FC": "seoul.png", "수원 FC": "suwon_fc.png",
    "수원 삼성 블루윙즈": "suwon_samsung.png", "용인 FC": "yongin.png"
}

def get_logo_html(team_name, size=22):
    file_name = LOGO_MAP.get(team_name)
    if file_name:
        for path in [file_name, os.path.join("emblem", file_name)]:
            if os.path.exists(path):
                encoded = base64.b64encode(open(path, "rb").read()).decode()
                return f'<img src="data:image/png;base64,{encoded}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 6px;">'
    return ""

# 3. Custom CSS
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

# 4. 데이터 로드 로직
@st.cache_data
def load_matches_dataset():
    csv_path = "matches.csv"
    if not os.path.exists(csv_path):
        return None, None
    
    df = pd.read_csv(csv_path)
    
    # 경기 결과 입력 유무에 따른 과거/잔여 경기 분류
    past_df = df[df['실제결과'].notna() & (df['실제결과'] != '')]
    future_df = df[df['실제결과'].isna() | (df['실제결과'] == '')]
    
    return past_df.to_dict('records'), future_df.to_dict('records')

@st.cache_data
def build_standings_from_matches(past_list):
    teams = list(LOGO_MAP.keys())
    stats = {t: {"팀": t, "승점": 0, "경기수": 0, "승": 0, "무": 0, "패": 0, "득점": 0, "실점": 0, "최근5경기승점": 8} for t in teams}
    
    for m in past_list:
        h, a = m["홈팀"], m["원정팀"]
        if h not in stats or a not in stats:
            continue
            
        hs, as_ = int(m["실제홈득점"]), int(m["실제원정득점"])
        stats[h]["경기수"] += 1
        stats[a]["경기수"] += 1
        stats[h]["득점"] += hs
        stats[h]["실점"] += as_
        stats[a]["득점"] += as_
        stats[a]["실점"] += hs
        
        if hs > as_:
            stats[h]["승점"] += 3
            stats[h]["승"] += 1
            stats[a]["패"] += 1
        elif hs == as_:
            stats[h]["승점"] += 1
            stats[a]["승점"] += 1
            stats[h]["무"] += 1
            stats[a]["무"] += 1
        else:
            stats[a]["승점"] += 3
            stats[a]["승"] += 1
            stats[h]["패"] += 1
            
    df_standings = pd.DataFrame(list(stats.values()))
    df_standings = df_standings.sort_values(by=["승점", "득점"], ascending=False).reset_index(drop=True)
    return df_standings

past_matches, remaining_matches = load_matches_dataset()

if past_matches is None:
    st.error("⚠️ `matches.csv` 파일을 찾을 수 없습니다. 프로젝트 폴더에 경기 데이터 파일을 생성해 주세요.")
    st.stop()

df_standings = build_standings_from_matches(past_matches)

# --- UI 레이아웃 ---
st.title("⚽ K리그2 승격 시뮬레이터")
st.info("실제 K리그2 데이터셋 연동 완료! What-If 시나리오를 적용해 최종 승격 확률을 계산해보세요.")
st.caption(f"총 {len(past_matches)}개 완료 경기 / {len(remaining_matches)}개 잔여 경기 로드됨")
st.divider()

# 시뮬레이션 엔진
def calculate_match_probabilities(home_row, away_row, form_weight, home_advantage):
    h_att = home_row['득점'] / max(home_row['경기수'], 1)
    h_def = home_row['실점'] / max(home_row['경기수'], 1)
    a_att = away_row['득점'] / max(away_row['경기수'], 1)
    a_def = away_row['실점'] / max(away_row['경기수'], 1)
    
    h_form = (home_row['최근5경기승점'] / 15.0) * form_weight
    a_form = (away_row['최근5경기승점'] / 15.0) * form_weight
    
    exp_home_goals = (h_att * a_def) * (1 + home_advantage) + h_form
    exp_away_goals = (a_att * h_def) * (1 - home_advantage) + a_form
    
    diff = exp_home_goals - exp_away_goals
    p_home = 1.0 / (1.0 + np.exp(-1.1 * diff))
    p_draw = 0.26
    p_home_adj = p_home * (1 - p_draw)
    p_away_adj = (1 - p_home) * (1 - p_draw)
    
    return [p_home_adj, p_draw, p_away_adj]

def run_what_if_simulation(df_base, past_list, past_preds, future_schedule, future_preds, form_w, home_adv, total_games=36, n_sims=5000):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    pts_mod = np.zeros(n_teams)
    
    for m in past_list:
        if m["홈팀"] not in team_idx or m["원정팀"] not in team_idx:
            continue
        h_i, a_i = team_idx[m["홈팀"]], team_idx[m["원정팀"]]
        o_h, o_a = int(m["실제홈득점"]), int(m["실제원정득점"])
        
        if o_h > o_a: pts_mod[h_i] -= 3
        elif o_h == o_a: pts_mod[h_i] -= 1; pts_mod[a_i] -= 1
        else: pts_mod[a_i] -= 3
        
        p_choice = past_preds.get(m["id"], f"🏠 {m['홈팀']} 승")
        if f"🏠 {m['홈팀']} 승" in p_choice: pts_mod[h_i] += 3
        elif "🔺 무승부" in p_choice: pts_mod[h_i] += 1; pts_mod[a_i] += 1
        elif f"✈️ {m['원정팀']} 승" in p_choice: pts_mod[a_i] += 3
        
    base_pts = df['승점'].values.astype(np.float64) + pts_mod
    games_played = df['경기수'].values.copy()
    
    pts_sim = np.tile(base_pts, (n_sims, 1))
    gf_sim = np.tile(df['득점'].values.astype(np.float64), (n_sims, 1))
    ga_sim = np.tile(df['실점'].values.astype(np.float64), (n_sims, 1))
    
    for m_idx, match in enumerate(future_schedule):
        home_team, away_team = match["홈팀"], match["원정팀"]
        if home_team not in team_idx or away_team not in team_idx:
            continue
            
        h_i, a_i = team_idx[home_team], team_idx[away_team]
        choice = future_preds.get(m_idx, "🎲 자동 (가중치 승률)")
        
        if choice == "🎲 자동 (가중치 승률)":
            h_row = df[df['팀'] == home_team].iloc[0]
            a_row = df[df['팀'] == away_team].iloc[0]
            probs = calculate_match_probabilities(h_row, a_row, form_w, home_adv)
            res = np.random.choice([3, 1, 0], size=n_sims, p=probs)
            pts_sim[:, h_i] += np.where(res == 3, 3, np.where(res == 1, 1, 0))
            pts_sim[:, a_i] += np.where(res == 0, 3, np.where(res == 1, 1, 0))
        else:
            if f"🏠 {home_team} 승" in choice: pts_sim[:, h_i] += 3
            elif "🔺 무승부" in choice: pts_sim[:, h_i] += 1; pts_sim[:, a_i] += 1
            elif f"✈️ {away_team} 승" in choice: pts_sim[:, a_i] += 3
                
        games_played[h_i] += 1
        games_played[a_i] += 1

    for i in range(n_teams):
        rem = total_games - games_played[i]
        if rem > 0:
            sim_adds = np.random.choice([3, 1, 0], size=(n_sims, int(rem)), p=[0.38, 0.26, 0.36]).sum(axis=1)
            pts_sim[:, i] += sim_adds

    gd_sim = gf_sim - ga_sim
    rank_matrix = np.zeros((n_sims, n_teams))
    for s in range(n_sims):
        scores = [(pts_sim[s, i], gf_sim[s, i], gd_sim[s, i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx

col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.markdown("### ⚙️ 승률 분석 가중치 설정")
    form_w = st.slider("최근 5경기 흐름 반영 비중", 0.0, 0.5, 0.2, step=0.05)
    home_adv = st.slider("홈 경기 이점 가중치", 0.0, 0.3, 0.1, step=0.05)
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측", "🔄 경기 기록 & What-If"])
    
    future_preds = {}
    with tab_future:
        if remaining_matches:
            fut_rounds = sorted(list(set([m["R"] for m in remaining_matches])))
            for r in fut_rounds:
                with st.expander(f"📌 Round {r} 잔여 경기", expanded=True):
                    r_matches = [m for m in remaining_matches if m["R"] == r]
                    for idx, match in enumerate(r_matches):
                        m_global_idx = remaining_matches.index(match)
                        h_team, a_team = match['홈팀'], match['원정팀']
                        st.caption(f"📅 {match.get('날짜','')} | 📍 {match.get('장소','')}")
                        st.markdown(f"**{get_logo_html(h_team)}{h_team} VS {get_logo_html(a_team)}{a_team}**", unsafe_allow_html=True)
                        choice = st.radio(
                            label=f"r_fut_{r}_{idx}",
                            options=["🎲 자동 (가중치 승률)", f"🏠 {h_team} 승", "🔺 무승부", f"✈️ {a_team} 승"],
                            horizontal=True, key=f"radio_fut_{m_global_idx}", label_visibility="collapsed"
                        )
                        future_preds[m_global_idx] = choice
        else:
            st.write("잔여 경기가 없거나 모두 종료되었습니다.")

    past_preds = {}
    with tab_past:
        past_rounds = sorted(list(set([m["R"] for m in past_matches])))
        if past_rounds:
            selected_round = st.selectbox("🔍 조회할 라운드 선택", options=past_rounds, index=len(past_rounds)-1)
            r_matches = [m for m in past_matches if m["R"] == selected_round]
            for idx, m in enumerate(r_matches):
                st.caption(f"📅 {m.get('날짜','')} | 📍 {m.get('장소','')}")
                st.markdown(f"<div class='tooltip'><b>{get_logo_html(m['홈팀'])}{m['홈팀']} <span style='color:#0085FF'>{m['실제홈득점']} : {m['실제원정득점']}</span> {get_logo_html(m['원정팀'])}{m['원정팀']}</b><span class='tooltiptext'>{m.get('내용','')}</span></div>", unsafe_allow_html=True)
                default_idx = 0 if m['실제결과'] == "홈승" else (1 if m['실제결과'] == "무승부" else 2)
                p_choice = st.radio(
                    label=f"r_past_{m['R']}_{idx}",
                    options=[f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                    index=default_idx, horizontal=True, key=f"radio_past_{m['id']}", label_visibility="collapsed"
                )
                past_preds[m["id"]] = p_choice

with col2:
    st.subheader("📊 승격 확률 및 순위 예측")
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx = run_what_if_simulation(
        df_standings, past_matches, past_preds, remaining_matches, future_preds, form_w, home_adv, total_games=36, n_sims=sim_count
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
            title=f"<b>{target_team} 시나리오 최종 순위 분포 ({sim_count:,}회)</b>",
            color_discrete_sequence=["#0085FF"]
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickmode='linear', tick0=1, dtick=1),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
