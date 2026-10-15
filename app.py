import streamlit as st
import sqlite3
import pandas as pd
import html
import io
import uuid
from datetime import datetime

# ==================================================
# N2 SUSHI POS - CHỈ MỘT FILE APP.PY
# ==================================================

st.set_page_config(
    page_title="N2 Sushi | Premium POS",
    page_icon="🍣",
    layout="wide"
)

DB = "n2_sushi.db"

# THAY BẰNG THÔNG TIN THẬT CỦA QUÁN
SHOP = {
    "name": "N2 Sushi",
    "address": "123 Đường ABC, Thủ Dầu Một, Bình Dương",
    "phone": "0900 123 456",
    "hours": "09:00 - 22:00 hằng ngày",
    "image": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=1800&q=85"
}

# ==================================================
# GIAO DIỆN & CSS
# ==================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}
.stApp {
    background: #f7f5f0;
    color: #242424;
}
section[data-testid="stSidebar"] {
    background: #191919;
}
section[data-testid="stSidebar"] * {
    color: #f8f1e8;
}
.hero {
    background: linear-gradient(115deg,#191919,#67202b);
    color: white;
    padding: 25px;
    border-radius: 16px;
    margin-bottom: 20px;
}
.hero h1 {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: 2px;
}
.hero p {
    color: #f0dfcf;
    line-height: 1.9;
}
.section-title {
    color: #7d1f2a;
    font-size: 22px;
    font-weight: 800;
    margin: 20px 0 12px;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #eadfd2;
    border-radius: 12px;
    padding: 15px;
}
div.stButton > button {
    border-radius: 9px;
    font-weight: 600;
    min-height: 40px;
}
div.stButton > button[kind="primary"] {
    background: #7d1f2a;
    color: white;
    border: none;
}
.total-card {
    background: #191919;
    color: white;
    padding: 23px;
    border-radius: 15px;
}
.total-price {
    color: #f2cb83;
    font-size: 30px;
    font-weight: 800;
}
.chat-panel {
    background: #191919;
    padding: 20px;
    border-radius: 15px;
    color: white;
}
.chat-bubble {
    background: white;
    color: #222;
    padding: 13px 15px;
    border-radius: 12px;
    margin: 9px 0;
    line-height: 1.7;
    overflow-wrap: anywhere;
}
.chat-user {
    background: #7d1f2a;
    color: white;
    padding: 13px 15px;
    border-radius: 12px;
    margin: 9px 0;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)


def money(n):
    return f"{int(n):,}".replace(",", ".") + " đ"


# ==================================================
# DATABASE - TỰ ĐỘNG KHỞI TẠO
# ==================================================

def connect():
    return sqlite3.connect(DB, timeout=30)


def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            bestseller INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS customers (
            phone TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            visits INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            customer TEXT,
            phone TEXT,
            table_no TEXT,
            created_at TEXT,
            subtotal INTEGER,
            discount INTEGER,
            total INTEGER,
            points INTEGER,
            voucher TEXT,
            payment TEXT,
            status TEXT DEFAULT 'Đã thanh toán'
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            name TEXT,
            category TEXT,
            price INTEGER,
            quantity INTEGER,
            line_total INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """)

        count = con.execute("SELECT COUNT(*) FROM menu").fetchone()[0]

        if count == 0:
            items = [
                ("🍣 Sushi cá hồi", "Sushi", 45000, 1),
                ("🍣 Sushi cá ngừ", "Sushi", 40000, 0),
                ("🍣 Sushi lươn Nhật", "Sushi", 55000, 1),
                ("🍣 Sushi tôm", "Sushi", 35000, 0),
                ("🍣 Sushi thanh cua", "Sushi", 30000, 0),
                ("🍣 Sushi trứng Nhật", "Sushi", 25000, 0),
                ("🍣 Sushi tổng hợp 8 miếng", "Sushi", 99000, 1),
                ("🐟 Sashimi cá hồi", "Sashimi", 129000, 1),
                ("🐟 Sashimi cá ngừ", "Sashimi", 119000, 0),
                ("🐟 Sashimi tổng hợp", "Sashimi", 189000, 1),
                ("🍜 Ramen bò", "Món nóng", 89000, 1),
                ("🍜 Ramen hải sản", "Món nóng", 95000, 0),
                ("🍤 Tempura tôm", "Món nóng", 79000, 1),
                ("🍗 Gà sốt teriyaki", "Món nóng", 69000, 0),
                ("🍚 Cơm bò Nhật", "Món nóng", 75000, 0),
                ("🥟 Há cảo Nhật", "Món nóng", 49000, 0),
                ("🥗 Salad rong biển", "Món nóng", 39000, 0),
                ("🎎 Combo N2 Couple", "Combo", 199000, 1),
                ("🍱 Combo Sakura", "Combo", 299000, 1),
                ("👨‍👩‍👧 Combo Family 3-4 người", "Combo", 499000, 1),
                ("👑 Combo Premium", "Combo", 699000, 1),
                ("🍵 Trà xanh Nhật", "Thức uống", 25000, 0),
                ("🧋 Trà đào", "Thức uống", 30000, 1),
                ("🥤 Coca-Cola", "Thức uống", 20000, 0),
                ("🍋 Nước chanh", "Thức uống", 25000, 0),
                ("🍓 Soda dâu", "Thức uống", 35000, 0),
                ("💧 Nước suối", "Thức uống", 15000, 0)
            ]
            con.executemany("""
                INSERT INTO menu(name,category,price,bestseller)
                VALUES (?,?,?,?)
            """, items)
        con.commit()


init_db()


def get_menu(active=True):
    with connect() as con:
        query = "SELECT * FROM menu"
        if active:
            query += " WHERE active=1"
        query += " ORDER BY category,name"
        return pd.read_sql_query(query, con)


def get_customer(phone):
    if not phone.strip():
        return None
    with connect() as con:
        r = con.execute(
            "SELECT * FROM customers WHERE phone=?",
            (phone.strip(),)
        ).fetchone()
    return r


def voucher_discount(code, subtotal):
    code = code.strip().upper()
    if code == "N2WELCOME":
        return min(int(subtotal * 0.10), 50000), "Giảm 10%, tối đa 50.000đ"
    if code == "SUSHI20" and subtotal >= 200000:
        return 20000, "Giảm 20.000đ"
    if code == "N2VIP" and subtotal >= 500000:
        return min(int(subtotal * 0.15), 100000), "Giảm 15%, tối đa 100.000đ"
    if code == "SUSHI20":
        return 0, "Đơn chưa đủ 200.000đ"
    if code == "N2VIP":
        return 0, "Đơn chưa đủ 500.000đ"
    if code:
        return 0, "Voucher không hợp lệ"
    return 0, ""


def invoice_html(order, items):
    safe = lambda x: html.escape(str(x or ""))
    rows = ""
    for x in items:
        rows += f"""
        <tr>
        <td>{safe(x['name'])}</td>
        <td>{x['quantity']}</td>
        <td>{money(x['price'])}</td>
        <td>{money(x['line_total'])}</td>
        </tr>
        """
    return f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hóa đơn N2 Sushi</title>
<style>
body{{font-family:Arial;max-width:750px;margin:25px auto;padding:20px;color:#222}}
h1{{color:#7d1f2a;text-align:center}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{border-bottom:1px solid #ddd;padding:10px;text-align:left}}
th{{background:#f7f2e9}}
.total{{font-size:22px;color:#7d1f2a;font-weight:bold;text-align:right}}
@media print{{button{{display:none}}}}
</style></head><body>
<h1>🍣 N2 SUSHI</h1>
<p style="text-align:center">
{safe(SHOP['address'])}<br>
Điện thoại: {safe(SHOP['phone'])}<br>
Giờ mở cửa: {safe(SHOP['hours'])}
</p><hr>
<h2>HÓA ĐƠN THANH TOÁN</h2>
<p>Mã hóa đơn: <b>{safe(order['code'])}</b><br>
Thời gian: {safe(order['created_at'])}<br>
Khách hàng: {safe(order['customer'])}<br>
Điện thoại: {safe(order['phone'])}<br>
Số bàn: {safe(order['table'])}<br>
Thanh toán: {safe(order['payment'])}</p>
<table><thead><tr><th>Món</th><th>SL</th>
<th>Đơn giá</th><th>Thành tiền</th></tr></thead>
<tbody>{rows}</tbody></table>
<p style="text-align:right">Tạm tính: {money(order['subtotal'])}</p>
<p style="text-align:right">Giảm giá: -{money(order['discount'])}</p>
<p class="total">THANH TOÁN: {money(order['total'])}</p>
<p>Điểm tích lũy: {order['points']} điểm</p>
<p style="text-align:center;margin-top:35px">
Cảm ơn quý khách đã đến N2 Sushi ❤️</p>
<button onclick="window.print()">In hóa đơn / Lưu PDF</button>
</body></html>"""


# ==================================================
# HEADER
# ==================================================

try:
    st.image(SHOP["image"], use_container_width=True)
except Exception:
    pass

st.markdown(f"""
<div class="hero">
<h1>🍣 N2 SUSHI</h1>
<p>JAPANESE DINING · FRESH TASTE · PREMIUM EXPERIENCE<br>📍 {html.escape(SHOP['address'])}<br>
☎️ {html.escape(SHOP['phone'])} &nbsp; | &nbsp;🕒 {html.escape(SHOP['hours'])}</p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# SESSION STATE
# ==================================================

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "last_invoice" not in st.session_state:
    st.session_state.last_invoice = None

if "chat" not in st.session_state:
    st.session_state.chat = [{
        "role": "assistant",
        "text": "Xin chào! 🍣 Mình là trợ lý N2 Sushi. Bạn muốn tìm món best seller, món giá rẻ hay cần tư vấn menu, voucher?"
    }]


# ==================================================
# MENU ĐIỀU HƯỚNG
# ==================================================

st.sidebar.markdown("# 🍣 N2 SUSHI")
st.sidebar.caption("PREMIUM POS SYSTEM")

page = st.sidebar.radio(
    "CHỨC NĂNG",
    [
        "🧾 Tạo đơn & tính tiền",
        "🍱 Quản lý thực đơn",
        "📊 Báo cáo doanh thu",
        "🗂️ Lịch sử hóa đơn",
        "💬 Chatbot tư vấn"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("### 🎟️ VOUCHER")
st.sidebar.markdown("""
**N2WELCOME** — giảm 10%, tối đa 50.000đ

**SUSHI20** — giảm 20.000đ cho đơn từ 200.000đ

**N2VIP** — giảm 15%, tối đa 100.000đ cho đơn từ 500.000đ
""")


# ==================================================
# TẠO ĐƠN HÀNG
# ==================================================

if page == "🧾 Tạo đơn & tính tiền":

    st.markdown(
        '<div class="section-title">👤 THÔNG TIN KHÁCH HÀNG</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        customer = st.text_input("Tên khách hàng")
    with c2:
        phone = st.text_input("Số điện thoại")
    with c3:
        table_no = st.text_input("Số bàn", placeholder="B01 / Mang đi")

    existing = get_customer(phone)
    if existing:
        st.success(
            f"⭐ Khách hàng thành viên: {existing[1]} | "
            f"{existing[2]} điểm | {existing[4]} lượt ghé"
        )

    st.divider()
    st.markdown(
        '<div class="section-title">🍱 THỰC ĐƠN N2 SUSHI</div>',
        unsafe_allow_html=True
    )

    menu = get_menu()
    categories = ["Tất cả"] + menu["category"].drop_duplicates().tolist()
    category = st.selectbox("Danh mục món", categories)

    filtered = menu if category == "Tất cả" else menu[
        menu["category"] == category
    ]

    display = filtered[["name", "category", "price", "bestseller"]].copy()
    display.columns = ["Tên món", "Danh mục", "Giá", "Best seller"]
    display["Giá"] = display["Giá"].apply(money)
    display["Best seller"] = display["Best seller"].map({1: "⭐", 0: ""})
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("### 🛒 Chọn món và số lượng")

    names = filtered["name"].tolist()
    selected = st.multiselect(
        "Chọn nhiều món trong cùng một đơn",
        options=names,
        key="selected_names"
    )

    for old in list(st.session_state.cart):
        if old not in selected:
            del st.session_state.cart[old]

    for name in selected:
        row = menu[menu["name"] == name].iloc[0]
        a, b, c = st.columns([4, 2, 2])
        with a:
            st.write(f"**{name}**")
            st.caption(money(row["price"]))
        with b:
            qty = st.number_input(
                "Số lượng",
                min_value=1,
                max_value=100,
                value=int(st.session_state.cart.get(name, 1)),
                key=f"qty_{row['id']}"
            )
        with c:
            st.write("Thành tiền")
            st.write(money(int(row["price"]) * qty))
        st.session_state.cart[name] = int(qty)

    menu = get_menu()
    items = []

    for name, qty in st.session_state.cart.items():
        row = menu[menu["name"] == name]
        if row.empty:
            continue
        r = row.iloc[0]
        price = int(r["price"])
        items.append({
            "name": name,
            "category": r["category"],
            "price": price,
            "quantity": int(qty),
            "line_total": price * int(qty)
        })

    subtotal = sum(x["line_total"] for x in items)

    st.divider()
    st.markdown(
        '<div class="section-title">💳 TỔNG KẾT THANH TOÁN</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns([3, 2])

    with left:
        if items:
            detail = pd.DataFrame(items)
            detail.columns = [
                "Tên món", "Danh mục", "Đơn giá", "Số lượng", "Thành tiền"
            ]
            detail["Đơn giá"] = detail["Đơn giá"].apply(money)
            detail["Thành tiền"] = detail["Thành tiền"].apply(money)
            st.dataframe(detail, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa chọn món.")

    with right:
        st.write("Tạm tính:", money(subtotal))
        voucher = st.text_input("🎟️ Mã voucher")
        discount, voucher_msg = voucher_discount(voucher, subtotal)
        discount = min(discount, subtotal)
        total = max(0, subtotal - discount)

        if voucher.strip():
            if discount:
                st.success(voucher_msg)
            else:
                st.warning(voucher_msg)

        st.markdown(f"""
        <div class="total-card">
        <div>TỔNG THANH TOÁN</div>
        <div class="total-price">{money(total)}</div>
        <hr>
        <div>Giảm giá: -{money(discount)}</div>
        <div>Điểm dự kiến: {total // 10000} điểm</div>
        </div>
        """, unsafe_allow_html=True)

        payment = st.selectbox(
            "Phương thức thanh toán",
            ["Tiền mặt", "Chuyển khoản", "Thẻ ngân hàng", "Ví điện tử"]
        )

        if st.button(
            "✅ THANH TOÁN & XUẤT HÓA ĐƠN",
            type="primary",
            use_container_width=True
        ):
            if not customer.strip():
                st.error("Nhập tên khách hàng trước.")
            elif not items:
                st.error("Vui lòng chọn ít nhất một món.")
            elif phone.strip() and not phone.strip().isdigit():
                st.error("Số điện thoại chỉ nhập chữ số.")
            else:
                code = "N2" + datetime.now().strftime("%y%m%d%H%M%S") + uuid.uuid4().hex[:4].upper()
                points = total // 10000
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    with connect() as con:
                        cur = con.cursor()
                        cur.execute("""
                        INSERT INTO orders(
                            code,customer,phone,table_no,created_at,
                            subtotal,discount,total,points,voucher,payment,status
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,'Đã thanh toán')
                        """, (
                            code, customer.strip(), phone.strip(),
                            table_no.strip() or "Mang đi", now,
                            subtotal, discount, total, points,
                            voucher.strip().upper() if discount else "",
                            payment
                        ))

                        order_id = cur.lastrowid

                        for x in items:
                            cur.execute("""
                            INSERT INTO order_items(
                                order_id,name,category,price,quantity,line_total
                            ) VALUES(?,?,?,?,?,?)
                            """, (
                                order_id, x["name"], x["category"],
                                x["price"], x["quantity"], x["line_total"]
                            ))

                        if phone.strip():
                            cur.execute("""
                            INSERT INTO customers(phone,name,points,total_spent,visits)
                            VALUES(?,?,?,?,1)
                            ON CONFLICT(phone) DO UPDATE SET
                                name=excluded.name,
                                points=customers.points+excluded.points,
                                total_spent=customers.total_spent+excluded.total_spent,
                                visits=customers.visits+1
                            """, (phone.strip(), customer.strip(), points, total))

                        con.commit()

                    order = {
                        "code": code,
                        "customer": customer.strip(),
                        "phone": phone.strip() or "Không cung cấp",
                        "table": table_no.strip() or "Mang đi",
                        "created_at": now,
                        "subtotal": subtotal,
                        "discount": discount,
                        "total": total,
                        "points": points,
                        "payment": payment
                    }

                    st.session_state.last_invoice = {
                        "order": order,
                        "items": items,
                        "html": invoice_html(order, items)
                    }

                    st.session_state.cart = {}
                    st.session_state["selected_names"] = []
                    st.success(f"Thanh toán thành công! Mã hóa đơn: {code}")
                    st.rerun()

                except sqlite3.Error as e:
                    st.error(f"Không thể lưu hóa đơn: {e}")

    if st.session_state.last_invoice:
        inv = st.session_state.last_invoice
        order = inv["order"]

        st.divider()
        st.markdown("## 🧾 HÓA ĐƠN VỪA THANH TOÁN")

        a, b, c = st.columns(3)
        a.metric("Mã hóa đơn", order["code"])
        b.metric("Tổng thanh toán", money(order["total"]))
        c.metric("Điểm tích lũy", order["points"])

        st.write("Khách hàng:", order["customer"])
        st.write("Điện thoại:", order["phone"])
        st.write("Số bàn:", order["table"])

        st.download_button(
            "📥 TẢI HÓA ĐƠN HTML",
            data=inv["html"].encode("utf-8"),
            file_name=f"hoa_don_{order['code']}.html",
            mime="text/html",
            use_container_width=True
        )
        st.caption("Mở file HTML trên trình duyệt để in hoặc lưu PDF.")


# ==================================================
# QUẢN LÝ THỰC ĐƠN
# ==================================================

elif page == "🍱 Quản lý thực đơn":

    st.markdown(
        '<div class="section-title">🍱 QUẢN LÝ THỰC ĐƠN</div>',
        unsafe_allow_html=True
    )

    menu = get_menu(active=False)
    st.dataframe(menu, use_container_width=True, hide_index=True)

    st.markdown("### ➕ Thêm món")

    with st.form("add_menu"):
        name = st.text_input("Tên món")
        category = st.selectbox(
            "Danh mục",
            ["Sushi", "Sashimi", "Món nóng", "Combo", "Thức uống"]
        )
        price = st.number_input(
            "Giá bán",
            min_value=1000,
            max_value=100000000,
            value=30000,
            step=1000
        )
        best = st.checkbox("Best seller")
        submit = st.form_submit_button("Thêm món")

        if submit:
            if not name.strip():
                st.error("Nhập tên món.")
            else:
                try:
                    with connect() as con:
                        con.execute("""
                        INSERT INTO menu(name,category,price,bestseller,active)
                        VALUES(?,?,?,?,1)
                        """, (name.strip(), category, int(price), int(best)))
                        con.commit()
                    st.success("Đã thêm món.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Tên món đã tồn tại.")

    st.markdown("### ✏️ Sửa giá và trạng thái")

    menu = get_menu(active=False)
    if not menu.empty:
        edit = st.selectbox("Chọn món", menu["name"].tolist())
        row = menu[menu["name"] == edit].iloc[0]
        new_price = st.number_input(
            "Giá mới",
            min_value=1000,
            max_value=100000000,
            value=int(row["price"]),
            step=1000
        )
        active = st.checkbox("Đang bán", value=bool(row["active"]))

        if st.button("Lưu thay đổi"):
            with connect() as con:
                con.execute(
                    "UPDATE menu SET price=?,active=? WHERE name=?",
                    (int(new_price), int(active), edit)
                )
                con.commit()
            st.success("Đã cập nhật.")
            st.rerun()


# ==================================================
# BÁO CÁO DOANH THU
# ==================================================

elif page == "📊 Báo cáo doanh thu":

    st.markdown(
        '<div class="section-title">📊 BÁO CÁO DOANH THU</div>',
        unsafe_allow_html=True
    )

    today = datetime.now().strftime("%Y-%m-%d")

    with connect() as con:
        today_data = con.execute("""
        SELECT COUNT(*),COALESCE(SUM(total),0)
        FROM orders WHERE substr(created_at,1,10)=?
        AND status='Đã thanh toán'
        """, (today,)).fetchone()

        all_data = con.execute("""
        SELECT COUNT(*),COALESCE(SUM(total),0)
        FROM orders WHERE status='Đã thanh toán'
        """).fetchone()

        daily = pd.read_sql_query("""
        SELECT substr(created_at,1,10) AS Ngày,
        COUNT(*) AS Số_đơn,SUM(total) AS Doanh_thu
        FROM orders WHERE status='Đã thanh toán'
        GROUP BY substr(created_at,1,10)
        ORDER BY Ngày
        """, con)

        best = pd.read_sql_query("""
        SELECT oi.name AS Tên_món, SUM(oi.quantity) AS Số_lượng,
               SUM(oi.line_total) AS Doanh_thu
        FROM order_items oi JOIN orders o ON oi.order_id=o.id
        WHERE o.status='Đã thanh toán'
        GROUP BY oi.name ORDER BY Số_lượng DESC LIMIT 10
        """, con)

    a, b, c, d = st.columns(4)
    a.metric("Đơn hôm nay", f"{today_data[0]:,}")
    b.metric("Doanh thu hôm nay", money(today_data[1]))
    c.metric("Tổng đơn", f"{all_data[0]:,}")
    d.metric("Tổng doanh thu", money(all_data[1]))

    st.markdown("### 📈 Doanh thu theo ngày")
    if not daily.empty:
        st.bar_chart(daily.set_index("Ngày")["Doanh_thu"])
        st.dataframe(daily, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu doanh thu.")

    st.markdown("### 🏆 Top món bán chạy")
    if not best.empty:
        best["Doanh_thu"] = best["Doanh_thu"].apply(money)
        st.dataframe(best, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu món bán.")


# ==================================================
# LỊCH SỬ HÓA ĐƠN
# ==================================================

elif page == "🗂️ Lịch sử hóa đơn":

    st.markdown(
        '<div class="section-title">🗂️ LỊCH SỬ HÓA ĐƠN</div>',
        unsafe_allow_html=True
    )

    search = st.text_input("Tìm mã hóa đơn / tên khách / số điện thoại")

    with connect() as con:
        df = pd.read_sql_query(
            "SELECT * FROM orders ORDER BY id DESC", con
        )

    if search.strip() and not df.empty:
        term = search.strip()
        mask = (
            df["code"].astype(str).str.contains(term, case=False, na=False)
            | df["customer"].astype(str).str.contains(term, case=False, na=False)
            | df["phone"].astype(str).str.contains(term, case=False, na=False)
        )
        df = df[mask]

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

        code = st.selectbox("Chọn hóa đơn", df["code"].tolist())

        if st.button("Xem chi tiết"):
            with connect() as con:
                order_row = con.execute(
                    "SELECT * FROM orders WHERE code=?", (code,)
                ).fetchone()

                item_rows = con.execute("""
                SELECT name,category,price,quantity,line_total
                FROM order_items WHERE order_id=?
                """, (order_row[0],)).fetchall()

            items = [{
                "name": r[0], "category": r[1], "price": r[2],
                "quantity": r[3], "line_total": r[4]
            } for r in item_rows]

            order = {
                "code": order_row[1],
                "customer": order_row[2],
                "phone": order_row[3],
                "table": order_row[4],
                "created_at": order_row[5],
                "subtotal": order_row[6],
                "discount": order_row[7],
                "total": order_row[8],
                "points": order_row[9],
                "payment": order_row[11]
            }

            st.write(f"Khách hàng: {order['customer']}")
            st.write(f"Tổng thanh toán: {money(order['total'])}")
            st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

            st.download_button(
                "📥 Tải lại hóa đơn",
                data=invoice_html(order, items).encode("utf-8"),
                file_name=f"hoa_don_{code}.html",
                mime="text/html"
            )

        st.download_button(
            "📥 Xuất lịch sử CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="lich_su_hoa_don_n2_sushi.csv",
            mime="text/csv"
        )
    else:
        st.info("Chưa có hóa đơn phù hợp.")


# ==================================================
# CHATBOT N2 SUSHI - TƯ VẤN BEST SELLER & MÓN RẺ
# ==================================================

elif page == "💬 Chatbot tư vấn":

    st.markdown(
        '<div class="section-title">💬 TRỢ LÝ N2 SUSHI</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="chat-panel">
    <h3>🍣 N2 Sushi Assistant</h3>
    <p style="color:#d0c4b8">
    Tư vấn Best Seller · Gợi ý món giá rẻ · Giờ mở cửa · Địa chỉ · Voucher
    </p></div>
    """, unsafe_allow_html=True)

    def reply(question):
        q = question.lower().strip()
        menu = get_menu()

        if any(k in q for k in ["chào", "hello", "hi"]):
            return "Xin chào! 🍣 Chào mừng bạn đến với N2 Sushi. Bạn cần mình tư vấn món best seller hay món giá rẻ nào không?"

        if any(k in q for k in ["giờ", "mở cửa", "đóng cửa", "mấy giờ"]):
            return f"🕒 Giờ mở cửa của N2 Sushi: {SHOP['hours']}."

        if any(k in q for k in ["địa chỉ", "ở đâu", "đường nào"]):
            return f"📍 Địa chỉ N2 Sushi: {SHOP['address']}."

        if any(k in q for k in ["số điện thoại", "hotline", "liên hệ", "gọi"]):
            return f"☎️ Bạn có thể liên hệ quán qua số {SHOP['phone']}."

        if any(k in q for k in ["voucher", "giảm giá", "khuyến mãi"]):
            return (
                "🎟️ Voucher trong hệ thống:\n"
                "• N2WELCOME: giảm 10%, tối đa 50.000đ.\n"
                "• SUSHI20: giảm 20.000đ cho đơn từ 200.000đ.\n"
                "• N2VIP: giảm 15%, tối đa 100.000đ cho đơn từ 500.000đ."
            )

        if any(k in q for k in ["tích điểm", "điểm", "thành viên"]):
            return "⭐ Mỗi 10.000đ thanh toán được cộng 1 điểm theo chính sách mẫu của app."

        # GỢI Ý MÓN BEST SELLER
        if any(k in q for k in ["best seller", "bán chạy", "ngon nhất", "nên ăn gì"]):
            best = menu[(menu["bestseller"] == 1) & (menu["active"] == 1)]
            return "⭐ **Các món Best Seller được yêu thích nhất tại quán:**\n" + "\n".join(
                f"• {r['name']}: {money(r['price'])}"
                for _, r in best.iterrows()
            )

        # GỢI Ý MÓN RẺ / TIẾT KIỆM
        if any(k in q for k in ["rẻ", "tiết kiệm", "bình dân", "giá rẻ", "ít tiền"]):
            cheap = menu[(menu["price"] <= 40000) & (menu["active"] == 1)].sort_values("price")
            return "💸 **Gợi ý các món giá rẻ, tiết kiệm (dưới 40.000đ):**\n" + "\n".join(
                f"• {r['name']}: {money(r['price'])}"
                for _, r in cheap.iterrows()
            )

        if any(k in q for k in ["combo", "đi hai người", "gia đình", "đi nhóm"]):
            combos = menu[(menu["category"] == "Combo") & (menu["active"] == 1)]
            return "🎎 Combo hiện có:\n" + "\n".join(
                f"• {r['name']}: {money(r['price'])}"
                for _, r in combos.iterrows()
            )

        if any(k in q for k in ["menu", "thực đơn", "có món gì", "giá món"]):
            return "🍱 Menu N2 Sushi:\n" + "\n".join(
                f"• {r['name']}: {money(r['price'])}"
                for _, r in menu[menu["active"] == 1].iterrows()
            )

        for keyword, category in [
            ("sushi", "Sushi"),
            ("sashimi", "Sashimi"),
            ("ramen", "Món nóng"),
            ("tempura", "Món nóng"),
            ("nước", "Thức uống"),
            ("uống", "Thức uống")
        ]:
            if keyword in q:
                subset = menu[
                    (menu["category"] == category)
                    & (menu["active"] == 1)
                ]
                return f"🍣 Các lựa chọn {category}:\n" + "\n".join(
                    f"• {r['name']}: {money(r['price'])}"
                    for _, r in subset.iterrows()
                )

        matched = menu[
            menu["name"].str.lower().str.contains(q, regex=False, na=False)
        ]
        if not matched.empty:
            return "\n".join(
                f"• {r['name']}: {money(r['price'])}"
                for _, r in matched.iterrows()
            )

        return (
            "Mình chưa hiểu câu hỏi này. 😊 Bạn có thể thử hỏi:\n"
            "• Món best seller?\n• Gợi ý món giá rẻ?\n"
            "• Combo cho 2 người?\n• Giờ mở cửa?\n"
            "• Địa chỉ quán?\n• Voucher nào đang dùng được?"
        )

    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.markdown(
                '<div class="chat-user">👤 '
                + html.escape(msg["text"]).replace("\n", "<br>")
                + '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="chat-bubble">🍣 '
                + html.escape(msg["text"]).replace("\n", "<br>")
                + '</div>',
                unsafe_allow_html=True
            )

    st.markdown("### ⚡ Câu hỏi nhanh")

    questions = [
        "Món best seller", "Gợi ý món giá rẻ", "Combo",
        "Voucher", "Giờ mở cửa", "Địa chỉ quán"
    ]

    cols = st.columns(3)
    for i, question in enumerate(questions):
        with cols[i % 3]:
            if st.button(question, key=f"quick_{i}", use_container_width=True):
                st.session_state.chat.append({
                    "role": "user", "text": question
                })
                st.session_state.chat.append({
                    "role": "assistant", "text": reply(question)
                })
                st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input(
            "Nhập câu hỏi",
            placeholder="VD: Gợi ý cho mình vài món giá rẻ hoặc best seller?"
        )
        send = st.form_submit_button("Gửi tin nhắn ✉️", use_container_width=True)
        
        if send and question.strip():
            st.session_state.chat.append({"role": "user", "text": question})
            st.session_state.chat.append({"role": "assistant", "text": reply(question)})
            st.rerun()
        
