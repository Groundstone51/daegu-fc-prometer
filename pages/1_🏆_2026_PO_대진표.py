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
# 예시 데이터: 두 팀 조합을 sorted([팀A, 팀B]) 튜플 키로 관리
# 형식: {"팀A": 승수, "무": 무승부수, "팀B": 패수(상대 승수)}
SEASON_2026_H2H = {
    tuple(sorted(["서울 이랜드 FC", "화성 FC"])): {"서울 이랜드 FC": 0, "무": 1, "화성 FC": 1},
    tuple(sorted(["대구 FC", "부산 아이파크"])): {"대구 FC": 1, "무": 1, "부산 아이파크": 0},
}

ALL_TIME_H2H = {
    tuple(sorted(["서울 이랜드 FC", "화성 FC"])): {"서울 이랜드 FC": 1, "무": 2, "화성 FC": 1},
    tuple(sorted(["대구 FC", "부산 아이파크"])): {"대구 FC": 8, "무": 5, "부산 아이파크": 6},
}


def calc_win_rate(record_dict, team):
    if not record_dict:
        return None, 0, 0, 0, 0
    w = record_dict.get(team, 0)
    d = record_dict.get("무", 0)
    # 상대 팀 승수 합산
    other_wins = sum(v for k, v in record_dict.items() if k not in (team, "무"))
    total = w + d + other_wins
    if total == 0:
        return None, 0, 0, 0, 0
    rate = (w / total) * 100
    return rate, w, d, other_wins, total


def render_dual_winrate_card(title, team_a, team_b):
    rate_a_26, wa_26, d_26, la_26, tot_26 = calc_win_rate(
        SEASON_2026_H2H.get(tuple(sorted([team_a, team_b]))), team_a
    )
    rate_b_26, wb_26, _, lb_26, _ = calc_win_rate(
        SEASON_2026_H2H.get(tuple(sorted([team_a, team_b]))), team_b
    )

    rate_a_all, wa_all, d_all, la_all, tot_all = calc_win_rate(
        ALL_TIME_H2H.get(tuple(sorted([team_a, team_b]))), team_a
    )
    rate_b_all, wb_all, _, lb_all, _ = calc_win_rate(
        ALL_TIME_H2H.get(tuple(sorted([team_a, team_b]))), team_b
    )

    with st.container(border=True):
        st.markdown(
            f"**{title}:** {get_logo_html(team_a, 18)}**{team_a}** vs **{team_b}** {get_logo_html(team_b, 18)}",
            unsafe_allow_html=True,
        )

        col_s, col_a = st.columns(2)
        with col_s:
            st.markdown("**📅 이번 시즌(2026) 기준**")
            if tot_26 > 0:
                st.caption(f"전적: {tot_26}전 ({team_a} {wa_26}승 {d_26}무 {la_26}패)")
                st.write(f"• **{team_a}** 승률: **{rate_a_26:.1f}%**")
                st.write(f"• **{team_b}** 승률: **{rate_b_26:.1f}%**")
            else:
                st.caption("2026시즌 맞대결 기록 없음")

        with col_a:
            st.markdown("**📚 전체 전적 기준**")
            if tot_all > 0:
                st.caption(f"전적: {tot_all}전 ({team_a} {wa_all}승 {d_all}무 {la_all}패)")
                st.write(f"• **{team_a}** 승률: **{rate_a_all:.1f}%**")
                st.write(f"• **{team_b}** 승률: **{rate_b_all:.1f}%**")
            else:
                st.caption("누적 맞대결 기록 없음")


st.divider()
st.subheader("📈 예상 PO 매치업 상대전적 & 승률 (이번 시즌 / 전체 전적)")
st.caption("※ 승률은 해당 기준 전체 경기 수 대비 승리 비율(승 ÷ 경기수 × 100)로 계산합니다.")

m1, m2 = st.columns(2)
with m1:
    render_dual_winrate_card("준플레이오프1 (3위 vs 6위)", t3, t6)
with m2:
    render_dual_winrate_card("준플레이오프2 (4위 vs 5위)", t4, t5)
