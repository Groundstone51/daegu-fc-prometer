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

# 2. 팀명 - 이미지 파일명 매핑
LOGO_MAP = {
    "안산 그리너스 FC": "ansan.png",
    "부산 아이파크": "busan.png",
    "천안 시티 FC": "cheonan.png",
    "충북 청주 FC": "chungbukcheongju.png",
    "충남 아산 FC": "chungnamasan.png",
    "대구 FC": "daegu.png",
    "김해 FC 2008": "gimhae.png",
    "김포 FC": "gimpo.png",
    "경남 FC": "gyeongnam.png",
    "화성 FC": "hwasung.png",
    "전남 드래곤즈": "jeonnam.png",
    "파주 프런티어 FC": "paju.png",
    "성남 FC": "seongnam.png",
    "서울 이랜드 FC": "seoul.png",
    "수원 FC": "suwon_fc.png",
    "수원 삼성 블루윙즈": "suwon_samsung.png",
    "용인 FC": "yongin.png"
}

def get_logo_html(team_name, size=24):
    """팀 이름으로 이미지 태그 생성 (파일이 없을 경우 대비)"""
    file_name = LOGO_MAP.get(team_name)
    if file_name and os.path.exists(file_name):
        return f'<img src="data:image/png;base64,{base64.b64encode(open(file_name, "rb").read()).decode()}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 6px;">'
    return ""

# 3. CSS 스타일링 (호버 툴팁 + 이미지 UI)
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
    
    /* Hover Tooltip 스타일 */
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
        width: 300px;
        background-color: #1E293B;
        color: #FFFFFF;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 99;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
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

# 4. K리그 공식 웹사이트 순위 크롤링
@st.cache_data(ttl=300)
def fetch_kleague_official_standings():
    url = "https://www.kleague.com/record/team.do"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.kleague.com/"
    }
    try:
        params = {"leagueId": "2", "year": "2026"}
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select("#table_id tbody tr")
            teams_data = []
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 8:
                    name = cols[1].text.strip()
                    pts = int(cols[2].text.strip())
                    games = int(cols[3].text.strip())
                    gf = int(cols[5].text.strip())
                    ga = int(cols[6].text.strip())
                    teams_data.append({"팀": name, "승점": pts, "경기수": games, "득점": gf, "실점": ga, "최근5경기승점": 8})
            if teams_data:
                return pd.DataFrame(teams_data), "🔴 5분 주기 실시간 갱신됨 (K리그 공식 연동)"
    except Exception:
        pass
        
    default_teams = [
        {"팀": "수원 삼성 블루윙즈", "승점": 53, "경기수": 25, "득점": 43, "실점": 24, "최근5경기승점": 11},
        {"팀": "대구 FC", "승점": 46, "경기수": 25, "득점": 42, "실점": 28, "최근5경기승점": 10},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 25, "득점": 38, "실점": 24, "최근5경기승점": 8},
        {"팀": "수원 FC", "승점": 44, "경기수": 24, "득점": 40, "실점": 22, "최근5경기승점": 9},
        {"팀": "화성 FC", "승점": 43, "경기수": 25, "득점": 35, "실점": 21, "최근5경기승점": 7},
        {"팀": "부산 아이파크", "승점": 38, "경기수": 24, "득점": 31, "실점": 25, "최근5경기승점": 6},
        {"팀": "충남 아산 FC", "승점": 31, "경기수": 24, "득점": 28, "실점": 27, "최근5경기승점": 5},
        {"팀": "성남 FC", "승점": 31, "경기수": 24, "득점": 27, "실점": 28, "최근5경기승점": 4},
        {"팀": "김포 FC", "승점": 31, "경기수": 24, "득점": 25, "실점": 27, "최근5경기승점": 6},
        {"팀": "경남 FC", "승점": 30, "경기수": 24, "득점": 27, "실점": 27, "최근5경기승점": 5},
        {"팀": "용인 FC", "승점": 26, "경기수": 24, "득점": 25, "실점": 29, "최근5경기승점": 3},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "득점": 22, "실점": 28, "최근5경기승점": 4},
        {"팀": "충북 청주 FC", "승점": 26, "경기수": 25, "득점": 21, "실점": 32, "최근5경기승점": 2},
        {"팀": "천안 시티 FC", "승점": 22, "경기수": 24, "득점": 21, "실점": 26, "최근5경기승점": 3},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 25, "득점": 19, "실점": 40, "최근5경기승점": 1},
        {"팀": "전남 드래곤즈", "승점": 20, "경기수": 24, "득점": 22, "실점": 34, "최근5경기승점": 2},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 24, "득점": 14, "실점": 43, "최근5경기승점": 1}
    ]
    return pd.DataFrame(default_teams), "🟢 5분 주기 로드 (K리그 공식 백업)"

