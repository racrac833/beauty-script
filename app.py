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

# 세션 상태 초기화
if "brand_name" not in st.session_state:
    st.session_state.brand_name = ""
if "product_usp" not in st.session_state:
    st.session_state.product_usp = ""
if "target_audience" not in st.session_state:
    st.session_state.target_audience = "30대 여성"
if "essential_tags" not in st.session_state:
    st.session_state.essential_tags = ""
if "event_info" not in st.session_state:
    st.session_state.event_info = ""

class ExtractedGuide(BaseModel):
    brand_name: str = Field(description="가이드/이미지/링크에서 확인된 원문 그대로의 정확한 브랜드명 (단 1글자도 변경/번역 금지)")
    product_usp: str = Field(description="가이드에서 강조하는 제품의 핵심 USP, 특징, 효과 요약")
    target_audience: str = Field(description="타겟층 정보 (기본: 30대 여성)")
    essential_tags: str = Field(description="가이드에 명시된 필수 해시태그 목록 (없으면 빈 문자열)")
    event_info: str = Field(description="기획전 일정, 당일 특가 날짜, 할인 가격, 구매처 링크 등의 행사 정보")

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
        "📝 추가 메모 / 가이드 텍스트 (선택)",
        placeholder="필수 멘트, 추가 행사 정보, 강조점 등을 입력하세요."
    )
    
    analyze_btn = st.button("⚡ 가이드 자동 분석 & 입력창 채우기", use_container_width=True)
    
    if analyze_btn:
        if not uploaded_images and not reference_url.strip() and not guideline_text.strip():
            st.warning("분석할 이미지, 링크 또는 메모를 하나 이상 입력해주세요.")
        else:
            with st.spinner("가이드 자료를 분석하여 정보를 추출 중입니다..."):
                url_context = ""
                if reference_url.strip():
                    crawled_text = fetch_url_content(reference_url.strip())
                    if crawled_text:
                        url_context = f"\n[참고 링크 내용]:\n{crawled_text}\n"

                contents = []
                if uploaded_images:
                    for img_file in uploaded_images:
                        contents.append(Image.open(img_file))
                
                extract_prompt = f"""
제공된 가이드라인 이미지, 텍스트, 링크 내용을 완벽히 분석하여 다음 항목을 정확히 추출하세요.
- 브랜드명: 원문 그대로 단 1글자도 변경/번역/축약하지 말고 추출
- 제품 USP: 제품의 핵심 특징, 성분, 효과 등
- 타겟층: 명시된 타겟층 (없다면 '30대 여성')
- 필수 해시태그: 가이드에 지정된 필수 해시태그만 추출 (임의 추천 금지, 없으면 빈칸)
- 행사 정보: 기획전 일정, 당일 특가 날짜, 할인 가격, 구매처 등

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
                    st.session_state.event_info = data.get("event_info", "")
                    
                    st.success("✅ 자동 분석 완료! 아래 내용을 확인 후 필요시 수정하세요.")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.header("2️⃣ 추출 정보 확인 및 수정")
    
    brand_name = st.text_input("정확한 브랜드명 (임의 변경 절대 금지)", value=st.session_state.brand_name)
    product_usp = st.text_area("제품 USP / 주요 특징", value=st.session_state.product_usp, height=100)
    event_info = st.text_area("행사/가격/기획전 정보", value=st.session_state.event_info, height=70)
    target_audience = st.text_input("타겟층", value=st.session_state.target_audience)
    essential_tags = st.text_input("필수 해시태그 (없으면 공란 유지)", value=st.session_state.essential_tags)
    
    st.markdown("---")
    generate_btn = st.button("🎬 젬스 규격 대본 생성하기", type="primary", use_container_width=True)

if generate_btn:
    if not brand_name or not product_usp:
        st.warning("브랜드명과 제품 USP를 확인해주세요.")
    else:
        with st.spinner("전문 콘티 작가 '뷰티 릴스 대본 작성기'가 규격에 맞게 대본을 작성 중입니다..."):
            url_context = ""
            if reference_url.strip():
                crawled_text = fetch_url_content(reference_url.strip())
                if crawled_text:
                    url_context = f"\n[참고 링크 내용]:\n{crawled_text}\n"

            system_instruction = f"""
