with col1:
    st.subheader("⚙️ 승/무/패 조건 직접 선택")
    
    # 💡 추가된 팀 필터 기능 (전체 팀 중 보고 싶은 팀만 선택)
    all_teams_list = sorted(list(set(matches_df['홈팀']).union(set(matches_df['원정팀']))))
    selected_filter_teams = st.multiselect(
        "🔍 보고 싶은 팀 선택 (선택하지 않으면 전체 표시)",
        options=all_teams_list,
        default=[]
    )
    
    tab_fut, tab_past = st.tabs(["🗓️ 잔여 경기 예측 (27~34R)", "🔄 과거 경기 What-If (1~26R)"])
    
    future_choices = {}
    with tab_fut:
        st.caption("👇 라운드 선택 후 클릭 한 번으로 잔여 경기 승/무/패를 변경하세요.")
        sel_fut_r = st.selectbox("📌 잔여 라운드 선택", options=scheduled_rounds, index=0)
        st.divider()
        
        filtered_fut = scheduled_df[scheduled_df['라운드'] == sel_fut_r]
        
        # 팀 필터 적용
        if selected_filter_teams:
            filtered_fut = filtered_fut[
                filtered_fut['홈팀'].isin(selected_filter_teams) | 
                filtered_fut['원정팀'].isin(selected_filter_teams)
            ]
            
        if filtered_fut.empty:
            st.info("선택한 팀의 해당 라운드 경기가 없습니다.")
        else:
            for _, m in filtered_fut.iterrows():
                f_id = f"{m['라운드']}_{m['홈팀']}_{m['원정팀']}"
                st.markdown(f"**{m['홈팀']} vs {m['원정팀']}** *(📅 {m['날짜']})*")
                choice = st.radio(
                    label=f"fut_radio_{f_id}",
                    options=["🎲 베이지안 자동", f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                    horizontal=True,
                    key=f"fut_{f_id}",
                    label_visibility="collapsed"
                )
                future_choices[f_id] = choice
                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)

    past_choices = {}
    with tab_past:
        st.caption("👇 1~26라운드 실경기 스코어를 확인하고 가상 시나리오를 적용해 보세요.")
        sel_past_r = st.selectbox("📌 과거 라운드 선택", options=completed_rounds, index=len(completed_rounds)-1)
        st.divider()
        
        filtered_past = completed_df[completed_df['라운드'] == sel_past_r]
        
        # 팀 필터 적용
        if selected_filter_teams:
            filtered_past = filtered_past[
                filtered_past['홈팀'].isin(selected_filter_teams) | 
                filtered_past['원정팀'].isin(selected_filter_teams)
            ]
            
        if filtered_past.empty:
            st.info("선택한 팀의 해당 라운드 경기가 없습니다.")
        else:
            for _, m in filtered_past.iterrows():
                m_id = f"{m['라운드']}_{m['홈팀']}_{m['원정팀']}"
                gh, ga = int(m['홈 스코어']), int(m['원정 스코어'])
                st.markdown(f"**{m['홈팀']} {gh} : {ga} {m['원정팀']}** *(📅 {m['날짜']})*")
                choice = st.radio(
                    label=f"past_radio_{m_id}",
                    options=["실제 결과", f"🏠 {m['홈팀']} 승", "🔺 무승부", f"✈️ {m['원정팀']} 승"],
                    horizontal=True,
                    key=f"past_{m_id}",
                    label_visibility="collapsed"
                )
                past_choices[m_id] = choice
                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)
