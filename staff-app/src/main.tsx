import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { createRoot } from "react-dom/client";
import { Capacitor } from "@capacitor/core";
import { PushNotifications } from "@capacitor/push-notifications";
import {
  AlertTriangle,
  Boxes,
  Check,
  CheckCheck,
  ChevronLeft,
  Clock3,
  LogOut,
  MessageCircle,
  PackageCheck,
  RefreshCw,
  Search,
  Send,
  ShoppingBag,
  Volume2,
  X,
} from "lucide-react";
import "./index.css";

type OrderStatus = "Pending" | "Approved" | "Rejected";
type OrderItem = { id: number; name: string; price: number; quantity: number; subtotal: number };
type Order = {
  id: string;
  created_at: string;
  customer_name: string;
  phone: string;
  address: string;
  payment_method: string;
  delivery_method: string;
  total: number;
  status: OrderStatus;
  reject_reason: string;
  items: OrderItem[];
  can_approve: boolean;
};
type InventoryProduct = { id: number; name: string; price: number; stock: number };
type ChatMessage = { id: number; order_id: string; sender_id: string; text: string; created_at: string };
type StaffUser = { id: string; name: string; role: string };

async function api<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    ...options,
    headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || "تعذر إكمال الطلب.");
  return result as T;
}

