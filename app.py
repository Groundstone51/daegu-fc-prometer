import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson
import matplotlib.pyplot as plt
import seaborn as sns

# Set Page Config
st.set_page_config(
    page_title="대구 FC 승격 가능성 예측 시스템",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (unsafe_allow_html=True 로 수정 완료)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0A3663;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #0A3663;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Data Loading with Caching & Column Cleaning
@st.cache_data
def load_data(csv_path='matches.csv'):
    df = pd.read_csv(csv_path)
    # 컬럼명에 불필요한 따옴표(') 및 양끝 공백 제거
    df.columns = df.columns.str.replace("'", "").str.replace('"', '').str.strip()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"matches.csv 파일을 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# Separate Finished & Remaining Matches
finished_df = df[df['경기상태'] == '종료'].copy()
remaining_df = df[df['경기상태'] != '종료'].copy()

teams = sorted(df['홈팀'].dropna().unique())
n_teams = len(teams)
t2i = {t: i for i, t in enumerate(teams)}

# Bayesian Poisson Model Fitting
@st.cache_data
def fit_bayesian_poisson_model(df_finished, prior_std=1.0):
    home_idx = df_finished['홈팀'].map(t2i).values
    away_idx = df_finished['원정팀'].map(t2i).values
    h_goals = df_finished['홈팀 점수'].values
    a_goals = df_finished['원정팀 점수'].values
    
    n_params = 2 + 2 * n_teams
    
    def neg_log_posterior(params):
        mu = params[0]
        h_adv = params[1]
        att = params[2:2+n_teams]
        deff = params[2+n_teams:]
        
        log_lambda_h = mu + h_adv + att[home_idx] + deff[away_idx]
        log_lambda_a = mu + att[away_idx] + deff[home_idx]
        
        lambda_h = np.exp(np.clip(log_lambda_h, -10, 10))
        lambda_a = np.exp(np.clip(log_lambda_a, -10, 10))
        
        ll_h = poisson.logpmf(h_goals, lambda_h)
        ll_a = poisson.logpmf(a_goals, lambda_a)
        
        # Gaussian Priors (Bayesian MAP estimation)
        log_prior_att = -0.5 * np.sum((att / prior_std) ** 2)
        log_prior_def = -0.5 * np.sum((deff / prior_std) ** 2)
        log_prior_h_adv = -0.5 * ((h_adv / 0.5) ** 2)
        
        total = np.sum(ll_h) + np.sum(ll_a) + log_prior_att + log_prior_def + log_prior_h_adv
        return -total

    init_params = np.zeros(n_params)
    init_params[0] = np.log(1.2)
    init_params[1] = 0.2
    
    res = minimize(neg_log_posterior, init_params, method='L-BFGS-B')
    
    return {
        'mu': res.x[0],
        'h_adv': res.x[1],
        'att': res.x[2:2+n_teams],
        'def': res.x[2+n_teams:]
    }

bayes_model = fit_bayesian_poisson_model(finished_df)

# Helper function to compute match probabilities
def predict_match(home_team, away_team, model, max_goals=6):
    h_i = t2i[home_team]
    a_i = t2i[away_team]
    
    mu = model['mu']
    h_adv = model['h_adv']
    att = model['att']
    deff = model['def']
    
    exp_h = np.exp(mu + h_adv + att[h_i] + deff[a_i])
    exp_a = np.exp(mu + att[a_i] + deff[h_i])
    
    score_matrix = np.zeros((max_goals + 1, max_goals + 1))
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            score_matrix[h, a] = poisson.pmf(h, exp_h) * poisson.pmf(a, exp_a)
            
    p_home_win = np.sum(np.tril(score_matrix, -1))
    p_draw = np.sum(np.diag(score_matrix))
    p_away_win = np.sum(np.triu(score_matrix, 1))
    
    return exp_h, exp_a, p_home_win, p_draw, p_away_win, score_matrix

# Helper function to calculate current standings
def calculate_standings(df_finished):
    table = []
    for t in teams:
        home_m = df_finished[df_finished['홈팀'] == t]
        away_m = df_finished[df_finished['원정팀'] == t]
        
        wins = (home_m['홈팀 점수'] > home_m['원정팀 점수']).sum() + (away_m['원정팀 점수'] > away_m['홈팀 점수']).sum()
        draws = (home_m['홈팀 점수'] == home_m['원정팀 점수']).sum() + (away_m['원정팀 점수'] == away_m['홈팀 점수']).sum()
        losses = (home_m['홈팀 점수'] < home_m['원정팀 점수']).sum() + (away_m['원정팀 점수'] < away_m['홈팀 점수']).sum()
        
        gf = home_m['홈팀 점수'].sum() + away_m['원정팀 점수'].sum()
        ga = home_m['원정팀 점수'].sum() + away_m['홈팀 점수'].sum()
        pts = wins * 3 + draws * 1
        played = len(home_m) + len(away_m)
        
        table.append({
            '팀': t,
            '경기수': played,
            '승': wins,
            '무': draws,
            '패': losses,
            '득점': int(gf),
            '실점': int(ga),
            '득실차': int(gf - ga),
            '승점': int(pts)
        })
    
    st_df = pd.DataFrame(table).sort_values(by=['승점', '득실차', '득점'], ascending=False).reset_index(drop=True)
    st_df.index += 1
    return st_df

standings = calculate_standings(finished_df)

# Sidebar Navigation
st.sidebar.image("https://img.freepik.com/free-vector/soccer-ball-concept-illustration_114360-9388.jpg", width=120)
st.sidebar.title("📌 메뉴")
section = st.sidebar.radio(
    "이동할 섹션을 선택하세요:",
    ["📊 지난 경기 정보 요약", "⚽ 다음 경기 예측", "🏆 대구 FC 승격 가능성 예측"]
)

# ---------------------------------------------------------
# SECTION 1: 지난 경기 정보 요약
# ---------------------------------------------------------
if section == "📊 지난 경기 정보 요약":
    st.markdown("<div class='main-header'>📊 지난 경기 정보 요약</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>현재 리그 순위 및 완료된 경기들의 핵심 통계를 확인합니다.</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 진행 경기", f"{len(finished_df)} 경기")
    with col2:
        st.metric("경기당 평균 득점", f"{(finished_df['홈팀 점수'].sum() + finished_df['원정팀 점수'].sum()) / len(finished_df):.2f} 골")
    with col3:
        daegu_st = standings[standings['팀'] == '대구 FC'].iloc[0]
        st.metric("대구 FC 현재 순위", f"{standings[standings['팀'] == '대구 FC'].index[0]}위", f"승점 {daegu_st['승점']}점")
    with col4:
        st.metric("대구 FC 전적", f"{daegu_st['승']}승 {daegu_st['무']}무 {daegu_st['패']}패", f"득실차 {daegu_st['득실차']:+d}")

    st.markdown("---")
    
    st.subheader("🏆 현재 리그 순위표")
    st.dataframe(standings.style.highlight_max(axis=0, subset=['승점'], color='#d4edda'), use_container_width=True)
    
    st.markdown("---")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("🔵 대구 FC 최근 경기 결과")
        daegu_finished = finished_df[(finished_df['홈팀'] == '대구 FC') | (finished_df['원정팀'] == '대구 FC')].tail(10)
        daegu_finished_display = daegu_finished[['라운드', '홈팀', '홈팀 점수', '원정팀 점수', '원정팀']].copy()
        st.dataframe(daegu_finished_display, use_container_width=True)
        
    with col_b:
        st.subheader("🎯 베이지안 모델 추정 팀 능력치")
        att_df = pd.DataFrame({
            '팀': teams,
            '공격력 지수': bayes_model['att'],
            '수비력 지수 (낮을수록 우수)': bayes_model['def']
        }).sort_values(by='공격력 지수', ascending=False)
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.scatterplot(data=att_df, x='공격력 지수', y='수비력 지수 (낮을수록 우수)', ax=ax, s=100, color='#0A3663')
        for i, row in att_df.iterrows():
            ax.annotate(row['팀'], (row['공격력 지수']+0.01, row['수비력 지수 (낮을수록 우수)']), fontsize=9)
        ax.axvline(0, color='gray', linestyle='--', alpha=0.5)
        ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax.set_title("팀별 베이지안 공격력 / 수비력 추정치 (0 = 리그 평균)")
        ax.set_ylabel("수비 실점 성향 (낮을수록 강함)")
        ax.set_xlabel("공격 득점 성향 (높을수록 강함)")
        st.pyplot(fig)

# ---------------------------------------------------------
# SECTION 2: 다음 경기 예측
# ---------------------------------------------------------
elif section == "⚽ 다음 경기 예측":
    st.markdown("<div class='main-header'>⚽ 다음 경기 예측 (베이지안 포아송 모델)</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>팀의 최근 공격/수비력과 홈 이점을 고려한 베이지안 승부 예측 시뮬레이션입니다.</div>", unsafe_allow_html=True)
    
    st.subheader("📌 경기 선택")
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        daegu_next = remaining_df[(remaining_df['홈팀'] == '대구 FC') | (remaining_df['원정팀'] == '대구 FC')]
        if len(daegu_next) > 0:
            default_home = daegu_next.iloc[0]['홈팀']
            default_away = daegu_next.iloc[0]['원정팀']
        else:
            default_home, default_away = teams[0], teams[1]
            
        home_team = st.selectbox("홈 팀 선택", teams, index=teams.index(default_home))
    with col_sel2:
        away_options = [t for t in teams if t != home_team]
        away_index = away_options.index(default_away) if default_away in away_options else 0
        away_team = st.selectbox("원정 팀 선택", away_options, index=away_index)
        
    exp_h, exp_a, p_home, p_draw, p_away, score_mat = predict_match(home_team, away_team, bayes_model)
    
    st.markdown("---")
    st.subheader(f"⚔️ {home_team} vs {away_team} 예상 분석 결과")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(f"🏠 {home_team} 승리 확률", f"{p_home * 100:.1f}%", f"기대 득점(xG): {exp_h:.2f}골")
    with c2:
        st.metric("🤝 무승부 확률", f"{p_draw * 100:.1f}%", "균형 경기 가능성")
    with c3:
        st.metric(f"✈️ {away_team} 승리 확률", f"{p_away * 100:.1f}%", f"기대 득점(xG): {exp_a:.2f}골")
        
    st.markdown("---")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.subheader("🎯 가장 유력한 예상 스코어 Top 5")
        scores = []
        for h in range(5):
            for a in range(5):
                scores.append({
                    '스코어': f"{h} : {a}",
                    '확률 (%)': score_mat[h, a] * 100
                })
        scores_df = pd.DataFrame(scores).sort_values(by='확률 (%)', ascending=False).head(5).reset_index(drop=True)
        scores_df.index += 1
        st.dataframe(scores_df.style.format({'확률 (%)': '{:.2f}%'}), use_container_width=True)
        
    with col_m2:
        st.subheader("🔥 스코어 확률 분포 히트맵")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(score_mat[:5, :5], annot=True, fmt=".1%", cmap="Blues", cbar=False,
                    xticklabels=[f"{i}골" for i in range(5)], yticklabels=[f"{i}골" for i in range(5)])
        ax.set_xlabel(f"{away_team} (원정) 득점")
        ax.set_ylabel(f"{home_team} (홈) 득점")
        st.pyplot(fig)

# ---------------------------------------------------------
# SECTION 3: 대구 FC 승격 가능성 예측
# ---------------------------------------------------------
elif section == "🏆 대구 FC 승격 가능성 예측":
    st.markdown("<div class='main-header'>🏆 대구 FC 승격 가능성 및 잔여 경기 시뮬레이션</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>잔여 경기 전체를 베이지안 포아송 몬테카를로 기법으로 수천 회 시뮬레이션하여 최종 순위를 시뮬레이션합니다.</div>", unsafe_allow_html=True)
    
    n_sims = st.sidebar.slider("몬테카를로 시뮬레이션 횟수", min_value=1000, max_value=10000, value=3000, step=1000)
    
    if st.button("🚀 몬테카를로 시뮬레이션 실행"):
        with st.spinner(f"{n_sims:,}회 잔여 경기 시뮬레이션을 진행하고 있습니다..."):
            base_pts = {t: 0 for t in teams}
            base_gf = {t: 0 for t in teams}
            base_ga = {t: 0 for t in teams}

            for _, row in finished_df.iterrows():
                h, a = row['홈팀'], row['원정팀']
                hs, as_ = int(row['홈팀 점수']), int(row['원정팀 점수'])
                base_gf[h] += hs
                base_ga[h] += as_
                base_gf[a] += as_
                base_ga[a] += hs
                if hs > as_:
                    base_pts[h] += 3
                elif hs < as_:
                    base_pts[a] += 3
                else:
                    base_pts[h] += 1
                    base_pts[a] += 1
                    
            base_pts_arr = np.array([base_pts[t] for t in teams], dtype=float)
            base_gf_arr = np.array([base_gf[t] for t in teams], dtype=float)
            base_ga_arr = np.array([base_ga[t] for t in teams], dtype=float)

            rem_h_arr = remaining_df['홈팀'].map(t2i).values
            rem_a_arr = remaining_df['원정팀'].map(t2i).values
            n_rem = len(remaining_df)

            mu = bayes_model['mu']
            h_adv = bayes_model['h_adv']
            att = bayes_model['att']
            deff = bayes_model['def']

            lh = np.exp(mu + h_adv + att[rem_h_arr] + deff[rem_a_arr])
            la = np.exp(mu + att[rem_a_arr] + deff[rem_h_arr])

            sim_h_goals = np.random.poisson(lh, size=(n_sims, n_rem))
            sim_a_goals = np.random.poisson(la, size=(n_sims, n_rem))

            sim_h_pts = np.where(sim_h_goals > sim_a_goals, 3, np.where(sim_h_goals == sim_a_goals, 1, 0))
            sim_a_pts = np.where(sim_a_goals > sim_h_goals, 3, np.where(sim_h_goals == sim_a_goals, 1, 0))

            pts_matrix = np.tile(base_pts_arr, (n_sims, 1))
            gf_matrix = np.tile(base_gf_arr, (n_sims, 1))
            ga_matrix = np.tile(base_ga_arr, (n_sims, 1))

            row_indices = np.arange(n_sims)[:, None]

            np.add.at(pts_matrix, (row_indices, rem_h_arr), sim_h_pts)
            np.add.at(pts_matrix, (row_indices, rem_a_arr), sim_a_pts)
            np.add.at(gf_matrix, (row_indices, rem_h_arr), sim_h_goals)
            np.add.at(gf_matrix, (row_indices, rem_a_arr), sim_a_goals)
            np.add.at(ga_matrix, (row_indices, rem_h_arr), sim_a_goals)
            np.add.at(ga_matrix, (row_indices, rem_a_arr), sim_h_goals)

            gd_matrix = gf_matrix - ga_matrix
            composite = pts_matrix * 1000000 + gd_matrix * 1000 + gf_matrix

            sorted_indices = np.argsort(-composite, axis=1)
            ranks = np.argsort(sorted_indices, axis=1) + 1 # 1-based rank

            daegu_idx = t2i['대구 FC']
            daegu_ranks = ranks[:, daegu_idx]
            daegu_pts = pts_matrix[:, daegu_idx]

            p_1st = np.mean(daegu_ranks == 1) * 100
            p_playoff = np.mean((daegu_ranks >= 2) & (daegu_ranks <= 5)) * 100
            p_total_promo = np.mean(daegu_ranks <= 5) * 100
            
            st.markdown("### 🏆 대구 FC 승격 확률 요약")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric("🥇 1위 직행 승격 확률", f"{p_1st:.1f}%")
            with mc2:
                st.metric("🥈 2~5위 (승격 플레이오프)", f"{p_playoff:.1f}%")
            with mc3:
                st.metric("🔥 Total 승격 가능권 (1~5위)", f"{p_total_promo:.1f}%")

            st.markdown("---")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("📊 대구 FC 예상 최종 순위 분포")
                unique_r, counts_r = np.unique(daegu_ranks, return_counts=True)
                rank_dist_df = pd.DataFrame({
                    '순위': [f"{r}위" for r in unique_r],
                    '확률 (%)': counts_r / n_sims * 100
                })
                
                fig, ax = plt.subplots(figsize=(7, 4))
                bars = ax.bar(rank_dist_df['순위'], rank_dist_df['확률 (%)'], color='#0A3663')
                ax.set_ylabel("확률 (%)")
                ax.set_ylim(0, max(rank_dist_df['확률 (%)']) * 1.2)
                for bar in bars:
                    yval = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.1f}%", ha='center', va='bottom')
                st.pyplot(fig)

            with col_g2:
                st.subheader("📈 대구 FC 예상 최종 승점 분포")
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.hist(daegu_pts, bins=range(int(min(daegu_pts)), int(max(daegu_pts))+2), color='#2B5B84', edgecolor='black', alpha=0.7)
                mean_pts = np.mean(daegu_pts)
                ax.axvline(mean_pts, color='red', linestyle='--', label=f'평균 승점 ({mean_pts:.1f}점)')
                ax.set_xlabel("최종 승점")
                ax.set_ylabel("시뮬레이션 빈도")
                ax.legend()
                st.pyplot(fig)
                
            st.markdown("---")
            st.subheader("📋 전체 구단 예상 평균 승점 및 승격권 진출 확률표")
            
            sim_summary = []
            for t in teams:
                idx = t2i[t]
                t_ranks = ranks[:, idx]
                t_pts = pts_matrix[:, idx]
                sim_summary.append({
                    '팀': t,
                    '현재 승점': base_pts[t],
                    '예상 평균 승점': round(np.mean(t_pts), 1),
                    '1위 확률 (%)': round(np.mean(t_ranks == 1) * 100, 1),
                    '2~5위 확률 (%)': round(np.mean((t_ranks >= 2) & (t_ranks <= 5)) * 100, 1),
                    '승격권(1~5위) 총확률 (%)': round(np.mean(t_ranks <= 5) * 100, 1)
                })
            
            summary_df = pd.DataFrame(sim_summary).sort_values(by='예상 평균 승점', ascending=False).reset_index(drop=True)
            summary_df.index += 1
            st.dataframe(summary_df.style.highlight_max(axis=0, subset=['1위 확률 (%)', '승격권(1~5위) 총확률 (%)'], color='#d4edda'), use_container_width=True)

    else:
        st.info("👆 위버튼을 눌러 몬테카를로 시뮬레이션을 실행해주세요.")