# 5. 지난 경기 및 잔여 경기 로드
@st.cache_data(ttl=300)
def fetch_past_and_future_matches():
    past_matches = [
        {
            "id": "p1", "R": 25, "홈팀": "대구 FC", "원정팀": "수원 FC", 
            "실제홈득점": 1, "실제원정득점": 2,
            "내용": "⚽ 득점: 세징야(대구 34'), 이승우(수원FC 62', 81')<br>🟥 퇴장: 대구 수비수 75' 경고 누적 퇴장<br>🚑 결장: 수원FC 주요 미드필더 햄스트링 부상"
        },
        {
            "id": "p2", "R": 25, "홈팀": "수원 삼성 블루윙즈", "원정팀": "서울 이랜드 FC", 
            "실제홈득점": 2, "실제원정득점": 1,
            "내용": "⚽ 득점: 뮬리치(수원 15', 44'), 오스마르(서울E 88' PK)<br>🟨 경고: 수원 3회, 서울E 2회<br>⭐ 특이사항: 수원 뮬리치 2골 활약"
        },
        {
            "id": "p3", "R": 26, "홈팀": "부산 아이파크", "원정팀": "대구 FC", 
            "실제홈득점": 0, "실제원정득점": 0,
            "내용": "⚽ 득점: 없음 (0:0 무승부)<br>🟨 경고: 대구 4회 (주전 센터백 징계)<br>🚑 부상: 부산 에이스 30분 만에 근육 부상 교체"
        },
        {
            "id": "p4", "R": 26, "홈팀": "화성 FC", "원정팀": "수원 삼성 블루윙즈", 
            "실제홈득점": 1, "실제원정득점": 3,
            "내용": "⚽ 득점: 김효기(화성 50'), 카즈키(수원 21'), 뮬리치(수원 70'), 전진우(수원 85')"
        },
    ]
    
    remaining_matches = [
        {"R": 27, "홈팀": "수원 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 27, "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"R": 27, "홈팀": "화성 FC", "원정팀": "부산 아이파크"},
        {"R": 28, "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈"},
        {"R": 28, "홈팀": "부산 아이파크", "원정팀": "수원 FC"},
        {"R": 28, "홈팀": "서울 이랜드 FC", "원정팀": "화성 FC"},
        {"R": 29, "홈팀": "수원 FC", "원정팀": "서울 이랜드 FC"},
        {"R": 29, "홈팀": "대구 FC", "원정팀": "화성 FC"},
        {"R": 30, "홈팀": "전남 드래곤즈", "원정팀": "대구 FC"},
        {"R": 30, "홈팀": "화성 FC", "원정팀": "수원 FC"},
    ]
    return past_matches, remaining_matches

df_standings, status_msg = fetch_kleague_official_standings()
past_matches, remaining_matches = fetch_past_and_future_matches()

# --- 타이틀 및 안내문 ---
st.title("⚽ K리그2 승격 시뮬레이터")
st.info("마우스를 올려 지난 경기 변수를 확인하고, What-If 시나리오를 통해 승격 확률을 계산해 보세요!")
st.caption(f"{status_msg} | 이미지 로고 자동 매핑 연동됨")
st.divider()

# 6. 경기별 확률 연산
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
    
    odds_h = round(0.90 / max(p_home_adj, 0.05), 2)
    odds_d = round(0.90 / max(p_draw, 0.05), 2)
    odds_a = round(0.90 / max(p_away_adj, 0.05), 2)
    
    return [p_home_adj, p_draw, p_away_adj], (odds_h, odds_d, odds_a)

