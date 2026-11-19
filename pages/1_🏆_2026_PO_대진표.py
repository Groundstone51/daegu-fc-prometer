import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os

st.set_page_config(
    page_title="2026 K리그2 PO 예상 대진표",
    page_icon="🏆",
    layout="wide",
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
    "김해 FC 2008": "gimhae.png",
    "광주 FC": "gwangju.png",
}


def get_logo_data_uri(team_name):
    file_name = LOGO_MAP.get(team_name)
    if file_name:
        for path in [
            file_name,
            os.path.join("emblem", file_name),
            os.path.join("..", "emblem", file_name),
        ]:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    return f"data:image/png;base64,{encoded}"
                except Exception:
                    pass
    return ""


def get_logo_html(team_name, size=20):
    uri = get_logo_data_uri(team_name)
    if uri:
        return (
            f'<img src="{uri}" width="{size}" height="{size}" '
            f'style="vertical-align: middle; margin-right: 8px; object-fit: contain;">'
        )
    return ""


def render_bracket_diagram(t3, t4, t5, t6):
    logo3 = get_logo_data_uri(t3)
    logo4 = get_logo_data_uri(t4)
    logo5 = get_logo_data_uri(t5)
    logo6 = get_logo_data_uri(t6)
    logo_gwangju = get_logo_data_uri("광주 FC")

    def img_tag(uri):
        if not uri:
            return ""
        return (
            f'<img src="{uri}" style="width:18px;height:18px;object-fit:contain;'
            f'vertical-align:middle;margin-right:6px;">'
        )

    html = f"""
    <div style="overflow-x:auto; padding:10px 0;">
      <div style="display:flex; align-items:center; gap:20px; min-width:920px; font-family:sans-serif; color:#0f172a;">

        <!-- 1단계: 준플레이오프 -->
        <div style="display:flex; flex-direction:column; gap:18px; width:260px;">
          <div style="font-weight:700; font-size:14px;">1단계 · 준플레이오프 (12/2)</div>

          <div style="border:1px solid #cbd5e1; border-radius:10px; padding:10px 12px; background:#f8fafc;">
            <div style="font-size:11px; color:#475569; font-weight:600; margin-bottom:6px;">
              준플레이오프1 (3위 vs 6위)
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:3px 0; font-size:13px;">
              <span>{img_tag(logo3)}<b>{t3}</b></span>
              <span style="color:#64748b; font-size:12px;">3위</span>
            </div>
            <div style="border-top:1px dashed #cbd5e1; margin:4px 0;"></div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:3px 0; font-size:13px;">
              <span>{img_tag(logo6)}<b>{t6}</b></span>
              <span style="color:#64748b; font-size:12px;">6위</span>
            </div>
          </div>

          <div style="border:1px solid #cbd5e1; border-radius:10px; padding:10px 12px; background:#f8fafc;">
            <div style="font-size:11px; color:#475569; font-weight:600; margin-bottom:6px;">
              준플레이오프2 (4위 vs 5위)
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:3px 0; font-size:13px;">
              <span>{img_tag(logo4)}<b>{t4}</b></span>
              <span style="color:#64748b; font-size:12px;">4위</span>
            </div>
            <div style="border-top:1px dashed #cbd5e1; margin:4px 0;"></div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:3px 0; font-size:13px;">
              <span>{img_tag(logo5)}<b>{t5}</b></span>
              <span style="color:#64748b; font-size:12px;">5위</span>
            </div>
          </div>
        </div>

        <!-- 연결선 1 -> 2 -->
        <svg width="36" height="220" viewBox="0 0 36 220" style="flex-shrink:0; margin-top:24px;">
          <path d="M 0 52 H 18 V 110 H 36" fill="none" stroke="#94a3b8" stroke-width="2"/>
          <path d="M 0 168 H 18 V 110" fill="none" stroke="#94a3b8" stroke-width="2"/>
        </svg>

        <!-- 2단계: 플레이오프 -->
        <div style="display:flex; flex-direction:column; gap:10px; width:275px; margin-top:24px;">
          <div style="font-weight:700; font-size:14px;">2단계 · K리그2 플레이오프 (12/5)</div>
          <div style="border:1.5px solid #3b82f6; border-radius:10px; padding:12px; background:#eff6ff;">
            <div style="font-size:11px; color:#1d4ed8; font-weight:600; margin-bottom:6px;">
              준PO 승자 중 리그 상위팀 vs 하위팀
            </div>
            <div style="padding:4px 0; font-size:13px;"><b>준PO 승자 (리그 상위팀)</b></div>
            <div style="border-top:1px dashed #bfdbfe; margin:4px 0;"></div>
            <div style="padding:4px 0; font-size:13px;"><b>준PO 승자 (리그 하위팀)</b></div>
            <div style="margin-top:8px; font-size:12px; font-weight:700; color:#15803d;">
              승리 팀 → K리그1 승격
            </div>
          </div>
        </div>

        <!-- 연결선 2 -> 3 -->
        <svg width="36" height="120" viewBox="0 0 36 120" style="flex-shrink:0; margin-top:24px;">
          <path d="M 0 60 H 36" fill="none" stroke="#94a3b8" stroke-width="2"/>
        </svg>

        <!-- 최종: 승강 플레이오프 -->
        <div style="display:flex; flex-direction:column; gap:10px; width:285px; margin-top:24px;">
          <div style="font-weight:700; font-size:14px;">최종 · 승강 플레이오프</div>
          <div style="border:1.5px solid #f59e0b; border-radius:10px; padding:12px; background:#fffbeb;">
            <div style="font-size:11px; color:#b45309; font-weight:600; margin-bottom:6px;">
              김천 상무 FC가 K리그1 12위가 아닐 경우 限
            </div>
            <div style="padding:4px 0; font-size:13px;">
              {img_tag(logo_gwangju)}<b>광주</b> <span style="color:#64748b; font-size:12px;">(K리그1 12위)</span>
            </div>
            <div style="border-top:1px dashed #fde68a; margin:4px 0;"></div>
            <div style="padding:4px 0; font-size:13px;">
              <b>K리그2 플레이오프 패자</b>
            </div>
          </div>
        </div>

      </div>
    </div>
    """
    components.html(html, height=285, scrolling=True)


