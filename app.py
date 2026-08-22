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

st.set_page_config(page_title="뷰티 릴스 대본 작성기", layout="wide")
st.title("🎬 뷰티 숏폼 릴스 대본 생성기")

# API 클라이언트 초기화
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error(".env 파일에 GEMINI_API_KEY를 설정해주세요.")
    st.stop()

client = genai.Client(api_key=api_key)

# 세션 상태(자동 입력값 유지) 초기화
if "brand_name" not in st.session_state:
    st.session_state.brand_name = ""
if "product_usp" not in st.session_state:
    st.session_state.product_usp = ""
if "target_audience" not in st.session_state:
    st.session_state.target_audience = ""
if "essential_tags" not in st.session_state:
    st.session_state.essential_tags = ""
if "tone_manner" not in st.session_state:
    st.session_state.tone_manner = "트렌디하고 발랄한"

# 가이드라인 자동 추출을 위한 Pydantic 구조체 정의
class ExtractedGuide(BaseModel):
    brand_name: str = Field(description="가이드/이미지/링크에서 확인된 정확한 브랜드명")
    product_usp: str = Field(description="가이드에서 강조하는 제품의 핵심 USP, 특징, 효과 2~3가지 요약")
    target_audience: str = Field(description="주요 추천 타겟층 (예: 2030 수부지, 모공 고민러 등)")
    recommended_tone: str = Field(description="어울리는 톤앤매너 (트렌디하고 발랄한, 전문적이고 신뢰감 있는, 솔직 담백한 리뷰형, 자연스러운 일상 브이로그형 중 택1)")
    essential_tags: str = Field(description="가이드에 명시된 필수 해시태그 목록 (쉼표로 구분)")

# 웹 링크 텍스트 추출 함수
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

# 사이드바 영역
with st.sidebar:
    st.header("1️⃣ 가이드 자료 등록")
    uploaded_images = st.file_uploader(
        "📷 가이드라인 / 기획안 이미지 첨부", 
        type=["png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True
    )
    reference_url = st.text_input(
        "🔗 참고 링크 URL",
        placeholder="https://example.com/product"
    )
    guideline_text = st.text_area(
        "📝 추가 메모 / 전달사항 (선택)",
        placeholder="추가로 반영할 내용이 있다면 입력하세요."
    )
    
    # 자동 채우기 버튼
    analyze_btn = st.button("⚡ 가이드 자동 분석 & 입력창 채우기", use_container_width=True)
    
    # 자동 채우기 분석 로직
    if analyze_btn:
        if not uploaded_images and not reference_url.strip() and not guideline_text.strip():
            st.warning("분석할 이미지, 링크 또는 메모를 하나 이상 입력해주세요.")
        else:
            with st.spinner("가이드 자료를 분석하여 정보를 추출 중입니다..."):
                url_context = ""
                if reference_url.strip():
                    crawled_text = fetch_url_content(reference_url.strip())
                    if crawled_text:
                        url_context = f"\n[참고 링크 텍스트]:\n{crawled_text}\n"
                    else:
                        url_context = f"\n[참고 링크 URL]: {reference_url.strip()}\n"

                contents = []
                if uploaded_images:
                    for img_file in uploaded_images:
                        contents.append(Image.open(img_file))
                
                extract_prompt = f"""
제공된 이미지, 웹페이지 내용, 메모를 꼼꼼히 분석하여 다음 항목을 정확히 추출해주세요.
- 브랜드명 (임의 변경 금지, 가이드에 적힌 명칭 그대로)
- 제품 USP / 주요 셀링 포인트
- 타겟층
- 어울리는 톤앤매너
- 필수 해시태그 (지정된 것이 있다면 쉼표로 연결, 없으면 추천 2~3개)

[추가 메모]: {guideline_text}
{url_context}
"""
                contents.append(extract_prompt)

                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ExtractedGuide,
                            temperature=0.2,
                        )
                    )
                    data = json.loads(response.text)
                    st.session_state.brand_name = data.get("brand_name", "")
                    st.session_state.product_usp = data.get("product_usp", "")
                    st.session_state.target_audience = data.get("target_audience", "")
                    st.session_state.essential_tags = data.get("essential_tags", "")
                    
                    tone_val = data.get("recommended_tone", "트렌디하고 발랄한")
                    if tone_val in ["트렌디하고 발랄한", "전문적이고 신뢰감 있는", "솔직 담백한 리뷰형", "자연스러운 일상 브이로그형"]:
                        st.session_state.tone_manner = tone_val
                    
                    st.success("✅ 자동 분석 완료! 아래 내용을 확인 후 필요시 수정하세요.")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.header("2️⃣ 추출 정보 확인 및 수정")
    
    # 자동 채워진 값 표시 및 사용자 직접 수정 가능
    brand_name = st.text_input("정확한 브랜드명", value=st.session_state.brand_name)
    product_usp = st.text_area("제품 USP / 주요 특징", value=st.session_state.product_usp, height=120)
    target_audience = st.text_input("타겟층", value=st.session_state.target_audience)
    
    tone_options = ["트렌디하고 발랄한", "전문적이고 신뢰감 있는", "솔직 담백한 리뷰형", "자연스러운 일상 브이로그형"]
    current_tone_idx = tone_options.index(st.session_state.tone_manner) if st.session_state.tone_manner in tone_options else 0
    tone_manner = st.selectbox("톤앤매너", tone_options, index=current_tone_idx)
    
    essential_tags = st.text_input("필수 해시태그 (쉼표 구분)", value=st.session_state.essential_tags)
    
    st.markdown("---")
    generate_btn = st.button("🎬 최종 대본 생성하기", type="primary", use_container_width=True)

