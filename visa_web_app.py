import streamlit as st
import easyocr
import cv2
import numpy as np
import re
import base64
import fitz
import os
import datetime
from PIL import Image

st.set_page_config(page_title="Visa Automation", layout="wide")

# --- Notification Pop-up Function ---
@st.dialog("အရေးကြီးသော အသိပေးချက် (Important Notice)")
def show_notice():
    st.markdown("""
    **မြန်မာဘာသာ:**
    * Customer ၏ အချက်အလက်များကို သိမ်းဆည်းထားခြင်း မရှိပါ။ File Download လုပ်ပြီး website ကို Refresh သို့မဟုတ် Close လုပ်တာနဲ့ အချက်အလက်များ Auto ဖျက်သွားမည် ဖြစ်သည်။
    * စာသားများသည် Photo Scan ဖတ်ရသောကြောင့် ပုံမရှင်းလင်းတာ သို့မဟုတ် တခါတရံ Scan Error ကြောင့် စာသားမပေါ်တာ၊ မှားယွင်းတာမျိုး ရှိနိုင်ပါသည်။ လိုအပ်ပါက Text Box များတွင် ကိုယ်တိုင် ပြင်ဆင်နိုင်ပါသည်။

    **English:**
    * We do not store any customer data. All information will be automatically deleted once you Refresh or Close the website after downloading your file.
    * Since text is extracted using Photo Scan, there might be slight errors or missing text due to image quality. You can manually edit any incorrect information in the text boxes provided.
    """)
    if st.button("နားလည်ပါပြီ (OK)", use_container_width=True):
        st.session_state.show_notice = False
        st.rerun()

# --- PDF ထဲ စာရိုက်မည့် Function ---
def overlay_text_on_pdf(template_path, data):
    try:
        if not os.path.exists(template_path):
            st.error(f"Error: {template_path} ကို ရှာမတွေ့ပါ")
            return None
        
        doc = fitz.open(template_path)
        
        current_year = datetime.datetime.now().year
        def get_age(dob_str):
            try:
                parts = str(dob_str).strip().split(' ')
                if len(parts) == 3 and parts[2].isdigit():
                    return str(current_year - int(parts[2]))
            except: pass
            return ""

        age = get_age(data.get("DOB", ""))
        def split_dt(dt_str):
            if not dt_str: return "", "", ""
            p = str(dt_str).strip().split(' ')
            if len(p) == 3: return (p[0], p[1], p[2])
            return (str(dt_str), "", "")

        d_d, d_m, d_y = split_dt(data.get("DOB"))
        i_d, i_m, i_y = split_dt(data.get("DOI"))
        e_d, e_m, e_y = split_dt(data.get("DOE"))
        arr_date = data.get("ARR_DATE")
        arr_d = arr_date.strftime("%d") if arr_date else ""
        arr_m = arr_date.strftime("%b").upper() if arr_date else ""
        arr_y = arr_date.strftime("%Y") if arr_date else ""

        def to_up(val):
            return str(val).upper() if val else ""

        # DAYS ဘေးတွင် " DAYS" စာသားထည့်ရန် ပြင်ဆင်ထားသည်
        v_days_val = to_up(data.get("DAYS"))
        v_days_display = f"{v_days_val} DAYS" if v_days_val else ""

        pages_layout = {
            0: [(437.5, 261, to_up(data.get("Name")), 0), (316.7, 365.9, to_up(data.get("PP")), 0), (376.8, 295.6, to_up(d_d), 0), (443.9, 297.9, to_up(d_m), 0), (523.3, 298.1, to_up(d_y), 0), (283.7, 294.8, to_up(age), 0), (479.3, 364.2, to_up(i_d), 0), (111.5, 399.7, to_up(i_m), 0), (218.5, 398.2, to_up(i_y), 0), (486.8, 401.2, to_up(e_d), 0), (115.3, 435.9, to_up(e_m), 0), (216.3, 434.4, to_up(e_y), 0), (448.8, 330.3, to_up(data.get("NAT")), 0), (157.5, 328.6, to_up(data.get("POB")), 0), (281.8, 401.2, to_up(data.get("ISS")), 0), (342.1, 466.1, to_up(data.get("FROM")), 0), (318.0, 435.1, to_up(data.get("V_TYPE")), 0), (129.6, 503.8, to_up(data.get("PORT")), 0), (165.8, 464.5, to_up(data.get("ARR_BY")), 0), (340.6, 503.0, to_up(arr_d), 0), (405.4, 503.0, to_up(arr_m), 0), (509.4, 502.2, to_up(arr_y), 0), (432.6, 589.0, to_up(data.get("DAYS")), 0), (167.3, 642.5, to_up(data.get("REASON")), 0)],
            1: [(243.4, 116.1, to_up(data.get("Name")), 0), (76.9, 454.0, to_up(data.get("PHONE")), 0), (180.9, 81.4, to_up(data.get("TM_ADDR")), 0), (125.8, 159.9, to_up(data.get("TM_NO")), 0), (244.2, 153.8, to_up(data.get("TM_ROAD")), 0), (390.4, 154.6, to_up(data.get("TM_SUB")), 0), (116.8, 194.6, to_up(data.get("TM_DIST")), 0), (342.9, 196.1, to_up(data.get("TM_PROV")), 0), (440.1, 196.1, to_up(data.get("TM_POST")), 0)],
            2: [(380, 176, to_up(data.get("Name")), 270), (380, 320, to_up(age), 270), (380, 455, to_up(data.get("NAT")), 270), (365, 475, to_up(data.get("REASON")), 270)],
            3: [(585, 455, to_up(data.get("Name")), 270), (543, 196, to_up(age), 270), (543, 294, to_up(data.get("NAT")), 270), (543, 455, to_up(data.get("PP")), 270)],
            4: [(380, 202, to_up(data.get("Name")), 270), (385, 470, to_up(age), 270), (365, 150, to_up(data.get("NAT")), 270), (365, 300, to_up(data.get("PP")), 270), (264, 180, to_up(data.get("REASON")), 270), (365, 480, to_up(data.get("PHONE")), 270), (299, 450, v_days_display, 270)]
        }

        for pno, page in enumerate(doc): 
            if pno in pages_layout:
                for x, y, val, rot in pages_layout[pno]:
                    if val:
                        page.insert_text(fitz.Point(x, y), str(val), fontsize=9, color=(0, 0, 1), rotate=rot)

        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', str(data.get("Name", "Form")))
        out_name = f"Visa_Final_{clean_name}.pdf"
        doc.save(out_name)
        doc.close()
        return out_name
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

