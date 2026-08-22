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

# 세션 상태 초기화
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
if "generated_result" not in st.session_state:
    st.session_state.generated_result = ""

is_insta = (st.session_state.content_mode == "instagram")

# 스타일 CSS 주입
insta_gradient = "linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)"
naver_green = "#03C75A"

st.html(f"""
<style>
    /* 1. 중앙 정렬 RAMILOVE 타이틀 */
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

    /* 2. 1열 수평 정렬 컨테이너 내부 수직 중앙 맞춤 */
    div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
    }}

    /* 좌측 탭: INSTAGRAM */
    .st-key-tab_insta button {{
        background: {insta_gradient if is_insta else '#484c54'} !important;
        border: {'2px solid #ff4b72' if is_insta else '1px solid #5a5f69'} !important;
        border-radius: 30px !important;
        height: 50px !important;
        box-shadow: {'0 4px 15px rgba(220, 39, 67, 0.5)' if is_insta else 'none'} !important;
    }}
    .st-key-tab_insta button * {{
        color: {'#ffffff' if is_insta else '#f0f0f0'} !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
    }}

    /* 우측 탭: BLOG */
    .st-key-tab_blog button {{
        background: {naver_green if not is_insta else '#484c54'} !important;
        border: {'2px solid #00ff6f' if not is_insta else '1px solid #5a5f69'} !important;
        border-radius: 30px !important;
        height: 50px !important;
        box-shadow: {'0 4px 15px rgba(3, 199, 90, 0.5)' if not is_insta else 'none'} !important;
    }}
    .st-key-tab_blog button * {{
        color: {'#ffffff' if not is_insta else '#f0f0f0'} !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
    }}

    /* 중앙 하트 생성 버튼 (98px 원형) */
    .st-key-btn_generate_main {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }}
    .st-key-btn_generate_main button {{
        width: 98px !important;
        height: 98px !important;
        min-width: 98px !important;
        max-width: 98px !important;
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
        margin: 0 auto !important;
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
        width: 44px !important;
        height: 44px !important;
        background: {insta_gradient if is_insta else naver_green} !important;
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
</style>
""")

# 중앙 영문 타이틀 출력
st.markdown('<div class="ramilove-header">RAMILOVE</div>', unsafe_allow_html=True)

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

with st.sidebar:
    st.header("1️⃣ 가이드 & 제품 자료 등록")
    uploaded_images = st.file_uploader(
        "📷 가이드라인 / 기획안 캡처 이미지 첨부 (권장)", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True,
        help="체험단 앱(오늘룩, 레뷰 등) 웹뷰는 보안상 링크 대신 화면을 캡처해서 올려주시면 100% 정확하게 인식합니다."
    )
    guideline_url = st.text_input(
        "🔗 가이드라인 링크 URL (노션, 웹페이지 등)",
        placeholder="https://notion.so/..."
    )
    product_url = st.text_input(
        "🛍️ 제품 상세페이지 링크 URL (올리브영/스마트스토어 등)",
        placeholder="https://oliveyoung.co.kr/..."
    )
    guideline_text = st.text_area(
        "📝 추가 메모 / 가이드 텍스트 (선택)",
        placeholder="필수 멘트, 추가 행사 정보, 강조점 등을 입력하세요."
    )
    
    analyze_btn = st.button("⚡ 자료 종합 분석 & 입력창 채우기", use_container_width=True)
    
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
3. 제품 USP: 제품의 실제 성분, 텍스처(제형), 고민 부위 해결 효과, 임상시험 수치 추출
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
                    
                    st.success("✅ 분석 완료! 추출된 내용을 확인하고 필요시 수정해주세요.")
                    
                    if (g_crawl_fail or p_crawl_fail) and not uploaded_images:
                        st.info("💡 팁: 앱 전용 웹뷰(오늘룩)나 일부 쇼핑몰은 웹 보안상 링크 직접 읽기가 제한됩니다. 가이드 화면을 캡처해서 상단 '📷 이미지 첨부'에 올리시면 100% 완벽하게 인식됩니다.")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.header("2️⃣ 추출 정보 확인 및 수정")
    
    brand_name = st.text_input("정확한 브랜드명 (임의 변경 절대 금지)", value=st.session_state.brand_name)
    product_usp = st.text_area("제품 USP / 주요 특징", value=st.session_state.product_usp, height=100)
    event_info = st.text_area("행사/가격/기획전 정보 (일정, 할인내용)", value=st.session_state.event_info, height=70)
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

# ==================== [1열 수평 정렬: INSTAGRAM - 하트 - BLOG] ====================
col_insta, col_heart, col_blog = st.columns([0.42, 0.16, 0.42])

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