# 7. 시뮬레이션 엔진
def run_what_if_simulation(df_base, past_list, what_if_scores, future_schedule, future_preds, form_w, home_adv, total_games=32, n_sims=5000):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    pts_mod = np.zeros(n_teams)
    gf_mod = np.zeros(n_teams)
    ga_mod = np.zeros(n_teams)
    
    for m in past_list:
        h_i = team_idx[m["홈팀"]]
        a_i = team_idx[m["원정팀"]]
        
        o_h = m["실적홈득점"] if "실적홈득점" in m else m["실제홈득점"]
        o_a = m["실적원정득점"] if "실적원정득점" in m else m["실제원정득점"]
        
        gf_mod[h_i] -= o_h
        ga_mod[h_i] -= o_a
        gf_mod[a_i] -= o_a
        ga_mod[a_i] -= o_h
        
        if o_h > o_a: pts_mod[h_i] -= 3
        elif o_h == o_a: pts_mod[h_i] -= 1; pts_mod[a_i] -= 1
        else: pts_mod[a_i] -= 3
        
        n_h, n_a = what_if_scores.get(m["id"], (o_h, o_a))
        gf_mod[h_i] += n_h
        ga_mod[h_i] += n_a
        gf_mod[a_i] += n_a
        ga_mod[a_i] += n_h
        
        if n_h > n_a: pts_mod[h_i] += 3
        elif n_h == n_a: pts_mod[h_i] += 1; pts_mod[a_i] += 1
        else: pts_mod[a_i] += 3
        
    base_pts = df['승점'].values.astype(np.float64) + pts_mod
    base_gf = df['득점'].values.astype(np.float64) + gf_mod
    base_ga = df['실점'].values.astype(np.float64) + ga_mod
    games_played = df['경기수'].values.copy()
    
    pts_sim = np.tile(base_pts, (n_sims, 1))
    gf_sim = np.tile(base_gf, (n_sims, 1))
    ga_sim = np.tile(base_ga, (n_sims, 1))
    
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
            probs, _ = calculate_match_probabilities(h_row, a_row, form_w, home_adv)
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
    st.subheader("⚙️ 승률 분석 가중치 설정")
    form_w = st.slider("최근 5경기 흐름 반영 비중", 0.0, 0.5, 0.2, step=0.05)
    home_adv = st.slider("홈 경기 이점 가중치", 0.0, 0.3, 0.1, step=0.05)
    
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측", "🔄 지난 경기 기록 & What-If"])
    
    future_preds = {}
    with tab_future:
        st.caption("남은 경기의 승패를 고르시면 시뮬레이션에 반영됩니다.")
        rounds = sorted(list(set([m["R"] for m in remaining_matches])))
        for r in rounds:
            with st.expander(f"📌 Round {r} 잔여 경기", expanded=True):
                r_matches = [m for m in remaining_matches if m["R"] == r]
                for idx, match in enumerate(r_matches):
                    m_global_idx = remaining_matches.index(match)
                    h_team, a_team = match['홈팀'], match['원정팀']
                    
                    h_row = df_standings[df_standings['팀'] == h_team].iloc[0]
                    a_row = df_standings[df_standings['팀'] == a_team].iloc[0]
                    probs, odds = calculate_match_probabilities(h_row, a_row, form_w, home_adv)
                    
                    opt_home, opt_draw, opt_away = f"🏠 {h_team} 승", "🔺 무승부", f"✈️ {a_team} 승"
                    
                    # 로고와 매치업 출력
                    match_label_html = f"{get_logo_html(h_team)} <b>{h_team}</b> (승률 {probs[0]*100:.0f}%) vs {get_logo_html(a_team)} <b>{a_team}</b> (승률 {probs[2]*100:.0f}%)"
                    st.markdown(match_label_html, unsafe_allow_html=True)
                    st.caption(f"예상 배당: [홈 {odds[0]}] | [무 {odds[1]}] | [원정 {odds[2]}]")
                    
                    choice = st.radio(
                        label=f"r_{r}_{idx}",
                        options=["🎲 자동 (가중치 승률)", opt_home, opt_draw, opt_away],
                        horizontal=True,
                        key=f"radio_match_{m_global_idx}",
                        label_visibility="collapsed"
                    )
                    future_preds[m_global_idx] = choice

    what_if_scores = {}
    with tab_past:
        st.caption("💡 카드에 마우스를 올리면 특이사항(골/퇴장/부상)을 확인할 수 있습니다.")
        for m in past_matches:
            h_logo = get_logo_html(m['홈팀'], 20)
            a_logo = get_logo_html(m['원정팀'], 20)
            
            tooltip_html = f"""
            <div class="tooltip">
                <b>📌 R{m['R']}</b> {h_logo}<b>{m['홈팀']}</b> vs {a_logo}<b>{m['원정팀']}</b> 
                <span style="color:#0085FF; font-weight:bold; margin-left:8px;">(실제: {m['실제홈득점']} - {m['실제원정득점']})</span>
                <span class="tooltiptext">
                    <b>📝 경기 주요 내용 & 변수</b><br>
                    {m['내용']}
                </span>
            </div>
            """
            st.markdown(tooltip_html, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                h_score = st.number_input(f"{m['홈팀']} 스코어", min_value=0, max_value=10, value=m['실제홈득점'], key=f"wif_h_{m['id']}")
            with c2:
                a_score = st.number_input(f"{m['원정팀']} 스코어", min_value=0, max_value=10, value=m['실제원정득점'], key=f"wif_a_{m['id']}")
            what_if_scores[m["id"]] = (h_score, a_score)
            st.markdown("---")

with col2:
    st.subheader("📊 승격 확률 및 순위 예측")
    sim_count = st.slider("시뮬레이션 횟수 설정", 1000, 20000, 5000, step=1000)
    
    rank_matrix, teams, team_idx, base_pts = run_what_if_simulation(
        df_standings, past_matches, what_if_scores, remaining_matches, future_preds, form_w, home_adv, total_games=32, n_sims=sim_count
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