@st.cache_resource
def load_reader(): return easyocr.Reader(['en'], gpu=False)

def is_date_format(text):
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    return any(m in text.upper() for m in months) or len(re.findall(r'\d+', text)) >= 2

def clean_and_fix_date(text):
    t = text.upper().strip()
    t = t.replace('[', '1').replace('|', '1').replace('I', '1').replace('O', '0').replace('S', '5').replace('B', '8')
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    found_month = next((m for m in months if m in t), None)
    if found_month:
        nums = re.findall(r'\d+', t)
        if len(nums) >= 2:
            day = nums[0].replace('3', '5') if len(nums[0]) <= 2 else nums[0]
            year = nums[-1]
            if len(year) == 2: year = "20" + year if int(year) < 45 else "19" + year
            elif len(year) >= 4: year = year[:4]
            return f"{day.zfill(2)} {found_month} {year}"
    return None

def fix_passport_logic(text):
    t = text.upper().replace(" ", "").replace("<", "")
    match = re.search(r'([A-Z0-9]{2})([0-9OISBZG]{6})', t)
    if match:
        p1 = match.group(1).replace('0', 'O').replace('1', 'I')
        p2 = match.group(2).replace('O', '0').replace('I', '1').replace('S', '5').replace('B', '8').replace('G', '6')
        final_pp = p1 + p2
        if re.match(r'^[A-Z]{2}\d{6}$', final_pp): return final_pp
    return None

def extract_tm30_data(pdf_file):
    data = {"addr": "", "no": "", "road": "", "sub": "", "dist": "", "prov": "", "post": ""}
    try:
        doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
        lines = []
        for page in doc:
            text = page.get_text("text")
            lines.extend([l.strip() for l in text.split('\n') if l.strip()])
        for i, line in enumerate(lines):
            if "Check-in Date" in line:
                idx_map = {"addr": -9, "post": -8, "prov": -7, "sub": -6, "dist": -5, "road": -3, "no": -2}
                for k, v in idx_map.items():
                    if i + v >= 0: data[k] = lines[i + v]
                break
    except: pass
    return data