# ==================== [대본 / 원고 생성 로직] ====================
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
            with st.spinner("7~8개 핵심 씬 구성의 30초 이상 고품질 릴스 콘티를 작성 중입니다..."):
                system_instruction_reels = f"""
[Role & Goal]
당신은 숏폼(릴스/쇼츠/틱톡) 뷰티 전문 최고급 콘티 작가 "뷰티 릴스 대본 작성기"입니다.
사용자가 제공하는 [가이드라인 이미지/텍스트, 제품 상세페이지 내용, 제품 USP, 이벤트/공구/기획전 정보]를 완벽히 분석하여, 초반 3초 극강 후킹과 7~8개의 알찬 핵심 장면으로 구성된 30초~45초 러닝타임의 고품질 릴스 촬영 콘티를 작성합니다.

[핵심 절대 원칙 (CRITICAL)]

1. [자막 분절 요약 원칙 (CRITICAL)]:
- 각 장면의 나레이션 문장을 크게 전반부와 후반부 2개의 핵심 의미로 나눈 뒤, 자막은 반드시 아래와 같이 [앞쪽 나레이션 요약 / 뒤쪽 나레이션 요약] 구조로 작성합니다.
- (예시 나레이션: "집에서도 시술급으로 모공 초집중 케어하고 싶다면 이번 올영세일 기간에 브이티코스메틱 신상으로 무조건 정착해 보세요")
  -> 자막:
     집에서 시술급 모공 집중 케어
     /
     올영세일 신상 무조건 정착

2. [썸네일 추천 문구 최소 5선 필수 생성]:
- [베스트 썸네일] 1종 외에 [추천 썸네일 문구 5선]을 반드시 별도로 작성합니다.
- 모든 썸네일은 2줄 형태이며, 첫째 줄은 공백 제외 10자 이내, 둘째 줄은 공백 제외 12자 이내를 엄수합니다.

3. [7~8개 핵심 씬(Scene) 구성 - 30초 이상 러닝타임 유지]:
- 장면 갯수를 [1. 장면]부터 [7. 장면] 또는 [8. 장면]까지 핵심 7~8개 씬으로 구성합니다.
- 각 씬마다 3~4초 분량의 대사와 연출을 알차게 담아, 씬 수는 7~8개이면서 전체 영상 시간은 반드시 30초 이상(30~45초) 나오도록 작성합니다.

4. [초반 0~3초 극강 후킹 연출 (1번 씬)]:
- 1번 씬은 시청자가 스크롤을 멈추도록 극명한 비포애프터, 파격적인 제형 토출, 외국인 싹쓸이 대란 등 시각적/청각적 후킹을 극대화하여 구성합니다.

5. [빠른 템포 나레이션 분량 엄수 (30초 이상)]:
- 빠른 템포로 읽었을 때 30초 이상(약 35~45초) 나오는 분량인 공백 포함 450자 ~ 550자 내외로 풍성하게 작성합니다.
- 전체 나레이션은 최하단 '나레이션만 정리'에 순서대로 모아서 출력합니다.

6. [서술어 중복 절대 금지 (표현 다양화)]:
- 한 대본 내에서 동일한 서술어나 종결 어미가 2회 이상 반복되지 않도록 엄격히 통제합니다.
- (금지 예시: ~좋아요. ~도 좋아요. / ~느낌이에요. ~하는 느낌이에요.)
- (권장 예시: ~정착했잖아요, ~감탄 나오더라고요, ~싹 잡히는 기분이에요, ~유용한 것 같아요, ~무조건 챙기세요, ~놀랍더라고요, ~손이 자주 가요 등 문장마다 종결 어미를 다채롭게 변형)

7. [브랜드명 및 필수 요소 원형 유지]:
- 브랜드명은 반드시 '{brand_name}' 그대로 단 1글자의 변형도 없이 사용합니다.
- 가이드 필수 해시태그('{essential_tags}') 외에는 임의 추천 태그를 추가하지 않습니다.
- 행사 정보('{event_info}')는 마지막 씬 및 캡션에 정확한 기간, 할인 가격, 구매처를 명시합니다.

8. [자막 표기 규칙]:
- 자막에 특수문자/이모티콘/느낌표 금지
- 자막 줄바꿈 시 한 줄에 쓰지 않고 반드시 단독 줄로 / 배치
- 각주는 (하단 각주 삽입)과 * 표시 명시
- 비포애프터 씬에는 자막 영역에 단독 줄로 '비포 애프터' 기재

[출력 양식 템플릿 - 아래 형태를 100% 준수하여 출력할 것]

썸네일
썸네일(비주얼 연출 컷 설명) : (영상의 핵심 후킹을 담은 직관적인 비주얼 연출 묘사)

[베스트 썸네일]
(첫째 줄: 띄어쓰기 포함, 공백 제외 10자 이내)
(둘째 줄: 띄어쓰기 포함, 공백 제외 12자 이내)

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

[1. 장면]
(0~3초 극강 후킹 연출: 해외 바이럴 대란 또는 고민 부위 클로즈업)

자막：
(앞쪽 나레이션 요약 문장)
/
(뒤쪽 나레이션 요약 문장)
/
(필요시 로고 또는 제품명)

나레이션：
(시선을 사로잡는 강력한 후킹 구어체 대사)


[2. 장면]
(피부 고민 공감 및 제품 제형 토출 연출)

자막：
비포 애프터
/
(앞쪽 나레이션 요약 문장)
/
(뒤쪽 나레이션 요약 문장)

나레이션：
(대사)


[3. 장면]
(핵심 성분 및 텍스처 발림성/흡수력 연출)

자막：
(앞쪽 나레이션 요약 문장)
/
(뒤쪽 나레이션 요약 문장)

나레이션：
(대사)


[4. 장면]
(고민 부위 집중 롤링/마사지 실사용 연출)

자막：
(앞쪽 나레이션 요약 문장)*
(하단 각주 삽입)
*각주 내용
/
(뒤쪽 나레이션 요약 문장)

나레이션：
(대사)


[5. 장면]
(풀페이스 확장 케어: 이마, 미간, 팔자, 목주름 등 꿀팁 연출)

자막：
(앞쪽 나레이션 요약 문장)
/
(뒤쪽 나레이션 요약 문장)

나레이션：
(대사)


[6. 장면]
(전후 비교 체감 비포&애프터 및 광채 탄력 연출)

자막：
비포 애프터
/
(앞쪽 나레이션 요약 문장)
/
(뒤쪽 나레이션 요약 문장)

나레이션：
(대사)


[7. 장면]
(프로모션 일정, 할인 가격, 올리브영 특가 구매처 안내 및 마무리 컷)

자막：
(프로모션 기간/일정)
/
(할인 안내 및 구매처)
(하단 각주 삽입)
*각주 내용 (있을 경우)

나레이션：
(행사 혜택 및 추천 마무리 대사)

로고 초반에 삽입 / 음악ㅇ / 끝

#광고 캡션
(30대 여성 찐후기 톤: 리얼 후킹 문구 + 솔직 사용 경험 및 핵심 장점 + 기획전/특가 일정, 할인 가격, 구매처 안내 포함)

{essential_tags if essential_tags else ''}
계정 태그: {account_tags if account_tags else '@공식계정아이디'}

댓글에 #올영1위 (또는 지정 댓글 태그)

장면 요약
1. 장면： (1번 씬 연출 요약)
2. 장면： (2번 씬 연출 요약)
3. 장면： (3번 씬 연출 요약)
4. 장면： (4번 씬 연출 요약)
5. 장면： (5번 씬 연출 요약)
6. 장면： (6번 씬 연출 요약)
7. 장면： (7번 씬 연출 요약)

나레이션만 정리
(1번부터 마지막 씬까지의 전체 나레이션 전문을 모아서 출력 / 서술어 중복 없는 자연스러운 30~45초 분량, 공백 포함 450~550자 내외)
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 템플릿과 원칙(자막 앞뒤 요약 분절, 썸네일 5선, 7~8개 씬 구성, 초반 3초 후킹, 30초 이상 나레이션, 서술어 중복 금지)을 100% 지켜 인스타그램 숏폼 대본을 작성해줘:
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
                    st.session_state.generated_result = response.text
                except Exception as e:
                    st.error(f"대본 생성 중 오류가 발생했습니다: {e}")

        else:
            with st.spinner("네이버 뷰티 인플루언서 스타일로 SEO 최적화 블로그 원고를 작성 중입니다..."):
                system_instruction_blog = f"""
