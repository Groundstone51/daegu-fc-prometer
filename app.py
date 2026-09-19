import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="K리그2 순수 베이지안 승격 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)