def main():
    if "show_notice" not in st.session_state:
        st.session_state.show_notice = True

    if st.session_state.show_notice:
        show_notice()

    st.title("📄 Visa Form Auto-Filler v179.5")
    st.divider()

    if 'v_res' not in st.session_state: st.session_state['v_res'] = None
    if 'img_bio' not in st.session_state: st.session_state['img_bio'] = None
    if 'img_tm30_preview' not in st.session_state: st.session_state['img_tm30_preview'] = None

    col_u1, col_u2 = st.columns(2)
    with col_u1: bio_file = st.file_uploader("Upload Passport Bio Page", type=['jpg', 'png', 'jpeg'])
    with col_u2: tm30_file = st.file_uploader("Upload TM30 Document", type=['jpg', 'png', 'jpeg', 'pdf'])

    if bio_file and tm30_file:
        if st.button("🔍 Process Documents", use_container_width=True, type="primary"):
            reader = load_reader()
            with st.spinner("Processing..."):
                img_bytes = np.asarray(bytearray(bio_file.getvalue()), dtype=np.uint8)
                img = cv2.imdecode(img_bytes, 1)
                st.session_state['img_bio'] = Image.open(bio_file)
                
                tm_data = {}
                if tm30_file.type == "application/pdf":
                    tm_data = extract_tm30_data(tm30_file)
                    pdf_doc = fitz.open(stream=tm30_file.getvalue(), filetype="pdf")
                    page = pdf_doc.load_page(0)
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    st.session_state['img_tm30_preview'] = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                else:
                    st.session_state['img_tm30_preview'] = Image.open(tm30_file)

                results = reader.readtext(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
                texts = [r[1].upper().strip() for r in results]
                res = {"Name": "", "PP": "", "DOB": "", "NAT": "MYANMAR", "POB": "", "ISS": "", "DOI": "", "DOE": "", "Dates": []}
                res.update({f"TM_{k.upper()}": v for k, v in tm_data.items()})

                for i, t in enumerate(texts):
                    if any(key in t for key in ["BIRTH", "PLACE"]):
                        for off in range(1, 4):
                            if i + off < len(texts):
                                cand = texts[i+off].strip()
                                if len(cand) >= 3 and not is_date_format(cand) and "MMR" not in cand:
                                    res["POB"] = cand; break
                    if any(k in t for k in ["MOHA", "ISSUED", "AUTH"]):
                        for off in range(0, 6):
                            if i + off < len(texts):
                                cand = texts[i+off].strip()
                                if "," in cand or "YANGON" in cand:
                                    res["ISS"] = cand; break
                    if any(k in t for k in ["SURNAME", "GIVEN", "NAME"]):
                        for off in range(1, 4):
                            if i + off < len(texts):
                                cand = texts[i + off].replace("MMR", "").strip()
                                if len(cand) >= 3 and not is_date_format(cand):
                                    res["Name"] = cand; break
                    if not res["PP"]:
                        pp_f = fix_passport_logic(t)
                        if pp_f: res["PP"] = pp_f
                    d = clean_and_fix_date(t)
                    if d: res["Dates"].append(d)

                v_dates = sorted([(d, int(re.search(r'\d{4}', d).group())) for d in res["Dates"] if re.search(r'\d{4}', d)], key=lambda x: x[1])
                if len(v_dates) >= 1: res["DOB"] = v_dates[0][0]
                if len(v_dates) >= 2: res["DOI"] = v_dates[1][0]
                if len(v_dates) >= 3: res["DOE"] = v_dates[2][0]
                st.session_state['v_res'] = res
                st.rerun()

    if st.session_state['v_res']:
        d = st.session_state['v_res']
        tab_bio, tab_tm30, tab_adding = st.tabs(["📁 Bio Page", "🏠 TM30", "➕ Additional Info"])
        with tab_bio:
            v_col, e_col = st.columns([1.5, 1])
            with v_col: st.image(st.session_state['img_bio'], use_container_width=True)
            with e_col:
                st.markdown("Name <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_n = st.text_input("n_label", d["Name"], key="n_in", label_visibility="collapsed").upper()
                st.markdown("Passport No <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_p = st.text_input("p_label", d["PP"], key="p_in", label_visibility="collapsed").upper()
                st.markdown("Date of Birth <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_db = st.text_input("db_label", d["DOB"], key="db_in", label_visibility="collapsed").upper()
                st.markdown("Nationality <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_nat = st.text_input("nat_label", d["NAT"], key="nat_in", label_visibility="collapsed").upper()
                st.markdown("Place of Birth <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_pb = st.text_input("pb_label", d["POB"], key="pb_in", label_visibility="collapsed").upper()
                st.markdown("Issue At <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_iss = st.text_input("iss_label", d["ISS"], key="iss_in", label_visibility="collapsed").upper()
                st.markdown("Date of Issue <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_di = st.text_input("di_label", d["DOI"], key="di_in", label_visibility="collapsed").upper()
                st.markdown("Date of Expire <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_de = st.text_input("de_label", d["DOE"], key="de_in", label_visibility="collapsed").upper()
        with tab_tm30:
            tm_v_col, tm_e_col = st.columns([1.5, 1])
            with tm_v_col:
                if st.session_state['img_tm30_preview']:
                    st.image(st.session_state['img_tm30_preview'], use_container_width=True)
                else: st.info("TM30 file not loaded.")
            with tm_e_col:
                st.markdown("Address <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm1 = st.text_input("tm1_label", d.get("TM_ADDR", ""), key="tm1", label_visibility="collapsed").upper()
                st.markdown("Address No <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm2 = st.text_input("tm2_label", d.get("TM_NO", ""), key="tm2", label_visibility="collapsed").upper()
                st.markdown("Road <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm3 = st.text_input("tm3_label", d.get("TM_ROAD", ""), key="tm3", label_visibility="collapsed").upper()
                st.markdown("Sub-district <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm4 = st.text_input("tm4_label", d.get("TM_SUB", ""), key="tm4", label_visibility="collapsed").upper()
                st.markdown("District <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm5 = st.text_input("tm5_label", d.get("TM_DIST", ""), key="tm5", label_visibility="collapsed").upper()
                st.markdown("Province <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm6 = st.text_input("tm6_label", d.get("TM_PROV", ""), key="tm6", label_visibility="collapsed").upper()
                st.markdown("Post Code <span style='color:red'>*</span>", unsafe_allow_html=True)
                val_tm7 = st.text_input("tm7_label", d.get("TM_POST", ""), key="tm7", label_visibility="collapsed").upper()
        with tab_adding:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("Visa Type <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_t = st.selectbox("vt_label", ["Tourist Visa", "14 days visa"], key="vtype", label_visibility="collapsed")
                st.markdown("From <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_f = st.text_input("vf_label", key="vfrom", label_visibility="collapsed").upper()
                st.markdown("Port of Arrival <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_po = st.text_input("vp_label", key="vport", label_visibility="collapsed").upper()
                st.markdown("Arrived by <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_a = st.text_input("va_label", key="varr", label_visibility="collapsed").upper()
            with c2:
                st.markdown("Arrival Date <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_d = st.date_input("vd_label", value=None, key="vdate", label_visibility="collapsed")
                st.markdown("Phone <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_ph = st.text_input("vph_label", key="vphone", label_visibility="collapsed").upper()
                st.markdown("Days <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_da = st.text_input("vda_label", key="vdays", label_visibility="collapsed").upper()
                st.markdown("Reason <span style='color:red'>*</span>", unsafe_allow_html=True)
                v_re = st.text_area("vre_label", key="vreason", label_visibility="collapsed").upper()
            
            can_download = all([val_n, val_p, val_db, val_nat, val_pb, val_iss, val_di, val_de, val_tm1, val_tm2, val_tm3, val_tm4, val_tm5, val_tm6, val_tm7, v_f, v_po, v_a, v_d, v_ph, v_da, v_re])
            
            if not can_download:
                st.warning("⚠️ ရှေ့တွင် * ပြထားသော အကွက်လပ်များအားလုံးကို ဖြည့်စွက်ပေးပါ။")

            if st.button("📥 Download Document", type="primary", use_container_width=True, disabled=not can_download):
                f_data = {
                    "Name": val_n, "PP": val_p, "DOB": val_db, "NAT": val_nat, "POB": val_pb, "ISS": val_iss, "DOI": val_di, "DOE": val_de,
                    "TM_ADDR": val_tm1, "TM_NO": val_tm2, "TM_ROAD": val_tm3, "TM_SUB": val_tm4, "TM_DIST": val_tm5, "TM_PROV": val_tm6, "TM_POST": val_tm7,
                    "V_TYPE": v_t, "FROM": v_f, "PORT": v_po, "ARR_BY": v_a, "ARR_DATE": v_d, "PHONE": v_ph, "DAYS": v_da, "REASON": v_re
                }
                out = overlay_text_on_pdf("Visa Extension.pdf", f_data)
                if out:
                    with open(out, "rb") as f:
                        st.download_button("✅ Click to Save PDF", f, file_name=out, use_container_width=True)

if __name__ == "__main__":
    main()
