import csv
import io
import os
import json
import sqlite3
import hashlib
import re
import secrets
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, Response, current_app, jsonify, render_template, redirect, request, send_from_directory, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "copra-development-secret-key")
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:5000").rstrip("/")
DATABASE_FILE = os.environ.get("DATABASE_FILE", os.path.join(os.path.dirname(__file__), "copra.db"))
ADMIN_PASSWORD = os.environ.get("STAFF_PASSWORD", os.environ.get("ADMIN_PASSWORD", "copra-admin-123"))
STAFF_APP_DIR = os.path.join(os.path.dirname(__file__), "staff-app", "dist")
FIREBASE_SERVICE_ACCOUNT_JSON = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
STORE_PHONE = os.environ.get("STORE_PHONE", "").strip()
WHATSAPP_NUMBER = re.sub(r"\D", "", os.environ.get("WHATSAPP_NUMBER", ""))
STORE_EMAIL = os.environ.get("STORE_EMAIL", "").strip()


@app.context_processor
def inject_site_config():
    social_links = []
    for label, key in (("Instagram", "INSTAGRAM_URL"), ("Facebook", "FACEBOOK_URL"), ("TikTok", "TIKTOK_URL"), ("X", "X_URL")):
        link = os.environ.get(key, "").strip()
        if link.startswith(("https://", "http://")):
            social_links.append({"label": label, "url": link})
    return {
        "site_url": SITE_URL,
        "now_year": datetime.now().year,
        "store_phone": STORE_PHONE,
        "whatsapp_number": WHATSAPP_NUMBER,
        "store_email": STORE_EMAIL,
        "social_links": social_links,
    }


@app.after_request
def add_pwa_support(response):
    if request.method != "GET" or response.mimetype != "text/html":
        return response

    response.direct_passthrough = False
    html = response.get_data(as_text=True)
    manifest = "/staff/manifest.webmanifest" if request.path == "/staff" or request.path.startswith("/staff/") else "/manifest.webmanifest"
    head_additions = (
        f'<link rel="manifest" href="{manifest}">'
        '<link rel="apple-touch-icon" href="/static/images/apple-touch-icon.png">'
        '<link rel="stylesheet" href="/static/css/pwa.css">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
    )
    if re.search(r'<meta\s+name=["\']viewport["\'][^>]*>', html, re.IGNORECASE):
        html = re.sub(
            r'(<meta\s+name=["\']viewport["\']\s+content=["\'])([^"\']*)(["\'][^>]*>)',
            lambda match: match.group(0) if "viewport-fit=" in match.group(2) else f"{match.group(1)}{match.group(2)}, viewport-fit=cover{match.group(3)}",
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    if "</head>" in html:
        html = html.replace("</head>", f"{head_additions}</head>", 1)
    if "</body>" in html:
        html = html.replace("</body>", '<script src="/static/js/pwa.js" defer></script></body>', 1)
    response.set_data(html)
    return response


def database_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with database_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                stock INTEGER NOT NULL DEFAULT 10,
                barcode TEXT NOT NULL,
                image_url TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                payment_method TEXT NOT NULL,
                delivery_method TEXT NOT NULL,
                delivery_fee INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                total INTEGER NOT NULL,
                status TEXT NOT NULL,
                items_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            );
            CREATE TABLE IF NOT EXISTS realtime_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS staff_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                platform TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        for column, definition in (
            ("tracking_token", "TEXT"),
            ("reject_reason", "TEXT"),
            ("customer_id", "TEXT"),
        ):
            existing_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(orders)")
            }
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")
        user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "name" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ''")
        if "role" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'customer'")
        connection.execute("CREATE INDEX IF NOT EXISTS messages_order_id_idx ON messages(order_id, id)")
        connection.execute("CREATE INDEX IF NOT EXISTS orders_created_at_idx ON orders(created_at)")
        timestamp = datetime.now().isoformat(timespec="seconds")
        for product in products:
            connection.execute(
                """INSERT OR IGNORE INTO products
                (id, name, price, stock, barcode, image_url, updated_at)
                VALUES (?, ?, ?, 10, ?, ?, ?)""",
                (product["id"], product["name"], product["price"], product["barcode"], product["image_url"], timestamp),
            )


def load_product_stock():
    with database_connection() as connection:
        return {row["id"]: row["stock"] for row in connection.execute("SELECT id, stock FROM products")}