# 메인 결과 출력 영역
if generate_btn:
    if not brand_name or not product_usp:
        st.warning("브랜드명과 제품 USP를 입력하거나 자동 분석을 먼저 실행해주세요.")
    else:
        with st.spinner("전문 콘티 작가가 가이드와 조건을 반영해 대본을 작성 중입니다..."):
            url_context = ""
            if reference_url.strip():
                crawled_text = fetch_url_content(reference_url.strip())
                if crawled_text:
                    url_context = f"\n[참고 링크 내용]: {crawled_text}\n"

            system_instruction = f"""
당신은 숏폼(릴스/쇼츠/틱톡) 뷰티 콘텐츠 전문 콘티 작가 '뷰티 릴스 대본 작성기'입니다.
제공된 이미지 가이드, 링크, 그리고 사용자가 확인/수정한 설정값에 맞춰 완벽한 콘티를 작성하세요.

[엄격 준수 규칙]
1. 브랜드 이름은 반드시 사용자가 지정한 '{brand_name}'만 사용해야 하며, 절대 임의로 수정하거나 변경하지 마세요.
2. 해시태그는 사용자가 지정한 필수 해시태그({essential_tags}) 이외에는 일절 임의로 추가하지 마세요.
3. 제공된 가이드라인 이미지 및 메모의 필수 소구점, 이벤트 정보, 주의사항을 철저히 반영하세요.
4. 숏폼에 최적화된 30~45초 분량의 대본을 [초반 후킹(0~3초) - 본론(제품 사용/비포애프터) - 결론/CTA] 형식으로 화면 연출(Visual)과 나레이션(Audio) 표 형태로 작성하세요.
"""
            prompt_text = f"""
다음 정보와 가이드 자료를 바탕으로 뷰티 숏폼 대본을 작성해줘:
- 브랜드명: {brand_name}
- 제품 USP: {product_usp}
- 타겟층: {target_audience}
- 톤앤매너: {tone_manner}
- 필수 해시태그: {essential_tags}
- 추가 메모: {guideline_text if guideline_text else '없음'}
{url_context}
"""
            contents = []
            if uploaded_images:
                for uploaded_file in uploaded_images:
                    contents.append(Image.open(uploaded_file))
            
            contents.append(prompt_text)

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    )
                )
                
                st.success("대본이 성공적으로 완성되었습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"대본 생성 중 오류가 발생했습니다: {e}")