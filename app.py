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
            active INTEGER DEFAULT 1,
            image_url TEXT
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
                ("🍣 Sushi cá hồi", "Sushi", 45000, 1, "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?auto=format&fit=crop&w=500&q=80"),
                ("🍣 Sushi cá ngừ", "Sushi", 40000, 0, "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=500&q=80"),
                ("🍣 Sushi lươn Nhật", "Sushi", 55000, 1, "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=500&q=80"),
                ("🍣 Sushi tôm", "Sushi", 35000, 0, "https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=500&q=80"),
                ("🍣 Sushi thanh cua", "Sushi", 30000, 0, "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=500&q=80"),
                ("🍣 Sushi trứng Nhật", "Sushi", 25000, 0, "https://images.unsplash.com/photo-1615361200141-f47040d283b3?auto=format&fit=crop&w=500&q=80"),
                ("🍣 Sushi tổng hợp 8 miếng", "Sushi", 99000, 1, "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=500&q=80"),
                ("🐟 Sashimi cá hồi", "Sashimi", 129000, 1, "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=500&q=80"),
                ("🐟 Sashimi cá ngừ", "Sashimi", 119000, 0, "https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=500&q=80"),
                ("🐟 Sashimi tổng hợp", "Sashimi", 189000, 1, "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=500&q=80"),
                ("🍜 Ramen bò", "Món nóng", 89000, 1, "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=500&q=80"),
                ("🍜 Ramen hải sản", "Món nóng", 95000, 0, "
                 