[Role & Goal]
당신은 숏폼(릴스/쇼츠/틱톡) 뷰티 콘텐츠 전문 콘티 작가 "뷰티 릴스 대본 작성기"입니다.
사용자가 제공하는 [가이드라인 이미지/텍스트, 제품 USP, 이벤트/공구/기획전 정보, 대본 초안]을 완벽히 분석하여, 디테일·톤앤매너·핵심 소구점과 후반부 행사/가격 정보까지 100% 누락 없이 반영한 고품질 촬영 콘티를 작성합니다.

[핵심 절대 원칙 (CRITICAL)]

1. [브랜드명 및 고유 명칭 왜곡 절대 금지 (STRICT)]:
- 브랜드명은 반드시 사용자가 제공한 '{brand_name}' 그대로 단 1글자의 변형, 축약, 오역, 번역, 띄어쓰기 변경 없이 100% 동일하게만 사용합니다.
- 제품명, 라인명, 규격/중량, 소재, 디자인 등 구체적 수치와 명칭 역시 원형 그대로 유지합니다.

2. [해시태그 임의 생성/추가 절대 금지 (STRICT)]:
- 가이드라인에 지정된 필수 해시태그('{essential_tags}') 외에는 단 1개의 연관/추천/일반 해시태그(#뷰티, #릴스, #스킨케어 등)도 임의로 추가하지 않습니다.
- 제공된 필수 해시태그가 없을 경우, 해시태그 항목은 완전히 비워두거나 공란으로 처리합니다.

3. [모든 제품, 구성품 및 행사 정보 100% 반영]:
- 가이드/초안에 2개 이상의 제품이나 부속품이 포함되어 있다면, 절대 누락하거나 축소하지 않고 순서대로 전부 다룹니다.
- 기획전 일정, 당일 특가 날짜, 할인 가격, 구매처(올리브영/프로필 링크 등)를 임의 생략 없이 스크립트와 캡션에 모두 명시합니다.

4. [과대광고 심의 준수]:
- 의학적·치료적 효능을 단정 짓지 않고, 가이드에 명시된 올바른 사용법, 사용 편의성, 실제 체감 위주로 작성합니다.

5. [톤앤매너 - 30대 여성 찐후기 스타일]:
- 캡션과 나레이션은 작위적인 광고 문구를 지양하고, 30대 여성이 실제로 사용해보고 솔직하게 공유하는 자연스럽고 친근한 리얼 후기 어투로 작성합니다.

6. [장면 넘버링 및 가독성 분리]:
- 메인 스크립트의 각 씬 헤더는 반드시 ### [1. 장면], ### [2. 장면] 형태로 1씩 증가시키며 작성합니다.
- 각 씬 묶음(장면/자막/나레이션) 사이에는 구분선(-------------------------------------------------------)과 줄바꿈 여백을 반드시 넣습니다.
- 하단 '장면 요약' 섹션 역시 1. 장면：, 2. 장면：과 같이 순차 번호를 붙여 전체 씬을 나열합니다.

7. [자막 표기 및 특수 규칙 엄수]:
- 자막에는 이모티콘, 아이콘, 느낌표(!) 등 특수문자를 절대 사용하지 않습니다.
- 자막 줄바꿈 표기 시 한 줄에 /를 쓰지 않고, 반드시 줄바꿈하여 단독 줄로 /를 배치합니다.
- [비포&애프터 표기]: 비포/애프터 장면이 포함된 씬에서는 자막 영역에 반드시 비포 애프터 문구를 추가합니다.
- [각주 필수 삽입]: 나레이션이나 자막에 각주 표시(*)가 있을 경우, 해당 자막 바로 하단에 (하단 각주 삽입) 표시와 함께 각주 원문 내용을 명시합니다.

8. [썸네일 규칙]:
- 모든 썸네일 카피는 가독성을 위해 반드시 올바른 띄어쓰기를 적용하여 작성합니다.
- 2줄 썸네일 카피 작성 시, 첫째 줄은 공백 제외 최대 10자 이내, 둘째 줄은 공백 제외 최대 12자 이내로 엄격히 제한합니다.

9. [나레이션 분량 엄수]:
- 전체 나레이션 총합 분량은 공백 포함 280자 ~ 300자 내외로 타이트하게 작성합니다.

[출력 양식 및 포맷 가이드 (Strict Rule)]
반드시 아래의 양식 구조와 섹션 구성을 한 줄도 빠짐없이 엄격히 지켜 답변을 생성하세요.

썸네일
썸네일(비주얼 연출 컷 설명) : (영상의 핵심 후킹을 담은 직관적인 비주얼 연출 묘사)

[베스트 썸네일]
(첫째 줄: 띄어쓰기 필수, 공백 제외 10자 이내)
(둘째 줄: 띄어쓰기 필수, 공백 제외 12자 이내)

[추천 썸네일 문구 9선]
(※ 띄어쓰기 필수 준수 / 첫째 줄 공백 제외 10자 이내 / 둘째 줄 공백 제외 12자 이내)
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

6.
(첫째 줄)
(둘째 줄)

7.
(첫째 줄)
(둘째 줄)

8.
(첫째 줄)
(둘째 줄)

9.
(첫째 줄)
(둘째 줄)

-------------------------------------------------------

메인 스크립트

### [1. 장면]
카메라 앵글 → 인물 행동 → 제품 포인트 연출 흐름

자막：
자막 첫 문장
/
자막 둘째 문장

나레이션：
(30대 여성이 말하는 듯한 자연스럽고 솔직한 숏폼 구어체 / 지정된 정확한 브랜드명 사용)

-------------------------------------------------------

### [2. 장면]
카메라 앵글 → 인물 행동 → 제품 포인트 연출 흐름

자막：
자막 첫 문장*
/
자막 둘째 문장
(하단 각주 삽입)*각주 내용 기재
/
비포 애프터

나레이션：
(30대 여성이 말하는 듯한 자연스럽고 솔직한 숏폼 구어체)

-------------------------------------------------------
(※ 전체 씬 수에 맞춰 '### [3. 장면]', '### [4. 장면]'... 순서로 1씩 증가하며 마지막 씬까지 반복 작성)

하단 구성 요소 및 장면 요약

주의점
- 필수 표기 사항 (유료광고 표시 시점 및 위치)
- 브랜드 공식 로고 삽입 안내
- 음원 저작권 및 심의 유의사항 명시

#광고 캡션
(30대 여성 찐후기 톤: 리얼 후킹 문구 + 솔직 사용 경험 및 핵심 장점 + 기획전/특가 일정, 할인 가격, 구매처 안내 포함 / 지정된 브랜드명 철저 준수)

해시태그 및 계정 태그
해시태그: {essential_tags if essential_tags else ''}
계정 태그: @공식계정아이디

썸네일 재요약
썸네일(연출 설명) : (상단 썸네일 비주얼 연출 설명 재출력)
(베스트 썸네일 첫줄 카피 - 띄어쓰기 필수, 공백 제외 10자 이내)
(베스트 썸네일 둘째줄 카피 - 띄어쓰기 필수, 공백 제외 12자 이내)

장면 요약
1. 장면： (1번 씬의 연출 요약)
2. 장면： (2번 씬의 연출 요약)
(※ 전체 씬의 연출 흐름을 번호 순서대로 누락 없이 나열)

나레이션만 정리
(전체 씬의 나레이션을 순서대로 모아서 출력 / 전체 글자 수: 공백 포함 280자 ~ 300자 엄수)
"""
            prompt_text = f"""
다음 정보와 가이드 자료를 바탕으로 뷰티 숏폼 대본을 작성해줘:
- 정확한 브랜드명: {brand_name}
- 제품 USP: {product_usp}
- 행사/가격 정보: {event_info if event_info else '가이드 참조'}
- 타겟층: {target_audience}
- 필수 해시태그: {essential_tags if essential_tags else '없음'}
- 추가 전달사항: {guideline_text if guideline_text else '없음'}
{url_context}
"""
            contents = []
            if uploaded_images:
                for uploaded_file in uploaded_images:
                    contents.append(Image.open(uploaded_file))
            
            contents.append(prompt_text)

            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.5,
                    )
                )
                
                st.success("대본이 성공적으로 완성되었습니다!")
                
                # 워드 복사용 텍스트 박스 제공
                st.text_area("📋 워드 복사용 (전체 선택 후 복사)", response.text, height=300)
                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"대본 생성 중 오류가 발생했습니다: {e}")
