document.addEventListener("DOMContentLoaded", function() {
    console.log("Welcome to Copra ⚡ Store!");

    const siteIntro = document.querySelector("#site-intro");
    const enterStore = document.querySelector("#enter-store");
    if (siteIntro && enterStore) {
        const introVideo = siteIntro.querySelector(".intro-video");
        const closeIntro = function() {
            siteIntro.classList.add("is-hidden");
        };

        if (introVideo) {
            introVideo.addEventListener("error", function() {
                siteIntro.classList.add("video-fallback");
            });
        }
        enterStore.addEventListener("click", closeIntro);
    }

    const translations = {
        "العربية": "Arabic",
        "بحث": "Search",
        "ابحث عن المنتجات ...": "Search products ...",
        "تسجيل الدخول": "Sign in",
        "مرحبًا، تسجيل الدخول": "Hello, sign in",
        "الحساب والقوائم": "Account & Lists",
        "طلباتك": "Your Orders",
        "عربة التسوق": "Cart",
        "كل الأقسام": "All Departments",
        "الرئيسية": "Home",
        "الإلكترونيات": "Electronics",
        "الهواتف": "Phones",
        "الكمبيوتر": "Computers",
        "الملابس": "Fashion",
        "الأحذية": "Shoes",
        "الإكسسوارات": "Accessories",
        "المنزل": "Home & Appliances",
        "الكتب والقرطاسية": "Books & Stationery",
        "العروض": "Deals",
        "أفضل المبيعات": "Best Sellers",
        "تصفح الأقسام": "Browse Categories",
        "عرض كل القسم": "Shop this department",
        "منتجاتنا المميزة": "Featured Products",
        "نتائج البحث": "Search results",
        "لم نجد هذا المنتج": "No products found",
        "جرب البحث باسم آخر أو اختر قسمًا من الأقسام الموجودة.": "Try another search or choose a department.",
        "عرض كل المنتجات": "Show all products",
        "تسوق الآن": "Shop now",
        "بأفضل الأسعار": "at the best prices",
        "عروض عادلة": "Fair offers",
        "على أجهزةك": "on your devices",
        "خصومات اليوم": "Today's deals",
        "توصيل مجاني": "Free delivery",
        "إرجاع سهل": "Easy returns",
        "بطاقة فيزا": "Visa card",
        "الدفع عند الاستلام": "Cash on delivery",
        "اختر طريقة الدفع": "Choose a payment method",
        "اسم حامل البطاقة": "Cardholder name",
        "رقم البطاقة": "Card number",
        "اسم الكامل": "Full name",
        "أدخل اسم المستلم": "Enter recipient name",
        "رقم الهاتف": "Phone number",
        "المحافظة": "Governorate",
        "اختر المحافظة": "Choose governorate",
        "سلة المشتريات": "Shopping cart",
        "السلة فارغة حاليًا.": "Your cart is currently empty.",
        "إتمام الطلب": "Place order",
        "متابعة التسوق": "Continue shopping",
        "الإجمالي": "Total",
        "الكمية": "Quantity",
        "منتج مميز": "Featured product",
        "توصيل سريع": "Fast delivery",
        "ضمان أصلية": "Authentic warranty",
        "استرجاع سهل": "Easy returns",
        "الدفع": "Checkout",
        "عرض السلة": "View cart",
        "حسابك": "Your Account",
        "عناوينك": "Your Addresses",
        "قوائمك": "Your Lists",
        "إنشاء قائمة": "Create a list",
        "ابدأ من هنا": "Start here",
        "ليس لديك حساب؟": "New customer?",
        "الدخول": "Sign in",
        "البريد الإلكتروني": "Email",
        "كلمة المرور": "Password",
        "كل الأقسام والفئات": "All departments and categories",
        "الأقسام | Copra": "Categories | Copra",
        "الدفع": "Checkout",
        "سلة المشتريات": "Shopping cart",
        "تسوق حسب احتياجك": "Shop by need",
        "اختار القسم، ثم الفئة، وشوف المنتجات المتاحة مباشرة.": "Choose a department, then browse its available products.",
        "المنتجات الموجودة في القسم المحدد.": "Products in the selected department."
    };

    const reverseTranslations = Object.fromEntries(
        Object.entries(translations).map(([arabic, english]) => [english, arabic])
    );

    const localizedTranslations = {
        fr: {
            "بحث": "Rechercher", "ابحث عن المنتجات ...": "Rechercher des produits...", "تسجيل الدخول": "Se connecter", "طلباتك": "Vos commandes", "عربة التسوق": "Panier", "الرئيسية": "Accueil", "كل الأقسام": "Tous les départements", "الإلكترونيات": "Électronique", "الهواتف": "Téléphones", "الكمبيوتر": "Ordinateurs", "الملابس": "Mode", "الأحذية": "Chaussures", "الإكسسوارات": "Accessoires", "المنزل": "Maison et appareils", "الكتب والقرطاسية": "Livres et papeterie", "العروض": "Offres", "تصفح الأقسام": "Parcourir les catégories", "منتجاتنا المميزة": "Produits vedettes", "نتائج البحث": "Résultats de recherche", "لم نجد هذا المنتج": "Aucun produit trouvé", "عرض كل المنتجات": "Voir tous les produits", "الدفع": "Paiement", "سلة المشتريات": "Panier", "الإجمالي": "Total", "الكمية": "Quantité", "إتمام الطلب": "Passer la commande", "متابعة التسوق": "Continuer les achats", "اختر طريقة الدفع": "Choisissez un mode de paiement", "بطاقة فيزا": "Carte Visa", "الدفع عند الاستلام": "Paiement à la livraison"
        },
        es: {
            "بحث": "Buscar", "ابحث عن المنتجات ...": "Buscar productos...", "تسجيل الدخول": "Iniciar sesión", "طلباتك": "Tus pedidos", "عربة التسوق": "Carrito", "الرئيسية": "Inicio", "كل الأقسام": "Todos los departamentos", "الإلكترونيات": "Electrónica", "الهواتف": "Teléfonos", "الكمبيوتر": "Ordenadores", "الملابس": "Moda", "الأحذية": "Zapatos", "الإكسسوارات": "Accesorios", "المنزل": "Hogar y electrodomésticos", "الكتب والقرطاسية": "Libros y papelería", "العروض": "Ofertas", "تصفح الأقسام": "Explorar categorías", "منتجاتنا المميزة": "Productos destacados", "نتائج البحث": "Resultados de búsqueda", "لم نجد هذا المنتج": "No se encontraron productos", "عرض كل المنتجات": "Ver todos los productos", "الدفع": "Pago", "سلة المشتريات": "Carrito de compras", "الإجمالي": "Total", "الكمية": "Cantidad", "إتمام الطلب": "Realizar pedido", "متابعة التسوق": "Continuar comprando", "اختر طريقة الدفع": "Elige un método de pago", "بطاقة فيزا": "Tarjeta Visa", "الدفع عند الاستلام": "Pago contra entrega"
        },
        de: {
            "بحث": "Suchen", "ابحث عن المنتجات ...": "Produkte suchen...", "تسجيل الدخول": "Anmelden", "طلباتك": "Ihre Bestellungen", "عربة التسوق": "Warenkorb", "الرئيسية": "Startseite", "كل الأقسام": "Alle Abteilungen", "الإلكترونيات": "Elektronik", "الهواتف": "Telefone", "الكمبيوتر": "Computer", "الملابس": "Mode", "الأحذية": "Schuhe", "الإكسسوارات": "Accessoires", "المنزل": "Haushalt und Geräte", "الكتب والقرطاسية": "Bücher und Schreibwaren", "العروض": "Angebote", "تصفح الأقسام": "Kategorien durchsuchen", "منتجاتنا المميزة": "Empfohlene Produkte", "نتائج البحث": "Suchergebnisse", "لم نجد هذا المنتج": "Keine Produkte gefunden", "عرض كل المنتجات": "Alle Produkte anzeigen", "الدفع": "Kasse", "سلة المشتريات": "Warenkorb", "الإجمالي": "Gesamt", "الكمية": "Menge", "إتمام الطلب": "Bestellung aufgeben", "متابعة التسوق": "Weiter einkaufen", "اختر طريقة الدفع": "Zahlungsart auswählen", "بطاقة فيزا": "Visa-Karte", "الدفع عند الاستلام": "Nachnahme"
        },
        it: {
            "بحث": "Cerca", "ابحث عن المنتجات ...": "Cerca prodotti...", "تسجيل الدخول": "Accedi", "طلباتك": "I tuoi ordini", "عربة التسوق": "Carrello", "الرئيسية": "Home", "كل الأقسام": "Tutte le categorie", "الإلكترونيات": "Elettronica", "الهواتف": "Telefoni", "الكمبيوتر": "Computer", "الملابس": "Moda", "الأحذية": "Scarpe", "الإكسسوارات": "Accessori", "المنزل": "Casa ed elettrodomestici", "الكتب والقرطاسية": "Libri e cancelleria", "العروض": "Offerte", "تصفح الأقسام": "Sfoglia categorie", "منتجاتنا المميزة": "Prodotti in evidenza", "نتائج البحث": "Risultati di ricerca", "لم نجد هذا المنتج": "Nessun prodotto trovato", "عرض كل المنتجات": "Mostra tutti i prodotti", "الدفع": "Pagamento", "سلة المشتريات": "Carrello", "الإجمالي": "Totale", "الكمية": "Quantità", "إتمام الطلب": "Completa ordine", "متابعة التسوق": "Continua lo shopping", "اختر طريقة الدفع": "Scegli un metodo di pagamento", "بطاقة فيزا": "Carta Visa", "الدفع عند الاستلام": "Pagamento alla consegna"
        },
        tr: {
            "بحث": "Ara", "ابحث عن المنتجات ...": "Ürünlerde ara...", "تسجيل الدخول": "Giriş yap", "طلباتك": "Siparişleriniz", "عربة التسوق": "Sepet", "الرئيسية": "Ana sayfa", "كل الأقسام": "Tüm kategoriler", "الإلكترونيات": "Elektronik", "الهواتف": "Telefonlar", "الكمبيوتر": "Bilgisayarlar", "الملابس": "Moda", "الأحذية": "Ayakkabılar", "الإكسسوارات": "Aksesuarlar", "المنزل": "Ev ve cihazlar", "الكتب والقرطاسية": "Kitap ve kırtasiye", "العروض": "Fırsatlar", "تصفح الأقسام": "Kategorilere göz at", "منتجاتنا المميزة": "Öne çıkan ürünler", "نتائج البحث": "Arama sonuçları", "لم نجد هذا المنتج": "Ürün bulunamadı", "عرض كل المنتجات": "Tüm ürünleri göster", "الدفع": "Ödeme", "سلة المشتريات": "Alışveriş sepeti", "الإجمالي": "Toplam", "الكمية": "Miktar", "إتمام الطلب": "Sipariş ver", "متابعة التسوق": "Alışverişe devam et", "اختر طريقة الدفع": "Ödeme yöntemi seçin", "بطاقة فيزا": "Visa kartı", "الدفع عند الاستلام": "Kapıda ödeme"
        },
        ru: {
            "بحث": "Поиск", "ابحث عن المنتجات ...": "Поиск товаров...", "تسجيل الدخول": "Войти", "طلباتك": "Ваши заказы", "عربة التسوق": "Корзина", "الرئيسية": "Главная", "كل الأقسام": "Все разделы", "الإلكترونيات": "Электроника", "الهواتف": "Телефоны", "الكمبيوتر": "Компьютеры", "الملابس": "Одежда", "الأحذية": "Обувь", "الإكسسوارات": "Аксессуары", "المنزل": "Дом и техника", "الكتب والقرطاسية": "Книги и канцелярия", "العروض": "Предложения", "تصفح الأقسام": "Просмотреть категории", "منتجاتنا المميزة": "Избранные товары", "نتائج البحث": "Результаты поиска", "لم نجد هذا المنتج": "Товары не найдены", "عرض كل المنتجات": "Показать все товары", "الدفع": "Оплата", "سلة المشتريات": "Корзина", "الإجمالي": "Итого", "الكمية": "Количество", "إتمام الطلب": "Оформить заказ", "متابعة التسوق": "Продолжить покупки", "اختر طريقة الدفع": "Выберите способ оплаты", "بطاقة فيزا": "Карта Visa", "الدفع عند الاستلام": "Оплата при получении"
        },
        zh: {
            "بحث": "搜索", "ابحث عن المنتجات ...": "搜索商品...", "تسجيل الدخول": "登录", "طلباتك": "我的订单", "عربة التسوق": "购物车", "الرئيسية": "首页", "كل الأقسام": "全部分类", "الإلكترونيات": "电子产品", "الهواتف": "手机", "الكمبيوتر": "电脑", "الملابس": "服装", "الأحذية": "鞋类", "الإكسسوارات": "配饰", "المنزل": "家居和电器", "الكتب والقرطاسية": "图书和文具", "العروض": "优惠", "تصفح الأقسام": "浏览分类", "منتجاتنا المميزة": "精选商品", "نتائج البحث": "搜索结果", "لم نجد هذا المنتج": "未找到商品", "عرض كل المنتجات": "查看所有商品", "الدفع": "结账", "سلة المشتريات": "购物车", "الإجمالي": "总计", "الكمية": "数量", "إتمام الطلب": "提交订单", "متابعة التسوق": "继续购物", "اختر طريقة الدفع": "选择付款方式", "بطاقة فيزا": "Visa 卡", "الدفع عند الاستلام": "货到付款"
        },
        ja: {
            "بحث": "検索", "ابحث عن المنتجات ...": "商品を検索...", "تسجيل الدخول": "ログイン", "طلباتك": "注文履歴", "عربة التسوق": "カート", "الرئيسية": "ホーム", "كل الأقسام": "すべてのカテゴリー", "الإلكترونيات": "電子機器", "الهواتف": "スマートフォン", "الكمبيوتر": "コンピューター", "الملابس": "ファッション", "الأحذية": "靴", "الإكسسوارات": "アクセサリー", "المنزل": "家庭用品・家電", "الكتب والقرطاسية": "本・文房具", "العروض": "セール", "تصفح الأقسام": "カテゴリーを見る", "منتجاتنا المميزة": "おすすめ商品", "نتائج البحث": "検索結果", "لم نجد هذا المنتج": "商品が見つかりません", "عرض كل المنتجات": "すべての商品を見る", "الدفع": "チェックアウト", "سلة المشتريات": "ショッピングカート", "الإجمالي": "合計", "الكمية": "数量", "إتمام الطلب": "注文を確定", "متابعة التسوق": "買い物を続ける", "اختر طريقة الدفع": "支払い方法を選択", "بطاقة فيزا": "Visaカード", "الدفع عند الاستلام": "代金引換"
        },
        ko: {
            "بحث": "검색", "ابحث عن المنتجات ...": "상품 검색...", "تسجيل الدخول": "로그인", "طلباتك": "주문 내역", "عربة التسوق": "장바구니", "الرئيسية": "홈", "كل الأقسام": "전체 카테고리", "الإلكترونيات": "전자제품", "الهواتف": "휴대폰", "الكمبيوتر": "컴퓨터", "الملابس": "패션", "الأحذية": "신발", "الإكسسوارات": "액세서리", "المنزل": "가정 및 가전", "الكتب والقرطاسية": "도서 및 문구", "العروض": "특가", "تصفح الأقسام": "카테고리 보기", "منتجاتنا المميزة": "추천 상품", "نتائج البحث": "검색 결과", "لم نجد هذا المنتج": "상품을 찾을 수 없습니다", "عرض كل المنتجات": "모든 상품 보기", "الدفع": "결제", "سلة المشتريات": "장바구니", "الإجمالي": "합계", "الكمية": "수량", "إتمام الطلب": "주문하기", "متابعة التسوق": "쇼핑 계속하기", "اختر طريقة الدفع": "결제 방법 선택", "بطاقة فيزا": "Visa 카드", "الدفع عند الاستلام": "착불 결제"
        },
        hi: {
            "بحث": "खोजें", "ابحث عن المنتجات ...": "उत्पाद खोजें...", "تسجيل الدخول": "साइन इन", "طلباتك": "आपके ऑर्डर", "عربة التسوق": "कार्ट", "الرئيسية": "होम", "كل الأقسام": "सभी विभाग", "الإلكترونيات": "इलेक्ट्रॉनिक्स", "الهواتف": "फोन", "الكمبيوتر": "कंप्यूटर", "الملابس": "फैशन", "الأحذية": "जूते", "الإكسسوارات": "सहायक उपकरण", "المنزل": "घर और उपकरण", "الكتب والقرطاسية": "किताबें और स्टेशनरी", "العروض": "ऑफर", "تصفح الأقسام": "श्रेणियां देखें", "منتجاتنا المميزة": "विशेष उत्पाद", "نتائج البحث": "खोज परिणाम", "لم نجد هذا المنتج": "कोई उत्पाद नहीं मिला", "عرض كل المنتجات": "सभी उत्पाद दिखाएं", "الدفع": "चेकआउट", "سلة المشتريات": "शॉपिंग कार्ट", "الإجمالي": "कुल", "الكمية": "मात्रा", "إتمام الطلب": "ऑर्डर करें", "متابعة التسوق": "खरीदारी जारी रखें", "اختر طريقة الدفع": "भुगतान विधि चुनें", "بطاقة فيزا": "Visa कार्ड", "الدفع عند الاستلام": "डिलीवरी पर भुगतान"
        },
        ur: {
            "بحث": "تلاش", "ابحث عن المنتجات ...": "مصنوعات تلاش کریں...", "تسجيل الدخول": "سائن ان", "طلباتك": "آپ کے آرڈرز", "عربة التسوق": "کارٹ", "الرئيسية": "ہوم", "كل الأقسام": "تمام شعبے", "الإلكترونيات": "الیکٹرانکس", "الهواتف": "فونز", "الكمبيوتر": "کمپیوٹرز", "الملابس": "فیشن", "الأحذية": "جوتے", "الإكسسوارات": "لوازمات", "المنزل": "گھر اور آلات", "الكتب والقرطاسية": "کتابیں اور اسٹیشنری", "العروض": "آفرز", "تصفح الأقسام": "زمرے دیکھیں", "منتجاتنا المميزة": "نمایاں مصنوعات", "نتائج البحث": "تلاش کے نتائج", "لم نجد هذا المنتج": "کوئی پروڈکٹ نہیں ملا", "عرض كل المنتجات": "تمام مصنوعات دیکھیں", "الدفع": "چیک آؤٹ", "سلة المشتريات": "خریداری کی ٹوکری", "الإجمالي": "کل", "الكمية": "مقدار", "إتمام الطلب": "آرڈر مکمل کریں", "متابعة التسوق": "خریداری جاری رکھیں", "اختر طريقة الدفع": "ادائیگی کا طریقہ منتخب کریں", "بطاقة فيزا": "Visa کارڈ", "الدفع عند الاستلام": "ڈیلیوری پر ادائیگی"
        },
        nl: {
            "بحث": "Zoeken", "ابحث عن المنتجات ...": "Producten zoeken...", "تسجيل الدخول": "Inloggen", "طلباتك": "Je bestellingen", "عربة التسوق": "Winkelwagen", "الرئيسية": "Home", "كل الأقسام": "Alle afdelingen", "الإلكترونيات": "Elektronica", "الهواتف": "Telefoons", "الكمبيوتر": "Computers", "الملابس": "Mode", "الأحذية": "Schoenen", "الإكسسوارات": "Accessoires", "المنزل": "Huis en apparaten", "الكتب والقرطاسية": "Boeken en kantoorartikelen", "العروض": "Aanbiedingen", "تصفح الأقسام": "Categorieën bekijken", "منتجاتنا المميزة": "Uitgelichte producten", "نتائج البحث": "Zoekresultaten", "لم نجد هذا المنتج": "Geen producten gevonden", "عرض كل المنتجات": "Alle producten bekijken", "الدفع": "Afrekenen", "سلة المشتريات": "Winkelwagen", "الإجمالي": "Totaal", "الكمية": "Aantal", "إتمام الطلب": "Bestelling plaatsen", "متابعة التسوق": "Verder winkelen", "اختر طريقة الدفع": "Kies een betaalmethode", "بطاقة فيزا": "Visa-kaart", "الدفع عند الاستلام": "Betalen bij levering"
        },
        pt: {
            "بحث": "Pesquisar", "ابحث عن المنتجات ...": "Pesquisar produtos...", "تسجيل الدخول": "Entrar", "طلباتك": "Seus pedidos", "عربة التسوق": "Carrinho", "الرئيسية": "Início", "كل الأقسام": "Todos os departamentos", "الإلكترونيات": "Eletrônicos", "الهواتف": "Telefones", "الكمبيوتر": "Computadores", "الملابس": "Moda", "الأحذية": "Calçados", "الإكسسوارات": "Acessórios", "المنزل": "Casa e eletrodomésticos", "الكتب والقرطاسية": "Livros e papelaria", "العروض": "Ofertas", "تصفح الأقسام": "Ver categorias", "منتجاتنا المميزة": "Produtos em destaque", "نتائج البحث": "Resultados da pesquisa", "لم نجد هذا المنتج": "Nenhum produto encontrado", "عرض كل المنتجات": "Ver todos os produtos", "الدفع": "Pagamento", "سلة المشتريات": "Carrinho de compras", "الإجمالي": "Total", "الكمية": "Quantidade", "إتمام الطلب": "Finalizar pedido", "متابعة التسوق": "Continuar comprando", "اختر طريقة الدفع": "Escolha um método de pagamento", "بطاقة فيزا": "Cartão Visa", "الدفع عند الاستلام": "Pagamento na entrega"
        }
    };

    function translateText(text, language) {
        const dictionary = language === "ar"
            ? reverseTranslations
            : { ...translations, ...(localizedTranslations[language] || {}) };
        const trimmed = text.trim();
        if (dictionary[trimmed]) {
            return text.replace(trimmed, dictionary[trimmed]);
        }
        if (language === "en") {
            return text
                .replace(/^السلة \((\d+)\)$/, "Cart ($1)")
                .replace(/^(\d+) منتجات$/, "$1 products")
                .replace(/^الإجمالي:/, "Total:")
                .replace(/^الكمية:/, "Quantity:");
        }
        return text
            .replace(/^Cart \((\d+)\)$/, "السلة ($1)")
            .replace(/^(\d+) products$/, "$1 منتجات")
            .replace(/^Total:/, "الإجمالي:")
            .replace(/^Quantity:/, "الكمية:");
    }

    function translatePage(language) {
        document.documentElement.lang = language;
        document.documentElement.dir = ["ar", "ur"].includes(language) ? "rtl" : "ltr";
        document.title = translateText(document.title, language);
        document.querySelectorAll("[data-language-select]").forEach(select => {
            select.value = language;
        });

        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const textNodes = [];
        while (walker.nextNode()) textNodes.push(walker.currentNode);
        textNodes.forEach(node => {
            if (node.parentElement && ["SCRIPT", "STYLE", "OPTION"].includes(node.parentElement.tagName)) return;
            node.nodeValue = translateText(node.nodeValue, language);
        });

        document.querySelectorAll("input[placeholder], textarea[placeholder]").forEach(field => {
            const placeholder = field.getAttribute("placeholder");
            const translated = translateText(placeholder, language);
            field.setAttribute("placeholder", translated);
        });
    }

    const savedLanguage = localStorage.getItem("copra-language") || "ar";
    translatePage(savedLanguage);

    document.querySelectorAll("[data-language-select]").forEach(select => {
        select.addEventListener("change", function() {
            localStorage.setItem("copra-language", select.value);
            window.location.reload();
        });
    });

    const deliveryOptions = document.querySelectorAll("input[name='delivery']");
    const deliveryFee = document.querySelector("#delivery-fee");
    const orderTotal = document.querySelector("#order-total");
    if (deliveryOptions.length && deliveryFee && orderTotal) {
        const updateDelivery = function() {
            const selected = document.querySelector("input[name='delivery']:checked");
            const fee = Number(selected.value);
            const subtotal = Number(orderTotal.dataset.subtotal);
            deliveryOptions.forEach(option => option.closest(".delivery-option").classList.toggle("is-selected", option.checked));
            deliveryFee.textContent = `${fee} ج.م`;
            orderTotal.textContent = `${subtotal + fee} ج.م`;
        };
        deliveryOptions.forEach(option => option.addEventListener("change", updateDelivery));
        updateDelivery();
    }

    const accountTrigger = document.querySelector(".account-trigger");
    const accountMenu = document.querySelector(".account-menu");

    if (accountTrigger && accountMenu) {
        accountTrigger.addEventListener("click", function() {
            const isOpen = accountMenu.classList.toggle("is-open");
            accountTrigger.setAttribute("aria-expanded", String(isOpen));
        });

        document.addEventListener("click", function(event) {
            if (!accountMenu.contains(event.target)) {
                accountMenu.classList.remove("is-open");
                accountTrigger.setAttribute("aria-expanded", "false");
            }
        });
    }
});
