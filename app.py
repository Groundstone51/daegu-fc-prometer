import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 순수 베이지안 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 팀명 표준화 및 엠블럼 매핑
TEAM_NAME_MAP = {
    "수원 삼성": "수원 삼성", "수원 삼성 블루윙즈": "수원 삼성",
    "부산 아이파크": "부산 아이파크",
    "대구 FC": "대구 FC",
    "수원 FC": "수원 FC",
    "서울 이랜드": "서울 이랜드", "서울 이랜드 FC": "서울 이랜드",
    "화성 FC": "화성 FC",
    "김포 FC": "김포 FC",
    "충남 아산": "충남 아산", "충남 아산 FC": "충남 아산",
    "용인 FC": "용인 FC",
    "경남 FC": "경남 FC",
    "파주 프런티어": "파주 프런티어", "파주 프런티어 FC": "파주 프런티어",
    "성남 FC": "성남 FC",
    "안산 그리너스": "안산 그리너스", "안산 그리너스 FC": "안산 그리너스",
    "천안 시티": "천안 시티", "천안 시티 FC": "천안 시티",
    "전남 드래곤즈": "전남 드래곤즈",
    "충북 청주": "충북 청주", "충북 청주 FC": "충북 청주",
    "김해 FC": "김해 FC", "김해 FC 2008": "김해 FC"
}

LOGO_MAP = {
    "수원 삼성": "suwon_samsung.png",
    "부산 아이파크": "busan.png",
    "대구 FC": "daegu.png",
    "수원 FC": "suwon_fc.png",
    "서울 이랜드": "seoul.png",
    "화성 FC": "hwasung.png",
    "김포 FC": "gimpo.png",
    "충남 아산": "chungnamasan.png",
    "용인 FC": "yongin.png",
    "경남 FC": "gyeongnam.png",
    "파주 프런티어": "paju.png",
    "성남 FC": "seongnam.png",
    "안산 그리너스": "ansan.png",
    "천안 시티": "cheonan.png",
    "전남 드래곤즈": "jeonnam.png",
    "충북 청주": "chungbukcheongju.png",
    "김해 FC": "gimhae.png"
}

VENUE_MAP = {
    "수원 삼성": "수원월드컵경기장",
    "부산 아이파크": "부산아시아드주경기장",
    "대구 FC": "DGB대구은행파크",
    "수원 FC": "수원종합운동장",
    "서울 이랜드": "목동종합운동장",
    "화성 FC": "화성종합경기타운",
    "김포 FC": "솔터축구전용구장",
    "충남 아산": "이순신종합운동장",
    "용인 FC": "용인미르스타디움",
    "경남 FC": "창원축구센터",
    "파주 프런티어": "파주스타디움",
    "성남 FC": "탄천종합운동장",
    "안산 그리너스": "안산와~스타디움",
    "천안 시티": "천안종합운동장",
    "전남 드래곤즈": "광양축구전용구장",
    "충북 청주": "청주종합경기장",
    "김해 FC": "김해운동장"
}

def normalize_team(name):
    clean_name = str(name).strip()
    return TEAM_NAME_MAP.get(clean_name, clean_name)

def get_logo_html(team_name, size=22):
    file_name = LOGO_MAP.get(normalize_team(team_name))
    if file_name:
        possible_paths = [file_name, os.path.join("emblem", file_name)]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    return f'<img src="data:image/png;base64,{encoded}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 6px;">'
                except Exception:
                    pass
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

