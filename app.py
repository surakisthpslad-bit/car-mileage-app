import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
from datetime import datetime

st.set_page_config(page_title="ระบบบันทึกไมล์รถยนต์ (มีระบบ Debug)", page_icon="🚗")
st.title("🚗 อัปโหลดรูปหน้าปัดรถยนต์")
st.write("ระบบจะอ่านวันที่, ระยะทางของวัน (Trip), และระยะทางรวม (ODO) ให้อัตโนมัติ")

# สร้างตัวแปรส่วนกลางสำหรับเก็บสถานะการตรวจสอบ (Debug)
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = {
        "api_key_status": "ยังไม่ได้ตรวจสอบ",
        "raw_response": "ยังไม่มีการส่งรูปภาพ",
        "error_message": "ไม่มีข้อผิดพลาด"
    }

# 1. ตรวจสอบการโหลด API Key จากระบบ Secrets ของ Streamlit
api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        if api_key == "วาง_API_KEY_ของคุณตรงนี้" or api_key == "":
            st.session_state.debug_info["api_key_status"] = "❌ พบ Key แต่ค่าว่างเปล่า หรือยังไม่ได้เปลี่ยนเป็น Key จริง"
            api_key = ""
        else:
            st.session_state.debug_info["api_key_status"] = "✅ พบบัญชี API Key ในระบบพร้อมใช้งานแล้ว"
    else:
        st.session_state.debug_info["api_key_status"] = "❌ ไม่พบตัวแปรชื่อ GEMINI_API_KEY ใน Streamlit Secrets"
except Exception as e:
    st.session_state.debug_info["api_key_status"] = f"❌ เกิดข้อผิดพลาดเกี่ยวกับตัวระบบคลาวด์: {str(e)}"

# เชื่อมต่อกับระบบ AI
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    st.error("🔒 ระบบล็อกอยู่: เนื่องจากยังไม่ได้ตั้งค่า API Key หรือตั้งค่าไม่ถูกต้อง (กรุณาดูวิธีแก้ไขในเมนู Debug ด้านล่าง)")

uploaded_file = st.file_uploader("📷 ถ่ายรูปหรืออัปโหลดรูปหน้าปัดรถ", type=["jpg", "jpeg", "png"])

# ค่าเริ่มต้นหากระบบตรวจจับไม่ได้
data = {"date": "Not Found", "trip": 0, "odo": 0}

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='รูปภาพที่อัปโหลด', use_column_width=True)
    
    with st.spinner('🤖 AI กำลังวิเคราะห์หน้าปัดรถ...'):
        prompt = """
        Analyze this car dashboard image. Extract the following 3 pieces of information:
        1. Date visible on the dashboard (if any). If not visible, return "Not Found".
        2. Trip mileage (distance for the current trip). Return only numbers/decimals. If not found, return 0.
        3. Total ODO mileage (total distance). Return only integer numbers. If not found, return 0.
        
        IMPORTANT: You must output ONLY a valid JSON object without any markdown tags or extra text.
        Format example: {"date": "15/10/2023", "trip": 45.2, "odo": 150000}
        """
        
        # รีเซ็ตค่าล็อกสำหรับการส่งภาพครั้งใหม่
        st.session_state.debug_info["raw_response"] = "กำลังรอผลลัพธ์จาก Google API..."
        st.session_state.debug_info["error_message"] = "ไม่มีข้อผิดพลาด"
        
        try:
            response = model.generate_content([prompt, image])
            
            # 🎯 ดักจับ: บันทึกค่าดิบที่ AI ส่งกลับมาจริงๆ
            st.session_state.debug_info["raw_response"] = response.text
            
            # ทำความสะอาดข้อความส่วนเกินเพื่อนำไปแปลงเป็น JSON
            raw_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(raw_text)
            st.success("✨ AI วิเคราะห์เสร็จสิ้น!")
            
        except Exception as e:
            # 🎯 ดักจับ: บันทึกข้อผิดพลาดของระบบโค้ด
            st.session_state.debug_info["error_message"] = str(e)
            st.error("⚠️ ไม่สามารถสกัดข้อมูลจากภาพได้สำเร็จ กรุณาเลื่อนลงไปตรวจสอบสาเหตุที่ 'กล่องข้อมูล Debug' ด้านล่าง")

    # แสดงฟอร์มตรวจสอบข้อมูล (จะทำงานแม้ระบบจะเอ๋อ เพื่อให้กรอกเองมือได้)
    st.write("---")
    with st.form("data_form"):
        default_date = datetime.today().strftime('%Y-%m-%d')
        display_date = default_date if data.get('date') == "Not Found" else data.get('date', default_date)
        
        input_date = st.text_input("📅 วันที่ใช้งาน", value=display_date)
        input_trip = st.number_input("🛣️ ระยะทางของวันนี้ (Trip)", value=float(data.get('trip', 0)), format="%.1f")
        input_odo = st.number_input("🔄 ระยะทางรวมทั้งหมด (ODO)", value=int(data.get('odo', 0)), step=1)
        
        submitted = st.form_submit_button("💾 ยืนยันและบันทึกข้อมูล")
        if submitted:
            st.balloons()
            st.success(f"บันทึกข้อมูลสำเร็จ! (ระยะทางรวม {input_odo} กม.)")

# =======================================================
# 🛠️ โซนระบบตรวจสอบข้อผิดพลาด (DEVELOPER DEBUG LOGS)
# =======================================================
st.write("---")
with st.expander("🛠️ กล่องเครื่องมือตรวจสอบข้อผิดพลาดหลังบ้าน (Debug Logs)สำหรับผู้พัฒนา"):
    st.info("ใช้ส่วนนี้เพื่อตรวจสอบว่าระบบของคุณเชื่อมต่อกับ Google API ได้สมบูรณ์หรือไม่")
    
    st.subheader("1. ตรวจสอบการเปิดใช้งาน API Key")
    st.code(st.session_state.debug_info["api_key_status"])
    
    st.subheader("2. ค่าดิบที่ Google API ส่งกลับมา (Raw Response)")
    st.write("ดูว่าจริงๆ แล้ว AI อ่านได้อะไร และทำไมระบบถึงแปลงค่าเป็นตัวเลขไม่ได้:")
    st.code(st.session_state.debug_info["raw_response"])
    
    st.subheader("3. ข้อความแจ้งเตือนความเสียหายของโค้ด (Error Message)")
    if st.session_state.debug_info["error_message"] != "ไม่มีข้อผิดพลาด":
        st.write("🔴 โค้ดหยุดทำงานเนื่องจากเหตุผลต่อไปนี้:")
        st.code(st.session_state.debug_info["error_message"], language="python")
    else:
        st.code("ไม่มีข้อผิดพลาดในระบบควบคุม")
