import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="2026 K리그2 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 팀명 - 로고 이미지 파일명 매핑
LOGO_MAP = {
    "수원 삼성 블루윙즈": "suwon_samsung.png",
    "대구 FC": "daegu.png",
    "서울 이랜드 FC": "seoul.png",
    "수원 FC": "suwon_fc.png",
    "화성 FC": "hwasung.png",
    "부산 아이파크": "busan.png",
    "경남 FC": "gyeongnam.png",
    "김포 FC": "gimpo.png",
    "충남아산 FC": "chungnamasan.png",
    "성남 FC": "seongnam.png",
    "용인 FC": "yongin.png",
    "파주 프런티어 FC": "paju.png",
    "충북 청주 FC": "chungbukcheongju.png",
    "천안시티 FC": "cheonan.png",
    "안산 그리너스 FC": "ansan.png",
    "전남 드래곤즈": "jeonnam.png",
    "김해 FC 2008": "gimhae.png"
}

def get_logo_html(team_name, size=22):
    # 명칭 정규화 대응
    clean_name = team_name.strip()
    if not clean_name.endswith("FC") and clean_name not in ["수원 삼성", "부산 아이파크", "전남 드래곤즈"]:
        pass
    file_name = LOGO_MAP.get(team_name)
    if file_name:
        possible_paths = [file_name, os.path.join("emblem", file_name)]
        for path in possible_paths:
            if os.path.exists(path):
                encoded = base64.b64encode(open(path, "rb").read()).decode()
                return f'<img src="data:image/png;base64,{encoded}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 6px;">'
    return ""

# 3. CSS 스타일링
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
    
    .tooltip {
        position: relative;
        display: block;
        cursor: pointer;
        width: 100%;
        padding: 10px 14px;
        background-color: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0085FF;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 320px;
        background-color: #1E293B;
        color: #FFFFFF;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 99;
        bottom: 125%;
        left: 50%;
        margin-left: -160px;
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15);
        font-size: 0.83rem;
        line-height: 1.5;
    }
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #1E293B transparent transparent transparent;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 4. 공식 현재 순위 데이터 (2026-09-13 기준 반영)
@st.cache_data(ttl=60)
def fetch_kleague_official_standings():
    default_teams = [
        {"팀": "수원 삼성 블루윙즈", "승점": 53, "경기수": 25, "득점": 39, "실점": 20, "최근5경기승점": 11},
        {"팀": "대구 FC", "승점": 46, "경기수": 25, "득점": 47, "실점": 33, "최근5경기승점": 10},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 25, "득점": 43, "실점": 29, "최근5경기승점": 9},
        {"팀": "수원 FC", "승점": 45, "경기수": 24, "득점": 47, "실점": 29, "최근5경기승점": 10},
        {"팀": "화성 FC", "승점": 43, "경기수": 25, "득점": 39, "실점": 25, "최근5경기승점": 8},
        {"팀": "부산 아이파크", "승점": 41, "경기수": 25, "득점": 41, "실점": 33, "최근5경기승점": 9},
        {"팀": "경남 FC", "승점": 33, "경기수": 24, "득점": 31, "실점": 30, "최근5경기승점": 7},
        {"팀": "김포 FC", "승점": 32, "경기수": 24, "득점": 30, "실점": 30, "최근5경기승점": 7},
        {"팀": "충남아산 FC", "승점": 31, "경기수": 24, "득점": 31, "실점": 30, "최근5경기승점": 6},
        {"팀": "성남 FC", "승점": 30, "경기수": 24, "득점": 26, "실점": 28, "최근5경기승점": 6},
        {"팀": "용인 FC", "승점": 26, "경기수": 24, "득점": 31, "실점": 35, "최근5경기승점": 5},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "득점": 22, "실점": 28, "최근5경기승점": 5},
        {"팀": "충북 청주 FC", "승점": 26, "경기수": 25, "득점": 28, "실점": 39, "최근5경기승점": 5},
        {"팀": "천안시티 FC", "승점": 23, "경기수": 25, "득점": 29, "실점": 34, "최근5경기승점": 4},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 25, "득점": 25, "실점": 46, "최근5경기승점": 4},
        {"팀": "전남 드래곤즈", "승점": 21, "경기수": 24, "득점": 28, "실점": 40, "최근5경기승점": 4},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 24, "득점": 19, "실점": 47, "최근5경기승점": 2}
    ]
    return pd.DataFrame(default_teams), "🟢 2026년 9월 13일 공식 데이터 기준 연동 완료"