# 4. matches.csv 데이터 파싱 및 정규화
@st.cache_data(ttl=300)
def fetch_data_from_csv(file_path="matches.csv"):
    if not os.path.exists(file_path):
        st.error(f"'{file_path}' 파일이 필요합니다.")
        return pd.DataFrame(), [], []
    
    df_matches = pd.read_csv(file_path)
    
    past_matches = []
    remaining_matches = []
    team_stats = {}

    for idx, row in df_matches.iterrows():
        h = normalize_team(row["홈팀"])
        a = normalize_team(row["원정팀"])
        r_str = str(row.get("라운드", "0라운드"))
        r_num = int(''.join(filter(str.isdigit, r_str)) or 0)
        
        venue = str(row.get("장소", "")) if pd.notna(row.get("장소")) else VENUE_MAP.get(h, f"{h} 홈경기장")
        date_info = str(row.get("날짜", "")) if pd.notna(row.get("날짜")) else f"라운드 {r_num} 예정"
        
        status = str(row.get("경기상태", ""))
        is_finished = (status == "종료") or (pd.notna(row.get("홈팀 점수")) and pd.notna(row.get("원정팀 점수")))
        
        for t in [h, a]:
            if t not in team_stats:
                team_stats[t] = {"팀": t, "승점": 0, "경기수": 0, "득점": 0, "실점": 0}

        if is_finished:
            hs = int(float(row["홈팀 점수"]))
            as_ = int(float(row["원정팀 점수"]))
            
            team_stats[h]["경기수"] += 1
            team_stats[a]["경기수"] += 1
            team_stats[h]["득점"] += hs
            team_stats[h]["실점"] += as_
            team_stats[a]["득점"] += as_
            team_stats[a]["실점"] += hs
            
            if hs > as_:
                team_stats[h]["승점"] += 3
                res_str = "홈승"
            elif hs < as_:
                team_stats[a]["승점"] += 3
                res_str = "원정승"
            else:
                team_stats[h]["승점"] += 1
                team_stats[a]["승점"] += 1
                res_str = "무승부"
                
            past_matches.append({
                "id": str(row.get("id", f"p_{idx}")),
                "R": r_num,
                "날짜": date_info,
                "장소": venue,
                "홈팀": h,
                "원정팀": a,
                "실제홈득점": hs,
                "실제원정득점": as_,
                "실제결과": res_str,
                "내용": str(row.get("내용", f"⚽ 스코어: {h} {hs} - {as_} {a}"))
            })
        else:
            remaining_matches.append({
                "id": str(row.get("id", f"f_{idx}")),
                "R": r_num,
                "날짜": date_info,
                "장소": venue,
                "홈팀": h,
                "원정팀": a
            })

    df_st = pd.DataFrame(list(team_stats.values()))
    df_st["득실차"] = df_st["득점"] - df_st["실점"]
    df_st = df_st.sort_values(by=["승점", "득점", "득실차"], ascending=[False, False, False]).reset_index(drop=True)
    
    return df_st, past_matches, remaining_matches

df_standings, past_matches, remaining_matches = fetch_data_from_csv("matches.csv")

st.title("⚽ K리그2 순수 베이지안 승격 시뮬레이터")
st.caption("🔮 감마-포아송 베이지안 추론(Gamma-Poisson Bayesian Inference) 기반 시뮬레이션")
st.divider()

