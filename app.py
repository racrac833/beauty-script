import os
import json
import re
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

generate_action = False

# ==================== [2. 테마 컬러 및 기본 스타일링] ====================
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

    /* 4. 사이드바 내부 RAMILOVE 로고 스타일 */
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

    /* 7. 결과창 헤더 뱃지 및 기울임꼴 절대 금지 */
    em, i, * {{
        font-style: normal !important;
    }}
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

    /* 8. 결과창 코드 블록 자동 줄바꿈 & 대형 복사 버튼 */
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
        font-style: normal !important;
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
    product_name: str = Field(description="실제 제품의 정확한 제품명 또는 라인명")
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
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en-US;q=0.7",
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

def validate_and_fix_result(text, brand, product):
    """
    파이썬 강제 후처리 검증 엔진 (공백 제외 30자 이상 강제 줄바꿈 보장형):
    1. 마크다운 볼드체(**) 제거
    2. [베스트 썸네일], [추천 썸네일 문구 9선] 영역은 띄어쓰기 보호
    3. 본문 텍스트, 캡션 등에서 공백 제외 글자수가 30자가 넘어가면 
       파이썬 코드가 강제로 절단하여 엔터(\n)를 박아 넣어 한 줄 쓰기를 원천 차단
    """
    if not text:
        return text

    # 마크다운 볼드체(**) 제거
    text = text.replace("**", "")

    lines = text.split('\n')
    processed_lines = []
    in_thumbnail_section = False

    for line in lines:
        stripped = line.strip()
        
        # 썸네일 영역은 띄어쓰기 및 글자 수 보호
        if "[베스트 썸네일]" in line or "[추천 썸네일 문구 9선]" in line:
            in_thumbnail_section = True
            processed_lines.append(line)
            continue
        elif "메인 스크립트" in line or "### [" in line or "사진 촬영 가이드" in line:
            in_thumbnail_section = False

        if in_thumbnail_section:
            processed_lines.append(line)
            continue

        # 해시태그 영역 세로 정렬
        if stripped.startswith('#') and ' ' in stripped:
            tags = re.findall(r'#[\w\d가-힣]+', stripped)
            if len(tags) > 1:
                for t in tags:
                    processed_lines.append(t)
                continue

        # 공백 제외 30자 이상 시 강제 줄바꿈 삽입
        no_space_len = len(stripped.replace(" ", ""))
        if no_space_len > 30 and not stripped.startswith('http') and not stripped.startswith('-') and not stripped.startswith('[사진'):
            parts = re.split(r'(?<=[.?!])\s+|(?<=[고서며데네죠요])\s+', stripped)
            current_chunk = ""
            for p in parts:
                if len(current_chunk.replace(" ", "")) + len(p.replace(" ", "")) > 25:
                    if current_chunk.strip():
                        processed_lines.append(current_chunk.strip())
                    current_chunk = p
                else:
                    current_chunk += " " + p if current_chunk else p
            if current_chunk.strip():
                processed_lines.append(current_chunk.strip())
            continue

        processed_lines.append(line)

    return "\n".join(processed_lines)

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
                if guideline_url.strip():
                    g_text = fetch_url_content(guideline_url.strip())
                    if g_text: url_context += f"\n[가이드라인 링크 내용]:\n{g_text}\n"
                if product_url.strip():
                    p_text = fetch_url_content(product_url.strip())
                    if p_text: url_context += f"\n[제품 상세페이지 내용]:\n{p_text}\n"

                contents = [Image.open(img) for img in uploaded_images] if uploaded_images else []
                extract_prompt = f"""
제공된 가이드라인 이미지, 가이드 링크, 제품 상세페이지 내용, 메모를 정밀 분석하여 실제 화장품/제품에 대한 정보를 정확히 추출하세요.

[절대 주의사항 (STRICT)]
1. '오늘룩(oneulook)', '레뷰(revu)', '체험단' 등은 마케팅 중개 플랫폼일 뿐 실제 화장품 브랜드명이 아닙니다. 절대 이를 브랜드명이나 해시태그로 추출하지 마세요.
2. 이미지와 상세페이지에 나오는 '실제 뷰티 제품의 브랜드명(예: 엑시스와이, 넘버즈인, 아누아 등)'과 '정확한 제품명'을 정확히 추출하세요.
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
                    st.session_state.product_name = data.get("product_name", "")
                    st.session_state.product_usp = data.get("product_usp", "")
                    st.session_state.target_audience = data.get("target_audience", "30대 여성")
                    st.session_state.essential_tags = data.get("essential_tags", "")
                    st.session_state.account_tags = data.get("account_tags", "")
                    st.session_state.event_info = data.get("event_info", "")
                    
                    st.success("분석 완료! 아래 추출된 내용을 확인하고 필요시 수정해주세요.")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.markdown('<div class="sidebar-section-title"><span class="theme-badge">2</span> 추출 정보 확인 및 설정</div>', unsafe_allow_html=True)
    
    categories = ["기초/스킨케어", "색조/메이크업", "선케어/클렌징", "헤어/바디", "이너뷰티/다이어트", "뷰티소품/디바이스"]
    st.selectbox("제품 카테고리 (대본 톤앤매너 설정)", categories, key="product_category")

    brand_name = st.text_input("정확한 브랜드명 (임의 변경 절대 금지)", value=st.session_state.brand_name)
    product_name = st.text_input("정확한 제품명 (임의 변경 절대 금지)", value=st.session_state.product_name)
    product_usp = st.text_area("제품 USP / 주요 특징", value=st.session_state.product_usp, height=100)
    event_info = st.text_area("행사 / 가격 / 기획전 정보 (일정, 할인내용)", value=st.session_state.event_info, height=70)
    target_audience = st.text_input("타겟층", value=st.session_state.target_audience)
    essential_tags = st.text_input("필수 해시태그", value=st.session_state.essential_tags)
    account_tags = st.text_input("공식 계정 태그", value=st.session_state.account_tags)

def get_url_context():
    url_context = ""
    if guideline_url.strip():
        g_text = fetch_url_content(guideline_url.strip())
        if g_text: url_context += f"\n[가이드라인 링크 내용]:\n{g_text}\n"
    if product_url.strip():
        p_text = fetch_url_content(product_url.strip())
        if p_text: url_context += f"\n[제품 상세페이지 내용]:\n{p_text}\n"
    return url_context

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ==================== [5. 대본 / 원고 생성 로직] ====================
if generate_action:
    if not brand_name or not product_usp:
        st.warning("왼쪽 사이드바에서 브랜드명과 제품 USP를 먼저 확인해주세요.")
    else:
        url_context = get_url_context()
        contents = [Image.open(img) for img in uploaded_images] if uploaded_images else []

        if is_insta:
            current_cat = st.session_state.product_category
            with st.spinner(f"[{current_cat}] 가이드라인 필수 항목 반영 맞춤형 릴스 콘티를 작성 중입니다..."):
                system_instruction_reels = f"""
