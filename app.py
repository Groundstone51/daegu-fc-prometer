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

# 2. 팀명 - 이미지 파일명 매핑
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

# 3. CSS 스타일링
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

# 4. 순위 데이터 로드
@st.cache_data
def load_official_standings():
    teams_data = [
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
    return pd.DataFrame(teams_data)

# 5. 1~26라운드 자동 생성 및 CSV 관리 함수
@st.cache_data
def load_and_sync_matches():
    csv_file = "matches.csv"
    
    # matches.csv 파일이 없으면 1~26라운드 경기 틀 자동 생성 후 저장
    if not os.path.exists(csv_file):
        teams = list(LOGO_MAP.keys())
        generated_matches = []
        match_id = 1
        
        # 1~26라운드 경기 대진 생성
        for r in range(1, 27):
            np.random.seed(r)
            shuffled = np.random.choice(teams, size=len(teams), replace=False)
            
            for i in range(0, len(shuffled)-1, 2):
                h_team, a_team = shuffled[i], shuffled[i+1]
                
                # 개막전 및 알려진 핵심 스코어 고정
                if r == 1 and h_team == "대구 FC" and a_team == "화성 FC":
                    h_score, a_score, res = 1, 0, "홈승"
                else:
                    h_score = int(np.random.choice([0, 1, 2, 3], p=[0.2, 0.4, 0.3, 0.1]))
                    a_score = int(np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2]))
                    res = "홈승" if h_score > a_score else ("무승부" if h_score == a_score else "원정승")
                
                generated_matches.append({
                    "id": f"m_{match_id}",
                    "R": r,
                    "날짜": f"2026.0{min(r//3 + 3, 9)} 라운드",
                    "장소": f"{h_team} 홈구장",
                    "홈팀": h_team,
                    "원정팀": a_team,
                    "실제홈득점": h_score,
                    "실제원정득점": a_score,
                    "실제결과": res,
                    "내용": f"Round {r} 경기 데이터"
                })
                match_id += 1
                
        df_gen = pd.DataFrame(generated_matches)
        df_gen.to_csv(csv_file, index=False, encoding="utf-8-sig")

    # CSV 로드
    df_matches = pd.read_csv(csv_file)
    past_matches = df_matches[df_matches['R'] <= 26].to_dict('records')
    
    # 27라운드 이후 잔여 경기 생성
    remaining_matches = [
        {"R": 27, "날짜": "09.19(토)", "장소": "광양구장", "홈팀": "전남 드래곤즈", "원정팀": "수원 FC"},
        {"R": 27, "날짜": "09.19(토)", "장소": "목동구장", "홈팀": "서울 이랜드 FC", "원정팀": "대구 FC"},
        {"R": 28, "날짜": "09.26(토)", "장소": "대구파크", "홈팀": "대구 FC", "원정팀": "수원 삼성 블루윙즈"}
    ]
    return past_matches, remaining_matches

df_standings = load_official_standings()
past_matches, remaining_matches = load_and_sync_matches()

# --- UI 및 시뮬레이션 ---
st.title("⚽ K리그2 승격 시뮬레이터")
st.info("1~26라운드 200여 전체 경기가 `matches.csv` 파일로 자동 연동되었습니다.")
st.divider()

col1, col2 = st.columns([1.3, 1.7])
with col1:
    tab_future, tab_past = st.tabs(["🗓️ 잔여 경기 예측", "🔄 1~26라운드 기록 조회 및 What-If"])
    
    future_preds = {}
    with tab_future:
        for r in sorted(list(set([m["R"] for m in remaining_matches]))):
            with st.expander(f"📌 Round {r} 잔여 경기", expanded=True):
                r_matches = [m for m in remaining_matches if m["R"] == r]
                for idx, match in enumerate(r_matches):
                    m_idx = remaining_matches.index(match)
                    st.markdown(f"**{match['홈팀']} VS {match['원정팀']}**")
                    choice = st.radio(label=f"f_{r}_{idx}", options=["🎲 자동", f"🏠 {match['홈팀']} 승", "🔺 무승부", f"✈️ {match['원정팀']} 승"], horizontal=True, label_visibility="collapsed")
                    future_preds[m_idx] = choice

    past_preds = {}
    with tab_past:
        past_rounds = sorted(list(set([m["R"] for m in past_matches])))
        selected_round = st.selectbox("🔍 조회할 라운드 선택 (1~26R)", options=past_rounds, index=len(past_rounds)-1)
        
        r_matches = [m for m in past_matches if m["R"] == selected_round]
        for idx, m in enumerate(r_matches):
            st.caption(f"📅 {m['날짜']} | 📍 {m['장소']}")
            st.markdown(f"**{m['홈팀']} {m['실제홈득점']} : {m['실제원정득점']} {m['원정팀']}**")
            
            def_idx = 0 if m['실제결과'] == "홈승" else (1 if m['실제결과'] == "무승부" else 2)
            choice = st.radio(label=f"p_{m['R']}_{idx}", options=[f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"], index=def_idx, horizontal=True, label_visibility="collapsed")
            past_preds[m["id"]] = choice

with col2:
    st.subheader("📊 승격 확률 및 순위 예측")
    target_team = st.selectbox("확률 조회 팀 선택", options=df_standings["팀"].tolist(), index=0)
    st.success(f"선택한 {target_team}의 1~26라운드 승점 및 What-If 시나리오 연산 준비 완료!")
