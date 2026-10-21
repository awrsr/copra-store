# نشر Copra على Render

## 1. رفع المشروع إلى GitHub

أنشئ مستودعًا جديدًا باسم `copra-store` على GitHub، ثم ارفع ملفات المشروع كلها.

لا ترفع أي ملف يحتوي على كلمات مرور أو مفاتيح دفع.

## 2. إنشاء الخدمة

1. افتح Render واختر `New` ثم `Web Service`.
2. اربط مستودع GitHub الخاص بالمشروع.
3. استخدم الإعدادات التالية:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --worker-class gthread --workers 2 --threads 16 --timeout 120 app:app`
4. اختر خطة مدفوعة مناسبة لمتجر حقيقي، لأن الخطط المجانية قد تتوقف عند عدم الاستخدام.

## 3. متغيرات البيئة

أضف:

```text
SECRET_KEY=<قيمة عشوائية طويلة>
STAFF_PASSWORD=<كلمة مرور قوية وفريدة للستاف>
SITE_URL=https://copra-eg.com
STORE_PHONE=+20...
WHATSAPP_NUMBER=20...
STORE_EMAIL=...
INSTAGRAM_URL=https://instagram.com/...
FACEBOOK_URL=https://facebook.com/...
TIKTOK_URL=https://tiktok.com/@...
X_URL=https://x.com/...
```

استبدل `copra-eg.com` بالنطاق الذي تشتريه فعلًا.
بيانات الهاتف والبريد وروابط التواصل اختيارية؛ لا تظهر روابطها في الموقع ما لم تضف بياناتك الحقيقية. اكتب رقم واتساب بأرقام دولية من دون `+` أو مسافات.

رسائل نموذج التواصل تُحفظ في لوحة الإدارة، واشتراكات النشرة تُحفظ بقاعدة البيانات؛ لا يتم إرسال بريد آلي من دون إعداد مزود بريد. ملف قاعدة البيانات على Render يُحفظ على القرص الدائم المحدد في `render.yaml`.

## لوحة الستاف وتطبيق الموبايل

- ابنِ لوحة React/Tailwind من مجلد `staff-app` باستخدام `npm install` ثم `npm run build`. تظهر اللوحة بعد النشر على `/staff`.
- لتجربة محلية مباشرة، شغّل Flask بـ `python app.py`، ثم من `staff-app` شغّل `npm run dev` وافتح `http://127.0.0.1:5173/staff/`.
- سجّل الدخول بكلمة مرور `STAFF_PASSWORD`، ثم أنشئ طلباً من المتجر في تبويب آخر. الطلبات والتحديثات والدردشة تظهر عبر اتصال Server-Sent Events.
- التطبيق يستخدم SQLite على القرص الدائم في Render ويُزامن سجلات المستخدمين والطلبات والمخزون والرسائل إلى Firestore عند ضبط `FIREBASE_SERVICE_ACCOUNT_JSON`. تشغّل الخدمة Gunicorn بنمط threaded لدعم اتصالات SSE المفتوحة دون حجب بقية الطلبات. انشر قواعد [firestore.rules](./firestore.rules) التي تمنع الوصول المباشر من المتصفح؛ مفتاح الخدمة يُحفظ في إعدادات الاستضافة فقط.
- إشعارات FCM تحتاج إعداد تطبيق Firebase، ورفع `google-services.json` إلى `staff-app/android/app` بعد إضافة منصة Android، ثم بناء التطبيق. بناء iOS وإشعارات APNs يتطلب جهاز Mac وبيانات اعتماد Apple. راجع [staff-app/README.md](./staff-app/README.md).

## تثبيت الموقع كتطبيق PWA

- المتجر متاح للتثبيت عبر `https://<نطاقك>/`، ولوحة الستاف عبر `https://<نطاقك>/staff/`. يحتاج الهاتف اتصال HTTPS (أو `localhost` للاختبار).
- على Android وChrome استخدم زر «تثبيت» الذي يظهر عندما يكون المتصفح جاهزاً، أو قائمة المتصفح ثم «تثبيت التطبيق». على iPhone/iPad افتح الرابط في Safari واضغط «مشاركة» ثم «إضافة إلى الشاشة الرئيسية».
- عند انقطاع الاتصال تعرض الصفحات المحمّلة رسالة عدم الاتصال، وتفتح صفحة مساعدة مخزنة مؤقتاً. الطلبات، تسجيل الدخول، والمخزون والدردشة تحتاج اتصالاً؛ لا تُخزّن بياناتها الخاصة أو تغييراتها لإرسالها لاحقاً.
- للتحقق افتح Chrome DevTools → Application: تأكد من ظهور Manifest وService Worker بحالة activated، ثم Lighthouse → Progressive Web App. جرّب أيضاً تحميل الموقع ثم فعّل Network → Offline وأعد تحميله للتحقق من صفحة عدم الاتصال.
- لإنشاء حزمة Android، استخدم `https://www.pwabuilder.com/` على النطاق المنشور HTTPS واتبع خطوات Android/Trusted Web Activity؛ قد تتطلب الحزمة توقيعاً ومفتاح Digital Asset Links لإزالة شريط المتصفح. iOS يسمح بإضافة PWA من Safari إلى الشاشة الرئيسية ولا يحتاج متجر تطبيقات.

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