function formatDate(value: string) {
  const date = new Date(value.replace(" ", "T"));
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("ar-EG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function App() {
  const [staff, setStaff] = useState<StaffUser | null>(null);
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [inventory, setInventory] = useState<InventoryProduct[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeOrderId, setActiveOrderId] = useState("");
  const [messageText, setMessageText] = useState("");
  const [search, setSearch] = useState("");
  const [activeSection, setActiveSection] = useState<"orders" | "inventory" | "chats">("orders");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [rejectTarget, setRejectTarget] = useState<Order | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [busyOrderId, setBusyOrderId] = useState("");
  const previousPendingIds = useRef<Set<string>>(new Set());
  const audioContext = useRef<AudioContext | null>(null);

  const refresh = useCallback(async (notify = false) => {
    const [orderData, inventoryData] = await Promise.all([
      api<{ orders: Order[] }>("/api/staff/orders"),
      api<{ products: InventoryProduct[] }>("/api/staff/inventory"),
    ]);
    const pendingIds = new Set(orderData.orders.filter((order) => order.status === "Pending").map((order) => order.id));
    const hasNewOrder = [...pendingIds].some((id) => !previousPendingIds.current.has(id));
    previousPendingIds.current = pendingIds;
    setOrders(orderData.orders);
    setInventory(inventoryData.products);
    if (notify && hasNewOrder) {
      if (soundEnabled) playNotification();
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("طلب جديد في Copra", { body: "تم استلام طلب جديد ويحتاج إلى المراجعة." });
      }
    }
  }, [soundEnabled]);

  const playNotification = useCallback(() => {
    try {
      const context = audioContext.current ?? new AudioContext();
      audioContext.current = context;
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0.0001, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.12, context.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.32);
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.34);
    } catch (audioError) {
      console.warn("تعذر تشغيل صوت إشعار الطلب.", audioError);
    }
  }, []);

  useEffect(() => {
    api<{ authenticated: boolean; staff: StaffUser }>("/api/staff/session")
      .then((result) => {
        setStaff(result.staff);
        return refresh();
      })
      .catch(() => setStaff(null))
      .finally(() => setLoading(false));
  }, [refresh]);

  useEffect(() => {
    if (!staff) return;
    let source: EventSource | undefined;
    let retryTimer: number | undefined;
    const connect = () => {
      source = new EventSource("/api/staff/events");
      source.addEventListener("order.created", () => { void refresh(true).catch(showError); });
      source.addEventListener("order.updated", () => { void refresh().catch(showError); });
      source.addEventListener("inventory.updated", () => { void refresh().catch(showError); });
      source.addEventListener("message.created", (event) => {
        void refresh().catch(showError);
        const payload = JSON.parse((event as MessageEvent).data) as { orderId: string };
        if (payload.orderId === activeOrderId) void loadMessages(payload.orderId).catch(showError);
      });
      source.onerror = () => {
        source?.close();
        retryTimer = window.setTimeout(connect, 1500);
      };
    };
    connect();
    return () => {
      source?.close();
      window.clearTimeout(retryTimer);
    };
  }, [staff, refresh, activeOrderId]);

  useEffect(() => {
    if (!staff || !activeOrderId) {
      setMessages([]);
      return;
    }
    void loadMessages(activeOrderId).catch(showError);
  }, [staff, activeOrderId]);

  const showError = (cause: unknown) => {
    setError(cause instanceof Error ? cause.message : "حدث خطأ غير متوقع.");
    setSuccess("");
  };

  const loadMessages = async (orderId: string) => {
    const result = await api<{ messages: ChatMessage[] }>(`/api/orders/${encodeURIComponent(orderId)}/messages`);
    setMessages(result.messages);
  };

  const pendingOrders = useMemo(() => orders.filter((order) => order.status === "Pending"), [orders]);
  const filteredOrders = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    const sectionOrders = activeSection === "orders" ? pendingOrders : orders;
    if (!query) return sectionOrders;
    return sectionOrders.filter((order) =>
      [order.id, order.customer_name, order.phone].some((value) => value.toLocaleLowerCase().includes(query)),
    );
  }, [activeSection, orders, pendingOrders, search]);
  const activeOrder = orders.find((order) => order.id === activeOrderId);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError("");
    try {
      const result = await api<{ staff: StaffUser }>("/api/staff/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ password }),
      });
      setStaff(result.staff);
      setPassword("");
      await refresh();
      if ("Notification" in window && Notification.permission === "default") {
        await Notification.requestPermission();
      }
      if (Capacitor.isNativePlatform()) await registerPushNotifications();
    } catch (cause) {
      setLoginError(cause instanceof Error ? cause.message : "تعذر تسجيل الدخول.");
    }
  }

  async function registerPushNotifications() {
    try {
      let permission = await PushNotifications.checkPermissions();
      if (permission.receive === "prompt" || permission.receive === "prompt-with-rationale") {
        permission = await PushNotifications.requestPermissions();
      }
      if (permission.receive !== "granted") return;
      await PushNotifications.addListener("registration", async ({ value }) => {
        await api("/api/staff/device-token", {
          method: "POST",
          body: JSON.stringify({ token: value, platform: Capacitor.getPlatform() }),
        });
      });
      await PushNotifications.addListener("registrationError", (event) => {
        console.error("تعذر تسجيل إشعارات الجهاز.", event);
      });
      await PushNotifications.register();
    } catch (cause) {
      console.error("تعذر إعداد الإشعارات الفورية.", cause);
      setError("تم تسجيل الدخول، لكن تعذر إعداد إشعارات الجهاز. تحقق من إعداد Firebase.");
    }
  }

  async function signOut() {
    try {
      await api("/api/staff/logout", { method: "POST" });
      setStaff(null);
      setOrders([]);
      setInventory([]);
      setMessages([]);
    } catch (cause) {
      showError(cause);
    }
  }

  async function updateOrder(order: Order, status: "Approved" | "Rejected", reason = "") {
    setBusyOrderId(order.id);
    setError("");
    setSuccess("");
    try {
      await api(`/api/staff/orders/${encodeURIComponent(order.id)}/status`, {
        method: "POST",
        body: JSON.stringify({ status, rejectReason: reason }),
      });
      setSuccess(status === "Approved" ? `تم تأكيد الطلب ${order.id}.` : `تم رفض الطلب ${order.id} وإتاحة الدردشة للعميل.`);
      setRejectTarget(null);
      setRejectReason("");
      setActiveOrderId(order.id);
      setActiveSection(status === "Rejected" ? "chats" : activeSection);
      await refresh();
      if (status === "Rejected") await loadMessages(order.id);
    } catch (cause) {
      showError(cause);
    } finally {
      setBusyOrderId("");
    }
  }

  async function submitReject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (rejectTarget) await updateOrder(rejectTarget, "Rejected", rejectReason);
  }

  async function updateStock(product: InventoryProduct, stock: number) {
    setError("");
    setSuccess("");
    try {
      await api(`/api/staff/inventory/${product.id}`, {
        method: "PATCH",
        body: JSON.stringify({ stock }),
      });
      setSuccess(`تم تحديث مخزون ${product.name}.`);
      await refresh();
    } catch (cause) {
      showError(cause);
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeOrderId || !messageText.trim()) return;
    try {
      await api(`/api/orders/${encodeURIComponent(activeOrderId)}/messages`, {
        method: "POST",
        body: JSON.stringify({ text: messageText }),
      });
      setMessageText("");
      await loadMessages(activeOrderId);
    } catch (cause) {
      showError(cause);
    }
  }

  if (loading) return <div className="loading-screen"><span className="loader" />جارٍ التحقق من الجلسة…</div>;

  if (!staff) {
    return (
      <main className="login-screen">
        <section className="login-card">
          <div className="brand-mark"><ShoppingBag size={24} /><span>COPRA <small>STAFF</small></span></div>
          <div className="login-intro"><span className="eyebrow">مساحة الفريق</span><h1>إدارة المتجر<br />تبدأ من هنا.</h1><p>سجّل الدخول لمراجعة الطلبات ومتابعة العملاء والمخزون.</p></div>
          <form onSubmit={signIn} className="login-form">
            <label htmlFor="staff-password">كلمة مرور الستاف</label>
            <input id="staff-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            {loginError && <p className="error-text" role="alert">{loginError}</p>}
            <button className="primary-button" type="submit">دخول لوحة الستاف <ChevronLeft size={18} /></button>
          </form>
          <a className="back-to-store" href="/">العودة إلى متجر Copra</a>
        </section>
      </main>
    );
  }

  return (
    <div className="staff-app">
      <aside className="sidebar">
        <a className="brand-mark" href="/staff"><ShoppingBag size={24} /><span>COPRA <small>STAFF</small></span></a>
        <div className="sidebar-label">مساحة العمل</div>
        <nav className="side-nav" aria-label="التنقل">
          <button className={activeSection === "orders" ? "active" : ""} onClick={() => setActiveSection("orders")}><ShoppingBag size={19} />الطلبات <span>{pendingOrders.length}</span></button>
          <button className={activeSection === "inventory" ? "active" : ""} onClick={() => setActiveSection("inventory")}><Boxes size={19} />المخزون</button>
          <button className={activeSection === "chats" ? "active" : ""} onClick={() => setActiveSection("chats")}><MessageCircle size={19} />دردشات العملاء</button>
        </nav>
        <div className="sidebar-bottom">
          <div className="staff-profile"><div className="avatar">C</div><div><strong>{staff.name}</strong><span>فريق Copra</span></div></div>
          <button className="logout-button" onClick={signOut}><LogOut size={18} />تسجيل الخروج</button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <div><span className="eyebrow">لوحة المتابعة</span><h1>{activeSection === "orders" ? "الطلبات الجديدة" : activeSection === "inventory" ? "إدارة المخزون" : "دردشات العملاء"}</h1></div>
          <div className="topbar-actions"><span className="live-pill"><i /> اتصال مباشر</span><button className="icon-button" onClick={() => setSoundEnabled(!soundEnabled)} title={soundEnabled ? "كتم الصوت" : "تفعيل الصوت"}><Volume2 size={19} className={soundEnabled ? "" : "muted"} /></button><button className="icon-button" onClick={() => void refresh().catch(showError)} title="تحديث"><RefreshCw size={18} /></button></div>
        </header>

        {error && <div className="alert alert-error" role="alert"><AlertTriangle size={18} />{error}<button onClick={() => setError("")} aria-label="إغلاق"><X size={16} /></button></div>}
        {success && <div className="alert alert-success" role="status"><Check size={18} />{success}<button onClick={() => setSuccess("")} aria-label="إغلاق"><X size={16} /></button></div>}

        <section className="stats-grid">
          <article className="stat-card"><div className="stat-icon orange"><ShoppingBag size={19} /></div><span>طلبات قيد المراجعة</span><strong>{pendingOrders.length}</strong><small>تحتاج إلى إجراء من الفريق</small></article>
          <article className="stat-card"><div className="stat-icon green"><PackageCheck size={19} /></div><span>طلبات مؤكدة</span><strong>{orders.filter((order) => order.status === "Approved").length}</strong><small>تم قبولها وتجهيزها</small></article>
          <article className="stat-card"><div className="stat-icon blue"><Boxes size={19} /></div><span>منتجات المخزون</span><strong>{inventory.length}</strong><small>{inventory.filter((product) => product.stock === 0).length} منتجات غير متوفرة</small></article>
          <article className="stat-card"><div className="stat-icon violet"><MessageCircle size={19} /></div><span>طلبات مرفوضة</span><strong>{orders.filter((order) => order.status === "Rejected").length}</strong><small>يمكن متابعة أصحابها بالدردشة</small></article>
        </section>

        {activeSection === "inventory" ? (
          <section className="panel">
            <div className="panel-heading"><div><h2>المنتجات والكميات</h2><p>تحديث المخزون ينعكس مباشرة على إمكانية الموافقة على الطلب.</p></div><span className="subtle-count">{inventory.length} منتج</span></div>
            <div className="inventory-list">
              {inventory.map((product) => <InventoryRow key={product.id} product={product} onSave={updateStock} />)}
            </div>
          </section>
        ) : activeSection === "chats" ? (
          <section className="chat-layout panel">
            <aside className="chat-order-list">
              <h2>اختر طلباً للمحادثة</h2>
              {orders.map((order) => (
                <button key={order.id} className={order.id === activeOrderId ? "chat-order active" : "chat-order"} onClick={() => setActiveOrderId(order.id)}>
                  <span className="avatar">{order.customer_name.slice(0, 1)}</span><span><strong>{order.customer_name}</strong><small>{order.id}</small></span><ChevronLeft size={16} />
                </button>
              ))}
              {!orders.length && <p className="empty-state">لا توجد طلبات لبدء محادثة مرتبطة بها.</p>}
            </aside>
            <div className="chat-workspace">
              {activeOrder ? <>
                <div className="chat-title"><div><strong>{activeOrder.customer_name}</strong><span>طلب {activeOrder.id}</span></div><a href={`tel:${activeOrder.phone}`} className="phone-link">{activeOrder.phone || "لا يوجد هاتف"}</a></div>
                <div className="messages-list">
                  {messages.map((message) => <div key={message.id} className={message.sender_id === "staff-admin" ? "message-row mine" : "message-row"}><p>{message.text}</p><time>{formatDate(message.created_at)}</time></div>)}
                  {!messages.length && <p className="empty-state">ابدأ المحادثة بإرسال رسالة للعميل.</p>}
                </div>
                <form className="message-compose" onSubmit={sendMessage}><input value={messageText} onChange={(event) => setMessageText(event.target.value)} maxLength={2000} placeholder="اكتب رسالة للعميل…" required /><button type="submit" aria-label="إرسال"><Send size={18} /></button></form>
              </> : <div className="empty-state centered">اختر محادثة من القائمة للبدء.</div>}
            </div>
          </section>
        ) : (
          <section className="panel">
            <div className="panel-heading orders-heading"><div><h2>طلبات العملاء</h2><p>تظهر الطلبات الجديدة هنا مباشرة دون تحديث الصفحة.</p></div><label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="ابحث برقم الطلب أو العميل" /></label></div>
            <div className="orders-list">
              {filteredOrders.map((order) => <OrderCard key={order.id} order={order} busy={busyOrderId === order.id} onApprove={() => void updateOrder(order, "Approved")} onReject={() => { setRejectTarget(order); setRejectReason(""); }} onChat={() => { setActiveOrderId(order.id); setActiveSection("chats"); }} />)}
              {!filteredOrders.length && <div className="empty-state centered"><div className="empty-icon"><CheckCheck size={24} /></div><strong>{activeSection === "orders" && !search ? "لا توجد طلبات جديدة" : "لا توجد نتائج مطابقة"}</strong><p>سيظهر أي طلب جديد تلقائياً هنا.</p></div>}
            </div>
          </section>
        )}
        <footer className="dashboard-footer"><span>Copra Staff · تحديثات لحظية</span><span><Clock3 size={14} /> {new Intl.DateTimeFormat("ar-EG", { dateStyle: "full" }).format(new Date())}</span></footer>
      </main>

      {rejectTarget && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setRejectTarget(null); }}><section className="reject-modal" role="dialog" aria-modal="true" aria-labelledby="reject-title"><button className="modal-close" onClick={() => setRejectTarget(null)} aria-label="إغلاق"><X size={19} /></button><div className="modal-icon"><AlertTriangle size={23} /></div><h2 id="reject-title">رفض الطلب</h2><p>أدخل سبباً واضحاً ليظهر للعميل في صفحة التتبع، ثم انتقل مباشرة إلى الدردشة.</p><form onSubmit={submitReject}><label htmlFor="reject-reason">سبب الرفض</label><textarea id="reject-reason" value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} maxLength={1000} rows={4} required placeholder="مثال: المنتج غير متوفر حالياً في المخزن" /><div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setRejectTarget(null)}>إلغاء</button><button type="submit" className="danger-button" disabled={busyOrderId === rejectTarget.id}>رفض وفتح الدردشة</button></div></form></section></div>}
      <button className="mobile-logout" onClick={signOut}><LogOut size={18} />خروج</button>
    </div>
  );
}

