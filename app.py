import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

# 2. 팀명 - 이미지 및 홈 경기장 매핑
LOGO_MAP = {
    "안산 그리너스": "ansan.png", "안산 그리너스 FC": "ansan.png",
    "부산 아이파크": "busan.png",
    "천안 시티": "cheonan.png", "천안 시티 FC": "cheonan.png",
    "충북 청주": "chungbukcheongju.png", "충북 청주 FC": "chungbukcheongju.png",
    "충남 아산": "chungnamasan.png", "충남 아산 FC": "chungnamasan.png",
    "대구 FC": "daegu.png",
    "김해 FC": "gimhae.png", "김해 FC 2008": "gimhae.png",
    "김포 FC": "gimpo.png",
    "경남 FC": "gyeongnam.png",
    "화성 FC": "hwasung.png",
    "전남 드래곤즈": "jeonnam.png",
    "파주 프런티어": "paju.png", "파주 프런티어 FC": "paju.png",
    "성남 FC": "seongnam.png",
    "서울 이랜드": "seoul.png", "서울 이랜드 FC": "seoul.png",
    "수원 FC": "suwon_fc.png",
    "수원 삼성": "suwon_samsung.png", "수원 삼성 블루윙즈": "suwon_samsung.png",
    "용인 FC": "yongin.png"
}

VENUE_MAP = {
    "수원 삼성": "수원월드컵경기장", "수원 삼성 블루윙즈": "수원월드컵경기장",
    "부산 아이파크": "부산아시아드주경기장",
    "대구 FC": "DGB대구은행파크",
    "수원 FC": "수원종합운동장",
    "서울 이랜드": "목동종합운동장", "서울 이랜드 FC": "목동종합운동장",
    "화성 FC": "화성종합경기타운",
    "김포 FC": "솔터축구전용구장",
    "충남 아산": "이순신종합운동장", "충남 아산 FC": "이순신종합운동장",
    "용인 FC": "용인미르스타디움",
    "경남 FC": "창원축구센터",
    "파주 프런티어": "파주스타디움", "파주 프런티어 FC": "파주스타디움",
    "성남 FC": "탄천종합운동장",
    "안산 그리너스": "안산와~스타디움", "안산 그리너스 FC": "안산와~스타디움",
    "천안 시티": "천안종합운동장", "천안 시티 FC": "천안종합운동장",
    "전남 드래곤즈": "광양축구전용구장",
    "충북 청주": "청주종합경기장", "충북 청주 FC": "청주종합경기장",
    "김해 FC": "김해운동장", "김해 FC 2008": "김해운동장"
}

def get_logo_html(team_name, size=22):
    """팀 이름으로 이미지 태그 생성"""
    file_name = LOGO_MAP.get(team_name)
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

# 4. matches.csv 로드 및 순정 순위 산출
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
        h = str(row["홈팀"]).strip()
        a = str(row["원정팀"]).strip()
        r_str = str(row.get("라운드", "0라운드"))
        r_num = int(''.join(filter(str.isdigit, r_str)) or 0)
        
        venue = str(row.get("장소", "")) if pd.notna(row.get("장소")) else VENUE_MAP.get(h, f"{h} 홈경기장")
        date_info = str(row.get("날짜", "")) if pd.notna(row.get("날짜")) else f"라운드 {r_num} 예정"
        
        status = str(row.get("경기상태", ""))
        is_finished = (status == "종료") or (pd.notna(row.get("홈팀 점수")) and pd.notna(row.get("원정팀 점수")))
        
        for t in [h, a]:
            if t not in team_stats:
                team_stats[t] = {"팀": t, "승점": 0, "경기수": 0, "득점": 0, "실점": 0, "최근5경기승점": 0, "최근경기결과": []}

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
                team_stats[h]["최근경기결과"].append(3)
                team_stats[a]["최근경기결과"].append(0)
                res_str = "홈승"
            elif hs < as_:
                team_stats[a]["승점"] += 3
                team_stats[a]["최근경기결과"].append(3)
                team_stats[h]["최근경기결과"].append(0)
                res_str = "원정승"
            else:
                team_stats[h]["승점"] += 1
                team_stats[a]["승점"] += 1
                team_stats[h]["최근경기결과"].append(1)
                team_stats[a]["최근경기결과"].append(1)
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

    for t in team_stats:
        team_stats[t]["최근5경기승점"] = sum(team_stats[t]["최근경기결과"][-5:])

    df_st = pd.DataFrame(list(team_stats.values()))
    df_st["득실차"] = df_st["득점"] - df_st["실점"]
    df_st = df_st.sort_values(by=["승점", "득점", "득실차"], ascending=[False, False, False]).reset_index(drop=True)
    
    return df_st, past_matches, remaining_matches

