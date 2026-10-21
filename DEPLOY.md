# نشر Copra مجاناً على Render وSupabase

## 1. رفع المشروع إلى GitHub

المشروع مرتبط بمستودع GitHub `awrsr/copra-store`. يحتفظ `.gitignore` بقاعدة SQLite المحلية ومفاتيح الخدمات خارج Git.

## 2. إنشاء قاعدة البيانات المجانية

1. أنشئ مشروعاً في [Supabase](https://supabase.com/dashboard) واختر خطة Free.
2. من لوحة المشروع افتح **Connect** واختر **Session pooler**، وانسخ رابط PostgreSQL الذي يحتوي على `sslmode=require`.
3. احتفظ بالرابط كسرّ؛ يحتوي على كلمة مرور قاعدة البيانات. لا تضعه في Git ولا ترسله في المحادثات.
4. ينشئ التطبيق الجداول والفهارس والمنتجات الابتدائية تلقائياً عند أول تشغيل باستخدام صلاحيات مالك قاعدة البيانات.
5. تبدأ قاعدة البيانات المنشورة فارغة من الطلبات والمخزون الذي كان محفوظاً محلياً؛ لم يتم رفع `copra.db`.

## 3. إنشاء الخدمة المجانية

1. افتح Render واختر `New` ثم `Web Service`.
2. اربط GitHub واختر `awrsr/copra-store` والفرع `main`.
3. استخدم Blueprint إعداد `render.yaml` أو اضبط الخدمة كالتالي:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --worker-class gthread --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT app:app`
   - Plan: Free (لا يوجد قرص محلي؛ البيانات تحفظ في PostgreSQL على Supabase).
4. عند طلب القيم السرية، أدخل `DATABASE_URL` من Supabase، واضبط `STAFF_PASSWORD` على كلمة مرور فريدة من **12 حرفاً على الأقل**. لا تستخدم كلمة `123456789`.
5. يحفظ Render `SECRET_KEY` تلقائياً في إعداد البيئة. لا تنشر قبل ضبط `DATABASE_URL` و`STAFF_PASSWORD`؛ يتوقف التطبيق عمداً في الإنتاج إذا كان أحدهما ناقصاً أو كانت كلمة المرور قصيرة.

### حدود الاستضافة المجانية

- خدمة Render Free قد تدخل في وضع السكون عند الخمول، فيتأخر أول فتح إلى أن تستيقظ.
- مشروع Supabase Free قد يتوقف بعد أسبوع من دون نشاط، ومساحة قاعدة البيانات محدودة. راقب توفر قاعدة البيانات من لوحة Supabase.
- هذه الخطة مناسبة للتجربة والاستخدام منخفض الحركة، ولا تضمن توافراً دائماً أو اتفاقية مستوى خدمة لمتجر تجاري.

## 4. متغيرات البيئة الاختيارية

بعد إنشاء الخدمة يمكنك إضافة `SITE_URL` ورقم الهاتف وواتساب والبريد وروابط التواصل الاجتماعي في إعدادات البيئة. لا تظهر روابط التواصل ما لم تضف بيانات صحيحة. اكتب رقم واتساب دولياً من دون `+` أو مسافات.

## لوحة الستاف وتطبيق الموبايل

- ابنِ لوحة React/Tailwind من مجلد `staff-app` باستخدام `npm install` ثم `npm run build`. تظهر اللوحة بعد النشر على `/staff`.
- لتجربة محلية مباشرة، شغّل Flask بـ `python app.py`، ثم من `staff-app` شغّل `npm run dev` وافتح `http://127.0.0.1:5173/staff/`.
- سجّل الدخول بكلمة مرور `STAFF_PASSWORD`، ثم أنشئ طلباً من المتجر في تبويب آخر. الطلبات والتحديثات والدردشة تظهر عبر اتصال Server-Sent Events.
- التطبيق يستخدم PostgreSQL على Supabase في الإنتاج، وSQLite المحلي للتطوير فقط. يُزامن سجلات Firestore اختيارياً عند ضبط `FIREBASE_SERVICE_ACCOUNT_JSON`. تشغّل الخدمة Gunicorn بنمط threaded لدعم اتصالات SSE القصيرة القابلة لإعادة الاتصال. انشر قواعد [firestore.rules](./firestore.rules) التي تمنع الوصول المباشر من المتصفح؛ مفتاح الخدمة يبقى في إعدادات الاستضافة فقط.
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