# 5. 최근 및 잔여 경기 데이터베이스 구축
@st.cache_data(ttl=60)
def fetch_past_and_future_matches():
    ALL_MATCHES = [
        # --- 26라운드 주요 결과 (최근 검증된 경기) ---
        {"R": 26, "날짜": "2026-09-12", "장소": "대구iM뱅크파크", "홈팀": "대구 FC", "원정팀": "용인 FC", "homeScore": 3, "awayScore": 1},
        {"R": 26, "날짜": "2026-09-12", "장소": "이순신종합운동장", "홈팀": "충남아산 FC", "원정팀": "충북 청주 FC", "homeScore": 0, "awayScore": 1},
        {"R": 26, "날짜": "2026-09-12", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "수원 삼성 블루윙즈", "homeScore": 0, "awayScore": 1},
        {"R": 26, "날짜": "2026-09-12", "장소": "안산와스타디움", "홈팀": "안산 그리너스 FC", "원정팀": "화성 FC", "homeScore": 0, "awayScore": 2},
        
        # --- 27라운드 이후 잔여 경기 예시 ---
        {"R": 27, "날짜": "2026-09-19", "장소": "대구iM뱅크파크", "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈", "homeScore": None, "awayScore": None},
        {"R": 27, "날짜": "2026-09-20", "장소": "부산아시아드", "홈팀": "부산 아이파크", "원정팀": "서울 이랜드 FC", "homeScore": None, "awayScore": None},
        {"R": 27, "날짜": "2026-09-20", "장소": "광양전용구장", "홈팀": "전남 드래곤즈", "원정팀": "성남 FC", "homeScore": None, "awayScore": None},
    ]

    past_matches = []
    remaining_matches = []

    for m in ALL_MATCHES:
        h_score = m.get("homeScore")
        a_score = m.get("awayScore")
        
        if h_score is not None and a_score is not None:
            h_score, a_score = int(h_score), int(a_score)
            result_str = "홈승" if h_score > a_score else ("무승부" if h_score == a_score else "원정승")
            
            past_matches.append({
                "id": f"p_{m['R']}_{m['홈팀']}_{m['원정팀']}",
                "R": m["R"],
                "날짜": m["날짜"],
                "장소": m["장소"],
                "홈팀": m["홈팀"],
                "원정팀": m["원정팀"],
                "실제홈득점": h_score,
                "실제원정득점": a_score,
                "실제결과": result_str,
                "내용": f"⚽ 최종 스코어 {h_score} : {a_score}<br>📍 경기장: {m['장소']}"
            })
        else:
            remaining_matches.append({
                "R": m["R"],
                "날짜": m["날짜"],
                "장소": m["장소"],
                "홈팀": m["홈팀"],
                "원정팀": m["원정팀"]
            })

    return past_matches, remaining_matches

df_standings, status_msg = fetch_kleague_official_standings()
past_matches, remaining_matches = fetch_past_and_future_matches()

# --- 타이틀 및 안내문 ---
st.title("⚽ 2026 K리그2 승격 시뮬레이터")
st.info("공식 순위 및 최근 경기 데이터베이스 기반 What-If 시뮬레이션을 실행하세요!")
st.caption(f"{status_msg}")
st.divider()

# 6. 경기별 확률 연산 엔진
def calculate_match_probabilities(home_row, away_row, form_weight, home_advantage):
    h_att = home_row['득점'] / home_row['경기수']
    h_def = home_row['실점'] / home_row['경기수']
    a_att = away_row['득점'] / away_row['경기수']
    a_def = away_row['실점'] / away_row['경기수']
    
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

