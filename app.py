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
if "insta_scene_count" not in st.session_state:
    st.session_state.insta_scene_count = 7
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
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z'/%3E%3C/svg%3E") no-repeat center / contain !important;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z'/%3E%3C/svg%3E") no-repeat center / contain !important;
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
        box-shadow: {'0 0 8px rgba(220, 39, 67, 0.8)' if is_insta else '0 0 8px rgba(3, 199, 90, 0.8)'} !important;
    }}
    div[data-testid="stSlider"] [data-testid="stSliderTickBarMin"],
    div[data-testid="stSlider"] [data-testid="stSliderTickBarMax"],
    div[data-testid="stSlider"] [data-testid="stSliderTickBar"] {{
        display: none !important;
    }}

    /* 8. 결과창 헤더 뱃지 */
    .result-header-wrapper {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
        margin-bottom: 14px;
    }}
    .result-main-title {{
        font-size: 22px;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 0.5px;
    }}
    .result-config-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.08);
        border: 1.5px solid {theme_border};
        padding: 4px 12px;
        border-radius: 20px;
        color: #ffffff;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.5px;
        box-shadow: {'0 2px 10px rgba(220, 39, 67, 0.35)' if is_insta else '0 2px 10px rgba(3, 199, 90, 0.35)'};
    }}
    .result-config-badge span.dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: {theme_bg};
        display: inline-block;
    }}

    /* 9. 결과창 코드 블록 자동 줄바꿈 & 대형 복사 버튼 */
    .stCodeBlock {{
        position: relative !important;
        border-radius: 14px !important;
        border: 1px solid #3d424b !important;
        background: #1e2025 !important;
        overflow-x: hidden !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }}
    .stCodeBlock pre {{
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        overflow-x: hidden !important;
        padding-right: 55px !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }}
    .stCodeBlock code {{
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.7 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 15px !important;
        display: block !important;
        width: 100% !important;
    }}
    .stCodeBlock button[title="Copy to clipboard"], 
    .stCodeBlock button[aria-label="Copy to clipboard"],
    .stCodeBlock button {{
        background: {theme_bg} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        opacity: 0.95 !important;
        box-shadow: {'0 4px 14px rgba(220, 39, 67, 0.7)' if is_insta else '0 4px 14px rgba(3, 199, 90, 0.7)'} !important;
        transition: all 0.2s ease-in-out !important;
        top: 12px !important;
        right: 12px !important;
    }}
    .stCodeBlock button:hover {{
        transform: scale(1.15) !important;
        opacity: 1 !important;
        box-shadow: {'0 6px 20px rgba(220, 39, 67, 0.9)' if is_insta else '0 6px 20px rgba(3, 199, 90, 0.9)'} !important;
    }}
    .stCodeBlock button svg {{
        fill: #ffffff !important;
        width: 24px !important;
        height: 24px !important;
    }}
    .empty-result-box {{
        background: #1e2025;
        border: 1px dashed #444850;
        border-radius: 14px;
        padding: 40px 20px;
        text-align: center;
        color: #9aa0a6;
        font-size: 15px;
        font-weight: 600;
        margin-top: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ==================== [3. 상단 레이아웃 렌더링] ====================
st.markdown('<div class="ramilove-header">RAMILOVE</div>', unsafe_allow_html=True)

col_insta, col_heart, col_blog = st.columns(3)

with col_insta:
    if st.button("INSTAGRAM", use_container_width=True, key="tab_insta"):
        st.session_state.content_mode = "instagram"
        st.rerun()

with col_heart:
    generate_action = st.button("EXECUTE", key="btn_generate_main")

with col_blog:
    if st.button("BLOG", use_container_width=True, key="tab_blog"):
        st.session_state.content_mode = "blog"
        st.rerun()

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# API 클라이언트 초기화
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error(".env 파일에 GEMINI_API_KEY를 설정해주세요.")
    st.stop()

client = genai.Client(api_key=api_key)

class ExtractedGuide(BaseModel):
    brand_name: str = Field(description="가이드/상세페이지에서 소개하는 실제 화장품/뷰티 브랜드명")
    product_usp: str = Field(description="실제 제품의 핵심 USP, 제형 특성, 주요 성분 및 효과 요약")
    target_audience: str = Field(description="타겟층 정보 (기본: 30대 여성)")
    essential_tags: str = Field(description="가이드에 명시된 필수 해시태그 목록 (#포함)")
    account_tags: str = Field(description="실제 브랜드의 공식 계정 태그 (@포함)")
    event_info: str = Field(description="실제 소비자가 보는 프로모션 일정, 할인 가격, 구매처")

def fetch_url_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://m.oliveyoung.co.kr/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script", "style", "nav", "footer", "noscript"]):
                script.decompose()
            text = soup.get_text(separator=" ", strip=True)
            if len(text) < 100:
                return ""
            return text[:4000]
        return ""
    except Exception:
        return ""

# ==================== [4. 사이드바 구성] ====================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">RAMILOVE</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section-title"><span class="theme-badge">1</span> 가이드 & 제품 자료 등록</div>', unsafe_allow_html=True)
    uploaded_images = st.file_uploader(
        "가이드라인 / 기획안 캡처 이미지 첨부 (권장)", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True,
        help="체험단 앱(오늘룩, 레뷰 등) 웹뷰는 보안상 링크 대신 화면을 캡처해서 올려주시면 100% 정확하게 인식합니다."
    )
    guideline_url = st.text_input(
        "가이드라인 링크 URL (노션, 웹페이지 등)",
        placeholder="https://notion.so/..."
    )
    product_url = st.text_input(
        "제품 상세페이지 링크 URL (올리브영/스마트스토어 등)",
        placeholder="https://oliveyoung.co.kr/..."
    )
    guideline_text = st.text_area(
        "추가 메모 / 가이드 텍스트 (선택)",
        placeholder="필수 멘트, 추가 행사 정보, 강조점 등을 입력하세요."
    )
    
    analyze_btn = st.button("추출 정보 채우기", use_container_width=True, key="btn_analyze")
    
    if analyze_btn:
        if not uploaded_images and not guideline_url.strip() and not product_url.strip() and not guideline_text.strip():
            st.warning("분석할 이미지, 링크 또는 메모를 하나 이상 입력해주세요.")
        else:
            with st.spinner("가이드와 상세페이지를 정밀 분석 중입니다..."):
                url_context = ""
                g_crawl_fail = False
                p_crawl_fail = False

                if guideline_url.strip():
                    g_text = fetch_url_content(guideline_url.strip())
                    if g_text:
                        url_context += f"\n[가이드라인 링크 내용]:\n{g_text}\n"
                    else:
                        g_crawl_fail = True
                
                if product_url.strip():
                    p_text = fetch_url_content(product_url.strip())
                    if p_text:
                        url_context += f"\n[제품 상세페이지 내용]:\n{p_text}\n"
                    else:
                        p_crawl_fail = True

                contents = []
                if uploaded_images:
                    for img_file in uploaded_images:
                        contents.append(Image.open(img_file))
                
                extract_prompt = f"""
제공된 가이드라인 이미지, 가이드 링크, 제품 상세페이지 내용, 메모를 정밀 분석하여 실제 화장품/제품에 대한 정보를 정확히 추출하세요.

[절대 주의사항 (STRICT)]
1. '오늘룩(oneulook)', '레뷰(revu)', '체험단' 등은 마케팅 중개 플랫폼일 뿐 실제 화장품 브랜드명이 아닙니다. 절대 이를 브랜드명이나 해시태그로 추출하지 마세요.
2. 이미지와 상세페이지에 나오는 '실제 뷰티 제품의 브랜드명(예: 엑시스와이, 넘버즈인, 아누아 등)'과 '제품명'을 정확히 추출하세요.
3. 제품 USP: 제품의 실제 성분, 제형 특성, 고민 부위 해결 효과, 임상시험 수치 추출
4. 행사 정보: 올리브영 프로모션 일정, 할인율/가격, 구매처 추출
5. 필수 해시태그: 가이드에 지정된 실제 제품 필수 해시태그만 추출 (플랫폼 태그 제외)

[추가 메모]: {guideline_text}
{url_context}
"""
                contents.append(extract_prompt)

                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ExtractedGuide,
                            temperature=0.1,
                        )
                    )
                    data = json.loads(response.text)
                    st.session_state.brand_name = data.get("brand_name", "")
                    st.session_state.product_usp = data.get("product_usp", "")
                    st.session_state.target_audience = data.get("target_audience", "30대 여성")
                    st.session_state.essential_tags = data.get("essential_tags", "")
                    st.session_state.account_tags = data.get("account_tags", "")
                    st.session_state.event_info = data.get("event_info", "")
                    
                    st.success("분석 완료! 아래 추출된 내용을 확인하고 필요시 수정해주세요.")
                    
                    if (g_crawl_fail or p_crawl_fail) and not uploaded_images:
                        st.info("팁: 앱 전용 웹뷰(오늘룩)나 일부 쇼핑몰은 웹 보안상 링크 직접 읽기가 제한됩니다. 가이드 화면을 캡처해서 상단 파일 첨부에 올리시면 완벽하게 인식됩니다.")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.markdown('<div class="sidebar-section-title"><span class="theme-badge">2</span> 추출 정보 확인 및 설정</div>', unsafe_allow_html=True)
    
    # 공통: 제품 카테고리
    categories = ["기초/스킨케어", "색조/메이크업", "선케어/클렌징", "헤어/바디", "이너뷰티/다이어트", "뷰티소품/디바이스"]
    st.selectbox("제품 카테고리 (대본 톤앤매너 설정)", categories, key="product_category")

    # 슬라이더 적용
    if is_insta:
        st.slider("인스타 영상 장면 수 (6~12장)", min_value=6, max_value=12, step=1, key="insta_scene_count")
    else:
        st.slider("블로그 사진 장수 (15~20장)", min_value=15, max_value=20, step=1, key="blog_photo_count")

    brand_name = st.text_input("정확한 브랜드명 (임의 변경 절대 금지)", value=st.session_state.brand_name)
    product_usp = st.text_area("제품 USP / 주요 특징", value=st.session_state.product_usp, height=100)
    event_info = st.text_area("행사 / 가격 / 기획전 정보 (일정, 할인내용)", value=st.session_state.event_info, height=70)
    target_audience = st.text_input("타겟층", value=st.session_state.target_audience)
    essential_tags = st.text_input("필수 해시태그", value=st.session_state.essential_tags)
    account_tags = st.text_input("공식 계정 태그", value=st.session_state.account_tags)

