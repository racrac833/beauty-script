import os
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field

load_dotenv()

st.set_page_config(page_title="RAMILOVE", layout="wide")

# ==================== [1. 세션 상태 초기화] ====================
if "brand_name" not in st.session_state:
    st.session_state.brand_name = ""
if "product_name" not in st.session_state:
    st.session_state.product_name = ""
if "product_usp" not in st.session_state:
    st.session_state.product_usp = ""
if "target_audience" not in st.session_state:
    st.session_state.target_audience = "30대 여성"
if "essential_tags" not in st.session_state:
    st.session_state.essential_tags = ""
if "account_tags" not in st.session_state:
    st.session_state.account_tags = ""
if "event_info" not in st.session_state:
    st.session_state.event_info = ""
if "content_mode" not in st.session_state:
    st.session_state.content_mode = "instagram"
if "insta_result" not in st.session_state:
    st.session_state.insta_result = ""
if "blog_result" not in st.session_state:
    st.session_state.blog_result = ""
if "product_category" not in st.session_state:
    st.session_state.product_category = "기초/스킨케어"

# 인스타 기본값: 6 (범위: 5~10)
if "insta_scene_count" not in st.session_state:
    st.session_state.insta_scene_count = 6
# 블로그 기본값: 15 (범위: 14~20)
if "blog_photo_count" not in st.session_state:
    st.session_state.blog_photo_count = 15

generate_action = False

# ==================== [2. 테마 컬러 및 기본 슬라이더 스타일링] ====================
is_insta = (st.session_state.content_mode == "instagram")
insta_gradient = "linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)"
naver_green = "#03C75A"

theme_bg = insta_gradient if is_insta else naver_green
slider_fill_color = "#e6683c" if is_insta else naver_green
theme_border = "#ff4b72" if is_insta else "#00ff6f"