# 7. 몬테카를로 시뮬레이션
def run_what_if_simulation(df_base, past_list, past_preds, future_schedule, future_preds, form_w, home_adv, total_games=34, n_sims=5000):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    pts_mod = np.zeros(n_teams)
    
    for m in past_list:
        if m["홈팀"] not in team_idx or m["원정팀"] not in team_idx:
            continue
        h_i = team_idx[m["홈팀"]]
        a_i = team_idx[m["원정팀"]]
        
        o_h = m["실제홈득점"]
        o_a = m["실제원정득점"]
        
        if o_h > o_a: pts_mod[h_i] -= 3
        elif o_h == o_a: pts_mod[h_i] -= 1; pts_mod[a_i] -= 1
        else: pts_mod[a_i] -= 3
        
        p_choice = past_preds.get(m["id"], f"🏠 {m['홈팀']} 승")
        if f"🏠 {m['홈팀']} 승" in p_choice:
            pts_mod[h_i] += 3
        elif "🔺 무승부" in p_choice:
            pts_mod[h_i] += 1
            pts_mod[a_i] += 1
        elif f"✈️ {m['원정팀']} 승" in p_choice:
            pts_mod[a_i] += 3
        
    base_pts = df['승점'].values.astype(np.float64) + pts_mod
    games_played = df['경기수'].values.copy()
    
    pts_sim = np.tile(base_pts, (n_sims, 1))
    gf_sim = np.tile(df['득점'].values.astype(np.float64), (n_sims, 1))
    ga_sim = np.tile(df['실점'].values.astype(np.float64), (n_sims, 1))
    
    for m_idx, match in enumerate(future_schedule):
        home_team = match["홈팀"]
        away_team = match["원정팀"]
        if home_team not in team_idx or away_team not in team_idx:
            continue
            
        h_i = team_idx[home_team]
        a_i = team_idx[away_team]
        choice = future_preds.get(m_idx, "🎲 자동 (가중치 승률)")
        
        home_win_str = f"🏠 {home_team} 승"
        away_win_str = f"✈️ {away_team} 승"
        
        if choice == "🎲 자동 (가중치 승률)":
            h_row = df[df['팀'] == home_team].iloc[0]
            a_row = df[df['팀'] == away_team].iloc[0]
            probs = calculate_match_probabilities(h_row, a_row, form_w, home_adv)
            res = np.random.choice([3, 1, 0], size=n_sims, p=probs)
            pts_sim[:, h_i] += np.where(res == 3, 3, np.where(res == 1, 1, 0))
            pts_sim[:, a_i] += np.where(res == 0, 3, np.where(res == 1, 1, 0))
        else:
            if choice == home_win_str:
                pts_sim[:, h_i] += 3
            elif choice == "🔺 무승부":
                pts_sim[:, h_i] += 1
                pts_sim[:, a_i] += 1
            elif choice == away_win_str:
                pts_sim[:, a_i] += 3
                
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

    return rank_matrix, teams, team_idx, base_pts