def get_url_context():
    url_context = ""
    if guideline_url.strip():
        g_text = fetch_url_content(guideline_url.strip())
        if g_text:
            url_context += f"\n[가이드라인 링크 내용]: {g_text}\n"
    if product_url.strip():
        p_text = fetch_url_content(product_url.strip())
        if p_text:
            url_context += f"\n[제품 상세페이지 내용]: {p_text}\n"
    return url_context

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ==================== [5. 대본 / 원고 생성 로직] ====================
if generate_action:
    if not brand_name or not product_usp:
        st.warning("왼쪽 사이드바에서 브랜드명과 제품 USP를 먼저 확인해주세요.")
    else:
        url_context = get_url_context()
        contents = []
        if uploaded_images:
            for img in uploaded_images:
                contents.append(Image.open(img))

        if is_insta:
            target_scenes = st.session_state.insta_scene_count
            current_cat = st.session_state.product_category
            with st.spinner(f"[{current_cat}] 맞춤 장면 {target_scenes}개 구성의 릴스 콘티를 작성 중입니다..."):
                system_instruction_reels = f"""
[Role & Goal]
당신은 숏폼(릴스/쇼츠/틱톡) 뷰티 전문 최고급 콘티 작가 "뷰티 릴스 대본 작성기"입니다.
사용자가 제공하는 [카테고리: {current_cat}, 장면 수: {target_scenes}개, 가이드라인, 제품 상세페이지 내용, 제품 USP, 행사 정보]를 분석하여 완벽한 인스타그램 릴스 촬영 콘티를 작성합니다.

[카테고리별 숏폼 연출 특화 지침 - 현재 카테고리: {current_cat}]
- 기초/스킨케어: 텍스처 수분 광채 클로즈업, 부위별 롤링/흡수 모션, 결 정돈 비포애프터
- 색조/메이크업: 본통 컬러 팁 컷, 자연광 피부/입술 발색 모션, 밀착력 및 묻어남 방지 테스트
- 선케어/클렌징: 백탁 없는 투명 밀착 발림, 메이크업 세정 롤링 액션, 산뜻한 마무리감
- 헤어/바디: 풍성한 거품 텍스처 연출, 젖은/마른 모발 윤기 변화, 기분 좋은 잔향 묘사
- 이너뷰티/다이어트: 파우치/스틱 이지컷 오픈 컷, 섭취 모션, 가방 속 휴대 루틴
- 뷰티소품/디바이스: 기기 헤드 클로즈업, 턱선/광대/목선 리프팅 롤링 모션, 간편한 조작법

[핵심 절대 원칙 (CRITICAL)]

1. [슬래시(/) 사용 범위 엄격 제한 (STRICT)]:
- 슬래시(`/`)는 **오직 자막과 자막 사이의 컷 구분(줄바꿈)** 용도로만 사용하세요.
- **각주 내부나 문장 중간에는 절대로 슬래시를 넣지 마세요.** 각주 내에서 여러 내용을 적을 때는 쉼표(`,`)나 자연스러운 연결어를 사용하세요.

2. [자막 및 각주 세트 배치 규칙 (STRICT)]:
- 가이드라인에 임상시험 수치나 인증 정보 등 각주가 있는 경우, 각주가 필요한 해당 자막 문구 바로 아래에 세트로 묶어서 아래 포맷처럼 작성하세요.

  [필수 포맷 예시]:
  자막：
  900샷 마이크로 니들*
  (하단 각주 삽입)
  *패치 1회 분량 기준 니들 수
  /
  시카리들 PDRN 흡수 부스팅

3. [나레이션 엄격 규칙 (CRITICAL - 글자수 및 특수문자 금지)]:
- 나레이션 대사에는 느낌표(!), 슬래시(/) 등 어떠한 특수문자나 기호도 절대 포함하지 마세요.
- 전체 나레이션의 총 글자 수는 공백을 포함하여 **30대 여성 찐후기 톤으로 간결하게 300자 이내**로 작성하세요.

4. [정확히 {target_scenes}개 핵심 씬 구성 (STRICT)]:
- 반드시 [1. 장면]부터 [ {target_scenes}. 장면]까지 정확히 {target_scenes}개의 장면으로만 구성합니다.
- 마지막 장면([ {target_scenes}. 장면])은 반드시 프로모션 일정, 할인 가격, 구매처 안내 및 마무리 컷으로 배치합니다.

5. [가로 스크롤 방지 20~30자 줄바꿈 (STRICT)]:
- 썸네일 설명, 씬별 비주얼 연출 설명, 나레이션 문장, #광고 캡션 등 모든 텍스트는 1줄당 20~30자 내외로 자연스럽게 엔터(줄바꿈)를 쳐서 가로 스크롤이 절대 생기지 않도록 작성하세요.

6. [의료/피부과 시술명 및 시술 비교 표현 절대 금지 (STRICT BAN)]:
- '시술', '시술급', '시술받은 것처럼', '보톡스', '필러', '리쥬란', '레이저' 등 모든 시술명 및 비교 표현 절대 금지.
- 순수 홈케어 화장품 사용 경험과 만족감으로만 작성하세요.

7. [브랜드명 원형 유지]:
- 브랜드명은 반드시 '{brand_name}' 그대로 단 1글자의 변형도 없이 사용합니다.

[출력 양식 템플릿]

썸네일
썸네일(비주얼 연출 컷 설명) : ({current_cat} 특성을 살린 후킹 비주얼 /
20~30자 단위 줄바꿈)

[베스트 썸네일]
(첫째 줄: 띄어쓰기 포함 10자 이내)
(둘째 줄: 띄어쓰기 포함 12자 이내)

[추천 썸네일 문구 5선]
1.
(첫째 줄)
(둘째 줄)

2.
(첫째 줄)
(둘째 줄)

3.
(첫째 줄)
(둘째 줄)

4.
(첫째 줄)
(둘째 줄)

5.
(첫째 줄)
(둘째 줄)


[1. 장면] 부터 [ {target_scenes}. 장면] 까지 순서대로:

[장면 번호]
카메라 앵글 → 인물 행동 및 제품 포인트 흐름
(20~30자 단위로 줄바꿈)

자막：
(자막 컷 구분에만 슬래시 사용 / 각주는 해당 문구 바로 아래에 세트 배치 / 각주 내 슬래시 금지)

나레이션：
(특수문자 없이 공백 포함 300자 이내의 솔직하고 빠른 구어체 대사 /
20~30자 내외로 자연스럽게 줄바꿈하여 작성)


(마지막 {target_scenes}번 씬 하단):
로고 초반에 삽입 / 음악ㅇ / 끝



#광고 캡션
(30대 여성 찐후기 톤: 리얼 후킹 문구)

(솔직 사용 경험 및 핵심 장점 설명 /
한 줄로 길어지지 않게 20~30자마다 엔터로 줄바꿈)

(기획전/특가 일정, 할인 가격, 구매처 안내 포함)

{essential_tags if essential_tags else ''}
계정 태그: {account_tags if account_tags else '@공식계정아이디'}

댓글에 #올영1위 (또는 지정 댓글 태그)

(1번 씬부터 {target_scenes}번 씬까지 순서대로 요약):
장면： (1번 씬 연출 요약)
...
장면： ({target_scenes}번 씬 연출 요약)
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 템플릿과 [카테고리: {current_cat}], [정확히 {target_scenes}개 장면 구성], [슬래시(/)는 오직 자막 컷 구분에만 사용], [각주는 해당 문구 바로 아래에 세트 배치 및 각주 내 슬래시 금지], [나레이션 특수문자 금지 및 공백 포함 300자 이내], [가로 스크롤 방지 20~30자 줄바꿈], [시술명 금지], [베스트 썸네일 + 추천 5선]을 100% 지켜 인스타그램 숏폼 대본을 작성해줘:
- 카테고리: {current_cat}
- 장면 수: {target_scenes}개 씬
- 브랜드명: {brand_name}
- 제품 USP: {product_usp}
- 행사/가격 정보: {event_info if event_info else '가이드 참조'}
- 타겟층: {target_audience}
- 필수 해시태그: {essential_tags if essential_tags else '없음'}
- 공식 계정 태그: {account_tags if account_tags else '없음'}
- 추가 전달사항: {guideline_text if guideline_text else '없음'}
{url_context}
"""
                contents.append(prompt_text)

                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_reels,
                            temperature=0.4,
                        )
                    )
                    st.session_state.insta_result = response.text
                except Exception as e:
                    st.error(f"대본 생성 중 오류가 발생했습니다: {e}")

        else:
            target_photos = st.session_state.blog_photo_count
            current_cat = st.session_state.product_category
            with st.spinner(f"[{current_cat}] 맞춤 사진 {target_photos}장 기준 네이버 SEO 블로그 원고를 작성 중입니다..."):
                system_instruction_blog = f"""
[Role & Goal]
당신은 네이버 상위 노출 전문 뷰티 블로거이자 전문 에디터입니다.
사용자가 제공한 [카테고리: {current_cat}, 사진 장수: {target_photos}장, 가이드라인, 제품 상세페이지 내용, USP, 행사 정보]를 분석하여 네이버 블로그 검색 알고리즘과 스마트블록에 최적화된 고품질 포스팅 원고를 작성합니다.

[카테고리별 전문 톤앤매너 지침 - 현재 카테고리: {current_cat}]
- 기초/스킨케어: 수분감, 속건조, 피부결 정돈, 유수분 밸런스, 쿨링감 중심
- 색조/메이크업: 자연광 발색, 홋수/톤체크, 밀착력, 묻어남/지속력 테스트 중심
- 선케어/클렌징: 백탁/눈시림 여부, 세정력 테스트, 잔여감 없는 산뜻함 중심
- 헤어/바디: 향기 노트(탑/미들/베이스), 거품력, 모발 윤기 및 끈적임 없는 보습 중심
- 이너뷰티/다이어트: 맛, 섭취 편의성, 개별 포장 휴대성, 꾸준한 데일리 루틴 중심
- 뷰티소품/디바이스: 그립감, 기기 조작법 단계별 안내, 부위별 마사지 모션 중심

[핵심 절대 원칙 (CRITICAL)]

1. [촬영 가이드 및 본문 줄바꿈 원칙 (STRICT - 가로 스크롤 절대 방지)]:
- (촬영 가이드: ...) 설명이 한 줄로 길게 늘어지지 않게 20~30자 내외마다 엔터(줄바꿈)를 쳐서 2~3줄로 나누어 작성하세요.
- 본문 [원고 텍스트] 역시 1줄당 25~35자 내외로 자연스럽게 엔터를 쳐서 작성하세요.

2. [사진 장수 정확히 {target_photos}장 구성 (STRICT)]:
- 반드시 [사진 1]부터 [사진 {target_photos}]까지 정확히 {target_photos}개의 사진 가이드와 원고 문단으로 분절하여 작성하세요.
- 각 사진마다 '{current_cat}' 특성에 맞는 최적의 [촬영 가이드]를 명시하고, 제형/발림성/롤링/사용 과정에는 체류시간 증대를 위해 '[GIF 권장]'을 1~2개 포함하세요.

3. [네이버 SEO 최적화 제목 (공백 포함 25~35자 내외)]:
- [브랜드명 + 핵심 키워드 + 제품군]을 앞단(15자 이내)에 배치한 제목 5선을 추천합니다.

4. [의료/피부과 시술명 및 시술 비교 표현 절대 금지 (STRICT BAN)]:
- '시술', '시술급', '시술받은 것처럼', '보톡스', '필러', '리쥬란', '레이저' 등 모든 시술명 및 비교 표현 절대 금지.
- 순수 홈케어 사용감과 만족도 위주로 기술하세요.

5. [종결 어미 스타일 엄수]:
- '~했다', '~해봤다' 등 딱딱한 어미 대신 부드러운 30대 여성 찐후기 어조(~해보고, ~발라봤는데, ~직접 써보니까 등)를 유지하세요.

6. [브랜드명 및 필수 요소 원형 유지]:
- 브랜드명은 반드시 '{brand_name}' 그대로 단 1글자의 변형도 없이 사용합니다.
- 마지막 사진과 최하단에 프로모션 일정('{event_info}') 및 필수 해시태그('{essential_tags}')를 명시하세요.

[출력 양식 템플릿]

[네이버 블로그 추천 제목 5선 (SEO 최적 글자수 25~35자)]
1. (브랜드명+키워드 전면 배치 제목)
2. (브랜드명+키워드 전면 배치 제목)
3. (브랜드명+키워드 전면 배치 제목)
4. (브랜드명+키워드 전면 배치 제목)
5. (브랜드명+키워드 전면 배치 제목)

-------------------------------------------------------

[사진 1] 부터 [사진 {target_photos}] 까지 순서대로:

[사진 번호]
(촬영 가이드: {current_cat} 특성에 맞춘 촬영 가이드 /
한 줄로 길어지지 않게 20~30자마다
자연스럽게 엔터로 줄바꿈)

[원고 텍스트]
(1~2문장 단위로 줄바꿈을 적용한 30대 찐후기 텍스트 /
가로로 길어지지 않게 25~35자마다 엔터 적용)

-------------------------------------------------------

[필수 해시태그]
{essential_tags if essential_tags else ''}
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 블로그 템플릿 규칙([카테고리: {current_cat}], [사진 장수: 최소 공백포함 1500자 이상, 정확히 {target_photos}장], [SEO 25~35자 제목], [촬영가이드 및 본문 20~30자 줄바꿈], [구분선 유지], [시술명 금지], [~했다 금지])을 100% 지켜 네이버 블로그 원고를 작성해줘:
- 카테고리: {current_cat}
- 사진 장수: {target_photos}장 (공백 포함 총 분량 최소 1500자 이상으로 매우 상세하고 풍성하게 작성)
- 브랜드명: {brand_name}
- 제품 USP: {product_usp}
- 행사/가격 정보: {event_info if event_info else '가이드 참조'}
- 타겟층: {target_audience}
- 필수 해시태그: {essential_tags if essential_tags else '없음'}
- 공식 계정 태그: {account_tags if account_tags else '없음'}
- 추가 전달사항: {guideline_text if guideline_text else '없음'}
{url_context}
"""
                contents = []
                if uploaded_images:
                    for img in uploaded_images:
                        contents.append(Image.open(img))
                contents.append(prompt_text)

                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_blog,
                            temperature=0.4,
                        )
                    )
                    st.session_state.blog_result = response.text
                except Exception as e:
                    st.error(f"블로그 원고 생성 중 오류가 발생했습니다: {e}")

# ==================== [6. 결과 화면: 눈에 띄는 설정값 뱃지 UI] ====================
current_result = st.session_state.insta_result if is_insta else st.session_state.blog_result
main_title = "인스타그램 대본" if is_insta else "블로그 원고"
config_info = f"{st.session_state.product_category} · 장면 {st.session_state.insta_scene_count}개" if is_insta else f"{st.session_state.product_category} · 사진 {st.session_state.blog_photo_count}장"

badge_html = f'<div class="result-header-wrapper"><span class="result-main-title">{main_title}</span><span class="result-config-badge"><span class="dot"></span>{config_info}</span></div>'
st.markdown(badge_html, unsafe_allow_html=True)

if current_result:
    st.code(current_result, language="markdown")
else:
    st.markdown(
        f'<div class="empty-result-box">아직 생성된 {main_title}가 없습니다.<br>상단 중앙의 <b>하트(❤️) 버튼</b>을 누르면 생성이 시작됩니다.</div>', 
        unsafe_allow_html=True
    )