function OrderCard({ order, busy, onApprove, onReject, onChat }: {
  order: Order;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
  onChat: () => void;
}) {
  return (
    <article className="order-card">
      <header className="order-card-header"><div><span className="order-number">{order.id}</span><span className={`status-badge ${order.status.toLowerCase()}`}>{order.status === "Pending" ? "قيد المراجعة" : order.status === "Approved" ? "تم التأكيد" : "مرفوض"}</span></div><time><Clock3 size={15} />{formatDate(order.created_at)}</time></header>
      <div className="order-customer"><div className="avatar">{order.customer_name.slice(0, 1)}</div><div><strong>{order.customer_name}</strong><a href={`tel:${order.phone}`}>{order.phone || "لا يوجد هاتف"}</a></div><span className="customer-address">{order.address}</span></div>
      <div className="order-items">{order.items.map((item) => <div key={item.id} className="order-item"><span><strong>{item.name}</strong><small>الكمية: {item.quantity} × {item.price} ج.م</small></span><b>{item.subtotal} ج.م</b></div>)}</div>
      <footer className="order-card-footer"><div><span>التوصيل: {order.delivery_method}</span><strong>الإجمالي <b>{order.total} ج.م</b></strong></div><div className="order-actions">{order.status === "Pending" ? <><button className="secondary-button" onClick={onReject} disabled={busy}><X size={16} />رفض</button><button className="primary-button" onClick={onApprove} disabled={busy || !order.can_approve} title={!order.can_approve ? "المخزون غير كافٍ لقبول الطلب" : ""}><Check size={16} />{busy ? "جارٍ الحفظ…" : !order.can_approve ? "المخزون غير كافٍ" : "موافقة"}</button></> : order.status === "Rejected" ? <button className="secondary-button" onClick={onChat}><MessageCircle size={16} />مراسلة العميل</button> : <span className="approved-label"><CheckCheck size={16} /> تم تأكيد الطلب</span>}</div></footer>
    </article>
  );
}