df_standings, past_matches, remaining_matches = fetch_data_from_csv("matches.csv")

# --- 타이틀 ---
st.title("⚽ K리그2 승격 시뮬레이터")
st.info("마우스를 올려 지난 경기 변수를 확인하고, What-If 시나리오를 통해 승격 확률을 계산해 보세요!")
st.caption("🔴 CSV 기반 실시간 연동 | K리그2 규정 적용 (1~2위 직행, 3~6위 PO)")
st.divider()

# 5. 경기 확률 연산 함수
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

# 6. 시뮬레이션 엔진
def run_what_if_simulation(df_base, past_list, past_preds, future_schedule, future_preds, form_w, home_adv, total_games=32, n_sims=5000):
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
        # 순위 결정 정렬: 승점 -> 득점 -> 득실차
        scores = [(pts_sim[s, i], gf_sim[s, i], gd_sim[s, i], i) for i in range(n_teams)]
        scores.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        for rank, item in enumerate(scores, start=1):
            rank_matrix[s, item[3]] = rank

    return rank_matrix, teams, team_idx, base_pts

# 7. 레이아웃
col1, col2 = st.columns([1.3, 1.7])

with col1:
    tooltip_header_html = """
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <h3 style="margin: 0; padding: 0; font-size: 1.3rem; font-weight: 700;">⚙️ 승률 분석 가중치 설정</h3>
        <div class="tooltip" style="display: inline-block; width: auto; margin-left: 8px; padding: 0; border: none; background: none;">
            <span style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 50%; background-color: #E2E8F0; color: #475569; font-size: 0.8rem; font-weight: bold; cursor: pointer;">?</span>
            <span class="tooltiptext" style="width: 300px; left: 50%; margin-left: -150px;">
                <b>💡 승률 분석 가중치란?</b><br>
                시뮬레이션 시 각 팀의 승리 확률을 계산할 때 <b>최근 흐름</b>과 <b>홈 이점</b>을 반영하는 조절값입니다.
            </span>
        </div>
    </div>
    """
    st.markdown(tooltip_header_html, unsafe_allow_html=True)
    
    form_w = st.slider("최근 5경기 흐름 반영 비중", 0.0, 0.5, 0.2, step=0.05)
    home_adv = st.slider("홈 경기 이점 가중치", 0.0, 0.3, 0.1, step=0.05)
    
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측", "🔄 지난 경기 기록 & What-If"])
    
    future_preds = {}
    with tab_future:
        if not remaining_matches:
            st.info("남은 잔여 경기가 없습니다.")
        else:
            st.caption("라운드별 경기의 승패를 선택해 시뮬레이션에 반영할 수 있습니다.")
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
                            options=["🎲 자동 (가중치 승률)", opt_home, opt_draw, opt_away],
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
            st.caption("💡 지난 경기를 선택하여 What-If 승점을 변경해 보세요.")
            
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
    st.subheader("📊 승격 확률 및 순위 예측")
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx, base_pts = run_what_if_simulation(
        df_standings, past_matches, past_preds, remaining_matches, future_preds, form_w, home_adv, total_games=32, n_sims=sim_count
    )
    
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=0)
    target_i = team_idx[target_team]
    target_ranks = rank_matrix[:, target_i]
    
    # K리그2 규정: 1~2위 직행 승격, 3~6위 PO권
    direct_p = (np.sum(target_ranks <= 2) / sim_count) * 100
    po_p = (np.sum((target_ranks >= 3) & (target_ranks <= 6)) / sim_count) * 100
    total_promotion_p = direct_p + po_p
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{target_team} 1~2위 (직행 승격)", f"{direct_p:.1f}%")
    m2.metric(f"{target_team} 3~6위 (PO권)", f"{po_p:.1f}%")
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
        title=f"<b>{target_team} What-If 시나리오 최종 순위 분포 ({sim_count:,}회)</b>",
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
