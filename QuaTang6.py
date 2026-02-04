import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import io
import time
import re
from fpdf import FPDF

# --- 1. THIẾT LẬP HỆ THỐNG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = {
    "gifts": os.path.join(BASE_DIR, "danhmuc_qua.csv"),
    "trans": os.path.join(BASE_DIR, "nhatky_xuatnhap.csv")
}


def init_csv():
    if not os.path.exists(FILE_PATH["gifts"]):
        pd.DataFrame(columns=["MaQua", "TenQua"]).to_csv(FILE_PATH["gifts"], index=False, encoding='utf-8-sig')
    if not os.path.exists(FILE_PATH["trans"]):
        pd.DataFrame(columns=["Loai", "Ngay", "Gio", "SoChungTu", "MaQua", "TenQua", "SoLuong", "NguoiThucHien",
                              "GhiChu"]).to_csv(FILE_PATH["trans"], index=False, encoding='utf-8-sig')


def no_accent_vietnamese(s):
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s);
    s = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s);
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s);
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s);
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s);
    s = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s);
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[đ]', 'd', s);
    s = re.sub(r'[Đ]', 'D', s)
    return s


def get_current_stock(ma_qua):
    df_t = pd.read_csv(FILE_PATH["trans"])
    if df_t.empty: return 0
    return df_t[df_t["MaQua"].astype(str) == str(ma_qua)]["SoLuong"].sum()


def export_pdf(df, date_range):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="BAO CAO XUAT NHAP TON", ln=True, align='C')
    pdf.ln(10)
    cols = ["Ma", "Ten Qua", "Ton Dau", "Nhap", "Xuat", "Ton Cuoi"]
    widths = [20, 65, 25, 25, 25, 30]
    pdf.set_fill_color(200, 220, 255)
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 8, col, border=1, fill=True, align='C')
    pdf.ln()
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(widths[0], 8, no_accent_vietnamese(str(row['Mã'])), border=1)
        pdf.cell(widths[1], 8, no_accent_vietnamese(str(row['Tên'])), border=1)
        pdf.cell(widths[2], 8, str(row['Tồn đầu']), border=1, align='C')
        pdf.cell(widths[3], 8, str(row['Nhập']), border=1, align='C')
        pdf.cell(widths[4], 8, str(row['Xuất']), border=1, align='C')
        pdf.cell(widths[5], 8, str(row['Tồn cuối']), border=1, align='C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin1', errors='replace')


# --- 2. GIAO DIỆN ĐĂNG NHẬP & TỰ ĐIỀN ---
st.set_page_config(page_title="Hệ Thống Kho", layout="wide")
init_csv()


def lookup_user_name():
    m_id = st.session_state.get('login_id', '')
    if m_id:
        df_t = pd.read_csv(FILE_PATH["trans"])
        if not df_t.empty:
            # Tìm kiếm nhân viên trong lịch sử
            match = df_t[df_t['NguoiThucHien'].str.contains(f"^{m_id} - ", regex=True)]
            if not match.empty:
                info = match.iloc[0]['NguoiThucHien']
                st.session_state['login_name'] = info.split(" - ")[1]


if 'user_info' not in st.session_state:
    with st.container(border=True):
        st.subheader("🔐 Đăng nhập phiên làm việc")
        u_id = st.text_input("Mã nhân viên (ID) *", key='login_id', on_change=lookup_user_name)
        u_name = st.text_input("Họ và Tên nhân viên *", key='login_name')
        if st.button("XÁC NHẬN BẮT ĐẦU", type="primary", use_container_width=True):
            if u_id and u_name:
                st.session_state['user_info'] = {"id": u_id, "name": u_name}
                st.rerun()
            else:
                st.warning("Vui lòng điền đủ Mã và Tên.")
    st.stop()

# --- 3. GIAO DIỆN CHÍNH ---
with st.sidebar:
    st.success(f"👤 {st.session_state['user_info']['name']}")
    if st.button("Đăng xuất / Kết thúc ca"):
        del st.session_state['user_info']
        st.rerun()

# Đổi thứ tự Tab: XUẤT đứng trước NHẬP
tabs = st.tabs(["📤 Xuất kho", "📥 Nhập kho", "📊 Báo cáo XNT", "📜 Nhật ký"])


