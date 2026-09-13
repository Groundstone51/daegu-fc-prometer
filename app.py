# -*- coding: utf-8 -*-
"""
K리그2 순위표 크롤러 (헤드리스 브라우저 방식)
------------------------------------------------
- kleague.com 의 순위 페이지는 자바스크립트가 표를 그리기 때문에
  requests + BeautifulSoup 만으로는 빈 표만 나옵니다.
- 그래서 Playwright로 '진짜 브라우저처럼' 페이지를 열고,
  자바스크립트가 표를 다 그린 뒤의 HTML을 읽어옵니다.
- API 주소나 파라미터를 전혀 몰라도 되고, 화면에 보이는 그대로 긁어옵니다.

사전 준비 (최초 1회, 로컬/서버에서):
    pip install playwright beautifulsoup4
    playwright install chromium
    playwright install-deps      # 리눅스 서버라면 필요 (폰트/라이브러리 설치)

주의:
- Streamlit Community Cloud처럼 시스템 패키지 설치 권한이 제한된 호스팅에서는
  playwright install-deps 가 실패할 수 있습니다. 이 경우 requests 기반의
  비공식 JSON 엔드포인트 방식(이전에 드린 kleague_api_probe.py 방향)이
  훨씬 가볍게 동작합니다.
- 표의 실제 class/id 이름을 몰라도 되도록, '헤더 텍스트(순위/클럽/경기/승점...)'
  로 열을 찾는 방식으로 짰습니다. 그래도 사이트 구조가 바뀌면 깨질 수 있으니
  실행 후 반드시 print(df) 로 결과를 한 번 확인하세요.
"""

import re
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

STANDINGS_URL = "https://www.kleague.com/record/team.do?leagueId=2"

# 페이지에 표시되는 컬럼명 -> 우리 데이터프레임에서 쓸 컬럼명
COLUMN_MAP = {
    "순위": "순위",
    "클럽": "팀",
    "경기": "경기수",
    "승점": "승점",
    "승": "승",
    "무": "무",
    "패": "패",
    "득점": "득점",
    "실점": "실점",
    "득실": "득실",
}


def _clean_team_name(text: str) -> str:
    """로고 alt텍스트나 공백이 섞여 들어오는 경우를 대비한 정리."""
    return re.sub(r"\s+", " ", text).strip()


def fetch_kleague2_standings_via_browser(headless: bool = True) -> pd.DataFrame:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        )
        page.goto(STANDINGS_URL, wait_until="networkidle", timeout=30000)

        # 표가 자바스크립트로 채워질 때까지 대기.
        # '전체' 탭 표에 최소 1개 이상의 데이터 행(tr)이 생길 때까지 기다린다.
        page.wait_for_selector("table tbody tr", timeout=15000)

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # 페이지에 표가 여러 개(전체/홈/원정, 파이널 그룹 등) 있을 수 있으므로,
    # 헤더에 '순위'와 '승점'이 동시에 들어있는 첫 번째 표를 찾는다.
    target_table = None
    for table in soup.find_all("table"):
        header_cells = [th.get_text(strip=True) for th in table.find_all("th")]
        if "순위" in header_cells and "승점" in header_cells:
            target_table = table
            header_texts = header_cells
            break

    if target_table is None:
        raise RuntimeError(
            "순위표를 찾지 못했습니다. 사이트 구조가 바뀐 것 같습니다. "
            "브라우저에서 F12 → Elements 로 <table> 구조를 확인해주세요."
        )

    rows = []
    for tr in target_table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue  # 헤더 행
        values = [_clean_team_name(td.get_text(strip=True)) for td in cells]
        if len(values) < len(header_texts):
            continue
        row = dict(zip(header_texts, values))
        rows.append(row)

    if not rows:
        raise RuntimeError("표는 찾았지만 데이터 행이 비어 있습니다.")

    df = pd.DataFrame(rows)
    df = df.rename(columns=COLUMN_MAP)

    # 숫자 컬럼 형변환
    for col in ["순위", "경기수", "승점", "승", "무", "패", "득점", "실점"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 앱의 run_what_if_simulation() 이 기대하는 컬럼 형태로 정리
    #   필요 컬럼: 팀, 승점, 경기수, 득점, 실점, 최근5경기승점
    # '최근 5경기' 는 이 표에는 승/무/패로 안 나오는 경우가 많아
    # 별도 처리(0으로 채우거나, W/D/L 아이콘 셀을 따로 파싱)가 필요합니다.
    if "최근5경기승점" not in df.columns:
        df["최근5경기승점"] = 0  # TODO: '최근 5경기' 셀 안의 승/무/패 아이콘을 파싱해 실제 값으로 교체

    keep_cols = ["팀", "승점", "경기수", "득점", "실점", "최근5경기승점"]
    return df[[c for c in keep_cols if c in df.columns]]


if __name__ == "__main__":
    df = fetch_kleague2_standings_via_browser(headless=True)
    print(df)
    