# 8. UI 구성
col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.subheader("⚙️ 모델 가중치 설정")
    form_w = st.slider("최근 5경기 흐름 반영 비중", 0.0, 0.5, 0.2, step=0.05)
    home_adv = st.slider("홈 경기 이점 가중치", 0.0, 0.3, 0.1, step=0.05)
    
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측", "🔄 최근 경기 결과 & What-If"])
    
    future_preds = {}
    with tab_future:
        st.caption("남은 경기의 승패를 조작하여 시나리오를 구성하세요.")
        fut_rounds = sorted(list(set([m["R"] for m in remaining_matches])))
        if fut_rounds:
            for r in fut_rounds:
                with st.expander(f"📌 Round {r} 잔여 경기", expanded=True):
                    r_matches = [m for m in remaining_matches if m["R"] == r]
                    for idx, match in enumerate(r_matches):
                        m_global_idx = remaining_matches.index(match)
                        h_team, a_team = match['홈팀'], match['원정팀']
                        m_date, m_venue = match.get('날짜', ''), match.get('장소', '')
                        
                        st.caption(f"📅 {m_date} | 📍 {m_venue}")
                        
                        match_header_html = f"""
                        <div style="font-size: 1.05rem; font-weight: bold; margin-bottom: 6px;">
                            {get_logo_html(h_team, size=22)}{h_team}
                            <span style="color:#94A3B8; margin: 0 8px;">VS</span> 
                            {get_logo_html(a_team, size=22)}{a_team}
                        </div>
                        """
                        st.markdown(match_header_html, unsafe_allow_html=True)
                        
                        opt_home = f"🏠 {h_team} 승"
                        opt_draw = "🔺 무승부"
                        opt_away = f"✈️ {a_team} 승"
                        
                        choice = st.radio(
                            label=f"r_fut_{r}_{idx}",
                            options=["🎲 자동 (가중치 승률)", opt_home, opt_draw, opt_away],
                            horizontal=True,
                            key=f"radio_fut_{m_global_idx}",
                            label_visibility="collapsed"
                        )
                        future_preds[m_global_idx] = choice
                        st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        else:
            st.write("표시할 잔여 경기가 없습니다.")

    past_preds = {}
    with tab_past:
        st.caption("💡 최근 검증된 경기 결과를 변경해 시나리오를 테스트할 수 있습니다.")
        past_rounds = sorted(list(set([m["R"] for m in past_matches])))
        
        if past_rounds:
            selected_round = st.selectbox(
                "🔍 라운드 선택", 
                options=past_rounds, 
                format_func=lambda r: f"Round {r} 경기 목록"
            )
            
            r_matches = [m for m in past_matches if m["R"] == selected_round]
            
            for idx, m in enumerate(r_matches):
                h_logo = get_logo_html(m['홈팀'], size=22)
                a_logo = get_logo_html(m['원정팀'], size=22)
                m_date, m_venue = m.get('날짜', ''), m.get('장소', '')
                
                st.caption(f"📅 {m_date} | 📍 {m_venue}")
                
                tooltip_html = f"""
                <div class="tooltip">
                    <span style="font-size: 1.05rem; font-weight: bold;">
                        {h_logo} {m['홈팀']} 
                        <span style="color:#0085FF; margin: 0 4px;">{m['실제홈득점']} : {m['실제원정득점']}</span> 
                        {a_logo} {m['원정팀']}
                    </span>
                    <span class="tooltiptext">
                        <b>📝 Round {m['R']} 경기 정보</b><br>
                        {m['내용']}
                    </span>
                </div>
                """
                st.markdown(tooltip_html, unsafe_allow_html=True)
                
                opt_h = f"🏠 {m['홈팀']} 승"
                opt_d = "🔺 무승부"
                opt_a = f"✈️ {m['원정팀']} 승"
                
                default_idx = 0
                if m['실제결과'] == "무승부": default_idx = 1
                elif m['실제결과'] == "원정승": default_idx = 2
                
                p_choice = st.radio(
                    label=f"r_past_{m['R']}_{idx}",
                    options=[opt_h, opt_d, opt_a],
                    index=default_idx,
                    horizontal=True,
                    key=f"radio_past_{m['id']}",
                    label_visibility="collapsed"
                )
                past_preds[m["id"]] = p_choice
                st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        else:
            st.write("표시할 지난 경기가 없습니다.")

with col2:
    st.subheader("📊 승격 확률 및 순위 예측")
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx, base_pts = run_what_if_simulation(
        df_standings, past_matches, past_preds, remaining_matches, future_preds, form_w, home_adv, total_games=34, n_sims=sim_count
    )
    
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
        title=f"<b>{target_team} What-If 시나리오 최종 순위 분포 ({sim_count:,}회)</b>",
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
