python
# -*- coding: utf-8 -*-
"""
K리그2 What-if 순위 시뮬레이터
============================================================

기능
------------------------------------------------------------
1. K리그 공식 홈페이지에서 현재 K리그2 순위 자동 수집
2. 현재 순위표 표시
3. 사용자가 남은 경기 결과 입력
4. 입력된 경기 결과를 기반으로 최종 순위 계산
5. 현재 순위 vs 예상 순위 비교
6. 순위 상승/하락 표시
7. 결과에 따른 승점 / 경기수 / 승 / 무 / 패 반영
8. 득점 / 실점까지 입력하면 득실차까지 반영
9. CSV 다운로드

실행
------------------------------------------------------------
pip install streamlit pandas beautifulsoup4 playwright

playwright install chromium

streamlit run app.py

Linux 서버라면:
playwright install-deps chromium


주의
------------------------------------------------------------
K League 홈페이지의 HTML 구조가 변경될 경우
크롤러 부분을 수정해야 할 수 있습니다.
"""

import re
from typing import Optional

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


# ============================================================
# 설정
# ============================================================

STANDINGS_URL = (
    "https://www.kleague.com/record/team.do?leagueId=2"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ============================================================
# 페이지 컬럼명
# ============================================================

COLUMN_MAP = {
    "순위": "순위",
    "클럽": "팀",
    "경기": "경기수",
    "출장": "경기수",
    "승점": "승점",
    "승": "승",
    "무": "무",
    "패": "패",
    "득점": "득점",
    "실점": "실점",
    "득실": "득실",
    "최근 5경기": "최근5경기",
}


# ============================================================
# 공통 함수
# ============================================================

def clean_text(text: str) -> str:
    """문자열 공백 정리."""

    if text is None:
        return ""

    return re.sub(r"\s+", " ", str(text)).strip()


# ============================================================
# 최근 5경기
# ============================================================

def normalize_result(value: str) -> Optional[str]:
    """
    승/무/패를 W/D/L로 변환
    """

    if not value:
        return None

    value = clean_text(value).lower()

    if value in {"승", "win", "w", "won"}:
        return "W"

    if value in {"무", "draw", "d", "drawn"}:
        return "D"

    if value in {"패", "loss", "l", "lose", "lost"}:
        return "L"

    return None


def parse_recent_5_results(td) -> list[str]:
    """
    최근 5경기 셀에서 W/D/L 추출.
    """

    results = []

    # --------------------------------------------------------
    # 1. 텍스트
    # --------------------------------------------------------

    text = clean_text(
        td.get_text(" ", strip=True)
    )

    korean_results = re.findall(
        r"[승무패]",
        text
    )

    for result in korean_results:

        normalized = normalize_result(result)

        if normalized:
            results.append(normalized)

    if results:
        return results[-5:]

    # --------------------------------------------------------
    # 2. img / span / i 등
    # --------------------------------------------------------

    for element in td.find_all(
        ["img", "span", "i", "em", "strong"]
    ):

        candidates = [
            element.get("alt", ""),
            element.get("title", ""),
            element.get("aria-label", ""),
        ]

        for candidate in candidates:

            normalized = normalize_result(candidate)

            if normalized:
                results.append(normalized)
                break

    if results:
        return results[-5:]

    # --------------------------------------------------------
    # 3. class
    # --------------------------------------------------------

    for element in td.find_all(True):

        classes = element.get("class", [])

        if isinstance(classes, str):
            classes = [classes]

        class_text = " ".join(classes).lower()

        if any(
            x in class_text
            for x in ["win", "victory", "success"]
        ):
            results.append("W")

        elif any(
            x in class_text
            for x in ["draw", "tie"]
        ):
            results.append("D")

        elif any(
            x in class_text
            for x in ["loss", "lose", "defeat"]
        ):
            results.append("L")

    return results[-5:]


def calculate_recent_points(
    results: list[str]
) -> int:

    points = {
        "W": 3,
        "D": 1,
        "L": 0,
    }

    return sum(
        points.get(result, 0)
        for result in results
    )


# ============================================================
# 순위표 찾기
# ============================================================

def find_standings_table(soup):

    candidates = []

    for table in soup.find_all("table"):

        headers = [
            clean_text(
                th.get_text(
                    " ",
                    strip=True
                )
            )
            for th in table.find_all("th")
        ]

        header_set = set(headers)

        score = 0

        if "순위" in header_set:
            score += 3

        if "클럽" in header_set:
            score += 3

        if "승점" in header_set:
            score += 3

        if "경기" in header_set:
            score += 1

        if "득점" in header_set:
            score += 1

        if "실점" in header_set:
            score += 1

        if score >= 6:
            candidates.append(
                (
                    score,
                    table,
                    headers
                )
            )

    if not candidates:
        return None, None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    _, table, headers = candidates[0]

    return table, headers


# ============================================================
# 테이블 파싱
# ============================================================

def parse_table(
    table,
    headers
) -> list[dict]:

    rows = []

    for tr in table.find_all("tr"):

        cells = tr.find_all("td")

        if not cells:
            continue

        if len(cells) < len(headers):
            continue

        row = {}

        for index, header in enumerate(headers):

            if index >= len(cells):
                break

            value = clean_text(
                cells[index].get_text(
                    " ",
                    strip=True
                )
            )

            normalized_header = COLUMN_MAP.get(
                header,
                header
            )

            row[normalized_header] = value

        # ----------------------------------------------------
        # 최근 5경기
        # ----------------------------------------------------

        recent_index = None

        for index, header in enumerate(headers):

            if header == "최근 5경기":
                recent_index = index
                break

        if recent_index is not None:

            recent_results = parse_recent_5_results(
                cells[recent_index]
            )

            row["최근5경기"] = (
                "".join(recent_results)
            )

            row["최근5경기승점"] = (
                calculate_recent_points(
                    recent_results
                )
            )

        rows.append(row)

    return rows


# ============================================================
# DataFrame 정리
# ============================================================

def normalize_dataframe(
    df: pd.DataFrame
) -> pd.DataFrame:

    if df.empty:
        raise RuntimeError(
            "순위표 데이터가 비어 있습니다."
        )

    if "팀" not in df.columns:
        raise RuntimeError(
            "팀 컬럼을 찾지 못했습니다."
        )

    # 숫자 컬럼
    numeric_columns = [
        "순위",
        "경기수",
        "승점",
        "승",
        "무",
        "패",
        "득점",
        "실점",
        "득실",
        "최근5경기승점",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # 필요한 기본 컬럼 보정
    defaults = {
        "경기수": 0,
        "승점": 0,
        "승": 0,
        "무": 0,
        "패": 0,
        "득점": 0,
        "실점": 0,
        "득실": 0,
        "최근5경기": "",
        "최근5경기승점": 0,
    }

    for column, default in defaults.items():

        if column not in df.columns:
            df[column] = default

        df[column] = (
            df[column]
            .fillna(default)
        )

    # 팀명
    df["팀"] = (
        df["팀"]
        .astype(str)
        .map(clean_text)
    )

    # 필요한 컬럼
    columns = [
        "팀",
        "승점",
        "경기수",
        "승",
        "무",
        "패",
        "득점",
        "실점",
        "득실",
        "최근5경기",
        "최근5경기승점",
    ]

    if "순위" in df.columns:
        columns.insert(0, "순위")

    return df[columns].copy()


# ============================================================
# K리그 순위 가져오기
# ============================================================

@st.cache_data(ttl=300)
def fetch_kleague2_standings() -> pd.DataFrame:
    """
    K리그2 현재 순위 가져오기.
    5분 동안 캐시.
    """

    with sync_playwright() as p:

        browser = None

        try:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page(
                user_agent=USER_AGENT,
                viewport={
                    "width": 1440,
                    "height": 1000,
                },
                locale="ko-KR",
            )

            page.goto(
                STANDINGS_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # table 대기
            try:

                page.wait_for_selector(
                    "table",
                    timeout=15000
                )

            except PlaywrightTimeoutError:

                page.wait_for_timeout(5000)

            # JS 렌더링 대기
            page.wait_for_timeout(2000)

            # 실제 순위표 렌더링 대기
            try:

                page.wait_for_function(
                    """
                    () => {
                        const tables =
                            document.querySelectorAll("table");

                        for (const table of tables) {

                            const text =
                                table.innerText || "";

                            if (
                                text.includes("순위") &&
                                text.includes("승점") &&
                                text.includes("클럽")
                            ) {
                                return true;
                            }
                        }

                        return false;
                    }
                    """,
                    timeout=15000
                )

            except PlaywrightTimeoutError:
                pass

            html = page.content()

        finally:

            if browser is not None:
                browser.close()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table, headers = find_standings_table(
        soup
    )

    if table is None:

        with open(
            "kleague_debug.html",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(html)

        raise RuntimeError(
            "K리그 순위표를 찾지 못했습니다. "
            "kleague_debug.html을 확인해주세요."
        )

    rows = parse_table(
        table,
        headers
    )

    if not rows:
        raise RuntimeError(
            "순위표 데이터 행이 없습니다."
        )

    df = pd.DataFrame(rows)

    df = normalize_dataframe(df)

    # --------------------------------------------------------
    # 현재 순위 계산
    # --------------------------------------------------------

    df = sort_standings(df)

    return df


# ============================================================
# 순위 정렬
# ============================================================

def sort_standings(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    승점 → 득실차 → 득점 순으로 정렬.

    실제 K리그 동률 처리 규정의 모든 세부 항목을
    완전히 구현하는 것이 아니라,
    What-if 시뮬레이션용 기본 정렬을 담당한다.
    """

    result = df.copy()

    # 득실차 계산
    result["득실"] = (
        pd.to_numeric(
            result["득점"],
            errors="coerce"
        ).fillna(0)
        -
        pd.to_numeric(
            result["실점"],
            errors="coerce"
        ).fillna(0)
    )

    result = result.sort_values(
        by=[
            "승점",
            "득실",
            "득점",
        ],
        ascending=[
            False,
            False,
            False,
        ],
        kind="mergesort",
    ).reset_index(
        drop=True
    )

    result["순위"] = (
        result.index + 1
    )

    return result


# ============================================================
# 경기 결과 적용
# ============================================================

def apply_match_result(
    standings: pd.DataFrame,
    home_team: str,
    away_team: str,
    result: str,
    home_goals: Optional[int] = None,
    away_goals: Optional[int] = None,
) -> pd.DataFrame:
    """
    한 경기 결과를 순위표에 반영한다.

    result:
        홈팀 승
        무승부
        원정팀 승
    """

    df = standings.copy()

    home_idx = df.index[
        df["팀"] == home_team
    ]

    away_idx = df.index[
        df["팀"] == away_team
    ]

    if len(home_idx) == 0:
        raise ValueError(
            f"홈팀을 찾을 수 없습니다: {home_team}"
        )

    if len(away_idx) == 0:
        raise ValueError(
            f"원정팀을 찾을 수 없습니다: {away_team}"
        )

    home_idx = home_idx[0]
    away_idx = away_idx[0]

    # 경기수 증가
    df.loc[
        home_idx,
        "경기수"
    ] += 1

    df.loc[
        away_idx,
        "경기수"
    ] += 1

    # --------------------------------------------------------
    # 결과
    # --------------------------------------------------------

    if result == "홈팀 승":

        df.loc[
            home_idx,
            "승"
        ] += 1

        df.loc[
            away_idx,
            "패"
        ] += 1

        df.loc[
            home_idx,
            "승점"
        ] += 3

    elif result == "무승부":

        df.loc[
            home_idx,
            "무"
        ] += 1

        df.loc[
            away_idx,
            "무"
        ] += 1

        df.loc[
            home_idx,
            "승점"
        ] += 1

        df.loc[
            away_idx,
            "승점"
        ] += 1

    elif result == "원정팀 승":

        df.loc[
            away_idx,
            "승"
        ] += 1

        df.loc[
            home_idx,
            "패"
        ] += 1

        df.loc[
            away_idx,
            "승점"
        ] += 3

    else:

        raise ValueError(
            f"잘못된 경기 결과: {result}"
        )

    # --------------------------------------------------------
    # 득점/실점
    # --------------------------------------------------------

    if (
        home_goals is not None
        and away_goals is not None
    ):

        df.loc[
            home_idx,
            "득점"
        ] += home_goals

        df.loc[
            home_idx,
            "실점"
        ] += away_goals

        df.loc[
            away_idx,
            "득점"
        ] += away_goals

        df.loc[
            away_idx,
            "실점"
        ] += home_goals

    return df


# ============================================================
# What-if 시뮬레이션
# ============================================================

def run_what_if_simulation(
    standings: pd.DataFrame,
    matches: list[dict],
) -> pd.DataFrame:
    """
    현재 순위에서 사용자가 입력한 모든 경기 결과를
    순차적으로 적용하여 최종 순위를 계산한다.

    matches 예시:

    [
        {
            "home": "팀A",
            "away": "팀B",
            "result": "홈팀 승",
            "home_goals": 2,
            "away_goals": 0,
        }
    ]
    """

    result_df = standings.copy()

    # 원래 순위 저장
    original_rank = (
        result_df
        .set_index("팀")["순위"]
        .to_dict()
    )

    # 경기 결과 순차 적용
    for match in matches:

        result_df = apply_match_result(
            standings=result_df,
            home_team=match["home"],
            away_team=match["away"],
            result=match["result"],
            home_goals=match.get(
                "home_goals"
            ),
            away_goals=match.get(
                "away_goals"
            ),
        )

    # 최종 순위 계산
    result_df = sort_standings(
        result_df
    )

    # --------------------------------------------------------
    # 순위 변동
    # --------------------------------------------------------

    result_df["기존순위"] = (
        result_df["팀"]
        .map(original_rank)
    )

    result_df["순위변동"] = (
        result_df["기존순위"]
        -
        result_df["순위"]
    )

    return result_df


# ============================================================
# Streamlit UI
# ============================================================

st.set_page_config(
    page_title="K리그2 What-if 시뮬레이터",
    page_icon="⚽",
    layout="wide",
)


# ============================================================
# 제목
# ============================================================

st.title(
    "⚽ K리그2 What-if 순위 시뮬레이터"
)

st.caption(
    "현재 K리그2 순위에서 원하는 경기 결과를 입력하면 "
    "예상 최종 순위를 계산합니다."
)


# ============================================================
# 데이터 로딩
# ============================================================

with st.spinner(
    "K리그2 현재 순위를 가져오는 중..."
):

    try:

        standings = fetch_kleague2_standings()

    except Exception as e:

        st.error(
            "K리그2 순위를 가져오지 못했습니다."
        )

        st.exception(e)

        st.stop()


# ============================================================
# 사이드바
# ============================================================

with st.sidebar:

    st.header("시뮬레이션")

    st.write(
        f"현재 {len(standings)}개 팀을 불러왔습니다."
    )

    if st.button(
        "🔄 순위 새로고침",
        use_container_width=True
    ):

        fetch_kleague2_standings.clear()

        st.rerun()


# ============================================================
# 현재 순위
# ============================================================

st.subheader(
    "현재 K리그2 순위"
)

current_display = standings.copy()

current_display["득실차"] = (
    current_display["득점"]
    -
    current_display["실점"]
)

current_display = current_display[
    [
        "순위",
        "팀",
        "경기수",
        "승",
        "무",
        "패",
        "득점",
        "실점",
        "득실차",
        "승점",
        "최근5경기",
        "최근5경기승점",
    ]
]

st.dataframe(
    current_display,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# 경기 입력
# ============================================================

st.divider()

st.subheader(
    "경기 결과 입력"
)

st.write(
    "예상하고 싶은 경기의 결과를 입력하세요. "
    "여러 경기를 입력할 수 있습니다."
)


# 세션 상태
if "matches" not in st.session_state:
    st.session_state.matches = []


# ============================================================
# 경기 입력 폼
# ============================================================

with st.form(
    "match_form",
    clear_on_submit=False
):

    col1, col2, col3 = st.columns(
        [2, 2, 2]
    )

    team_names = standings[
        "팀"
    ].tolist()

    with col1:

        home_team = st.selectbox(
            "홈팀",
            team_names,
            key="home_team"
        )

    with col2:

        away_options = [
            team
            for team in team_names
            if team != home_team
        ]

        away_team = st.selectbox(
            "원정팀",
            away_options,
            key="away_team"
        )

    with col3:

        match_result = st.selectbox(
            "경기 결과",
            [
                "홈팀 승",
                "무승부",
                "원정팀 승",
            ],
            key="match_result"
        )

    st.write(
        "선택사항: 스코어까지 입력하면 "
        "득실차에도 반영됩니다."
    )

    score_col1, score_col2 = st.columns(2)

    with score_col1:

        use_score = st.checkbox(
            "스코어 입력",
            key="use_score"
        )

    home_goals = None
    away_goals = None

    if use_score:

        score1, score2 = st.columns(2)

        with score1:

            home_goals = st.number_input(
                "홈팀 득점",
                min_value=0,
                max_value=30,
                value=1,
                step=1,
                key="home_goals"
            )

        with score2:

            away_goals = st.number_input(
                "원정팀 득점",
                min_value=0,
                max_value=30,
                value=0,
                step=1,
                key="away_goals"
            )

    submitted = st.form_submit_button(
        "➕ 경기 추가",
        use_container_width=True
    )


# ============================================================
# 경기 추가
# ============================================================

if submitted:

    # --------------------------------------------------------
    # 같은 팀 검사
    # --------------------------------------------------------

    if home_team == away_team:

        st.error(
            "홈팀과 원정팀은 같을 수 없습니다."
        )

    else:

        # ----------------------------------------------------
        # 스코어와 결과 일치 검사
        # ----------------------------------------------------

        score_valid = True

        if use_score:

            if (
                match_result == "홈팀 승"
                and home_goals <= away_goals
            ):
                score_valid = False

            elif (
                match_result == "무승부"
                and home_goals != away_goals
            ):
                score_valid = False

            elif (
                match_result == "원정팀 승"
                and away_goals <= home_goals
            ):
                score_valid = False

        if not score_valid:

            st.error(
                "입력한 경기 결과와 스코어가 일치하지 않습니다."
            )

        else:

            # ------------------------------------------------
            # 중복 경기 검사
            # ------------------------------------------------

            duplicate = False

            for existing in st.session_state.matches:

                same_match = (
                    existing["home"] == home_team
                    and existing["away"] == away_team
                )

                reverse_match = (
                    existing["home"] == away_team
                    and existing["away"] == home_team
                )

                if same_match or reverse_match:

                    duplicate = True
                    break

            if duplicate:

                st.warning(
                    "이미 입력한 경기입니다."
                )

            else:

                st.session_state.matches.append(
                    {
                        "home": home_team,
                        "away": away_team,
                        "result": match_result,
                        "home_goals": (
                            int(home_goals)
                            if use_score
                            else None
                        ),
                        "away_goals": (
                            int(away_goals)
                            if use_score
                            else None
                        ),
                    }
                )

                st.success(
                    f"{home_team} vs {away_team} "
                    f"경기가 추가되었습니다."
                )


# ============================================================
# 입력 경기 목록
# ============================================================

if st.session_state.matches:

    st.divider()

    st.subheader(
        "입력한 경기"
    )

    match_rows = []

    for index, match in enumerate(
        st.session_state.matches
    ):

        if (
            match["home_goals"] is not None
            and match["away_goals"] is not None
        ):

            score = (
                f'{match["home_goals"]}'
                f' : '
                f'{match["away_goals"]}'
            )

        else:

            score = "-"

        match_rows.append(
            {
                "번호": index + 1,
                "홈팀": match["home"],
                "원정팀": match["away"],
                "결과": match["result"],
                "스코어": score,
            }
        )

    st.dataframe(
        pd.DataFrame(match_rows),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # 삭제
    # --------------------------------------------------------

    delete_col1, delete_col2 = st.columns(
        [3, 1]
    )

    with delete_col1:

        delete_index = st.selectbox(
            "삭제할 경기",
            options=range(
                len(
                    st.session_state.matches
                )
            ),
            format_func=lambda x:
                (
                    f'{x + 1}. '
                    f'{st.session_state.matches[x]["home"]}'
                    f' vs '
                    f'{st.session_state.matches[x]["away"]}'
                ),
        )

    with delete_col2:

        if st.button(
            "🗑 삭제",
            use_container_width=True
        ):

            st.session_state.matches.pop(
                delete_index
            )

            st.rerun()

    if st.button(
        "🗑 모든 경기 삭제",
        use_container_width=True
    ):

        st.session_state.matches = []

        st.rerun()


# ============================================================
# 시뮬레이션
# ============================================================

st.divider()

st.subheader(
    "최종 순위 시뮬레이션"
)

if not st.session_state.matches:

    st.info(
        "아직 입력한 경기가 없습니다. "
        "위에서 예상 경기 결과를 추가하세요."
    )

else:

    if st.button(
        "⚽ 최종 순위 계산",
        type="primary",
        use_container_width=True
    ):

        try:

            simulation = run_what_if_simulation(
                standings=standings,
                matches=st.session_state.matches,
            )

            st.session_state.simulation = (
                simulation
            )

        except Exception as e:

            st.error(
                "시뮬레이션 중 오류가 발생했습니다."
            )

            st.exception(e)


# ============================================================
# 시뮬레이션 결과
# ============================================================

if "simulation" in st.session_state:

    simulation = (
        st.session_state.simulation
    )

    st.divider()

    st.subheader(
        "📊 예상 최종 순위"
    )

    # --------------------------------------------------------
    # 순위 변동 표시 함수
    # --------------------------------------------------------

    def format_rank_change(value):

        if value > 0:
            return f"▲ {value}"

        if value < 0:
            return f"▼ {abs(value)}"

        return "-"

    result_display = simulation.copy()

    result_display["순위변동표시"] = (
        result_display["순위변동"]
        .apply(format_rank_change)
    )

    result_display["득실차"] = (
        result_display["득점"]
        -
        result_display["실점"]
    )

    result_display = result_display[
        [
            "순위",
            "팀",
            "기존순위",
            "순위변동표시",
            "경기수",
            "승",
            "무",
            "패",
            "득점",
            "실점",
            "득실차",
            "승점",
        ]
    ]

    st.dataframe(
        result_display,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # 순위 변동 요약
    # --------------------------------------------------------

    st.subheader(
        "순위 변동"
    )

    movement = simulation[
        [
            "팀",
            "기존순위",
            "순위",
            "순위변동",
            "승점",
        ]
    ].copy()

    movement["변동"] = (
        movement["순위변동"]
        .apply(format_rank_change)
    )

    movement = movement[
        [
            "팀",
            "기존순위",
            "순위",
            "변동",
            "승점",
        ]
    ]

    st.dataframe(
        movement,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # 가장 많이 올라간 팀
    # --------------------------------------------------------

    max_up = simulation[
        "순위변동"
    ].max()

    max_down = simulation[
        "순위변동"
    ].min()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "입력 경기 수",
            len(
                st.session_state.matches
            )
        )

    with col2:

        if max_up > 0:

            team = simulation.loc[
                simulation["순위변동"].idxmax(),
                "팀"
            ]

            st.metric(
                "최대 상승",
                team,
                f"▲ {max_up}위"
            )

        else:

            st.metric(
                "최대 상승",
                "-"
            )

    with col3:

        if max_down < 0:

            team = simulation.loc[
                simulation["순위변동"].idxmin(),
                "팀"
            ]

            st.metric(
                "최대 하락",
                team,
                f"▼ {abs(max_down)}위"
            )

        else:

            st.metric(
                "최대 하락",
                "-"
            )

    # --------------------------------------------------------
    # CSV 다운로드
    # --------------------------------------------------------

    csv_data = simulation.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        "⬇️ 예상 순위 CSV 다운로드",
        data=csv_data,
        file_name="kleague2_what_if_result.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# 안내
# ============================================================

st.divider()

with st.expander(
    "ℹ️ 시뮬레이션 계산 방식"
):

    st.markdown(
        """
### 승점

- 승리: +3점
- 무승부: +1점
- 패배: +0점

### 경기 기록

입력한 경기마다 다음 항목이 자동으로 변경됩니다.

- 경기수
- 승
- 무
- 패
- 승점

### 득실차

스코어를 입력한 경우:

- 득점
- 실점
- 득실차

까지 함께 계산합니다.

스코어를 입력하지 않은 경우에는
승점과 경기 기록만 변경됩니다.

### 순위 정렬

기본적으로 다음 순서로 정렬합니다.

1. 승점
2. 득실차
3. 득점

따라서 같은 승점인 팀은 득실차와 득점에 따라
순위가 바뀝니다.

※ 실제 K리그 공식 순위 결정에는 동률 시 추가적인
세부 기준이 적용될 수 있으므로, 이 시뮬레이터는
What-if 분석용으로 사용하세요.
"""
    )

