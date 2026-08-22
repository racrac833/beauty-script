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

st.set_page_config(page_title="뷰티 콘텐츠 생성기", layout="wide")

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

# 커스텀 CSS
st.markdown("""
<style>
    /* 상단 인스타그램 모드 선택 버튼 */
    div.stButton > button[key="tab_insta_active"] {
        background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        padding: 12px 0px !important;
        border-radius: 10px !important;
        border: none !important;
    }
    div.stButton > button[key="tab_insta_inactive"] {
        background-color: #f8f9fa !important;
        color: #666666 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 12px 0px !important;
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
    }
    
    /* 상단 블로그 모드 선택 버튼 */
    div.stButton > button[key="tab_blog_active"] {
        background-color: #03C75A !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        padding: 12px 0px !important;
        border-radius: 10px !important;
        border: none !important;
    }
    div.stButton > button[key="tab_blog_inactive"] {
        background-color: #f8f9fa !important;
        color: #666666 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 12px 0px !important;
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
    }

    /* 하단 인스타그램 생성 실행 버튼 */
    div.stButton > button[key="btn_insta_generate"] {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%) !important;
        color: white !important;
        font-size: 19px !important;
        font-weight: 800 !important;
        padding: 14px 20px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(220, 39, 67, 0.3) !important;
    }

    /* 하단 네이버 블로그 생성 실행 버튼 */
    div.stButton > button[key="btn_blog_generate"] {
        background-color: #03C75A !important;
        color: white !important;
        font-size: 19px !important;
        font-weight: 800 !important;
        padding: 14px 20px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(3, 199, 90, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("✨ 뷰티 인스타그램 대본 & 블로그 원고 생성기")

# API 클라이언트 초기화
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error(".env 파일에 GEMINI_API_KEY를 설정해주세요.")
    st.stop()

client = genai.Client(api_key=api_key)

class ExtractedGuide(BaseModel):
    brand_name: str = Field(description="가이드/상세페이지/이미지에서 확인된 원문 그대로의 정확한 브랜드명 (단 1글자도 변경/번역 금지)")
    product_usp: str = Field(description="제품의 핵심 USP, 제형 특성, 주요 성분 및 임상 효과 요약")
    target_audience: str = Field(description="타겟층 정보 (기본: 30대 여성)")
    essential_tags: str = Field(description="가이드에 명시된 필수 해시태그 목록 (#포함하여 쉼표로 연결)")
    account_tags: str = Field(description="가이드에 명시된 공식 계정 태그 (@포함)")
    event_info: str = Field(description="정확한 프로모션 일정(예: 8월 1일~8월 29일), 할인 가격, 혜택, 구매처")

def fetch_url_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text[:4000]
        return ""
    except Exception:
        return ""

with st.sidebar:
    st.header("1️⃣ 가이드 & 제품 자료 등록")
    uploaded_images = st.file_uploader(
        "📷 가이드라인 / 기획안 이미지 첨부", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    guideline_url = st.text_input(
        "🔗 가이드라인 링크 URL (노션, 구글문서 등)",
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
            with st.spinner("가이드와 상세페이지를 종합 분석하여 정보를 추출 중입니다..."):
                url_context = ""
                if guideline_url.strip():
                    g_text = fetch_url_content(guideline_url.strip())
                    if g_text:
                        url_context += f"\n[가이드라인 링크 내용]:\n{g_text}\n"
                
                if product_url.strip():
                    p_text = fetch_url_content(product_url.strip())
                    if p_text:
                        url_context += f"\n[제품 상세페이지 내용]:\n{p_text}\n"

                contents = []
                if uploaded_images:
                    for img_file in uploaded_images:
                        contents.append(Image.open(img_file))
                
                extract_prompt = f"""
제공된 가이드라인 이미지, 가이드 링크, 제품 상세페이지 내용, 메모를 100% 정밀 분석하여 다음 항목을 정확히 추출하세요.

[추출 주의사항]
1. 브랜드명: 원문 그대로 단 1글자도 변경/번역/축약하지 말고 추출
2. 제품 USP: 상세페이지와 가이드에서 강조하는 제형, 핵심 성분, 임상시험 수치, 실제 체감 장점을 매력적으로 요약
3. 행사 정보: 가이드의 내부 코드가 아닌, 실제 소비자에게 안내할 '정확한 프로모션 기간(예: 8월 1일~8월 29일)', '할인 가격/혜택', '구매처' 형태로 정제하여 추출
4. 필수 해시태그: 가이드 전체에서 필수 해시태그(#...)를 찾아 추출
5. 계정 태그: 공식 인스타그램 계정(@...) 추출

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
                    
                    st.success("✅ 자동 분석 완료! 아래 내용을 확인 후 필요시 수정하세요.")
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

# ==================== [메인 영역: 심플 모드 선택 버튼] ====================
col1, col2 = st.columns(2)

with col1:
    insta_key = "tab_insta_active" if st.session_state.content_mode == "instagram" else "tab_insta_inactive"
    if st.button("인스타그램", use_container_width=True, key=insta_key):
        st.session_state.content_mode = "instagram"
        st.rerun()

with col2:
    blog_key = "tab_blog_active" if st.session_state.content_mode == "blog" else "tab_blog_inactive"
    if st.button("블로그", use_container_width=True, key=blog_key):
        st.session_state.content_mode = "blog"
        st.rerun()

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# ==================== [선택된 모드에 따른 생성 실행] ====================

if st.session_state.content_mode == "instagram":
    generate_insta = st.button("📸 인스타그램 대본 생성하기", use_container_width=True, key="btn_insta_generate")
    
    if generate_insta:
        if not brand_name or not product_usp:
            st.warning("왼쪽 사이드바에서 브랜드명과 제품 USP를 먼저 확인해주세요.")
        else:
            with st.spinner("전문 콘티 작가가 젬스 표준 양식으로 인스타그램 대본을 작성 중입니다..."):
                url_context = get_url_context()

                system_instruction_reels = f"""
[Role & Goal]
당신은 숏폼(릴스/쇼츠/틱톡) 뷰티 콘텐츠 전문 콘티 작가 "뷰티 릴스 대본 작성기"입니다.
사용자가 제공하는 [가이드라인 이미지/텍스트, 제품 상세페이지 내용, 제품 USP, 이벤트/공구/기획전 정보, 대본 초안]을 완벽히 분석하여, 디테일·톤앤매너·핵심 소구점과 후반부 행사/가격 정보까지 100% 누락 없이 반영한 고품질 촬영 콘티를 작성합니다.

[핵심 절대 원칙 (CRITICAL)]
1. [브랜드명 왜곡 절대 금지]: 브랜드명은 반드시 '{brand_name}' 그대로 단 1글자의 변형도 없이 사용합니다.
2. [해시태그 임의 추가 금지]: 가이드에 지정된 필수 해시태그('{essential_tags}') 외에는 임의 추천 태그를 추가하지 않습니다.
3. [행사 정보 100% 반영]: '{event_info}'에 포함된 정확한 프로모션 일정, 할인 가격, 구매처를 대본 4번 장면과 캡션에 명시합니다.
4. [톤앤매너]: 30대 여성이 솔직하게 공유하는 자연스럽고 친근한 찐후기 구어체로 작성합니다.
5. [장면 넘버링 및 가독성]: [1. 장면], [2. 장면] 순차 넘버링을 적용하고 장면 사이 빈 줄을 유지합니다.
6. [자막 표기 규칙]: 자막에 특수문자/이모티콘/느낌표 금지, 줄바꿈 시 단독 줄로 / 배치, 각주는 (하단 각주 삽입)과 * 표시, 비포애프터는 단독 줄로 표기합니다.
7. [썸네일 규칙]: 2줄 작성, 첫줄 공백제외 10자 이내, 둘째줄 공백제외 12자 이내 엄수.
8. [나레이션 분량 엄수]: 전체 나레이션 총합 분량은 공백 포함 280자 ~ 300자 내외로 타이트하게 작성합니다.

[출력 양식 템플릿]
썸네일
썸네일(비주얼 연출 컷 설명) : (비주얼 연출 묘사)

(베스트 썸네일 첫줄: 띄어쓰기 포함, 공백 제외 10자 이내)
(베스트 썸네일 둘째줄: 띄어쓰기 포함, 공백 제외 12자 이내)

[1. 장면]
카메라 앵글 → 인물 행동 → 제품 포인트 연출 흐름

자막：
자막 첫 문장
/
자막 둘째 문장
/
(필요시 로고 또는 제품명)

나레이션：
(30대 여성이 말하는 솔직한 구어체 대사)


[2. 장면]
카메라 앵글 → 인물 행동 → 제품 포인트 연출 흐름

자막：
자막 문장
/
자막 문장
/
비포 애프터

나레이션：
(대사)


[3. 장면]
카메라 앵글 → 인물 행동 → 제품 포인트 연출 흐름

자막：
자막 문장*
(하단 각주 삽입)
*각주 내용
/
자막 문장

나레이션：
(대사)


[4. 장면]
카메라 앵글 → 인물 행동 → 행사/할인 혜택 안내 흐름

자막：
비포 애프터
/
(프로모션 기간/일정)
/
(할인 안내 및 구매처)
(하단 각주 삽입)
*각주 내용 (있을 경우)

나레이션：
(행사 혜택 및 제품 추천 마무리 대사)

로고 초반에 삽입 / 음악ㅇ / 끝

#광고 캡션
(30대 여성 찐후기 톤: 리얼 후킹 문구 + 솔직 사용 경험 및 핵심 장점 + 기획전/특가 일정, 할인 가격, 구매처 안내 포함)

{essential_tags if essential_tags else ''}
계정 태그: {account_tags if account_tags else '@공식계정아이디'}

댓글에 #올영1위 (또는 지정 댓글 태그)

장면： (1번 씬 연출 요약)

장면： (2번 씬 연출 요약)

장면： (3번 씬 연출 요약)

장면： (4번 씬 연출 요약)

나레이션만 정리
(1~4번 씬의 전체 나레이션 전문을 모아서 줄바꿈하여 출력 / 공백 포함 280~300자)
"""
                prompt_text = f"""
다음 정보를 바탕으로 위 템플릿과 규칙을 100% 동일하게 지켜 인스타그램 숏폼 대본을 작성해줘:
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
                            system_instruction=system_instruction_reels,
                            temperature=0.4,
                        )
                    )
                    st.success("📸 인스타그램 대본이 성공적으로 완성되었습니다!")
                    st.text_area("📋 워드 복사용 (전체 선택 후 복사하여 워드에 붙여넣으세요)", response.text, height=350)
                    st.markdown("---")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"대본 생성 중 오류가 발생했습니다: {e}")

else:
    generate_blog = st.button("📝 블로그 원고 생성하기", use_container_width=True, key="btn_blog_generate")
    
    if generate_blog:
        if not brand_name or not product_usp:
            st.warning("왼쪽 사이드바에서 브랜드명과 제품 USP를 먼저 확인해주세요.")
        else:
            with st.spinner("네이버 뷰티 인플루언서 스타일로 SEO 최적화 블로그 원고를 작성 중입니다..."):
                url_context = get_url_context()

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
                    st.success("📝 블로그 원고가 성공적으로 완성되었습니다!")
                    st.text_area("📋 블로그/워드 복사용 (전체 선택 후 복사)", response.text, height=400)
                    st.markdown("---")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"블로그 원고 생성 중 오류가 발생했습니다: {e}")
