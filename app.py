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

st.set_page_config(page_title="RAMILOVE v2", layout="wide")

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
theme_border = "#ff4b72" if is_insta else "#00ff6f"

st.markdown(f"""
<style>
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
    .st-key-tab_insta button {{
        background: {insta_gradient if is_insta else '#484c54'} !important;
        border: {'2px solid #ff4b72' if is_insta else '1px solid #5a5f69'} !important;
        border-radius: 30px !important;
        height: 48px !important;
        width: 100% !important;
    }}
    .st-key-tab_insta button * {{
        color: {'#ffffff' if is_insta else '#f0f0f0'} !important;
        font-size: 16px !important;
        font-weight: 800 !important;
    }}
    .st-key-tab_blog button {{
        background: {naver_green if not is_insta else '#484c54'} !important;
        border: {'2px solid #00ff6f' if not is_insta else '1px solid #5a5f69'} !important;
        border-radius: 30px !important;
        height: 48px !important;
        width: 100% !important;
    }}
    .st-key-tab_blog button * {{
        color: {'#ffffff' if not is_insta else '#f0f0f0'} !important;
        font-size: 16px !important;
        font-weight: 800 !important;
    }}
    .st-key-btn_generate_main button {{
        width: 80px !important;
        height: 80px !important;
        min-width: 80px !important;
        max-width: 80px !important;
        border-radius: 50% !important;
        background: #FFFFFF !important;
        border: {'5px solid transparent' if is_insta else f'5px solid {naver_green}'} !important;
        box-shadow: 0 0 18px { 'rgba(220, 39, 67, 0.5)' if is_insta else 'rgba(3, 199, 90, 0.5)' } !important;
        transition: all 0.25s ease-in-out !important;
        position: relative !important;
        padding: 0 !important;
        margin: 0 auto !important;
        overflow: hidden !important;
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
    }}
    .result-config-badge span.dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: {theme_bg};
        display: inline-block;
    }}
    .stCodeBlock {{
        position: relative !important;
        border-radius: 14px !important;
        border: 1px solid #3d424b !important;
        background: #1e2025 !important;
    }}
    .stCodeBlock pre {{
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
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
    }}
</style>
""", unsafe_allow_html=True)

# ==================== [3. 상단 레이아웃] ====================
st.markdown('<div class="ramilove-header">RAMILOVE v2</div>', unsafe_allow_html=True)

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
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script", "style", "nav", "footer", "noscript"]):
                script.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text[:4000] if len(text) >= 100 else ""
        return ""
    except Exception:
        return ""

# ==================== [파이썬 강제 후처리 엔진 (Validator Engine)] ====================
def strict_validator_engine(text, brand, product):
    """
    AI가 아무렇게나 출력해도 파이썬 정규식과 문자열 조작으로 
    모든 규칙을 강제로 교정하는 방망이 깎는 노인식 후처리기.
    """
    if not text:
        return text

    lines = text.split('\n')
    processed_lines = []
    
    in_caption = False
    in_tags = False

    for line in lines:
        stripped = line.strip()
        
        # 1. 캡션 영역 감지 및 문장 단위 강제 분할 (한 줄 뭉치기 방지)
        if "#광고 캡션" in line or "광고 캡션" in line:
            in_caption = True
            processed_lines.append(line)
            continue
        elif "해시태그 및 계정 태그" in line or "썸네일 재요약" in line:
            in_caption = False

        # 2. 해시태그 영역 감지 및 세로 정렬 강제
        if "#해시태그" in line or "해시태그:" in line:
            in_tags = True
            processed_lines.append(line)
            continue
        elif "계정 태그:" in line or "썸네일 재요약" in line:
            in_tags = False

        if in_tags and stripped.startswith('#'):
            # 해시태그가 가로로 붙어있으면 쪼개서 세로로 삽입
            tags = re.findall(r'#[\w\d가-힣]+', stripped)
            if len(tags) > 1:
                for t in tags:
                    processed_lines.append(t)
                continue

        # 3. 캡션 내 긴 문장 강제 줄바꿈 (. ? ! 기준으로 엔터 삽입)
        if in_caption and len(stripped) > 30:
            sentences = re.split(r'(?<=[.?!])\s+', stripped)
            for s in sentences:
                if s.strip():
                    processed_lines.append(s.strip())
            continue

        processed_lines.append(line)

    return "\n".join(processed_lines)