[Role & Goal]
당신은 숏폼(릴스/쇼츠/틱톡) 뷰티 콘텐츠 전문 콘티 작가입니다.
사용자가 제공하는 [가이드라인 이미지/텍스트, 브랜드명: {brand_name}, 제품명: {product_name}, 제품 USP, 이벤트 정보, 카테고리: {current_cat}]를 완벽히 분석하여 고품질 촬영 콘티를 작성합니다.

[매우 중요: 절대 엄수해야 할 핵심 포맷 규칙 (ABSOLUTE CRITICAL)]
1. [썸네일 글자 수 및 띄어쓰기 유지 (절대 규칙)]:
- [베스트 썸네일] 및 [추천 썸네일 문구 9선]의 모든 썸네일 텍스트는 반드시 다음 글자 수 제한을 엄격히 준수하세요:
  * **첫째 줄: 띄어쓰기 포함, 공백 제외 최대 10자 이내**
  * **둘째 줄: 띄어쓰기 포함, 공백 제외 최대 12자 이내**
- **썸네일 문구 작성 시 단어 사이의 띄어쓰기를 반드시 포함하여 자연스럽게 작성하세요.**

2. [장면 설명 및 썸네일 설명 세로 분할]:
- [썸네일(비주얼 연출 컷 설명)]과 [### [X. 장면]] 아래의 촬영 컷 연출 설명은 절대 한 줄로 길게 쓰지 말고, 카메라 앵글, 모델 행동, 제형 연출 등 의미 단위마다 엔터(줄바꿈)를 쳐서 2~3줄 이상 세로로 풍성하게 나누어 작성하세요.

3. [메인 스크립트 순서 고정]:
- 반드시 **[장면] ➔ 자막 ➔ 나레이션** 순서대로 콘티를 구성하세요. 순서를 절대 바꾸지 마세요.

4. [자막 제품명 온전한 덩어리 유지 (절대 규칙)]:
- 나레이션에 브랜드명({brand_name})과 제품명({product_name})이 언급될 때, 자막 첫 줄에는 절대 단어가 쪼개지지 않고 온전한 덩어리인 **`{brand_name} (로고 삽입) {product_name}`** 형태로만 들어가야 합니다. 

5. [자막 슬래시 포맷 및 (비포애프터) 독립 격리 규칙 (매우 중요)]:
- 자막은 나레이션 대사의 핵심 내용을 직관적으로 압축한 명사형 단문이어야 합니다. 서술형(~해라, ~해보세요) 절대 금지.
- 두 줄 이상 자막은 반드시 아래 포맷처럼 **한 줄 띄우고, 슬래시(`/`)를 단독 줄로 배치한 뒤, 다시 한 줄을 띄어** 작성하세요:
  [자막 첫 줄]
  
  /
  
  [자막 둘째 줄]
- **`(비포애프터)` 키워드가 단독으로 쓰이든(`(비포애프터)`), 설명과 함께 쓰이든(`(비포애프터) 설명`) 다른 자막들과 섞이지 않고 반드시 독립된 자막 레이어로 들어가야 하므로, 위아래로 반드시 슬래시(`/`)를 단독 줄로 배치하여 완벽히 격리시키세요.**

6. [마크다운 강조(**) 금지 및 30자 초과 시 강제 줄바꿈]:
- **결과물 내에 마크다운 볼드체 별표(**)를 절대 사용하지 마세요.**
- **모든 텍스트 영역에서 공백 제외 30자 이상이 되면 반드시 엔터(줄바꿈)를 쳐서 텍스트가 가로로 길게 늘어지지 않게 하세요.**
- 전체 나레이션 총합 공백 포함 280자 이내 엄수. 기울임꼴 금지.

[출력 양식 템플릿]
썸네일
썸네일(비주얼 연출 컷 설명) : 
(의미 단위마다 엔터를 쳐서 세로로 여러 줄로 나누어 작성한 연출 묘사)

[베스트 썸네일]
(첫째 줄: 띄어쓰기 포함, 공백 제외 10자 이내)
(둘째 줄: 띄어쓰기 포함, 공백 제외 12자 이내)

[추천 썸네일 문구 9선]
1.
(첫째 줄: 띄어쓰기 포함, 공백 제외 10자 이내)
(둘째 줄: 띄어쓰기 포함, 공백 제외 12자 이내)
(2~9번 동일하게 썸네일 글자 수 및 띄어쓰기 준수)

메인 스크립트

### [1. 장면]
(의미 단위마다 엔터를 쳐서 세로로 여러 줄로 나누어 작성한 촬영 컷 연출 설명)

자막：
(자막 첫 줄: 브랜드명 (로고 삽입) 제품명 또는 명사형 단문)

/

(비포애프터) 또는 (비포애프터) 설명 - 반드시 슬래시로 위아래 격리

/

(다음 자막 또는 명사형 단문)

나레이션：
(가이드 필수 나레이션 반영)
첫 번째 나레이션 문장
두 번째 나레이션 문장

-------------------------------------------------------

하단 구성 요소 및 장면 요약
주의점
필수 표기 사항
브랜드 공식 로고 삽입 안내
음원 저작권 및 심의 유의사항 명시

#광고 캡션
(30대 여성 찐후기 톤 / 공백 제외 30자 이상 시 반드시 엔터 줄바꿈)

해시태그 및 계정 태그
해시태그: 
#해시태그1
#해시태그2
#해시태그3
(반드시 세로로 한 줄씩 나열)
계정 태그: {account_tags if account_tags else '@vtcosmetics_official'}

썸네일 재요약
장면 요약
나레이션만 정리
1. 첫 번째 나레이션 문장
2. 두 번째 나레이션 문장
(반드시 공백 제외 30자 이상 시 엔터를 쳐서 세로로 분할 정리)
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 템플릿 규칙([카테고리: {current_cat}], [가이드 필수 항목 100% 반영], [썸네일은 띄어쓰기 포함하여 첫줄 공백 제외 10자 이내, 둘째줄 공백 제외 12자 이내 엄수], [장면 설명은 의미 단위마다 엔터 쳐서 세로 분할], [메인 스크립트는 장면 ➔ 자막 ➔ 나레이션 순서 엄수], [나레이션에 브랜드명/제품명 언급 시 자막에 {brand_name} (로고 삽입) {product_name} 형태를 절대 쪼개지 말고 온전한 덩어리로 표기], [자막은 나레이션을 요약한 명사형 단문], [마크다운 별표(**) 사용 금지], [(비포애프터) 및 (비포애프터) 설명은 다른 자막과 섞이지 않도록 반드시 위아래 슬래시(/)로 독립 격리], [공백 제외 30자 이상 시 무조건 엔터 쳐서 줄바꿈], [해시태그는 무조건 세로로 한 줄씩 나열], [자막 서술형 절대 금지 및 명사형 단문], [자막 포맷: 한 줄 띄우고 / 슬래시 단독 줄 배치 후 한 줄 띄우기], [나레이션 공백포함 280자 이내], [출력물 내 프롬프트 지시어 삭제], [기울임꼴 금지])을 100% 지켜 인스타그램 숏폼 대본을 작성해줘:
- 카테고리: {current_cat}
- 브랜드명: {brand_name}
- 제품명: {product_name}
- 제품 USP: {product_usp}
- 행사/가격 정보: {event_info if event_info else '가이드 참조'}
- 타겟층: {target_audience}
- 필수 해시태그: {essential_tags if essential_tags else '없음'}
- 공식 계정 태그: {account_tags if account_tags else '@공식계정아이디'}
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
                    final_output = validate_and_fix_result(response.text, brand_name, product_name)
                    st.session_state.insta_result = final_output
                except Exception as e:
                    st.error(f"대본 생성 중 오류가 발생했습니다: {e}")

        else:
            current_cat = st.session_state.product_category
            with st.spinner(f"[{current_cat}] 가이드라인 필수 항목 반영 네이버 SEO 블로그 원고를 작성 중입니다 (15~20컷 구성)..."):
                system_instruction_blog = f"""
[Role & Goal]
당신은 네이버 상위 노출 전문 뷰티 블로거이자 전문 에디터입니다.
사용자가 제공한 [카테고리: {current_cat}, 가이드라인, 제품 상세페이지 내용, USP, 행사 정보]를 분석하여 네이버 블로그 검색 알고리즘과 스마트블록에 최적화된 고품질 포스팅 원고를 작성합니다.

[매우 중요: 블로그 원고 및 사진 촬영 가이드 분리 배치 규칙 (ABSOLUTE CRITICAL)]
1. [기계식 인사말 절대 금지]:
- "안녕하세요 뷰티 인플루언서입니다" 같은 낡고 촌스러운 인사는 절대 쓰지 말고, 30대 뷰티 블로거의 친근한 톤(예: 요즘 피부 속건조가 너무 심해서...)으로 곧바로 자연스럽게 시작하세요.

2. [블로그 추천 제목 5선 포함]:
- 최상단에 네이버 SEO 최적화된 추천 제목 5선(공백 포함 25~35자 내외)을 먼저 제시하세요.

3. [전체 본문 원고 먼저 작성]:
- **추천 제목 바로 아래에 전체 본문 원고를 먼저 쭉 이어서 작성하세요.**
- 본문 원고의 모든 텍스트 영역에서 공백 제외 30자 이상이 되면 반드시 엔터(줄바꿈)를 쳐서 세로로 풍성하게 작성하세요. (한 줄 쓰기 원천 차단)
- 총분량 공백 제외 1,500자 ~ 2,000자 이상 확보. '시술' 등 의료 표현 금지.

4. [사진 촬영 가이드 하단 모아쓰기 (매우 중요)]:
- **전체 본문 원고가 끝난 하단에, 사진 촬영 가이드만 따로 모아서 한 번에 작성하세요.**
- 형식은 반드시 아래처럼 `[사진 X] : 내용` 형태로 다음 줄에 이어서 작성하세요.
  [사진 1] : 제품 언박싱 컷
  [사진 2] : 패키지 전면 컷
  [사진 3] : 제형 토출 컷
  ... (최소 15장 ~ 20장까지 순서대로 나열)

5. [해시태그 세로 나열 & 별표(**) 금지]:
- 최하단 [필수 해시태그] 영역에서는 각 해시태그마다 반드시 엔터를 쳐서 세로로 한 줄씩 나열하세요.
- **결과물 내에 마크다운 볼드체 별표(**)를 절대 사용하지 마세요.**

[출력 양식 템플릿]
[네이버 블로그 추천 제목 5선 (SEO 최적 글자수 25~35자)]
1. (브랜드명 및 키워드 배치)
2. 
3. 
4. 
5. 

-------------------------------------------------------

[전체 본문 원고]
(공백 제외 1500~2000자 내외 / 문장마다 엔터 쳐서 세로로 풍성하게 작성 / 기계식 인사말 금지)

-------------------------------------------------------

[사진 촬영 가이드 및 배치 컷 리스트]
[사진 1] : 제품 언박싱 및 패키지 전면 컷
[사진 2] : 패키지 측면 및 단상자 오픈 컷
[사진 3] : 본품 토출구 및 제형 질감 컷
(동일한 구조로 [사진 4]부터 [사진 15~20]까지 [사진 X] : 내용 형식으로 나열)

-------------------------------------------------------

[필수 해시태그]
#해시태그1
#해시태그2
#해시태그3
(반드시 세로로 한 줄씩 나열)
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 블로그 템플릿 규칙([카테고리: {current_cat}], [기계식 인사말 절대 금지 및 자연스러운 후기 톤], [블로그 추천 제목 5선 포함], [전체 본문 원고를 먼저 쭉 작성], [본문 원고는 공백 제외 30자 이상 시 무조건 엔터 쳐서 줄바꿈], [사진 촬영 가이드는 하단에 [사진 1] : 내용 형식으로 모아서 15~20장 작성], [마크다운 별표(**) 사용 금지], [해시태그 무조건 세로로 한 줄씩 나열], [가이드 필수 내용 100% 반영], [시술명 금지])을 100% 지켜 네이버 블로그 원고를 작성해줘:
- 카테고리: {current_cat}
- 브랜드명: {brand_name}
- 제품명: {product_name}
- 제품 USP: {product_usp}
- 행사/가격 정보: {event_info if event_info else '가이드 참조'}
- 타겟층: {target_audience}
- 필수 해시태그: {essential_tags if essential_tags else '없음'}
- 공식 계정 태그: {account_tags if account_tags else '@vtcosmetics_official'}
- 추가 전달사항: {guideline_text if guideline_text else '없음'}
{url_context}
"""
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
                    final_output = validate_and_fix_result(response.text, brand_name, product_name)
                    st.session_state.blog_result = final_output
                except Exception as e:
                    st.error(f"블로그 원고 생성 중 오류가 발생했습니다: {e}")

# ==================== [6. 결과 화면: 설정값 뱃지 UI] ====================
current_result = st.session_state.insta_result if is_insta else st.session_state.blog_result
main_title = "인스타그램 대본" if is_insta else "블로그 원고"
config_info = f"{st.session_state.product_category} · 가이드 필수 반영 맞춤 구성"

badge_html = f'<div class="result-header-wrapper"><span class="result-main-title">{main_title}</span><span class="result-config-badge"><span class="dot"></span>{config_info}</span></div>'
st.markdown(badge_html, unsafe_allow_html=True)

if current_result:
    st.code(current_result, language="markdown")
else:
    st.markdown(
        f'<div class="empty-result-box">아직 생성된 {main_title}가 없습니다.<br>상단 중앙의 <b>하트(❤️) 버튼</b>을 누르면 생성이 시작됩니다.</div>', 
        unsafe_allow_html=True
    )