[Role & Goal]
당신은 네이버 상위 노출 전문 뷰티 블로거이자 전문 에디터입니다.
사용자가 제공한 [가이드라인, 제품 상세페이지 내용, USP, 행사 정보]를 분석하여 네이버 블로그 검색 알고리즘(C-Rank, D.I.A.)과 스마트블록에 최적화된 고품질 포스팅 원고를 작성합니다.

[핵심 절대 원칙 (CRITICAL)]
1. [브랜드명 및 고유명칭 원형 유지]: 브랜드명은 반드시 '{brand_name}' 그대로 단 1글자의 변형도 없이 사용합니다.
2. [네이버 SEO 최적화 제목]:
   - 메인 키워드(브랜드명 + 제품군 + 핵심 고민/특징)가 앞단에 포함된 매력적인 제목 5선을 상단에 추천합니다.
3. [블로그 전용 구성]:
   - '자막', '#광고 캡션', '나레이션만 정리' 등 숏폼 전용 섹션은 일체 생성하지 않습니다.
   - 각 문단 흐름마다 [사진 1], [사진 2], [사진 3]... 순서대로 어떤 사진을 찍어 올려야 하는지 구체적인 [촬영 가이드]를 명시합니다.
   - 각 사진 아래에는 30대 여성 찐후기 톤의 자연스럽고 상세한 [원고 텍스트]를 작성합니다.
