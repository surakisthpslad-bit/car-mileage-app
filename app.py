import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
from datetime import datetime

# 1. ดึง API Key จากระบบหลังบ้านของ Streamlit (เพื่อความปลอดภัย)
# หากรันบนเครื่องตัวเองให้เปลี่ยนเป็น genai.configure(api_key="YOUR_API_KEY")
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.warning("⚠️ ยังไม่ได้ตั้งค่า API Key ใน Streamlit Secrets")

# ใช้ Gemini 1.5 Flash ซึ่งเร็วและเหมาะกับรูปภาพ
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="ระบบบันทึกไมล์รถยนต์", page_icon="🚗")
st.title("🚗 อัปโหลดรูปหน้าปัดรถยนต์")
st.write("ระบบจะอ่านวันที่, ระยะทางของวัน (Trip), และระยะทางรวม (ODO) ให้อัตโนมัติ")

uploaded_file = st.file_uploader("📷 ถ่ายรูปหรืออัปโหลดรูปหน้าปัดรถ", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='รูปภาพที่อัปโหลด', use_column_width=True)
    
    with st.spinner('🤖 AI กำลังวิเคราะห์หน้าปัดรถ...'):
        # 2. คำสั่ง (Prompt) บังคับให้ AI ตอบเป็น JSON
        prompt = """
        Analyze this car dashboard image. Extract the following 3 pieces of information:
        1. Date visible on the dashboard (if any). If not visible, return "Not Found".
        2. Trip mileage (distance for the current trip). Return only numbers/decimals. If not found, return 0.
        3. Total ODO mileage (total distance). Return only integer numbers. If not found, return 0.
        
        IMPORTANT: You must output ONLY a valid JSON object without any markdown tags or extra text.
        Format example: {"date": "15/10/2023", "trip": 45.2, "odo": 150000}
        """
        
        try:
            response = model.generate_content([prompt, image])
            # ทำความสะอาดข้อความเผื่อ AI ส่ง markdown ```json มาด้วย
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(raw_text)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านภาพ: กรุณาลองถ่ายรูปให้ชัดเจนขึ้น")
            data = {"date": "Not Found", "trip": 0, "odo": 0}

    st.success("✨ วิเคราะห์สำเร็จ! กรุณาตรวจสอบและแก้ไขข้อมูลก่อนบันทึก")
    
    # 3. สร้างฟอร์มให้ผู้ใช้ตรวจสอบความถูกต้อง
    with st.form("data_form"):
        # วันที่: หาก AI หาไม่เจอ ให้ใช้วันที่ปัจจุบันเป็นค่าเริ่มต้น
        default_date = datetime.today().strftime('%Y-%m-%d')
        display_date = default_date if data.get('date') == "Not Found" else data.get('date', default_date)
        
        input_date = st.text_input("📅 วันที่ใช้งาน", value=display_date)
        input_trip = st.number_input("🛣️ ระยะทางของวันนี้ (Trip)", value=float(data.get('trip', 0)), format="%.1f")
        input_odo = st.number_input("🔄 ระยะทางรวมทั้งหมด (ODO)", value=int(data.get('odo', 0)), step=1)
        
        submitted = st.form_submit_button("💾 ยืนยันและบันทึกข้อมูล")
        
        if submitted:
            # 4. ส่วนนี้คือจุดที่คุณสามารถนำข้อมูลไปต่อยอด เช่น ส่งเข้า Google Sheets
            st.balloons()
            st.info(f"✅ บันทึกข้อมูลเรียบร้อย!\n\nวันที่: {input_date}\nระยะทางวันนี้: {input_trip} กม.\nระยะทางรวม: {input_odo} กม.")