# ==================== [4. 사이드바 구성] ====================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">RAMILOVE v2</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section-title"><span class="theme-badge">1</span> 가이드 & 제품 자료 등록</div>', unsafe_allow_html=True)
    uploaded_images = st.file_uploader(
        "가이드라인 / 기획안 캡처 이미지 첨부 (권장)", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    guideline_url = st.text_input("가이드라인 링크 URL", placeholder="https://notion.so/...")
    product_url = st.text_input("제품 상세페이지 링크 URL", placeholder="https://oliveyoung.co.kr/...")
    guideline_text = st.text_area("추가 메모 / 가이드 텍스트", placeholder="필수 멘트, 행사 정보 입력")
    
    analyze_btn = st.button("추출 정보 채우기", use_container_width=True, key="btn_analyze")
    
    if analyze_btn:
        if not uploaded_images and not guideline_url.strip() and not product_url.strip() and not guideline_text.strip():
            st.warning("분석할 이미지, 링크 또는 메모를 입력해주세요.")
        else:
            with st.spinner("정보 추출 중..."):
                url_context = ""
                if guideline_url.strip():
                    g_text = fetch_url_content(guideline_url.strip())
                    if g_text: url_context += f"\n[가이드라인]:\n{g_text}\n"
                if product_url.strip():
                    p_text = fetch_url_content(product_url.strip())
                    if p_text: url_context += f"\n[상세페이지]:\n{p_text}\n"

                contents = [Image.open(img) for img in uploaded_images] if uploaded_images else []
                extract_prompt = f"가이드라인을 정밀 분석해 브랜드명, 제품명, USP, 행사정보, 해시태그를 추출하세요.\n메모: {guideline_text}\n{url_context}"
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
                    st.success("정보 추출 완료!")
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    st.markdown("---")
    st.markdown('<div class="sidebar-section-title"><span class="theme-badge">2</span> 설정 정보</div>', unsafe_allow_html=True)
    categories = ["기초/스킨케어", "색조/메이크업", "선케어/클렌징", "헤어/바디", "이너뷰티/다이어트", "뷰티소품/디바이스"]
    st.selectbox("제품 카테고리", categories, key="product_category")

    brand_name = st.text_input("정확한 브랜드명", value=st.session_state.brand_name)
    product_name = st.text_input("정확한 제품명", value=st.session_state.product_name)
    product_usp = st.text_area("제품 USP", value=st.session_state.product_usp, height=100)
    event_info = st.text_area("행사 정보", value=st.session_state.event_info, height=70)
    target_audience = st.text_input("타겟층", value=st.session_state.target_audience)
    essential_tags = st.text_input("필수 해시태그", value=st.session_state.essential_tags)
    account_tags = st.text_input("공식 계정 태그", value=st.session_state.account_tags)

def get_url_context():
    ctx = ""
    if guideline_url.strip():
        t = fetch_url_content(guideline_url.strip())
        if t: ctx += f"\n[가이드라인 링크 내용]: {t}\n"
    if product_url.strip():
        t = fetch_url_content(product_url.strip())
        if t: ctx += f"\n[제품 상세페이지 내용]: {t}\n"
    return ctx

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# ==================== [5. 콘텐츠 생성 로직] ====================
if generate_action:
    if not brand_name or not product_usp:
        st.warning("사이드바에서 브랜드명과 제품 USP를 입력해주세요.")
    else:
        url_context = get_url_context()
        contents = [Image.open(img) for img in uploaded_images] if uploaded_images else []

        if is_insta:
            current_cat = st.session_state.product_category
            with st.spinner("릴스 콘티 생성 중 (Validator 적용)..."):
                sys_instruct = f"""
당신은 숏폼 뷰티 전문 콘티 작가입니다. 브랜드: {brand_name}, 제품: {product_name}

[엄격 규칙]
1. 썸네일 글자 수 제한: 첫째 줄 공백 제외 최대 10자 이내 / 둘째 줄 공백 제외 최대 12자 이내.
2. 장면 설명 및 썸네일 설명은 의미 단위마다 엔터(\n)를 쳐서 2~3줄 이상 세로로 분할 작성.
3. 나레이션에 브랜드명({brand_name}) 언급 시 자막 첫 줄은 반드시 `{brand_name} (로고 삽입) {product_name}` 덩어리로 유지.
4. 자막은 나레이션의 명사형 요약. 서술형 금지. 슬래시 포맷('/') 사용 시 위아래 한 줄 띄우기.
5. 비포애프터 포함 시 자막에 (비포애프터) 단독 줄 추가.
6. 캡션은 문장마다 반드시 엔터를 쳐서 여러 줄 분할. 해시태그는 세로로 한 줄씩 나열. 나레이션 총합 공백 포함 280자 이내.
"""
                prompt = f"""
아래 정보를 바탕으로 인스타그램 릴스 콘티를 작성해줘:
- 카테고리: {current_cat}
- 브랜드명: {brand_name}
- 제품명: {product_name}
- USP: {product_usp}
- 행사정보: {event_info}
- 타겟: {target_audience}
- 해시태그: {essential_tags}
- 계정 태그: {account_tags}
- 메모: {guideline_text}
{url_context}
"""
                contents.append(prompt)
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruct,
                            temperature=0.4,
                        )
                    )
                    st.session_state.insta_result = strict_validator_engine(response.text, brand_name, product_name)
                except Exception as e:
                    st.error(f"오류 발생: {e}")

        else:
            current_cat = st.session_state.product_category
            with st.spinner("네이버 SEO 블로그 원고 생성 중 (15~20컷 구성 & Validator 적용)..."):
                sys_instruct = f"""
당신은 네이버 상위 노출 전문 뷰티 블로거입니다. 브랜드: {brand_name}, 제품: {product_name}

[엄격 규칙]
1. 기계식 인사말("안녕하세요 뷰티 인플루언서입니다") 절대 금지. 친근한 찐후기 톤으로 즉시 시작.
2. 네이버 SEO 최적화를 위해 **반드시 총 15장 ~ 20장 분량의 사진 컷([사진 1] ~ [사진 20])**을 구성할 것.
3. 사진 설명을 나중에 몰아서 쓰지 말고, **[사진 X] 촬영 가이드 바로 밑에 그 사진에 해당하는 상세 본문 원고를 즉시 1:1 밀착 매칭**할 것.
4. 본문 원고의 모든 문장은 문장마다 엔터(\n)를 쳐서 세로로 풍성하게 분할할 것. (한 줄 쓰기 뭉치기 엄격 금지)
5. 해시태그는 각 해시태그마다 반드시 엔터를 쳐서 세로로 한 줄씩 나열할 것.
6. 공백 제외 총분량 1,500자 ~ 2,000자 이상 확보. 시술명 금지.
"""
                prompt = f"""
아래 정보를 바탕으로 네이버 블로그 원고를 작성해줘:
- 카테고리: {current_cat}
- 브랜드명: {brand_name}
- 제품명: {product_name}
- USP: {product_usp}
- 행사정보: {event_info}
- 타겟: {target_audience}
- 해시태그: {essential_tags}
- 계정 태그: {account_tags}
- 메모: {guideline_text}
{url_context}
"""
                contents.append(prompt)
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruct,
                            temperature=0.4,
                        )
                    )
                    st.session_state.blog_result = strict_validator_engine(response.text, brand_name, product_name)
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# ==================== [6. 결과 화면 렌더링] ====================
current_result = st.session_state.insta_result if is_insta else st.session_state.blog_result
main_title = "인스타그램 대본" if is_insta else "블로그 원고"
config_info = f"{st.session_state.product_category} · Validator 엔진 활성화"

st.markdown(f'<div class="result-header-wrapper"><span class="result-main-title">{main_title}</span><span class="result-config-badge"><span class="dot"></span>{config_info}</span></div>', unsafe_allow_html=True)

if current_result:
    st.code(current_result, language="markdown")
else:
    st.markdown(f'<div class="empty-result-box">아직 생성된 {main_title}가 없습니다.<br>상단 중앙의 <b>EXECUTE (하트) 버튼</b>을 누르면 강제 후처리 엔진이 작동하여 생성이 시작됩니다.</div>', unsafe_allow_html=True)