def make_barcode(product_id):
    """Create a unique EAN-13-style code for the local catalog."""
    base = f"622000{product_id:06d}"[:12]
    checksum = sum((1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(base))
    return f"{base}{(10 - checksum % 10) % 10}"

products = [
    {"id": 1, "name": "Lenovo IdeaPad 3", "price": 45000, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "أجهزة الكمبيوتر", "subcategory": "لابتوبات"},
    {"id": 2, "name": "Samsung Galaxy A55", "price": 18000, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الهواتف والأجهزة اللوحية", "subcategory": "الهواتف الذكية"},
    {"id": 3, "name": "Sony WH-1000XM5", "price": 1800, "image": "headphones.svg", "department": "الأجهزة والإلكترونيات", "category": "الصوتيات", "subcategory": "سماعات الرأس"},
    {"id": 4, "name": "Samsung Crystal UHD 55 بوصة", "price": 22000, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "التلفزيونات والشاشات", "subcategory": "شاشات ذكية"},
    {"id": 5, "name": "Xiaomi Redmi Watch 4", "price": 3500, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الأجهزة القابلة للارتداء", "subcategory": "الساعات الذكية"},
    {"id": 6, "name": "LC Waikiki قميص قطني", "price": 650, "image": "headphones.svg", "department": "الملابس", "category": "ملابس رجالي", "subcategory": "قمصان وتيشيرتات"},
    {"id": 7, "name": "Defacto بنطلون جينز", "price": 900, "image": "laptop.svg", "department": "الملابس", "category": "ملابس حريمي", "subcategory": "بناطيل وجينز"},
    {"id": 8, "name": "H&M فستان صيفي", "price": 1200, "image": "phone.svg", "department": "الملابس", "category": "ملابس حريمي", "subcategory": "فساتين"},
    {"id": 9, "name": "LC Waikiki جاكيت أطفال", "price": 850, "image": "headphones.svg", "department": "الملابس", "category": "ملابس أطفال", "subcategory": "جاكيتات وملابس شتوية"},
    {"id": 10, "name": "Adidas Runfalcon 3", "price": 1800, "image": "laptop.svg", "department": "الملابس", "category": "الأحذية", "subcategory": "أحذية رياضية"},
    {"id": 11, "name": "American Tourister Backpack", "price": 900, "image": "phone.svg", "department": "الإكسسوارات", "category": "الحقائب", "subcategory": "حقائب ظهر"},
    {"id": 12, "name": "Ray-Ban Aviator", "price": 700, "image": "headphones.svg", "department": "الإكسسوارات", "category": "إكسسوارات شخصية", "subcategory": "نظارات"},
    {"id": 13, "name": "Casio Classic Watch", "price": 2500, "image": "laptop.svg", "department": "الإكسسوارات", "category": "إكسسوارات شخصية", "subcategory": "ساعات"},
    {"id": 14, "name": "Swarovski Silver Necklace", "price": 1500, "image": "phone.svg", "department": "الإكسسوارات", "category": "المجوهرات", "subcategory": "سلاسل ودلايات"},
    {"id": 15, "name": "Philips Blender 5000", "price": 2500, "image": "headphones.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أجهزة المطبخ", "subcategory": "خلاطات"},
    {"id": 16, "name": "Hoover Vacuum Cleaner", "price": 6000, "image": "laptop.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أجهزة التنظيف", "subcategory": "مكانس كهربائية"},
    {"id": 17, "name": "DeLonghi Coffee Machine", "price": 4500, "image": "phone.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أجهزة المطبخ", "subcategory": "ماكينات القهوة"},
    {"id": 18, "name": "Tornado Wall Fan", "price": 1200, "image": "headphones.svg", "department": "المنزل والأجهزة الكهربائية", "category": "التكييف والتهوية", "subcategory": "مراوح"},
    {"id": 19, "name": "Tefal Granite Cookware Set", "price": 3000, "image": "laptop.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أدوات المنزل", "subcategory": "أواني الطهي"},
    {"id": 20, "name": "نجيب محفوظ - رواية عربية", "price": 250, "image": "phone.svg", "department": "الكتب والقرطاسية", "category": "الكتب", "subcategory": "روايات وقصص"},
    {"id": 21, "name": "Moleskine Notebook", "price": 180, "image": "headphones.svg", "department": "الكتب والقرطاسية", "category": "القرطاسية", "subcategory": "دفاتر وأقلام"},
]

products.extend([
    {"id": 22, "name": "MacBook Air M2", "price": 52000, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "أجهزة الكمبيوتر", "subcategory": "لابتوبات"},
    {"id": 23, "name": "Lenovo ThinkPad E14", "price": 28500, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "أجهزة الكمبيوتر", "subcategory": "لابتوبات"},
    {"id": 24, "name": "HP Pavilion 15", "price": 32000, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "أجهزة الكمبيوتر", "subcategory": "لابتوبات"},
    {"id": 25, "name": "iPhone 15", "price": 46000, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الهواتف والأجهزة اللوحية", "subcategory": "الهواتف الذكية"},
    {"id": 26, "name": "Samsung Galaxy A55", "price": 18500, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الهواتف والأجهزة اللوحية", "subcategory": "الهواتف الذكية"},
    {"id": 27, "name": "Xiaomi Redmi Note 13", "price": 9500, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الهواتف والأجهزة اللوحية", "subcategory": "الهواتف الذكية"},
    {"id": 28, "name": "JBL Wireless Speaker", "price": 3200, "image": "headphones.svg", "department": "الأجهزة والإلكترونيات", "category": "الصوتيات", "subcategory": "سماعات الرأس"},
    {"id": 29, "name": "AirPods Pro", "price": 11500, "image": "headphones.svg", "department": "الأجهزة والإلكترونيات", "category": "الصوتيات", "subcategory": "سماعات الرأس"},
    {"id": 30, "name": "Samsung Smart TV 55", "price": 26000, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "التلفزيونات والشاشات", "subcategory": "شاشات ذكية"},
    {"id": 31, "name": "LG Smart TV 43", "price": 17500, "image": "laptop.svg", "department": "الأجهزة والإلكترونيات", "category": "التلفزيونات والشاشات", "subcategory": "شاشات ذكية"},
    {"id": 32, "name": "Apple Watch SE", "price": 14500, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الأجهزة القابلة للارتداء", "subcategory": "الساعات الذكية"},
    {"id": 33, "name": "Samsung Galaxy Watch 6", "price": 10500, "image": "phone.svg", "department": "الأجهزة والإلكترونيات", "category": "الأجهزة القابلة للارتداء", "subcategory": "الساعات الذكية"},
    {"id": 34, "name": "تيشيرت رياضي رجالي", "price": 550, "image": "headphones.svg", "department": "الملابس", "category": "ملابس رجالي", "subcategory": "قمصان وتيشيرتات"},
    {"id": 35, "name": "قميص كتان رجالي", "price": 900, "image": "headphones.svg", "department": "الملابس", "category": "ملابس رجالي", "subcategory": "قمصان وتيشيرتات"},
    {"id": 36, "name": "بنطلون قماش رجالي", "price": 800, "image": "laptop.svg", "department": "الملابس", "category": "ملابس رجالي", "subcategory": "بناطيل وجينز"},
    {"id": 37, "name": "بلوزة نسائية أنيقة", "price": 750, "image": "phone.svg", "department": "الملابس", "category": "ملابس حريمي", "subcategory": "بلوزات"},
    {"id": 38, "name": "تريننج أطفال", "price": 650, "image": "headphones.svg", "department": "الملابس", "category": "ملابس أطفال", "subcategory": "ملابس رياضية"},
    {"id": 39, "name": "حذاء كلاسيك رجالي", "price": 2200, "image": "laptop.svg", "department": "الملابس", "category": "الأحذية", "subcategory": "أحذية رسمية"},
    {"id": 40, "name": "حذاء أطفال خفيف", "price": 950, "image": "phone.svg", "department": "الملابس", "category": "الأحذية", "subcategory": "أحذية أطفال"},
    {"id": 41, "name": "حقيبة لابتوب", "price": 1200, "image": "phone.svg", "department": "الإكسسوارات", "category": "الحقائب", "subcategory": "حقائب لابتوب"},
    {"id": 42, "name": "حقيبة يد جلدية", "price": 1800, "image": "phone.svg", "department": "الإكسسوارات", "category": "الحقائب", "subcategory": "حقائب يد"},
    {"id": 43, "name": "نظارة شمسية مستقطبة", "price": 1100, "image": "headphones.svg", "department": "الإكسسوارات", "category": "إكسسوارات شخصية", "subcategory": "نظارات"},
    {"id": 44, "name": "سوار فضة", "price": 950, "image": "phone.svg", "department": "الإكسسوارات", "category": "المجوهرات", "subcategory": "أساور"},
    {"id": 45, "name": "غسالة ملابس أوتوماتيك", "price": 18500, "image": "laptop.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أجهزة التنظيف", "subcategory": "غسالات"},
    {"id": 46, "name": "قلاية هوائية", "price": 4200, "image": "headphones.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أجهزة المطبخ", "subcategory": "قلايات هوائية"},
    {"id": 47, "name": "ميكروويف 25 لتر", "price": 6500, "image": "phone.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أجهزة المطبخ", "subcategory": "ميكروويف"},
    {"id": 48, "name": "مروحة ستاند", "price": 1800, "image": "headphones.svg", "department": "المنزل والأجهزة الكهربائية", "category": "التكييف والتهوية", "subcategory": "مراوح"},
    {"id": 49, "name": "طقم حلل جرانيت", "price": 3800, "image": "laptop.svg", "department": "المنزل والأجهزة الكهربائية", "category": "أدوات المنزل", "subcategory": "أواني الطهي"},
    {"id": 50, "name": "كتاب تعلم البرمجة", "price": 450, "image": "phone.svg", "department": "الكتب والقرطاسية", "category": "الكتب", "subcategory": "كتب تعليمية"},
    {"id": 51, "name": "مجموعة أقلام ملونة", "price": 220, "image": "headphones.svg", "department": "الكتب والقرطاسية", "category": "القرطاسية", "subcategory": "دفاتر وأقلام"},
])

product_image_urls = {
    1: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85",
    2: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=85",
    3: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85",
    4: "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=85",
    5: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85",
    6: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85",
    7: "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=85",
    8: "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=85",
    9: "https://images.unsplash.com/photo-1519457431-44ccd64a579b?auto=format&fit=crop&w=900&q=85",
    10: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85",
    11: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85",
    12: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=85",
    13: "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=900&q=85",
    14: "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=900&q=85",
    15: "https://images.unsplash.com/photo-1570222094114-d054a817e56b?auto=format&fit=crop&w=900&q=85",
    16: "https://images.unsplash.com/photo-1558317374-067fb5f30001?auto=format&fit=crop&w=900&q=85",
    17: "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=85",
    18: "https://images.unsplash.com/photo-1567789884554-0b844b597180?auto=format&fit=crop&w=900&q=85",
    19: "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=85",
    20: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=85",
    21: "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=900&q=85",
    22: "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=900&q=85",
    23: "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=900&q=85",
    24: "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=900&q=85",
    25: "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?auto=format&fit=crop&w=900&q=85",
    26: "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=900&q=85",
    27: "https://images.unsplash.com/photo-1556656793-08538906a9f8?auto=format&fit=crop&w=900&q=85",
    28: "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=900&q=85",
    29: "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=900&q=85",
    30: "https://images.unsplash.com/photo-1461151304267-38535e780c79?auto=format&fit=crop&w=900&q=85",
    31: "https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=900&q=85",
    32: "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=85",
    33: "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=900&q=85",
    34: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85",
    35: "https://images.unsplash.com/photo-1603252110481-7ba873bf42ab?auto=format&fit=crop&w=900&q=85",
    36: "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=900&q=85",
    37: "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?auto=format&fit=crop&w=900&q=85",
    38: "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?auto=format&fit=crop&w=900&q=85",
    39: "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=900&q=85",
    40: "https://images.unsplash.com/photo-1514989940723-e8e51635b782?auto=format&fit=crop&w=900&q=85",
    41: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85",
    42: "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=900&q=85",
    43: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=85",
    44: "https://images.unsplash.com/photo-1611652022419-a9419f74343d?auto=format&fit=crop&w=900&q=85",
    45: "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=900&q=85",
    46: "https://images.unsplash.com/photo-1585515320310-259814833e62?auto=format&fit=crop&w=900&q=85",
    47: "https://images.unsplash.com/photo-1585659722983-3a675dabf23d?auto=format&fit=crop&w=900&q=85",
    48: "https://images.unsplash.com/photo-1594818379496-da1e345b0ded?auto=format&fit=crop&w=900&q=85",
    49: "https://images.unsplash.com/photo-1584990347449-ae7b4c6b4b3e?auto=format&fit=crop&w=900&q=85",
    50: "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=85",
    51: "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=900&q=85",
}

for product in products:
    product["image_url"] = product_image_urls.get(product["id"])

category_image_urls = {
    "لابتوبات": product_image_urls[1],
    "الهواتف الذكية": product_image_urls[2],
    "سماعات الرأس": product_image_urls[3],
    "شاشات ذكية": product_image_urls[4],
    "الساعات الذكية": product_image_urls[5],
    "قمصان وتيشيرتات": product_image_urls[6],
    "بناطيل وجينز": product_image_urls[7],
    "فساتين": product_image_urls[8],
    "جاكيتات وملابس شتوية": product_image_urls[9],
    "أحذية رياضية": product_image_urls[10],
    "أحذية رسمية": product_image_urls[10],
    "أحذية أطفال": product_image_urls[10],
    "حقائب ظهر": product_image_urls[11],
    "حقائب لابتوب": product_image_urls[1],
    "حقائب يد": product_image_urls[11],
    "نظارات": product_image_urls[12],
    "ساعات": product_image_urls[13],
    "سلاسل ودلايات": product_image_urls[14],
    "أساور": product_image_urls[14],
    "خلاطات": product_image_urls[15],
    "قلايات هوائية": product_image_urls[15],
    "ماكينات القهوة": product_image_urls[17],
    "ميكروويف": product_image_urls[15],
    "مكانس كهربائية": product_image_urls[16],
    "غسالات": product_image_urls[16],
    "مراوح": product_image_urls[18],
    "أواني الطهي": product_image_urls[19],
    "روايات وقصص": product_image_urls[20],
    "كتب تعليمية": product_image_urls[20],
    "دفاتر وأقلام": product_image_urls[21],
}

for product in products:
    product["image_url"] = product["image_url"] or category_image_urls.get(product["subcategory"], product_image_urls[1])
    product["barcode"] = make_barcode(product["id"])

initialize_database()
product_stock = load_product_stock()
for product in products:
    product["stock"] = product_stock.get(product["id"], 10)
if FIREBASE_SERVICE_ACCOUNT_JSON:
    with app.app_context():
        for product in products:
            sync_firestore("products", str(product["id"]), {
                "name": product["name"],
                "price": product["price"],
                "stock": product["stock"],
                "updatedAt": datetime.now().isoformat(timespec="seconds"),
            })

categories = [
    {"name": "الأجهزة والإلكترونيات", "desc": "هواتف وكمبيوتر وشاشات وصوتيات وأجهزة ذكية", "icon": "⚡"},
    {"name": "الملابس", "desc": "ملابس رجالي وحريمي وأطفال وأحذية", "icon": "👕"},
    {"name": "الإكسسوارات", "desc": "حقائب ومجوهرات وساعات ونظارات", "icon": "👜"},
    {"name": "المنزل والأجهزة الكهربائية", "desc": "أجهزة المطبخ والتنظيف والتهوية وأدوات المنزل", "icon": "🏠"},
    {"name": "الكتب والقرطاسية", "desc": "روايات وكتب ودفاتر وأدوات مكتبية", "icon": "📚"},
]

governorates = [
    {"name": "القاهرة", "cities": ["وسط القاهرة", "مدينة نصر", "مصر الجديدة", "المعادي", "الهرم", "الزمالك", "الدقي", "شبرا", "حلوان", "المرج", "روض الفرج", "المنيل"]},
    {"name": "الإسكندرية", "cities": ["وسط المدينة", "سبانخ", "المنتزه", "رأس التين", "سيدي بشر", "برج العرب", "شطا", "الجمرك", "العصافرة", "الورديان"]},
    {"name": "الجيزة", "cities": ["6 أكتوبر", "الشيخ زايد", "الدقي", "الهرم", "الجيزة", "إمبابة", "أكتوبر", "العاشر من رمضان", "الواحات البحرية", "أبو النمرس", "السادس من أكتوبر", "الفيوم"]},
    {"name": "الدقهلية", "cities": ["المنصورة", "طلخا", "ميت غمر", "منزلة", "الجمالية", "دكرنس", "شربين", "أجا", "السنبلاوين", "ديرب نجم"]},
    {"name": "الشرقية", "cities": ["الزقازيق", "بلبيس", "العاشر من رمضان", "الإبراهيمية", "حى الزهور", "أبو حماد", "منيا القمح", "فاقوس", "كفر صقر", "الزقازيق"]},
    {"name": "الغربية", "cities": ["طنطا", "المحلة الكبرى", "زفتي", "سمنود", "بسيون", "كفر الزيات", "بنها", "قويسنا", "كفر الشيخ"]},
    {"name": "المنوفية", "cities": ["شبين الكوم", "اشمون", "منوف", "تلا", "سمنود", "الباجور", "ميدوم", "بركة السبع", "قويسنا"]},
    {"name": "كفر الشيخ", "cities": ["كفر الشيخ", "فوة", "الرياض", "بيلا", "مطوبس", "الحامول", "سيدي سالم", "قلين", "بني مصدق", "دسوق"]},
    {"name": "دمياط", "cities": ["دمياط", "الروضة", "فارسكور", "كفر سعد", "رأس البر", "دمياط الجديدة", "الزرقا", "ميت أبو غالب"]},
    {"name": "بورسعيد", "cities": ["بورسعيد", "شرق بورسعيد", "غرب بورسعيد", "حي الزهور", "حي العرب", "حي الضواحي"]},
    {"name": "الإسماعيلية", "cities": ["الإسماعيلية", "فايد", "التل الكبير", "قنطرة شرق", "القصاصين", "أبو صوير"]},
    {"name": "السويس", "cities": ["السويس", "عتاقة", "الجناين", "السويس الجديدة", "الفيوم", "السويس"]},
    {"name": "الفيوم", "cities": ["الفيوم", "سنورس", "إطسا", "يوسف الصديق", "طامية", "مركز الفيوم"]},
    {"name": "بني سويف", "cities": ["بني سويف", "الفشن", "واسط", "الواسطى", "ناصر", "سمسطا", "ببا"]},
    {"name": "المنيا", "cities": ["المنيا", "مغاغة", "بني مزار", "ملوي", "العدوة", "أبو قرقاص", "سمالوط", "المدينة", "دير مواس"]},
    {"name": "أسيوط", "cities": ["أسيوط", "ديروط", "القوصية", "مركز أسيوط", "أبنوب", "صدفا", "الغنايم", "البداري"]},
    {"name": "سوهاج", "cities": ["سوهاج", "جرجا", "طهطا", "البلينا", "المراغة", "دار السلام", "المنشاة", "أخميم"]},
    {"name": "قنا", "cities": ["قنا", "قوص", "نقادة", "فرشوط", "دشنا", "أبو طشت", "نجع حمادي", "الوقف"]},
    {"name": "الأقصر", "cities": ["الأقصر", "البياضية", "ارمنت", "الزعفران", "البياضية", "الطود", "إسنا", "الرمسي", "ملوي"]},
    {"name": "أسوان", "cities": ["أسوان", "كوم أمبو", "نصر النوبة", "دراو", "إدفو", "أسوان الجديدة", "السباعية", "مركز أسوان"]},
    {"name": "الوادي الجديد", "cities": ["الخارجة", "باريس", "الفرافرة", "بلاط", "أبو المنقار", "الداخلة", "سيوة"]},
    {"name": "مطروح", "cities": ["مرسى مطروح", "الحمام", "سيدي براني", "النجيلة", "العلمين", "ضبعة", "السبتية", "الضبعة"]},
    {"name": "شمال سيناء", "cities": ["العريش", "رفح", "بئر العبد", "نخل", "الميل", "الشيخ زويد", "الطابا"]},
    {"name": "جنوب سيناء", "cities": ["الطور", "شرم الشيخ", "دهب", "نويبع", "أبو رديس", "سانت كاترين", "ايروت"]},
    {"name": "البحيرة", "cities": ["دمنهور", "كوم حمادة", "إدكو", "رشيد", "أبو المطامير", "أبو حمص", "شبراخيت", "وادي النطرون", "الرحمانية"]},
    {"name": "الوادى الجديد", "cities": ["الخارجة", "الفرافرة", "بلاط", "الخارجة الجديدة", "الداخلة", "سيوة"]},
    {"name": "القليوبية", "cities": ["بنها", "الخصوص", "قليوب", "شبين القناطر", "أبو كبير", "العبور", "طوخ", "كفر شكر"]},
    {"name": "المنوفية", "cities": ["شبين الكوم", "مركز منوف", "سيدى سالم", "تلا", "قويسنا", "اشمون", "الباجور"]}
]


def load_orders():
    with database_connection() as connection:
        orders = []
        for row in connection.execute("SELECT * FROM orders ORDER BY created_at DESC"):
            order = dict(row)
            order["items"] = json.loads(order.pop("items_json"))
            order["reject_reason"] = order.get("reject_reason") or ""
            orders.append(order)
        return orders


def save_orders(orders):
    with database_connection() as connection:
        for order in orders:
            connection.execute(
                """INSERT OR REPLACE INTO orders
                (id, created_at, customer_name, phone, address, payment_method,
                delivery_method, delivery_fee, subtotal, total, status, items_json,
                tracking_token, reject_reason, customer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (order["id"], order["created_at"], order["customer_name"], order.get("phone", ""),
                 order.get("address", ""), order["payment_method"], order["delivery_method"],
                 order["delivery_fee"], order["subtotal"], order["total"], order["status"],
                 json.dumps(order["items"], ensure_ascii=False), order.get("tracking_token"),
                 order.get("reject_reason", ""), order.get("customer_id")),
            )


def publish_event(event_type, payload):
    with database_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO realtime_events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")),
        )
    sync_firestore("realtime_events", str(cursor.lastrowid), {
        "event_type": event_type,
        "payload": payload,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })


def initialize_firebase_admin():
    if not FIREBASE_SERVICE_ACCOUNT_JSON:
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError as error:
        current_app.logger.error("Firebase Admin SDK is missing: %s", error)
        return None
    try:
        return firebase_admin.get_app()
    except ValueError:
        try:
            return firebase_admin.initialize_app(
                credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT_JSON))
            )
        except (ValueError, KeyError, TypeError) as error:
            current_app.logger.error("Firebase service-account configuration is invalid: %s", error)
            return None


def sync_firestore(collection, document_id, payload):
    if not FIREBASE_SERVICE_ACCOUNT_JSON:
        return
    firebase_app = initialize_firebase_admin()
    if firebase_app is None:
        return
    try:
        from google.api_core.exceptions import GoogleAPICallError
    except ImportError as error:
        current_app.logger.error("Google API client is unavailable: %s", error)
        return
    try:
        from firebase_admin import firestore
        firestore.client(app=firebase_app).collection(collection).document(str(document_id)).set(payload, merge=True)
    except ImportError as error:
        current_app.logger.error("Firestore support is unavailable: %s", error)
    except (ValueError, TypeError) as error:
        current_app.logger.error("Firestore document sync failed for %s/%s: %s", collection, document_id, error)
    except GoogleAPICallError as error:
        current_app.logger.error("Firestore request failed for %s/%s: %s", collection, document_id, error)


def notify_staff_new_order(order):
    if not FIREBASE_SERVICE_ACCOUNT_JSON:
        return
    try:
        import firebase_admin
        from firebase_admin import messaging
    except ImportError as error:
        current_app.logger.error("Firebase Admin SDK is missing; staff push notifications are unavailable: %s", error)
        return

    try:
        firebase_app = initialize_firebase_admin()
        if firebase_app is None:
            return
        with database_connection() as connection:
            tokens = [
                row["token"] for row in connection.execute("SELECT token FROM staff_devices")
            ]
        if not tokens:
            return
        for start in range(0, len(tokens), 500):
            response = messaging.send_each_for_multicast(messaging.MulticastMessage(
                notification=messaging.Notification(
                    title="طلب جديد في Copra",
                    body=f"{order['id']} · {order['customer_name']}",
                ),
                data={"orderId": order["id"]},
                tokens=tokens[start:start + 500],
            ), app=firebase_app)
            if response.failure_count:
                current_app.logger.warning("FCM failed to deliver %s staff order notifications.", response.failure_count)
    except (ImportError, ValueError, KeyError, TypeError) as error:
        current_app.logger.error("Firebase push notification setup failed: %s", error)
    except firebase_admin.exceptions.FirebaseError as error:
        current_app.logger.error("Firebase push notification delivery failed: %s", error)


def get_order(order_id):
    with database_connection() as connection:
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        return None
    order = dict(row)
    order["items"] = json.loads(order.pop("items_json"))
    order["reject_reason"] = order.get("reject_reason") or ""
    return order


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped_view


def get_cart_items():
    cart = session.get("cart", {})
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = next((p for p in products if p["id"] == int(product_id)), None)
        if product:
            subtotal = product["price"] * quantity
            items.append({
                "id": product["id"], "name": product["name"], "price": product["price"],
                "quantity": quantity, "subtotal": subtotal, "image": product["image"],
                "image_url": product["image_url"],
            })
            total += subtotal
    return items, total


def get_department_groups(catalog=None):
    catalog = products if catalog is None else catalog
    department_groups = []
    for department in categories:
        department_products = [product for product in catalog if product["department"] == department["name"]]
        category_groups = []
        category_names = []
        for product in department_products:
            if product["category"] not in category_names:
                category_names.append(product["category"])
        for category_name in category_names:
            category_groups.append({
                "name": category_name,
                "products": [product for product in department_products if product["category"] == category_name],
            })
        if department_products:
            department_groups.append({**department, "groups": category_groups, "product_count": len(department_products)})
    return department_groups


@app.route("/")
def index():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    search_query = request.args.get("q", "").strip()
    if search_query:
        normalized_query = search_query.casefold()
        filtered_products = [
            product for product in products
            if any(normalized_query in product[field].casefold() for field in ("name", "department", "category", "subcategory"))
        ]
    else:
        filtered_products = products

    return render_template(
        "index.html",
        products=filtered_products,
        department_groups=get_department_groups(filtered_products),
        cart_count=cart_count,
        search_query=search_query,
    )


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session["cart"] = cart
    return redirect(url_for("index"))


@app.route("/buy_now/<int:product_id>")
def buy_now(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        return redirect(url_for("index"))
    cart = session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session["cart"] = cart
    return redirect(url_for("checkout"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = get_cart_items()
    cart_count = sum(session.get("cart", {}).values())
    if request.method == "POST":
        if not items:
            return redirect(url_for("cart"))
        delivery_fee = max(0, min(int(request.form.get("delivery_fee", 10)), 50))
        for item in items:
            product = next(product for product in products if product["id"] == item["id"])
            if item["quantity"] > product.get("stock", 0):
                return redirect(url_for("cart"))
        tracking_token = secrets.token_urlsafe(32)
        order = {
            "id": f"COP-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "customer_name": request.form.get("full_name", "عميل جديد").strip() or "عميل جديد",
            "phone": request.form.get("phone", "").strip(),
            "address": request.form.get("address", "").strip(),
            "payment_method": request.form.get("payment_method", "الدفع عند الاستلام"),
            "delivery_method": request.form.get("delivery_method", "التوصيل العادي"),
            "delivery_fee": delivery_fee,
            "subtotal": total,
            "total": total + delivery_fee,
            "status": "Pending",
            "reject_reason": "",
            "tracking_token": tracking_token,
            "customer_id": session.get("user_id"),
            "items": items,
        }
        orders = load_orders()
        orders.insert(0, order)
        save_orders(orders)
        sync_firestore("orders", order["id"], {
            "customerId": order["customer_id"],
            "customerName": order["customer_name"],
            "phone": order["phone"],
            "address": order["address"],
            "items": order["items"],
            "totalPrice": order["total"],
            "deliveryFee": order["delivery_fee"],
            "status": order["status"],
            "rejectReason": "",
            "trackingToken": order["tracking_token"],
            "createdAt": order["created_at"],
        })
        publish_event("order.created", {"id": order["id"]})
        notify_staff_new_order(order)
        session["cart"] = {}
        return render_template("order_success.html", order=order)
    return render_template("checkout.html", cart_items=items, total=total, cart_count=cart_count, governorates=governorates)


@app.route("/cart")
def cart():
    items, total = get_cart_items()
    cart_count = sum(session.get("cart", {}).values())
    return render_template("cart.html", cart_items=items, total=total, cart_count=cart_count)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        return redirect(url_for("index"))

    cart_count = sum(session.get("cart", {}).values())
    return render_template("product_detail.html", product=product, cart_count=cart_count)


@app.route("/login")
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password_hash = hashlib.sha256(request.form.get("password", "").encode()).hexdigest()
        with database_connection() as connection:
            user = connection.execute("SELECT id FROM users WHERE email = ? AND password_hash = ?", (email, password_hash)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["user_email"] = email
            sync_firestore("users", str(user["id"]), {
                "name": "",
                "email": email,
                "role": "customer",
            })
            return redirect(url_for("index"))
        error = "البريد الإلكتروني أو كلمة المرور غير صحيحة"
    return render_template("login.html", error=error)


def staff_api_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({"error": "يلزم تسجيل دخول الستاف."}), 401
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/staff/")
@app.route("/staff")
def staff_app():
    if not os.path.isfile(os.path.join(STAFF_APP_DIR, "index.html")):
        return Response("واجهة الستاف غير مبنية بعد. شغّل npm run build داخل staff-app.", status=503, mimetype="text/plain")
    return send_from_directory(STAFF_APP_DIR, "index.html")


@app.route("/staff/<path:asset_path>")
def staff_assets(asset_path):
    requested_asset = os.path.join(STAFF_APP_DIR, asset_path)
    if os.path.isfile(requested_asset):
        return send_from_directory(STAFF_APP_DIR, asset_path)
    if os.path.splitext(asset_path)[1]:
        return Response("الملف المطلوب غير موجود.", status=404, mimetype="text/plain")
    if os.path.isfile(os.path.join(STAFF_APP_DIR, "index.html")):
        return send_from_directory(STAFF_APP_DIR, "index.html")
    return Response("واجهة الستاف غير مبنية بعد.", status=503, mimetype="text/plain")


@app.route("/api/staff/login", methods=["POST"])
def staff_api_login():
    password = request.form.get("password", "")
    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        return jsonify({"error": "كلمة المرور غير صحيحة."}), 401
    session.clear()
    session["admin_logged_in"] = True
    session["staff_id"] = "staff-admin"
    sync_firestore("users", "staff-admin", {
        "name": "مدير المتجر",
        "email": os.environ.get("STAFF_EMAIL", ""),
        "role": "staff",
    })
    return jsonify({"staff": {"id": "staff-admin", "name": "مدير المتجر", "role": "staff"}})


@app.route("/api/staff/session")
def staff_api_session():
    if not session.get("admin_logged_in"):
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "staff": {"id": session.get("staff_id", "staff-admin"), "name": "فريق Copra", "role": "staff"},
    })


@app.route("/api/staff/logout", methods=["POST"])
@staff_api_required
def staff_api_logout():
    session.pop("admin_logged_in", None)
    session.pop("staff_id", None)
    return jsonify({"ok": True})


@app.route("/api/staff/device-token", methods=["POST"])
@staff_api_required
def staff_api_device_token():
    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token", "")).strip()
    platform = str(payload.get("platform", "")).strip().lower()
    if not token or len(token) > 4096 or platform not in {"android", "ios", "web"}:
        return jsonify({"error": "بيانات تسجيل الإشعارات غير صالحة."}), 400
    with database_connection() as connection:
        connection.execute(
            """INSERT INTO staff_devices (token, platform, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(token) DO UPDATE SET platform = excluded.platform, updated_at = excluded.updated_at""",
            (token, platform, datetime.now().isoformat(timespec="seconds")),
        )
    return jsonify({"ok": True})


def prepare_staff_order(order):
    order = dict(order)
    order["items"] = order.get("items", [])
    normalized = {
        "جديد": "Pending",
        "قيد التجهيز": "Approved",
        "خرج للتوصيل": "Approved",
        "تم التسليم": "Approved",
        "ملغي": "Rejected",
    }
    order["status"] = normalized.get(order.get("status"), order.get("status", "Pending"))
    with database_connection() as connection:
        inventory = {
            row["id"]: row["stock"]
            for row in connection.execute("SELECT id, stock FROM products")
        }
    order["can_approve"] = all(
        inventory.get(item["id"], 0) >= item["quantity"]
        for item in order["items"]
    ) and bool(order["items"])
    return order


@app.route("/api/staff/orders")
@staff_api_required
def staff_api_orders():
    orders = [prepare_staff_order(order) for order in load_orders()]
    orders.sort(key=lambda order: (order["status"] != "Pending", order["created_at"]), reverse=False)
    return jsonify({"orders": orders})


@app.route("/api/staff/inventory")
@staff_api_required
def staff_api_inventory():
    with database_connection() as connection:
        stock_by_id = {
            row["id"]: row["stock"]
            for row in connection.execute("SELECT id, stock FROM products")
        }
    return jsonify({
        "products": [
            {"id": product["id"], "name": product["name"], "price": product["price"], "stock": stock_by_id.get(product["id"], 0)}
            for product in products
        ]
    })


@app.route("/api/staff/inventory/<int:product_id>", methods=["PATCH"])
@staff_api_required
def staff_api_update_inventory(product_id):
    product = next((item for item in products if item["id"] == product_id), None)
    if product is None:
        return jsonify({"error": "المنتج غير موجود."}), 404
    try:
        stock = int(request.get_json(silent=True).get("stock"))
    except (AttributeError, TypeError, ValueError):
        return jsonify({"error": "أدخل كمية مخزون صحيحة."}), 400
    if stock < 0 or stock > 1_000_000:
        return jsonify({"error": "يجب أن تكون الكمية بين 0 و 1,000,000."}), 400
    with database_connection() as connection:
        connection.execute(
            "UPDATE products SET stock = ?, updated_at = ? WHERE id = ?",
            (stock, datetime.now().isoformat(timespec="seconds"), product_id),
        )
    sync_firestore("products", str(product_id), {
        "name": product["name"],
        "price": product["price"],
        "stock": stock,
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
    })
    product["stock"] = stock
    publish_event("inventory.updated", {"id": product_id, "stock": stock})
    return jsonify({"product": {"id": product_id, "stock": stock}})


@app.route("/api/staff/orders/<order_id>/status", methods=["POST"])
@staff_api_required
def staff_api_update_order_status(order_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    reject_reason = str(payload.get("rejectReason", "")).strip()[:1000]
    if status not in {"Approved", "Rejected"}:
        return jsonify({"error": "الحالة المطلوبة غير صالحة."}), 400
    if status == "Rejected" and not reject_reason:
        return jsonify({"error": "يرجى كتابة سبب الرفض."}), 400

    with database_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            connection.rollback()
            return jsonify({"error": "الطلب غير موجود."}), 404
        current_status = {"جديد": "Pending"}.get(row["status"], row["status"])
        if current_status != "Pending":
            connection.rollback()
            return jsonify({"error": "تمت معالجة هذا الطلب مسبقاً."}), 409
        order_items = json.loads(row["items_json"])
        if status == "Approved":
            for item in order_items:
                update = connection.execute(
                    "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ? AND stock >= ?",
                    (item["quantity"], datetime.now().isoformat(timespec="seconds"), item["id"], item["quantity"]),
                )
                if update.rowcount != 1:
                    connection.rollback()
                    return jsonify({"error": f"المخزون غير كافٍ للمنتج: {item['name']}"}), 409
        connection.execute(
            "UPDATE orders SET status = ?, reject_reason = ? WHERE id = ?",
            (status, reject_reason if status == "Rejected" else "", order_id),
        )
        connection.commit()

    for item in order_items:
        product = next((entry for entry in products if entry["id"] == item["id"]), None)
        if product:
            product["stock"] = max(0, product["stock"] - item["quantity"]) if status == "Approved" else product["stock"]
            sync_firestore("products", str(product["id"]), {
                "name": product["name"],
                "price": product["price"],
                "stock": product["stock"],
                "updatedAt": datetime.now().isoformat(timespec="seconds"),
            })
    order = get_order(order_id)
    sync_firestore("orders", order_id, {
        "status": status,
        "rejectReason": reject_reason if status == "Rejected" else "",
    })
    publish_event("order.updated", {"id": order_id, "status": status, "rejectReason": reject_reason})
    return jsonify({"order": prepare_staff_order(order)})


@app.route("/api/staff/events")
@staff_api_required
def staff_api_events():
    try:
        last_id = max(0, int(request.headers.get("Last-Event-ID", request.args.get("after", 0))))
    except ValueError:
        last_id = 0

    def event_stream():
        nonlocal last_id
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            with database_connection() as connection:
                rows = connection.execute(
                    "SELECT id, event_type, payload FROM realtime_events WHERE id > ? ORDER BY id LIMIT 100",
                    (last_id,),
                ).fetchall()
            for row in rows:
                last_id = row["id"]
                yield f"id: {row['id']}\nevent: {row['event_type']}\ndata: {row['payload']}\n\n"
            if not rows:
                yield ": keep-alive\n\n"
            time.sleep(1)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/track/<tracking_token>")
def track_order(tracking_token):
    with database_connection() as connection:
        row = connection.execute(
            "SELECT id FROM orders WHERE tracking_token = ?",
            (tracking_token,),
        ).fetchone()
    if not row:
        return render_template("order_success.html", order=None), 404
    return render_template("track_order.html", order_id=row["id"], tracking_token=tracking_token)


@app.route("/api/orders/<order_id>")
def customer_order_status(order_id):
    tracking_token = request.args.get("token", "")
    order = get_order(order_id)
    if not order or not tracking_token or not secrets.compare_digest(order.get("tracking_token") or "", tracking_token):
        return jsonify({"error": "الطلب غير موجود."}), 404
    return jsonify({
        "order": {
            "id": order["id"],
            "status": {
                "جديد": "Pending",
                "قيد التجهيز": "Approved",
                "خرج للتوصيل": "Approved",
                "تم التسليم": "Approved",
                "ملغي": "Rejected",
            }.get(order["status"], order["status"]),
            "rejectReason": order.get("reject_reason", ""),
            "createdAt": order["created_at"],
            "customerName": order["customer_name"],
            "items": order["items"],
            "total": order["total"],
        }
    })


@app.route("/api/orders/<order_id>/events")
def customer_order_events(order_id):
    order = get_order(order_id)
    tracking_token = request.args.get("token", "")
    if not order or not tracking_token or not secrets.compare_digest(order.get("tracking_token") or "", tracking_token):
        return jsonify({"error": "الطلب غير موجود."}), 404
    try:
        last_id = max(0, int(request.headers.get("Last-Event-ID", request.args.get("after", 0))))
    except ValueError:
        last_id = 0

    def event_stream():
        nonlocal last_id
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            with database_connection() as connection:
                rows = connection.execute(
                    "SELECT id, event_type, payload FROM realtime_events WHERE id > ? ORDER BY id LIMIT 100",
                    (last_id,),
                ).fetchall()
            for row in rows:
                last_id = row["id"]
                payload = json.loads(row["payload"])
                if payload.get("id") == order_id or payload.get("orderId") == order_id:
                    yield f"id: {row['id']}\nevent: {row['event_type']}\ndata: {row['payload']}\n\n"
            if not rows:
                yield ": keep-alive\n\n"
            time.sleep(1)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def load_order_messages(order_id):
    with database_connection() as connection:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT id, order_id, sender_id, text, created_at FROM messages WHERE order_id = ? ORDER BY id",
                (order_id,),
            )
        ]


@app.route("/api/orders/<order_id>/messages", methods=["GET", "POST"])
def order_messages(order_id):
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "الطلب غير موجود."}), 404
    is_staff = bool(session.get("admin_logged_in"))
    tracking_token = request.args.get("token", "") or (request.get_json(silent=True) or {}).get("token", "")
    is_customer = bool(tracking_token) and secrets.compare_digest(order.get("tracking_token") or "", tracking_token)
    if not is_staff and not is_customer:
        return jsonify({"error": "غير مصرح بالوصول إلى دردشة هذا الطلب."}), 403
    if request.method == "GET":
        return jsonify({"messages": load_order_messages(order_id)})
    payload = request.get_json(silent=True) or {}
    message_text = str(payload.get("text", "")).strip()
    if not message_text or len(message_text) > 2000:
        return jsonify({"error": "اكتب رسالة لا تتجاوز 2000 حرف."}), 400
    sender_id = session.get("staff_id", "staff-admin") if is_staff else (str(order.get("customer_id") or "customer"))
    with database_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO messages (order_id, sender_id, text, created_at) VALUES (?, ?, ?, ?)",
            (order_id, sender_id, message_text, datetime.now().isoformat(timespec="seconds")),
        )
        message_id = cursor.lastrowid
    sync_firestore("messages", str(message_id), {
        "orderId": order_id,
        "senderId": sender_id,
        "text": message_text,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })
    publish_event("message.created", {"orderId": order_id, "messageId": message_id})
    return jsonify({"message": {
        "id": message_id,
        "order_id": order_id,
        "sender_id": sender_id,
        "text": message_text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }}), 201


@app.route("/categories")
def cats():
    category_filter = request.args.get("category", "").strip()
    if category_filter:
        filtered_catalog = [
            product for product in products
            if category_filter in (product["department"], product["category"], product["subcategory"])
        ]
    else:
        filtered_catalog = products

    return render_template(
        "categories.html",
        categories=get_department_groups(filtered_catalog),
        cart_count=sum(session.get("cart", {}).values()),
        category_filter=category_filter,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "كلمة المرور غير صحيحة"
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    orders = load_orders()
    with database_connection() as connection:
        contact_messages = connection.execute(
            "SELECT name, email, phone, message, created_at FROM contact_messages ORDER BY id DESC LIMIT 30"
        ).fetchall()
    revenue = sum(order.get("total", 0) for order in orders)
    units_sold = sum(item.get("quantity", 0) for order in orders for item in order.get("items", []))
    product_sales = {}
    for order in orders:
        for item in order.get("items", []):
            product_sales[item["name"]] = product_sales.get(item["name"], 0) + item.get("quantity", 0)
    top_products = sorted(product_sales.items(), key=lambda item: item[1], reverse=True)[:5]
    return render_template("admin_dashboard.html", orders=orders, revenue=revenue, units_sold=units_sold, top_products=top_products, products=products, contact_messages=contact_messages)


@app.route("/admin/orders/<order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    allowed_statuses = {"جديد", "قيد التجهيز", "خرج للتوصيل", "تم التسليم", "ملغي"}
    status = request.form.get("status", "جديد")
    if status in allowed_statuses:
        with database_connection() as connection:
            connection.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        if status in allowed_statuses:
            canonical_status = "Pending" if status == "جديد" else "Rejected" if status == "ملغي" else "Approved"
            publish_event("order.updated", {"id": order_id, "status": canonical_status, "rejectReason": ""})
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/<int:product_id>/stock", methods=["POST"])
@admin_required
def update_product_stock(product_id):
    stock = max(0, int(request.form.get("stock", 0)))
    with database_connection() as connection:
        connection.execute("UPDATE products SET stock = ?, updated_at = ? WHERE id = ?", (stock, datetime.now().isoformat(timespec="seconds"), product_id))
    product = next((product for product in products if product["id"] == product_id), None)
    if product:
        product["stock"] = stock
    publish_event("inventory.updated", {"id": product_id, "stock": stock})
    return redirect(url_for("admin_dashboard"))


@app.route("/export/products.csv")
def export_products():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "barcode", "name", "department", "category", "subcategory", "price_egp", "image_url"])
    writer.writeheader()
    for product in products:
        writer.writerow({
            "id": product["id"],
            "barcode": product["barcode"],
            "name": product["name"],
            "department": product["department"],
            "category": product["category"],
            "subcategory": product["subcategory"],
            "price_egp": product["price"],
            "image_url": product["image_url"],
        })

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=copra-products.csv"},
    )


@app.route("/health")
def health():
    return {"status": "ok"}


def pwa_manifest(name, short_name, start_url, scope):
    return {
        "name": name,
        "short_name": short_name,
        "description": "Copra — متجر إلكتروني ولوحة فريق العمل.",
        "start_url": start_url,
        "scope": scope,
        "display": "standalone",
        "background_color": "#090a0c",
        "theme_color": "#ff3b30",
        "icons": [
            {"src": "/static/images/copra-icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/static/images/copra-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/static/images/copra-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }


@app.route("/manifest.webmanifest")
def customer_pwa_manifest():
    response = jsonify(pwa_manifest("Copra Store", "Copra", "/", "/"))
    response.mimetype = "application/manifest+json"
    return response


@app.route("/staff/manifest.webmanifest")
def staff_pwa_manifest():
    response = jsonify(pwa_manifest("Copra Staff", "Copra Staff", "/staff/", "/staff/"))
    response.mimetype = "application/manifest+json"
    return response


@app.route("/service-worker.js")
def pwa_service_worker():
    response = send_from_directory(os.path.join(os.path.dirname(__file__), "static"), "service-worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/offline")
def pwa_offline():
    return render_template("offline.html"), 200


@app.route("/contact", methods=["POST"])
def submit_contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()
    if not name or len(name) > 120:
        return {"error": "يرجى إدخال اسم صحيح."}, 400
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
        return {"error": "يرجى إدخال بريد إلكتروني صحيح."}, 400
    if len(phone) > 30 or not message or len(message) > 3000:
        return {"error": "يرجى إدخال رقم صحيح ورسالة لا تتجاوز 3000 حرف."}, 400

    with database_connection() as connection:
        connection.execute(
            "INSERT INTO contact_messages (name, email, phone, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone, message, datetime.now().isoformat(timespec="seconds")),
        )
    return {"message": "تم استلام رسالتك بنجاح."}


@app.route("/newsletter", methods=["POST"])
def subscribe_newsletter():
    email = request.form.get("email", "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
        return {"error": "يرجى إدخال بريد إلكتروني صحيح."}, 400

    with database_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO newsletter_subscribers (email, created_at) VALUES (?, ?)",
            (email, datetime.now().isoformat(timespec="seconds")),
        )
    return {"message": "تم تسجيل بريدك في النشرة البريدية."}


@app.route("/robots.txt")
def robots():
    return Response(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
        mimetype="text/plain",
    )


@app.route("/sitemap.xml")
def sitemap():
    urls = [f"{SITE_URL}/", f"{SITE_URL}/categories"]
    urls.extend(f"{SITE_URL}/product/{product['id']}" for product in products)
    xml_urls = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_urls}</urlset>',
        mimetype="application/xml",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
