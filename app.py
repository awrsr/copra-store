import csv
import io
import os

from flask import Flask, Response, render_template, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "copra-development-secret-key")
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:5000").rstrip("/")


@app.context_processor
def inject_site_config():
    return {"site_url": SITE_URL}

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


def get_cart_items():
    cart = session.get("cart", {})
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = next((p for p in products if p["id"] == int(product_id)), None)
        if product:
            subtotal = product["price"] * quantity
            items.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": subtotal,
                "image": product["image"],
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
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/checkout")
def checkout():
    items, total = get_cart_items()
    cart_count = sum(session.get("cart", {}).values())
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
def login():
    return render_template("login.html")


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


@app.route("/export/products.csv")
def export_products():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "name", "department", "category", "subcategory", "price_egp", "image_url"])
    writer.writeheader()
    for product in products:
        writer.writerow({
            "id": product["id"],
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
