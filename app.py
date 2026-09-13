# 5. 1라운드부터 전 라운드 경기 일정/결과 크롤링 (API 연동)
@st.cache_data(ttl=300)
def fetch_past_and_future_matches():
    past_matches = []
    remaining_matches = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.kleague.com/schedule/schedule_list.do",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        # K리그2(leagueId: 2) 2026시즌 전체 일정 API 조회
        url = "https://www.kleague.com/api/schedule.do"
        params = {"leagueId": "2", "yearId": "2026"}
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            # K리그 API의 경기 목록 배열 추출
            match_list = data.get("data", []) or data.get("datalist", []) or data.get("list", [])
            
            for m in match_list:
                r_num = int(m.get("MEET_RND", m.get("round", 1)))
                h_team = m.get("HOME_TEAM_NAME", m.get("homeTeamName", ""))
                a_team = m.get("AWAY_TEAM_NAME", m.get("awayTeamName", ""))
                m_date = m.get("GAME_DATE", m.get("gameDate", ""))
                m_venue = m.get("STADIUM_NAME", m.get("stadiumName", ""))
                
                h_score = m.get("HOME_SCORE", m.get("homeScore"))
                a_score = m.get("AWAY_SCORE", m.get("awayScore"))
                
                # 점수가 존재하면 치러진 지난 경기 (1라운드~현재)
                if h_score is not None and a_score is not None and str(h_score).isdigit():
                    h_score = int(h_score)
                    a_score = int(a_score)
                    
                    if h_score > a_score:
                        result_str = "홈승"
                    elif h_score == a_score:
                        result_str = "무승부"
                    else:
                        result_str = "원정승"
                        
                    past_matches.append({
                        "id": f"p_{r_num}_{h_team}_{a_team}",
                        "R": r_num,
                        "날짜": m_date,
                        "장소": m_venue,
                        "홈팀": h_team,
                        "원정팀": a_team,
                        "실제홈득점": h_score,
                        "실제원정득점": a_score,
                        "실제결과": result_str,
                        "내용": f"⚽ 최종 스코어 {h_score} : {a_score}<br>📍 경기장: {m_venue}"
                    })
                else:
                    # 점수가 없으면 잔여 경기
                    remaining_matches.append({
                        "R": r_num,
                        "날짜": m_date,
                        "장소": m_venue,
                        "홈팀": h_team,
                        "원정팀": a_team
                    })
    except Exception as e:
        st.warning(f"일정 불러오기 중 예외 발생: {e}")

    return past_matches, remaining_matches
    