4. [체계적인 흐름 (체류시간 극대화)]:
   - 도입부: 일상 피부 고민 공감 및 제품을 접하게 된 계기 (후킹)
   - 패키지 및 성분 분석: 제품 외관, 토출구(팁/용기), 주요 성분 및 USP 소개
   - 제형 및 발림성: 텍스처, 끈적임 여부, 흡수력 디테일 묘사
   - 실사용 과정 및 부위별 케어법: 사용 방법 및 꿀팁 (눈가, 팔자, 목주름 등)
   - 전후 비교 및 총평: 비포/애프터 체감 후기
   - 프로모션 및 특가 안내: 프로모션 일정('{event_info}'), 할인 가격, 구매처 링크 안내
5. [과대광고 심의 준수]: 치료/의학적 효능 대신 사용감과 체감 위주로 기술합니다.
6. [필수 해시태그]: 가이드에 지정된 필수 해시태그('{essential_tags}')만 최하단에 정확히 배치합니다.

[출력 양식 템플릿 - 아래 형식을 엄격히 지켜 출력할 것]

[네이버 블로그 추천 제목 5선]
1. (메인 키워드 포함 클릭률 높은 제목)
2. (메인 키워드 포함 클릭률 높은 제목)
3. (메인 키워드 포함 클릭률 높은 제목)
4. (메인 키워드 포함 클릭률 높은 제목)
5. (메인 키워드 포함 클릭률 높은 제목)

-------------------------------------------------------

[사진 1]
(촬영 가이드: 제품 본품 연출 컷 또는 고민 부위 클로즈업 컷)

[원고 텍스트]
(도입부: 최근 겪고 있는 피부 고민과 제품을 사용해보게 된 계기를 솔직하고 친근하게 이야기하는 텍스트)


[사진 2]
(촬영 가이드: 제품 패키지 외관 및 토출구/어플리케이터 클로즈업 컷)

[원고 텍스트]
(브랜드 및 제품의 핵심 성분과 USP, 특징을 소개하는 텍스트)


[사진 3]
(촬영 가이드: 손등이나 피부에 제형을 덜어내어 텍스처와 발림성을 보여주는 컷)

[원고 텍스트]
(제형의 촉촉함, 흡수력, 끈적임 여부 등을 생생하게 묘사하는 텍스트)


[사진 4]
(촬영 가이드: 실제 얼굴/고민 부위에 제품을 도포하고 롤링/마사지하며 바르는 실사용 컷)

[원고 텍스트]
(직접 사용하면서 느낀 사용 편의성과 부위별 관리 꿀팁을 전하는 텍스트)


[사진 5]
(촬영 가이드: 제품 사용 전후 비교(비포&애프터) 컷 또는 광채/탄력이 정돈된 피부 컷)

[원고 텍스트]
(실제 사용 후 피부 변화 체감과 솔직한 찐후기 총평)


[사진 6]
(촬영 가이드: 올리브영/판매처 화면 캡처 또는 제품을 들고 있는 마무리 컷)

[원고 텍스트]
(프로모션 일정, 할인 혜택, 특가 가격, 구매처 안내 및 마무리 추천 멘트)

-------------------------------------------------------

[필수 해시태그]
{essential_tags if essential_tags else ''}
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 블로그 템플릿 규칙을 100% 지켜 네이버 블로그 원고를 작성해줘:
- 브랜드명: {brand_name}
- 제품 USP: {product_usp}
- 행사/가격 정보: {event_info if event_info else '가이드 참조'}
- 타겟층: {target_audience}
- 필수 해시태그: {essential_tags if essential_tags else '없음'}
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
                    st.session_state.generated_result = response.text
                except Exception as e:
                    st.error(f"블로그 원고 생성 중 오류가 발생했습니다: {e}")

# ==================== [결과 화면: 복사하기 아이콘 & 원문 출력] ====================
if st.session_state.generated_result:
    label_type = "인스타그램 대본" if is_insta else "블로그 원고"
    
    # 텍스트 복사 버튼 (JS 클립보드 복사)
    escaped_result = json.dumps(st.session_state.generated_result)
    copy_html = f"""
    <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
        <button onclick="navigator.clipboard.writeText({escaped_result}); alert('📋 {label_type}이(가) 클립보드에 복사되었습니다!');" 
                style="background: #2a2d32; color: #ffffff; border: 1px solid #5a5f69; border-radius: 8px; padding: 10px 18px; font-size: 15px; font-weight: 800; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all 0.2s;">
            📋 {label_type} 복사하기
        </button>
    </div>
    """
    st.components.v1.html(copy_html, height=55)
    st.markdown(st.session_state.generated_result)