function InventoryRow({ product, onSave }: { product: InventoryProduct; onSave: (product: InventoryProduct, stock: number) => Promise<void> }) {
  const [stock, setStock] = useState(String(product.stock));
  const [saving, setSaving] = useState(false);
  useEffect(() => setStock(String(product.stock)), [product.stock]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextStock = Number(stock);
    if (!Number.isInteger(nextStock) || nextStock < 0) return;
    setSaving(true);
    try {
      await onSave(product, nextStock);
    } finally {
      setSaving(false);
    }
  }
  return <form className="inventory-row" onSubmit={submit}><div className="inventory-product"><div className="inventory-icon"><Boxes size={18} /></div><div><strong>{product.name}</strong><small>{product.price.toLocaleString("ar-EG")} ج.م</small></div></div><span className={product.stock === 0 ? "stock-count out" : product.stock < 4 ? "stock-count low" : "stock-count"}>{product.stock === 0 ? "نفد" : product.stock < 4 ? `مخزون منخفض · ${product.stock}` : `${product.stock} متاح`}</span><div className="inventory-edit"><label className="visually-hidden" htmlFor={`stock-${product.id}`}>كمية {product.name}</label><input id={`stock-${product.id}`} type="number" min="0" max="1000000" value={stock} onChange={(event) => setStock(event.target.value)} /><button className="secondary-button" type="submit" disabled={saving}>{saving ? "حفظ…" : "حفظ الكمية"}</button></div></form>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
