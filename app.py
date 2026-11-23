# 📋 app.py · [과제 화면] 분리수거 도우미 — 제목 · 칸은 내 API 의 GET / 에서 가져옴 (분석 한 번에 요청 1번)
# · Secrets 두 줄 : API_URL (내 과제 API 의 vercel.app 주소) · APP_ACCESS_CODE (Vercel 과 같은 값)
# · 예시 사진(bottle.jpg)을 저장소에 같이 올리면 '예시 사진으로 해 보기' 버튼이 생김
import base64
import io
import os

import requests
import streamlit as st
from PIL import Image

EXAMPLE_IMAGE = "bottle.jpg"

try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = "http://localhost:8000"
try:
    ACCESS_CODE = st.secrets["APP_ACCESS_CODE"]
except Exception:
    ACCESS_CODE = ""

try:                                                 # GET / — 이름 · 아이콘 · 소개 · 칸 (Gemini 요청 없음)
    info = requests.get(f"{API_URL}/", timeout=30).json()
    fields = info["fields"]
except (requests.RequestException, ValueError, KeyError):
    st.error("❌ API 서버에 닿지 못함 — Secrets 의 API_URL 이 내 vercel.app 주소인지 확인하세요.")
    st.caption(f"API 주소 : {API_URL}")
    st.stop()

st.set_page_config(page_title=info.get("name", "나만의 AI"), page_icon=info.get("icon", "📷"))
st.title(f"{info.get('icon', '')} {info.get('name', '나만의 AI')}")
st.caption(f"{info.get('description', '')} · 결과 칸 : {' · '.join(fields)} · 얼굴 · 신분증 · 카드 번호가 보이는 사진은 올리지 마세요")


def photo_b64(raw):
    """사진을 긴 쪽 1024px 이하 JPEG 로 줄이고 base64 글자로 바꾼다"""
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    image.thumbnail((1024, 1024))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def analyze(raw):
    try:
        response = requests.post(f"{API_URL}/analyze", json={"image_b64": photo_b64(raw)},
                                 headers={"X-Access-Code": ACCESS_CODE}, timeout=120)
    except requests.RequestException:
        st.error("❌ API 서버에 닿지 못함 — 잠시 뒤 다시 눌러 보세요.")
        return
    if response.status_code != 200:
        st.error(f"❌ 상태 번호 {response.status_code} : {response.json().get('detail')}")
        return
    data = response.json()
    st.table([{"칸": name, "내용": data["result"].get(name, "")} for name in fields])
    st.caption(f"상태 번호 200 · 토큰 {data['tokens']} · 지역마다 기준이 다를 수 있으니 참고용입니다")


camera = st.camera_input("카메라로 찍기") if st.toggle("카메라 켜기") else None
upload = st.file_uploader("또는 버릴 물건 사진 올리기", type=["png", "jpg", "jpeg", "webp"])
photo = camera or upload
if photo is not None:
    st.image(photo, width=240)
if st.button("버리는 방법 알아보기", key="go", disabled=photo is None):
    with st.spinner("내 API 에 묻는 중..."):
        analyze(photo.getvalue())
if os.path.exists(EXAMPLE_IMAGE) and st.button("예시 사진으로 해 보기", key="sample"):
    st.image(EXAMPLE_IMAGE, width=240)
    with st.spinner("내 API 에 묻는 중..."):
        analyze(open(EXAMPLE_IMAGE, "rb").read())