# 5. 순수 베이지안 몬테카를로 시뮬레이션 엔진
def run_bayesian_simulation(df_base, past_list, past_preds, future_schedule, future_preds, n_sims=5000):
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
    
    prior_alpha, prior_beta = 2.0, 1.5
    
    post_alpha_att = prior_alpha + df['득점'].values
    post_beta_att = prior_beta + games_played
    post_alpha_def = prior_alpha + df['실점'].values
    post_beta_def = prior_beta + games_played

    lambda_att = np.random.gamma(post_alpha_att, 1.0 / post_beta_att, size=(n_sims, n_teams))
    lambda_def = np.random.gamma(post_alpha_def, 1.0 / post_beta_def, size=(n_sims, n_teams))

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
        choice = future_preds.get(m_idx, "🎲 베이지안 추론")
        
        if choice == "🎲 베이지안 추론":
            exp_h = lambda_att[:, h_i] * lambda_def[:, a_i]
            exp_a = lambda_att[:, a_i] * lambda_def[:, h_i]
            
            sim_h = np.random.poisson(exp_h)
            sim_a = np.random.poisson(exp_a)
            
            pts_sim[:, h_i] += np.where(sim_h > sim_a, 3, np.where(sim_h == sim_a, 1, 0))
            pts_sim[:, a_i] += np.where(sim_a > sim_h, 3, np.where(sim_h == sim_a, 1, 0))
            gf_sim[:, h_i] += sim_h
            ga_sim[:, h_i] += sim_a
            gf_sim[:, a_i] += sim_a
            ga_sim[:, a_i] += sim_h
        else:
            if f"🏠 {home_team} 승" in choice:
                pts_sim[:, h_i] += 3
            elif "🔺 무승부" in choice:
                pts_sim[:, h_i] += 1
                pts_sim[:, a_i] += 1
            elif f"✈️ {away_team} 승" in choice:
                pts_sim[:, a_i] += 3

    gd_sim = gf_sim - ga_sim
    rank_matrix = np.zeros((n_sims, n_teams))
    
    for s in range(n_sims):
        scores = [(pts_sim[s, i], gf_sim[s, i], gd_sim[s, i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx, base_pts

# 6. UI 구성
col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.subheader("🗓️ 경기 시나리오 설정")
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측", "🔄 지난 경기 기록 & What-If"])
    
    future_preds = {}
    with tab_future:
        if not remaining_matches:
            st.info("남은 잔여 경기가 없습니다.")
        else:
            fut_rounds = sorted(list(set([m["R"] for m in remaining_matches])))
            for r in fut_rounds:
                with st.expander(f"📌 Round {r} 잔여 경기 목록", expanded=True):
                    r_matches = [m for m in remaining_matches if m["R"] == r]
                    for idx, match in enumerate(r_matches):
                        m_global_idx = remaining_matches.index(match)
                        h_team, a_team = match['홈팀'], match['원정팀']
                        m_date, m_venue = match.get('날짜', ''), match.get('장소', '')
                        
                        st.caption(f"📅 일시: {m_date} | 📍 장소: {m_venue}")
                        
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
                            options=["🎲 베이지안 추론", opt_home, opt_draw, opt_away],
                            horizontal=True,
                            key=f"radio_fut_r{r}_idx{idx}_g{m_global_idx}_{h_team}_vs_{a_team}",
                            label_visibility="collapsed"
                        )
                        future_preds[m_global_idx] = choice
                        st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    past_preds = {}
    with tab_past:
        if not past_matches:
            st.info("조회 가능한 지난 경기 기록이 없습니다.")
        else:
            past_rounds = sorted(list(set([m["R"] for m in past_matches])))
            selected_round = st.selectbox(
                "🔍 조회할 라운드 선택", 
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
                        <b>📝 Round {m['R']} 경기 주요 내용</b><br>
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
                    key=f"radio_past_r{m['R']}_idx{idx}_id{m.get('id', idx)}",
                    label_visibility="collapsed"
                )
                past_preds[m["id"]] = p_choice
                st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

with col2:
    st.subheader("📊 베이지안 승격 확률 및 순위 예측")
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx, base_pts = run_bayesian_simulation(
        df_standings, past_matches, past_preds, remaining_matches, future_preds, n_sims=sim_count
    )
    
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=0)
    target_i = team_idx[target_team]
    target_ranks = rank_matrix[:, target_i]
    
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    total_promotion_p = direct_p + po_p
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{target_team} 1~2위 (직행)", f"{direct_p:.1f}%")
    m2.metric(f"{target_team} 3~6위 (PO)", f"{po_p:.1f}%")
    m3.metric("총 승격 가시권 (1~6위)", f"{total_promotion_p:.1f}%")
    
    rank_df = pd.DataFrame({"예상 최종 순위": target_ranks})
    rank_counts = rank_df["예상 최종 순위"].value_counts().reset_index()
    rank_counts.columns = ["순위", "빈도수"]
    rank_counts = rank_counts.sort_values("순위")
    
    fig = px.bar(
        rank_counts, 
        x="순위", 
        y="빈도수", 
        text="빈도수", 
        title=f"<b>{target_team} 베이지안 사후 최종 순위 분포 ({sim_count:,}회)</b>",
        color_discrete_sequence=["#0085FF"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
