import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import math
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 결정론적 경기력 기반 승격 예측기",
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

# 3. 26R 기준 경기력 스탯 데이터셋 (xG/xGA 기반)
@st.cache_data
def get_performance_league_data():
    standings = [
        {"팀": "수원 삼성 블루윙즈", "승점": 56, "경기수": 26, "승": 17, "무": 5, "패": 4, "득점": 44, "실점": 24, "xG": 46.2, "xGA": 22.8, "최근5경기승점": 13},
        {"팀": "대구 FC", "승점": 49, "경기수": 26, "승": 15, "무": 4, "패": 7, "득점": 45, "실점": 29, "xG": 43.8, "xGA": 27.5, "최근5경기승점": 10},
        {"팀": "화성 FC", "승점": 46, "경기수": 26, "승": 13, "무": 7, "패": 6, "득점": 37, "실점": 21, "xG": 38.1, "xGA": 22.0, "최근5경기승점": 10},
        {"팀": "서울 이랜드 FC", "승점": 45, "경기수": 26, "승": 13, "무": 6, "패": 7, "득점": 38, "실점": 25, "xG": 40.5, "xGA": 24.1, "최근5경기승점": 8},
        {"팀": "수원 FC", "승점": 45, "경기수": 25, "승": 13, "무": 6, "패": 6, "득점": 41, "실점": 23, "xG": 42.0, "xGA": 25.4, "최근5경기승점": 9},
        {"팀": "부산 아이파크", "승점": 41, "경기수": 25, "승": 12, "무": 5, "패": 8, "득점": 33, "실점": 25, "xG": 35.4, "xGA": 26.2, "최근5경기승점": 7},
        {"팀": "경남 FC", "승점": 33, "경기수": 25, "승": 9, "무": 6, "패": 10, "득점": 28, "실점": 27, "xG": 30.2, "xGA": 28.1, "최근5경기승점": 8},
        {"팀": "김포 FC", "승점": 32, "경기수": 25, "승": 8, "무": 8, "패": 9, "득점": 27, "실점": 29, "xG": 29.5, "xGA": 30.0, "최근5경기승점": 6},
        {"팀": "충남 아산 FC", "승점": 31, "경기수": 25, "승": 8, "무": 7, "패": 10, "득점": 28, "실점": 28, "xG": 29.0, "xGA": 27.8, "최근5경기승점": 4},
        {"팀": "성남 FC", "승점": 31, "경기수": 25, "승": 8, "무": 7, "패": 10, "득점": 27, "실점": 29, "xG": 28.6, "xGA": 30.5, "최근5경기승점": 4},
        {"팀": "충북 청주 FC", "승점": 29, "경기수": 26, "승": 7, "무": 8, "패": 11, "득점": 22, "실점": 32, "xG": 23.5, "xGA": 33.2, "최근5경기승점": 5},
        {"팀": "용인 FC", "승점": 26, "경기수": 25, "승": 6, "무": 8, "패": 11, "득점": 26, "실점": 32, "xG": 27.1, "xGA": 31.8, "최근5경기승점": 3},
        {"팀": "파주 프런티어 FC", "승점": 26, "경기수": 24, "승": 6, "무": 8, "패": 10, "득점": 22, "실점": 28, "xG": 24.0, "xGA": 29.0, "최근5경기승점": 4},
        {"팀": "천안 시티 FC", "승점": 23, "경기수": 25, "승": 5, "무": 8, "패": 12, "득점": 22, "실점": 27, "xG": 23.8, "xGA": 28.5, "최근5경기승점": 3},
        {"팀": "안산 그리너스 FC", "승점": 22, "경기수": 26, "승": 5, "무": 7, "패": 14, "득점": 19, "실점": 42, "xG": 21.0, "xGA": 41.5, "최근5경기승점": 1},
        {"팀": "전남 드래곤즈", "승점": 21, "경기수": 25, "승": 4, "무": 9, "패": 12, "득점": 24, "실점": 36, "xG": 26.3, "xGA": 37.0, "최근5경기승점": 3},
        {"팀": "김해 FC 2008", "승점": 13, "경기수": 25, "승": 2, "무": 7, "패": 16, "득점": 14, "실점": 45, "xG": 16.5, "xGA": 44.0, "최근5경기승점": 1}
    ]
    
    h2h_index = {
        ("전남 드래곤즈", "수원 FC"): 0.85, ("충남 아산 FC", "천안 시티 FC"): 1.15,
        ("서울 이랜드 FC", "대구 FC"): 0.95, ("김포 FC", "부산 아이파크"): 0.90,
        ("수원 삼성 블루윙즈", "경남 FC"): 1.25, ("부산 아이파크", "전남 드래곤즈"): 1.10
    }
    
    past_matches = [
        {"id": "r26_1", "R": 26, "날짜": "09.12(토)", "장소": "목동종합", "홈팀": "서울 이랜드 FC", "원정팀": "수원 삼성 블루윙즈", "실제홈득점": 0, "실제원정득점": 1, "실제결과": "원정승", "내용": "⚽ 두비츠카스 9' 결승골"},
        {"id": "r26_2", "R": 26, "날짜": "09.12(토)", "장소": "대구파크", "홈팀": "대구 FC", "원정팀": "용인 FC", "실제홈득점": 3, "실제원정득점": 1, "실제결과": "홈승", "내용": "⚽ 세징야 멀티골"},
        {"id": "r26_5", "R": 26, "날짜": "09.13(일)", "장소": "창원축구센터", "홈팀": "경남 FC", "원정팀": "성남 FC", "실제홈득점": 1, "실제원정득점": 0, "실제결과": "홈승", "내용": "⚽ 경남 FC 1:0 성남 제압"},
        {"id": "r26_8", "R": 26, "날짜": "09.13(일)", "장소": "부산구덕", "홈팀": "부산 아이파크", "원정팀": "김해 FC 2008", "실제홈득점": 2, "실제원정득점": 0, "실제결과": "홈승", "내용": "⚽ 부산 2:0 완승"}
    ]
    
    remaining_matches = [
        {"R": 27, "날짜": "09.19(토) 16:30", "장소": "광양전용구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 FC"},
        {"R": 27, "날짜": "09.19(토) 16:30", "장소": "아산이순신구장", "홈팀": "충남 아산 FC", "원정팀": "천안 시티 FC"},
        {"R": 27, "날짜": "09.19(토) 19:00", "장소": "김포솔터구장", "홈팀": "김포 FC", "원정팀": "부산 아이파크"},
        {"R": 27, "날짜": "09.19(토) 19:00", "장소": "목동종합운동장", "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"R": 28, "날짜": "10.09(금) 14:00", "장소": "청주종합운동장", "홈팀": "충북 청주 FC", "원정팀": "성남 FC"},
        {"R": 28, "날짜": "10.10(토) 16:30", "장소": "빅버드", "홈팀": "수원 삼성 블루윙즈", "원정팀": "안산 그리너스 FC"},
        {"R": 34, "날짜": "11.29(일) 15:00", "장소": "광양전용구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 삼성 블루윙즈"}
    ]
    return pd.DataFrame(standings), h2h_index, past_matches, remaining_matches

df_standings, h2h_index, past_matches, remaining_matches = get_performance_league_data()

# 4. 포아송 확률 산출 함수 (결정론적 계산)
def calculate_poisson_expected_points(lambda_h, lambda_a, max_goals=8):
    k = np.arange(max_goals)
    # P(X = k) = (lambda^k * exp(-lambda)) / k!
    fact = np.array([math.factorial(i) for i in range(max_goals)])
    pmf_h = (lambda_h**k) * np.exp(-lambda_h) / fact
    pmf_a = (lambda_a**k) * np.exp(-lambda_a) / fact
    
    grid = np.outer(pmf_h, pmf_a) # grid[i, j] = 홈 i골, 원정 j골 확률
    
    p_win = float(np.sum(np.tril(grid, -1)))
    p_draw = float(np.sum(np.diag(grid)))
    p_loss = float(np.sum(np.triu(grid, 1)))
    
    total = p_win + p_draw + p_loss
    p_win, p_draw, p_loss = p_win/total, p_draw/total, p_loss/total
    
    exp_pts_h = 3.0 * p_win + 1.0 * p_draw
    exp_pts_a = 3.0 * p_loss + 1.0 * p_draw
    
    return exp_pts_h, exp_pts_a, p_win, p_draw, p_loss

# 5. 결정론적 승점 계산 연산 엔진
def run_deterministic_prediction(df_base, h2h_dict, past_list, past_preds, future_schedule, future_preds, form_w, h2h_w, home_adv, total_games=34):
    df = df_base.copy()
    teams = df['팀'].values
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    
    pts_calc = df['승점'].values.astype(np.float64)
    games_played = df['경기수'].values.copy()
    total_xg = df['xG'].values.astype(np.float64)
    total_xga = df['xGA'].values.astype(np.float64)
    recent_5_pts = df['최근5경기승점'].values.astype(np.float64)
    
    # Past Match What-If 반영
    for m in past_list:
        if m["홈팀"] not in team_idx or m["원정팀"] not in team_idx: continue
        h_i, a_i = team_idx[m["홈팀"]], team_idx[m["원정팀"]]
        o_h, o_a = int(m["실제홈득점"]), int(m["실제원정득점"])
        
        if o_h > o_a: pts_calc[h_i] -= 3
        elif o_h == o_a: pts_calc[h_i] -= 1; pts_calc[a_i] -= 1
        else: pts_calc[a_i] -= 3
        
        p_choice = past_preds.get(m["id"], f"🏠 {m['홈팀']} 승")
        if f"🏠 {m['홈팀']} 승" in p_choice:
            pts_calc[h_i] += 3; total_xg[h_i] += 1.8; total_xga[a_i] += 1.8
        elif "🔺 무승부" in p_choice:
            pts_calc[h_i] += 1; pts_calc[a_i] += 1; total_xg[h_i] += 1.0; total_xga[h_i] += 1.0; total_xg[a_i] += 1.0; total_xga[a_i] += 1.0
        elif f"✈️ {m['원정팀']} 승" in p_choice:
            pts_calc[a_i] += 3; total_xg[a_i] += 1.8; total_xga[h_i] += 1.8

    # 팀별 경기당 평균 공격력/수비 불안도 계산
    avg_att = total_xg / np.maximum(games_played, 1)
    avg_def = total_xga / np.maximum(games_played, 1)
    league_avg_xg = np.mean(avg_att)
    
    norm_att = avg_att / max(league_avg_xg, 0.1)
    norm_def = avg_def / max(league_avg_xg, 0.1)
    form_factor = 1.0 + form_w * ((recent_5_pts / 15.0) - 0.5)
    
    match_details = []
    
    # Future Schedule 기대 승점 계산
    for m_idx, match in enumerate(future_schedule):
        h_t, a_t = match["홈팀"], match["원정팀"]
        if h_t not in team_idx or a_t not in team_idx: continue
        h_i, a_i = team_idx[h_t], team_idx[a_t]
        choice = future_preds.get(m_idx, "🤖 결정론적 승점 자동 계산")
        
        if choice == "🤖 결정론적 승점 자동 계산":
            h2h_val = h2h_dict.get((h_t, a_t), 1.0)
            h2h_h = 1.0 + h2h_w * (h2h_val - 1.0)
            h2h_a = 1.0 - h2h_w * (h2h_val - 1.0)
            
            lambda_h = (norm_att[h_i] * norm_def[a_i]) * league_avg_xg * form_factor[h_i] * h2h_h * (1 + home_adv)
            lambda_a = (norm_att[a_i] * norm_def[h_i]) * league_avg_xg * form_factor[a_i] * h2h_a
            
            exp_h, exp_a, p_win, p_draw, p_loss = calculate_poisson_expected_points(lambda_h, lambda_a)
            
            pts_calc[h_i] += exp_h
            pts_calc[a_i] += exp_a
            match_details.append({
                "홈팀": h_t, "원정팀": a_t, "홈기대득점": round(lambda_h, 2), "원정기대득점": round(lambda_a, 2),
                "홈승률": f"{p_win*100:.1f}%", "무승부": f"{p_draw*100:.1f}%", "원정승률": f"{p_loss*100:.1f}%",
                "홈기대승점": round(exp_h, 2), "원정기대승점": round(exp_a, 2)
            })
        else:
            if f"🏠 {h_t} 승" in choice: pts_calc[h_i] += 3.0
            elif "🔺 무승부" in choice: pts_calc[h_i] += 1.0; pts_calc[a_i] += 1.0
            elif f"✈️ {a_t} 승" in choice: pts_calc[a_i] += 3.0
            match_details.append({"홈팀": h_t, "원정팀": a_t, "선택": choice})
            
        games_played[h_i] += 1
        games_played[a_i] += 1

    # 미정 남아있는 기타 잔여 경기 기대 승점 반영
    for i in range(n_teams):
        rem = total_games - games_played[i]
        if rem > 0:
            lambda_h = norm_att[i] * 1.0 * league_avg_xg * form_factor[i] * (1 + home_adv * 0.5)
            lambda_a = 1.0 * norm_def[i] * league_avg_xg
            exp_h, _, _, _, _ = calculate_poisson_expected_points(lambda_h, lambda_a)
            pts_calc[i] += exp_h * rem

    result_df = pd.DataFrame({
        "팀명": teams,
        "예상최종승점": np.round(pts_calc, 1),
        "현재xG": np.round(total_xg, 1),
        "현재xGA": np.round(total_xga, 1),
        "득실차": np.round(total_xg - total_xga, 1)
    }).sort_values(by=["예상최종승점", "득실차"], ascending=False).reset_index(drop=True)
    
    result_df["예상순위"] = result_df.index + 1
    return result_df, pd.DataFrame(match_details)

# --- UI 레이아웃 ---
st.title("⚽ K리그2 경기력 기반 결정론적 승격 예측기")
st.info("난수 기반 몬테카를로를 제거하고 경기력 스탯(xG, xGA, 최근 기세, 상대 전적)으로부터 기대 승점(xPts)을 직접 계산합니다.")
st.divider()

col1, col2 = st.columns([1.3, 1.7])

with col1:
    st.markdown("### ⚙️ 경기력 스탯 가중치 조절")
    form_w = st.slider("🔥 최근 5경기 기세(Form) 반영 비중", 0.0, 0.5, 0.25, step=0.05)
    h2h_w = st.slider("⚔️ 상대 전적(H2H) 반영 비중", 0.0, 0.5, 0.20, step=0.05)
    home_adv = st.slider("🏟️ 홈 경기 이점 가중치", 0.0, 0.3, 0.10, step=0.05)
    st.divider()
    
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측 (What-If)", "🔄 경기 기록 & What-If"])
    
    future_preds = {}
    with tab_future:
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
                        options=["🤖 결정론적 승점 자동 계산", f"🏠 {h_team} 승", "🔺 무승부", f"✈️ {a_team} 승"],
                        horizontal=True, key=f"radio_fut_{m_global_idx}", label_visibility="collapsed"
                    )
                    future_preds[m_global_idx] = choice

    past_preds = {}
    with tab_past:
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
    st.subheader("📊 경기력 기반 최종 순위 산출표")
    
    result_df, match_df = run_deterministic_prediction(
        df_standings, h2h_index, past_matches, past_preds, remaining_matches, future_preds,
        form_w, h2h_w, home_adv, total_games=34
    )
    
    # 1~2위(직행 승격), 3~6위(플레이오프) 라벨 부여
    def get_status(rank):
        if rank <= 2: return "🟢 1~2위 (직행 승격)"
        elif rank <= 6: return "🔵 3~6위 (PO 진출)"
        else: return "⚪ 잔류"
        
    result_df["승격 가시권"] = result_df["예상순위"].apply(get_status)
    
    st.dataframe(
        result_df[["예상순위", "팀명", "예상최종승점", "승격 가시권", "현재xG", "현재xGA", "득실차"]],
        use_container_width=True,
        hide_index=True
    )
    
    st.subheader("📈 상위권 팀 예상 최종 승점 비교")
    fig = px.bar(
        result_df.head(8),
        x="팀명", y="예상최종승점", text="예상최종승점",
        color="예상순위",
        color_continuous_scale="Blues_r",
        title="<b>상위 8개 팀 예상 최종 승점 (xPts 기준)</b>"
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