def render_form(type="XUẤT"):
    df_g = pd.read_csv(FILE_PATH["gifts"])
    for key in [f"in_ma_{type}", f"in_ten_{type}", f"is_new_{type}"]:
        if key not in st.session_state: st.session_state[key] = "" if "in_" in key else False

    # BƯỚC 1: TÌM KIẾM (Mobile Friendly)
    st.markdown(f"🔍 **Tìm quà để {type}:**")
    search_term = st.text_input("Nhập tên hoặc mã để lọc...", key=f"src_{type}")

    filtered = df_g[df_g['MaQua'].astype(str).str.contains(search_term, case=False, na=False) |
                    df_g['TenQua'].str.contains(search_term, case=False, na=False)] if search_term else pd.DataFrame()

    if not filtered.empty:
        opts = filtered.apply(lambda x: f"{x['MaQua']} - {x['TenQua']}", axis=1).tolist()
        sel = st.radio("Chọn món quà:", opts, key=f"rad_{type}")
        if sel:
            m, t = sel.split(" - ")
            st.session_state[f"in_ma_{type}"] = m
            st.session_state[f"in_ten_{type}"] = t
            st.session_state[f"is_new_{type}"] = False
    elif search_term != "" and type == "NHẬP":
        if st.button("➕ Tạo quà tặng mới", use_container_width=True):
            st.session_state[f"in_ma_{type}"] = "";
            st.session_state[f"in_ten_{type}"] = search_term;
            st.session_state[f"is_new_{type}"] = True

    # BƯỚC 2: FORM CHI TIẾT
    with st.container(border=True):
        st.markdown(f"📝 **Chi tiết phiếu {type}**")
        so_ct = st.text_input("Số chứng từ (VD: PX001, PN001) *", key=f"c_{type}")

        # Lock info logic
        is_locked = True
        if type == "NHẬP" and (st.session_state[f"is_new_{type}"] or df_g.empty):
            is_locked = False

        c1, c2 = st.columns(2)
        with c1:
            ma = st.text_input("Mã Quà tặng *", key=f"in_ma_{type}", disabled=is_locked)
        with c2:
            ten = st.text_input("Tên Quà tặng *", key=f"in_ten_{type}", disabled=is_locked)

        sl = st.number_input(f"Số lượng {type} *", min_value=1, step=1, key=f"l_{type}")

        # Tồn kho hiển thị ngay dưới số lượng
        if ma:
            current = get_current_stock(ma)
            st.info(f"📊 Tồn kho hiện tại của mã này: **{current}**")

        note = st.text_input("Ghi chú", key=f"n_{type}")

        if st.button(f"XÁC NHẬN GHI SỔ {type}", type="primary", use_container_width=True):
            stk = get_current_stock(ma) if ma else 0
            if type == "XUẤT" and (not ma or sl > stk):
                st.error("Lỗi: Quà không tồn tại hoặc kho không đủ để xuất!")
            elif ma and ten and so_ct:
                d = {
                    "Loai": type, "Ngay": date.today().strftime("%Y-%m-%d"),
                    "Gio": datetime.now().strftime("%H:%M:%S"), "SoChungTu": so_ct,
                    "MaQua": ma, "TenQua": ten, "SoLuong": sl if type == "NHẬP" else -sl,
                    "NguoiThucHien": f"{st.session_state['user_info']['id']} - {st.session_state['user_info']['name']}",
                    "GhiChu": note
                }
                df_t = pd.read_csv(FILE_PATH["trans"])
                pd.concat([df_t, pd.DataFrame([d])], ignore_index=True).to_csv(FILE_PATH["trans"], index=False,
                                                                               encoding='utf-8-sig')

                if type == "NHẬP":
                    df_g_c = pd.read_csv(FILE_PATH["gifts"])
                    if str(ma) not in df_g_c["MaQua"].astype(str).values:
                        pd.concat([df_g_c, pd.DataFrame([{"MaQua": ma, "TenQua": ten}])], ignore_index=True).to_csv(
                            FILE_PATH["gifts"], index=False, encoding='utf-8-sig')

                st.success(f"✅ Đã lưu phiếu {type} thành công!")
                time.sleep(1)
                for k in [f"in_ma_{type}", f"in_ten_{type}", f"src_{type}", f"c_{type}", f"n_{type}", f"l_{type}",
                          f"rad_{type}", f"is_new_{type}"]:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
            else:
                st.error("Vui lòng điền đủ các trường bắt buộc (*)")


with tabs[0]: render_form("XUẤT")
with tabs[1]: render_form("NHẬP")

# --- PHẦN BÁO CÁO & LỊCH SỬ (Giữ nguyên) ---
with tabs[2]:
    st.subheader("Báo cáo XNT")
    c1, c2 = st.columns(2);
    d1 = c1.date_input("Từ", date(date.today().year, date.today().month, 1));
    d2 = c2.date_input("Đến", date.today())
    if st.button("📊 Xem dữ liệu", use_container_width=True):
        df_t = pd.read_csv(FILE_PATH["trans"])
        if not df_t.empty:
            df_t['Ngay'] = pd.to_datetime(df_t['Ngay']).dt.date
            df_g = pd.read_csv(FILE_PATH["gifts"])
            rpt = []
            for _, item in df_g.iterrows():
                m, t = item['MaQua'], item['TenQua']
                t_dau = df_t[(df_t['MaQua'] == m) & (df_t['Ngay'] < d1)]['SoLuong'].sum()
                nhap = \
                df_t[(df_t['MaQua'] == m) & (df_t['Loai'] == "NHẬP") & (df_t['Ngay'] >= d1) & (df_t['Ngay'] <= d2)][
                    'SoLuong'].sum()
                xuat = abs(
                    df_t[(df_t['MaQua'] == m) & (df_t['Loai'] == "XUẤT") & (df_t['Ngay'] >= d1) & (df_t['Ngay'] <= d2)][
                        'SoLuong'].sum())
                rpt.append(
                    {"Mã": m, "Tên": t, "Tồn đầu": t_dau, "Nhập": nhap, "Xuất": xuat, "Tồn cuối": t_dau + nhap - xuat})
            st.session_state['res'] = pd.DataFrame(rpt)
            st.dataframe(st.session_state['res'], use_container_width=True, hide_index=True)
    if 'res' in st.session_state:
        ce, cp = st.columns(2)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: st.session_state['res'].to_excel(wr, index=False)
        ce.download_button("📥 Excel", out.getvalue(), "Bao_cao_XNT.xlsx", use_container_width=True)
        cp.download_button("📄 PDF (Không dấu)", export_pdf(st.session_state['res'], f"{d1}-{d2}"), "Bao_cao_XNT.pdf",
                           use_container_width=True)

with tabs[3]:
    st.subheader("Nhật ký chi tiết")
    st.dataframe(pd.read_csv(FILE_PATH["trans"]).iloc[::-1], use_container_width=True, hide_index=True)