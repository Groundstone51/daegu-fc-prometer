import streamlit as st
import pandas as pd
import base64
import os

st.set_page_config(
    page_title="2026 K리그2 PO 예상 대진표",
    page_icon="🏆",
    layout="wide"
)

LOGO_MAP = {
    "수원 삼성 블루윙즈": "suwon_samsung.png",
    "대구 FC": "daegu.png",
    "수원 FC": "suwon_fc.png",
    "서울 이랜드 FC": "seoul.png",
    "화성 FC": "hwasung.png",
    "부산 아이파크": "busan.png",
    "경남 FC": "gyeongnam.png",
    "김포 FC": "gimpo.png",
    "충남 아산 FC": "chungnamasan.png",
    "성남 FC": "seongnam.png",
    "용인 FC": "yongin.png",
    "충북 청주 FC": "chungbukcheongju.png",
    "파주 프런티어 FC": "paju.png",
    "천안 시티 FC": "cheonan.png",
    "안산 그리너스 FC": "ansan.png",
    "전남 드래곤즈": "jeonnam.png",
    "김해 FC 2008": "gimhae.png"
}

def get_logo_html(team_name, size=24):
    file_name = LOGO_MAP.get(team_name)
    if file_name:
        for path in [file_name, os.path.join("emblem", file_name), os.path.join("..", "emblem", file_name)]:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    return f'<img src="data:image/png;base64,{encoded}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 8px;">'
                except Exception:
                    pass
    return ""

# 현재 상위 순위 예시 (실제 운영 시 app.py와 공통 데이터 모듈로 분리 권장)
standings_data = [
    {"순위": 1, "팀": "수원 삼성 블루윙즈", "경기": 30, "승점": 66, "득실차": "+27"},
    {"순위": 2, "팀": "수원 FC", "경기": 30, "승점": 60, "득실차": "+26"},
    {"순위": 3, "팀": "서울 이랜드 FC", "경기": 30, "승점": 57, "득실차": "+19"},
    {"순위": 4, "팀": 30, "팀": "대구 FC", "경기": 30, "승점": 56, "득실차": "+18"},
    {"순위": 5, "팀": "부산 아이파크", "경기": 30, "승점": 48, "득실차": "+9"},
    {"순위": 6, "팀": "화성 FC", "경기": 31, "승점": 48, "득실차": "+12"},
]
df_top6 = pd.DataFrame(standings_data)

st.title("🏆 2026 K리그2 플레이오프(PO) 예상 대진표")
st.caption("현재 순위 기준 예상 대진이며, 잔여 라운드 결과에 따라 변동될 수 있습니다.")
st.divider()

t1, t2, t3, t4, t5, t6 = [df_top6.loc[i, "팀"] for i in range(6)]

st.info(f"**1위 직행 후보:** {get_logo_html(t1, 20)}**{t1}** &nbsp;|&nbsp; **2위 승격 PO 대기:** {get_logo_html(t2, 20)}**{t2}**", icon="📌")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("1단계 · 준플레이오프(예상)")
    st.markdown(f"**3위 vs 6위**")
    st.markdown(f"{get_logo_html(t3)} **{t3}** vs **{t6}** {get_logo_html(t6)}", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"**4위 vs 5위**")
    st.markdown(f"{get_logo_html(t4)} **{t4}** vs **{t5}** {get_logo_html(t5)}", unsafe_allow_html=True)

with col_b:
    st.subheader("2단계 · 플레이오프(예상)")
    st.markdown("준PO 승자 1 vs 준PO 승자 2")
    st.caption("단판 승부 기준 상위 시드 홈 개최 원칙 적용")

with col_c:
    st.subheader("최종 · 승격 PO")
    st.markdown(f"**2위 ({t2})** vs PO 승자")
    st.caption("K리그1 승강 PO 또는 직행/승격 규정 확인 필요")

st.divider()
st.subheader("현재 PO 진출권(1~6위) 요약")
st.dataframe(df_top6, use_container_width=True, hide_index=True)