# 현재 상위 순위 예시 (실제 운영 시 app.py와 공통 데이터 모듈로 분리 권장)
standings_data = [
    {"순위": 1, "팀": "수원 삼성 블루윙즈", "경기": 30, "승점": 66, "득실차": "+27"},
    {"순위": 2, "팀": "수원 FC", "경기": 30, "승점": 60, "득실차": "+26"},
    {"순위": 3, "팀": "서울 이랜드 FC", "경기": 30, "승점": 57, "득실차": "+19"},
    {"순위": 4, "팀": "대구 FC", "경기": 30, "승점": 56, "득실차": "+18"},
    {"순위": 5, "팀": "부산 아이파크", "경기": 30, "승점": 48, "득실차": "+9"},
    {"순위": 6, "팀": "화성 FC", "경기": 31, "승점": 48, "득실차": "+12"},
]

df_top6 = pd.DataFrame(standings_data)

st.title("🏆 2026 K리그2 플레이오프(PO) 예상 대진표")
st.caption("현재 순위 기준 예상 대진이며, 잔여 라운드 결과에 따라 변동될 수 있습니다.")
st.divider()

t1, t2, t3, t4, t5, t6 = [df_top6.loc[i, "팀"] for i in range(6)]

with st.container(border=True):
    st.markdown(
        f"🎉 **K리그1 직행 승격 확정권 (1·2위):** &nbsp; "
        f"**1위** {get_logo_html(t1, 20)}**{t1}** &nbsp;|&nbsp; "
        f"**2위** {get_logo_html(t2, 20)}**{t2}**",
        unsafe_allow_html=True,
    )

render_bracket_diagram(t3, t4, t5, t6)

st.divider()
st.subheader("현재 PO 진출권(1~6위) 요약")
st.dataframe(df_top6, use_container_width=True, hide_index=True)
