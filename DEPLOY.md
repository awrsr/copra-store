# نشر Copra على Render

## 1. رفع المشروع إلى GitHub

أنشئ مستودعًا جديدًا باسم `copra-store` على GitHub، ثم ارفع ملفات المشروع كلها.

لا ترفع أي ملف يحتوي على كلمات مرور أو مفاتيح دفع.

## 2. إنشاء الخدمة

1. افتح Render واختر `New` ثم `Web Service`.
2. اربط مستودع GitHub الخاص بالمشروع.
3. استخدم الإعدادات التالية:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. اختر خطة مدفوعة مناسبة لمتجر حقيقي، لأن الخطط المجانية قد تتوقف عند عدم الاستخدام.

## 3. متغيرات البيئة

أضف:

```text
SECRET_KEY=<قيمة عشوائية طويلة>
SITE_URL=https://copra-eg.com
```

استبدل `copra-eg.com` بالنطاق الذي تشتريه فعلًا.

## 4. ربط النطاق

من Render افتح `Settings` ثم `Custom Domains` وأضف النطاق. سيعرض Render سجلات DNS المطلوبة.

في لوحة شركة النطاق أضف السجلات التي يعرضها Render، ثم انتظر انتشار DNS وتفعيل HTTPS.

## 5. Google

بعد عمل الموقع على النطاق العام:

- افتح Google Search Console.
- أضف النطاق.
- تحقق من الملكية عبر DNS.
- أرسل:
  - `https://copra-eg.com/sitemap.xml`

## روابط الفحص

- `https://copra-eg.com/health`
- `https://copra-eg.com/robots.txt`
- `https://copra-eg.com/sitemap.xml`