st.markdown(f"""
<style>
    /* 1. 중앙 영문 타이틀 */
    .ramilove-header {{
        text-align: center;
        font-size: 38px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        letter-spacing: 2px !important;
        margin-top: 5px !important;
        margin-bottom: 25px !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    /* 2. 상단 3단 네비게이션 가로 1열 완벽 대칭 */
    div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 16px !important;
        width: 100% !important;
        max-width: 680px !important;
        margin: 0 auto !important;
    }}

    div[data-testid="stHorizontalBlock"] > div {{
        flex: 1 1 0px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        min-width: 0 !important;
    }}

    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {{
        flex: 0 0 90px !important;
    }}

    /* 좌측 탭: INSTAGRAM */
    .st-key-tab_insta {{
        width: 100% !important;
    }}
    .st-key-tab_insta button {{
        background: {insta_gradient if is_insta else '#484c54'} !important;
        border: {'2px solid #ff4b72' if is_insta else '1px solid #5a5f69'} !important;
        border-radius: 30px !important;
        height: 48px !important;
        width: 100% !important;
        box-shadow: {'0 4px 15px rgba(220, 39, 67, 0.5)' if is_insta else 'none'} !important;
    }}
    .st-key-tab_insta button * {{
        color: {'#ffffff' if is_insta else '#f0f0f0'} !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
    }}

    /* 우측 탭: BLOG */
    .st-key-tab_blog {{
        width: 100% !important;
    }}
    .st-key-tab_blog button {{
        background: {naver_green if not is_insta else '#484c54'} !important;
        border: {'2px solid #00ff6f' if not is_insta else '1px solid #5a5f69'} !important;
        border-radius: 30px !important;
        height: 48px !important;
        width: 100% !important;
        box-shadow: {'0 4px 15px rgba(3, 199, 90, 0.5)' if not is_insta else 'none'} !important;
    }}
    .st-key-tab_blog button * {{
        color: {'#ffffff' if not is_insta else '#f0f0f0'} !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
    }}

    /* 중앙 하트 생성 버튼 (80px 정원형 완벽 복원) */
    .st-key-btn_generate_main {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 80px !important;
        height: 80px !important;
        margin: 0 auto !important;
    }}
    .st-key-btn_generate_main button {{
        width: 80px !important;
        height: 80px !important;
        min-width: 80px !important;
        max-width: 80px !important;
        border-radius: 50% !important;
        background: #FFFFFF !important;
        border: {'5px solid transparent' if is_insta else f'5px solid {naver_green}'} !important;
        {'background-image: linear-gradient(#FFFFFF, #FFFFFF), ' + insta_gradient + ' !important; background-origin: border-box !important; background-clip: padding-box, border-box !important;' if is_insta else ''}
        box-shadow: {
            "0 0 18px rgba(220, 39, 67, 0.5)" 
            if is_insta else "0 0 18px rgba(3, 199, 90, 0.5)"
        } !important;
        transition: all 0.25s ease-in-out !important;
        position: relative !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    .st-key-btn_generate_main button * {{
        display: none !important;
    }}
    .st-key-btn_generate_main button::after {{
        content: "" !important;
        display: block !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 36px !important;
        height: 36px !important;
        background: {theme_bg} !important;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z'/%3E%3/svg%3E") no-repeat center / contain !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z'/%3E%3/svg%3E") no-repeat center / contain !important;
    }}
    .st-key-btn_generate_main button:hover {{
        transform: scale(1.08) !important;
        box-shadow: {
            "0 0 28px rgba(220, 39, 67, 0.8)" 
            if is_insta else "0 0 28px rgba(3, 199, 90, 0.8)"
        } !important;
    }}

    /* 3. 사이드바 분석 버튼 */
    .st-key-btn_analyze button {{
        background: {theme_bg} !important;
        border: none !important;
        border-radius: 12px !important;
        height: 48px !important;
        box-shadow: {'0 4px 15px rgba(220, 39, 67, 0.4)' if is_insta else '0 4px 15px rgba(3, 199, 90, 0.4)'} !important;
        transition: all 0.2s ease-in-out !important;
    }}
    .st-key-btn_analyze button * {{
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 900 !important;
    }}

    /* 4. 사이드바 내부 RAMILOVE 로고 스타일 (간격 50% 확장) */
    .sidebar-logo {{
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        letter-spacing: 1.5px !important;
        margin-bottom: 38px !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    /* 5. 사이드바 동적 넘버링 뱃지 */
    .sidebar-section-title {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 12px;
    }}
    .theme-badge {{
        background: {theme_bg};
        color: #ffffff;
        border-radius: 50%;
        width: 26px;
        height: 26px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 900;
        box-shadow: {'0 2px 8px rgba(220, 39, 67, 0.5)' if is_insta else '0 2px 8px rgba(3, 199, 90, 0.5)'};
    }}

    /* 6. 사이드바 소제목 앞 미니 포인트 원 (Bullet Dot) */
    section[data-testid="stSidebar"] label p {{
        display: flex !important;
        align-items: center !important;
        gap: 7px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        color: #e3e3e3 !important;
    }}
    section[data-testid="stSidebar"] label p::before {{
        content: "" !important;
        display: inline-block !important;
        width: 8px !important;
        height: 8px !important;
        min-width: 8px !important;
        border-radius: 50% !important;
        background: {theme_bg} !important;
        box-shadow: {'0 0 6px rgba(220, 39, 67, 0.6)' if is_insta else '0 0 6px rgba(3, 199, 90, 0.6)'} !important;
    }}

    /* 7. 슬라이더 바 테마 동기화 */
    div[data-testid="stSlider"] {{
        margin-bottom: 14px !important;
    }}
    div[data-testid="stSlider"] div[data-baseweb="slider"] {{
        margin-top: 6px !important;
        margin-bottom: 6px !important;
    }}
    div[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child {{
        background-color: #383c46 !important;
        height: 6px !important;
        border-radius: 4px !important;
    }}
    div[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child > div {{
        background: {slider_fill_color} !important;
    }}
    div[data-testid="stSlider"] div[role="slider"] {{
        background: {slider_fill_color} !important;
        border: 2.5px solid #ffffff !important;
        width: 18px !important;
        height: 18px !important;
        box-shadow: {'0 0 8px rgba(220, 39, 67, 0.8)' if is_insta else '0 0 8px rgba(3, 199, 90,
