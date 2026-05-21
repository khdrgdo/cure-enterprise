"""
╔══════════════════════════════════════════════════════════════════╗
║        CURE ENTERPRISE ERP  –  نظام إدارة الصيدليات            ║
║                   Professional Edition  v4.0                     ║
╚══════════════════════════════════════════════════════════════════╝
pip install customtkinter tkcalendar pillow
دخول: admin / admin123
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3, hashlib, os, shutil, sys
from datetime import datetime, timedelta

_BASE = os.path.dirname(os.path.abspath(__file__))

try:
    from tkcalendar import DateEntry
    HAS_CAL = True
except ImportError:
    HAS_CAL = False

# ═══════════════════════════════════════════
#  DESIGN TOKENS  —  4 ready themes
# ═══════════════════════════════════════════
THEMES = {
    "dawn":{
        "bg":"#0d1117","surface":"#161b22","card":"#1c2128","border":"#30363d",
        "accent":"#2563eb","acc_h":"#1d4ed8","success":"#10b981","warning":"#f59e0b",
        "danger":"#ef4444","purple":"#8b5cf6","teal":"#14b8a6","txt":"#f0f6fc",
        "txt_s":"#8b949e","txt_m":"#484f58","inp":"#0d1117","inp_b":"#30363d","hover":"#21262d",
    },
    "bloom":{
        "bg":"#f8fafc","surface":"#ffffff","card":"#f1f5f9","border":"#e2e8f0",
        "accent":"#2563eb","acc_h":"#1d4ed8","success":"#10b981","warning":"#f59e0b",
        "danger":"#ef4444","purple":"#8b5cf6","teal":"#14b8a6","txt":"#0f172a",
        "txt_s":"#64748b","txt_m":"#cbd5e1","inp":"#ffffff","inp_b":"#cbd5e1","hover":"#e2e8f0",
    },
    "emerald":{
        "bg":"#0d1117","surface":"#0f1a14","card":"#14281d","border":"#1f3d2c",
        "accent":"#10b981","acc_h":"#059669","success":"#34d399","warning":"#fbbf24",
        "danger":"#f87171","purple":"#a78bfa","teal":"#2dd4bf","txt":"#ecfdf5",
        "txt_s":"#6ee7b7","txt_m":"#28523c","inp":"#0d1117","inp_b":"#1f3d2c","hover":"#1a3022",
    },
    "royal":{
        "bg":"#0d1117","surface":"#1c1228","card":"#2a1a3d","border":"#3e2555",
        "accent":"#8b5cf6","acc_h":"#7c3aed","success":"#10b981","warning":"#f59e0b",
        "danger":"#ef4444","purple":"#a78bfa","teal":"#2dd4bf","txt":"#f0f6fc",
        "txt_s":"#c4b5fd","txt_m":"#4a3670","inp":"#0d1117","inp_b":"#3e2555","hover":"#2f1f42",
    },
    "sandy":{
        "bg":"#1a1410","surface":"#2a2218","card":"#32281c","border":"#4a3d2a",
        "accent":"#d97706","acc_h":"#b45309","success":"#10b981","warning":"#f59e0b",
        "danger":"#ef4444","purple":"#a78bfa","teal":"#2dd4bf","txt":"#fef3c7",
        "txt_s":"#d4a373","txt_m":"#5c4b37","inp":"#1a1410","inp_b":"#4a3d2a","hover":"#3a3020",
    },
    "neon":{
        "bg":"#0a0a1a","surface":"#12122a","card":"#1a1a3a","border":"#2a2a5a",
        "accent":"#06b6d4","acc_h":"#0891b2","success":"#22c55e","warning":"#eab308",
        "danger":"#ef4444","purple":"#c084fc","teal":"#2dd4bf","txt":"#f0f6fc",
        "txt_s":"#67e8f9","txt_m":"#3b3b7a","inp":"#0a0a1a","inp_b":"#2a2a5a","hover":"#1e1e4a",
    },
    "classic":{
        "bg":"#0f172a","surface":"#1e293b","card":"#334155","border":"#475569",
        "accent":"#3b82f6","acc_h":"#2563eb","success":"#10b981","warning":"#f59e0b",
        "danger":"#ef4444","purple":"#8b5cf6","teal":"#14b8a6","txt":"#f8fafc",
        "txt_s":"#94a3b8","txt_m":"#475569","inp":"#0f172a","inp_b":"#475569","hover":"#1e293b",
    },
}
C = dict(THEMES["dawn"])
FONT  = "Cairo"
FONT_SCALE = 1.0
def _fs(size):
    return max(8, int(size * FONT_SCALE))
VER   = "4.0"
ROLES = {"admin": "مدير النظام", "pharmacist": "صيدلاني", "cashier": "كاشير"}

# صلاحيات كل دور
PERMS = {
    "admin":      {"pos","inventory","ledger","reports","users","settings","delete","edit_price","credit","returns","expenses"},
    "pharmacist": {"pos","inventory","ledger","reports","credit","expenses"},
    "cashier":    {"pos"},
}

def can(user, perm):
    role_perms = PERMS.get(user.get("role","cashier"), set())
    custom = user.get("custom_perms","") or ""
    if custom:
        custom_set = set(c.strip() for c in custom.split(",") if c.strip())
        if perm in custom_set: return True
        if f"!{perm}" in custom_set: return False
    return perm in role_perms

def data_dir():
    d=os.path.join(_BASE,"data")
    if not getattr(sys,"frozen",False):
        return d
    return os.path.join(os.environ.get("APPDATA",os.path.expanduser("~")),"Cure Enterprise","data")

def app_dir():
    if not getattr(sys,"frozen",False):
        return _BASE
    return os.path.join(os.environ.get("APPDATA",os.path.expanduser("~")),"Cure Enterprise")

# ═══════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════
class DB:
    def __init__(self):
        db_dir=data_dir(); os.makedirs(db_dir,exist_ok=True)
        self.con = sqlite3.connect(
            os.path.join(db_dir,"cure_v4.db"), check_same_thread=False, isolation_level=None
        )
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.execute("PRAGMA journal_mode  = WAL")
        self._schema(); self._seed()

    def _schema(self):
        self.con.executescript("""
        BEGIN;
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, full_name TEXT NOT NULL,
            password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'cashier',
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL, color TEXT DEFAULT '#2563eb'
        );
        CREATE TABLE IF NOT EXISTS medicines(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE, name TEXT NOT NULL,
            category_id INTEGER, generic_name TEXT, manufacturer TEXT,
            buy_price REAL DEFAULT 0, sell_price REAL NOT NULL,
            stock INTEGER DEFAULT 0, min_stock INTEGER DEFAULT 5,
            unit TEXT DEFAULT 'قطعة', expiry DATE,
            location TEXT, notes TEXT, is_active INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            subtotal REAL NOT NULL, discount REAL DEFAULT 0, total REAL NOT NULL,
            pay_method TEXT DEFAULT 'كاش', amount_paid REAL DEFAULT 0,
            change_amount REAL DEFAULT 0, ref_no TEXT, customer_name TEXT,
            user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS sale_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL, medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL, unit_price REAL NOT NULL,
            buy_price REAL DEFAULT 0, total REAL NOT NULL,
            FOREIGN KEY(sale_id) REFERENCES sales(id),
            FOREIGN KEY(medicine_id) REFERENCES medicines(id)
        );
        CREATE TABLE IF NOT EXISTS ledger(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL,
            description TEXT, ref_id INTEGER, user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, val TEXT);
        CREATE TABLE IF NOT EXISTS activity_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, action TEXT, detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS credit_payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            user_id INTEGER,
            FOREIGN KEY(sale_id) REFERENCES sales(id)
        );
        CREATE TABLE IF NOT EXISTS batches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            quantity_strips INTEGER DEFAULT 0,
            buy_price REAL DEFAULT 0,
            expiry DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(medicine_id) REFERENCES medicines(id)
        );
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            expense_date DATE NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        COMMIT;
        """)
        # Migrations v4.1 – إضافة أعمدة جديدة
        for col,typ in [("strip_price","REAL DEFAULT 0"),("sell_by_strip","INTEGER DEFAULT 0"),("strips_per_box","INTEGER DEFAULT 1")]:
            try: self.con.execute(f"ALTER TABLE medicines ADD COLUMN {col} {typ}")
            except: pass
        for col,typ in [("credit_status","TEXT DEFAULT NULL"),("approved_by","INTEGER DEFAULT NULL"),("approved_at","TIMESTAMP DEFAULT NULL")]:
            try: self.con.execute(f"ALTER TABLE sales ADD COLUMN {col} {typ}")
            except: pass
        try: self.con.execute("ALTER TABLE medicines ADD COLUMN image_path TEXT DEFAULT NULL")
        except: pass
        try: self.con.execute("ALTER TABLE sale_items ADD COLUMN strip_qty INTEGER DEFAULT 0")
        except: pass
        try: self.con.execute("ALTER TABLE sale_items ADD COLUMN returned_qty INTEGER DEFAULT 0")
        except: pass
        try: self.con.execute("ALTER TABLE users ADD COLUMN custom_perms TEXT DEFAULT ''")
        except: pass
        try: self.con.execute("ALTER TABLE medicines ADD COLUMN stock_migrated INTEGER DEFAULT 0")
        except: pass
        # تعبئة strips_per_box للمنتجات القديمة التي تبيع بالشريط
        try: self.con.execute("UPDATE medicines SET strips_per_box=COALESCE(NULLIF(strips_per_box,0),1) WHERE sell_by_strip=1")
        except: pass
        # ONE-TIME: تحويل المخزون القديم (مخزون = علب) إلى (مخزون = شرائط × strips_per_box)
        self.con.execute("UPDATE medicines SET stock=stock*strips_per_box, stock_migrated=1 WHERE sell_by_strip=1 AND strips_per_box>1 AND stock_migrated=0")
        # ONE-TIME: تصحيح buy_price التاريخي في sale_items (البيع بالشريط كان buy_price لعلبة كاملة)
        try:
            self.con.execute("""
                UPDATE sale_items SET buy_price = buy_price / (
                    SELECT COALESCE(NULLIF(m.strips_per_box,0),1) FROM medicines m WHERE m.id = sale_items.medicine_id
                )
                WHERE strip_qty = 0
                AND EXISTS (
                    SELECT 1 FROM medicines m WHERE m.id = sale_items.medicine_id
                    AND m.sell_by_strip = 1 AND m.strips_per_box > 1
                )
            """)
        except: pass
        # v4.3: تحسين الأداء — فهارس للبحث السريع
        for idx in ["idx_med_active_stock","idx_med_barcode","idx_med_name","idx_med_category"]:
            try: self.con.execute(f"DROP INDEX IF EXISTS {idx}")
            except: pass
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_med_active_stock ON medicines(is_active,stock)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_med_barcode ON medicines(barcode)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_med_name ON medicines(name)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_med_category ON medicines(category_id)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(created_at)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id)")
        # v4.2: Multiple pricing + purchases
        for col,typ in [("price_wholesale","REAL DEFAULT 0"),("price_distributor","REAL DEFAULT 0")]:
            try: self.con.execute(f"ALTER TABLE medicines ADD COLUMN {col} {typ}")
            except: pass
        self.con.executescript("""
        CREATE TABLE IF NOT EXISTS purchases(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL, supplier TEXT DEFAULT '',
            total REAL NOT NULL, discount REAL DEFAULT 0,
            notes TEXT, user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS purchase_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL, medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL, unit_price REAL NOT NULL,
            total REAL NOT NULL, expiry DATE,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id),
            FOREIGN KEY(medicine_id) REFERENCES medicines(id)
        );
        """)

    def _seed(self):
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        self.con.execute(
            "INSERT OR IGNORE INTO users(username,full_name,password,role) VALUES(?,?,?,?)",
            ("admin","المدير العام",pw,"admin"))
        # default cashier for demo
        pw2 = hashlib.sha256("1234".encode()).hexdigest()
        self.con.execute(
            "INSERT OR IGNORE INTO users(username,full_name,password,role) VALUES(?,?,?,?)",
            ("cashier","كاشير الصيدلية",pw2,"cashier"))
        for cat,col in [
            ("مضادات حيوية","#ef4444"),("مسكنات","#f59e0b"),("أدوية قلب","#ec4899"),
            ("فيتامينات","#10b981"),("أدوية ضغط","#8b5cf6"),("أدوية سكر","#2563eb"),
            ("مستلزمات طبية","#14b8a6"),("أخرى","#6b7280"),
        ]:
            self.con.execute("INSERT OR IGNORE INTO categories(name,color) VALUES(?,?)",(cat,col))
        for k,v in {
            "pharmacy_name":"صيدلية كيور","pharmacy_address":"العنوان",
            "pharmacy_phone":"0000000000","currency":"SDG","tax_rate":"0",
            "logo_login":"","logo_invoice":"",
        }.items():
            self.con.execute("INSERT OR IGNORE INTO settings(key,val) VALUES(?,?)",(k,v))

    def q(self,sql,p=()):
        return [dict(r) for r in self.con.execute(sql,p).fetchall()]
    def q1(self,sql,p=()):
        r=self.con.execute(sql,p).fetchone(); return dict(r) if r else None
    def run(self,sql,p=()):
        return self.con.execute(sql,p).lastrowid
    def setting(self,k,d=""):
        r=self.q1("SELECT val FROM settings WHERE key=?",(k,)); return r["val"] if r else d
    def set_setting(self,k,v):
        self.run("INSERT OR REPLACE INTO settings(key,val) VALUES(?,?)",(k,v))
    def log(self,uid,action,detail=""):
        self.run("INSERT INTO activity_log(user_id,action,detail) VALUES(?,?,?)",(uid,action,detail))


# ═══════════════════════════════════════════
#  TOAST
# ═══════════════════════════════════════════
class Toast:
    _q=[]
    @classmethod
    def show(cls,root,msg,kind="success",ms=3000):
        pal={"success":("#10b981","✓"),"error":("#ef4444","✗"),
             "warning":("#f59e0b","⚠"),"info":("#2563eb","ℹ")}
        bg,ic=pal.get(kind,pal["info"])
        t=ctk.CTkToplevel(root)
        t.wm_overrideredirect(True); t.attributes("-topmost",True); t.attributes("-alpha",0.0)
        fr=ctk.CTkFrame(t,fg_color=bg,corner_radius=10); fr.pack(padx=2,pady=2)
        ctk.CTkLabel(fr,text=f"  {ic}  {msg}  ",font=(FONT,_fs(12),"bold"),text_color="white").pack(padx=16,pady=10)
        t.update_idletasks()
        sw=t.winfo_screenwidth(); sh=t.winfo_screenheight()
        w=t.winfo_width(); h=t.winfo_height()
        t.geometry(f"+{sw-w-24}+{sh-h-52-len(cls._q)*64}"); cls._q.append(t)
        def fade(a=0.0,inn=True):
            if inn:
                if a<1.0: t.attributes("-alpha",a); t.after(18,lambda:fade(a+.15))
            else:
                if a>0: t.attributes("-alpha",a); t.after(18,lambda:fade(a-.15,False))
                else:
                    if t in cls._q: cls._q.remove(t)
                    try: t.destroy()
                    except: pass
        fade(); t.after(ms,lambda:fade(1.0,False))


# ═══════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db=DB(); self.user=None
        global FONT_SCALE, C
        try: FONT_SCALE=float(self.db.setting("font_scale","1.0"))
        except: FONT_SCALE=1.0
        tn=self.db.setting("theme","dawn")
        if tn in THEMES: C.update(THEMES[tn])
        self.title("Cure Enterprise — تسجيل الدخول")
        self.geometry("980x600"); self.resizable(False,False)
        self.configure(fg_color=C["bg"]); self._ui(); self._center()
        self.protocol("WM_DELETE_WINDOW",self._on_close)

    def _on_close(self):
        if messagebox.askyesno("تأكيد الخروج","هل تريد إغلاق البرنامج؟"):
            self.db.log(0,"EXIT","إغلاق البرنامج من شاشة الدخول")
            self.destroy()
            try: self.master.quit()
            except: pass

    def _center(self):
        self.update_idletasks()
        w,h=self.winfo_width(),self.winfo_height()
        self.geometry(f"+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

    def _ui(self):
        self.grid_columnconfigure(0,weight=3); self.grid_columnconfigure(1,weight=2)
        self.grid_rowconfigure(0,weight=1)
        # Brand
        brand=ctk.CTkFrame(self,fg_color=C["accent"],corner_radius=0)
        brand.grid(row=0,column=0,sticky="nsew")
        mid=ctk.CTkFrame(brand,fg_color="transparent")
        mid.place(relx=0.5,rely=0.5,anchor="center")
        # Logo or default
        logo_path=self.db.setting("logo_login","")
        if logo_path and os.path.exists(logo_path):
            try:
                from PIL import Image
                img=ctk.CTkImage(Image.open(logo_path),size=(80,80))
                ctk.CTkLabel(mid,text="",image=img).pack()
            except:
                ctk.CTkLabel(mid,text="💊",font=("Arial",72)).pack()
        else:
            ctk.CTkLabel(mid,text="💊",font=("Arial",72)).pack()
        ctk.CTkLabel(mid,text="CURE",font=(FONT,_fs(52),"bold"),text_color="white").pack()
        ctk.CTkLabel(mid,text="ENTERPRISE",font=(FONT,_fs(17)),text_color="#bfdbfe").pack()
        ctk.CTkLabel(mid,text="نظام إدارة الصيدليات المتكامل",font=(FONT,_fs(13)),text_color="#dbeafe").pack(pady=(4,28))
        for f in ["✓  نقطة بيع سهلة وسريعة","✓  إدارة مخزن ذكية مع تنبيهات","✓  تقارير مالية وفواتير احترافية"]:
            ctk.CTkLabel(mid,text=f,font=(FONT,_fs(12)),text_color="#dbeafe").pack(anchor="w")
        ctk.CTkLabel(mid,text=f"v{VER}",font=(FONT,_fs(11)),text_color="#93c5fd").pack(pady=(18,0))
        # Form
        panel=ctk.CTkFrame(self,fg_color=C["surface"],corner_radius=0)
        panel.grid(row=0,column=1,sticky="nsew")
        frm=ctk.CTkFrame(panel,fg_color="transparent")
        frm.place(relx=0.5,rely=0.5,anchor="center")
        ctk.CTkLabel(frm,text="مرحباً بك 👋",font=(FONT,_fs(24),"bold"),text_color=C["txt"]).pack(anchor="e")
        ctk.CTkLabel(frm,text="سجّل دخولك للمتابعة",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(anchor="e",pady=(2,22))
        def ent(ph,show=""):
            e=ctk.CTkEntry(frm,placeholder_text=ph,width=300,height=46,justify="right",
                           font=(FONT,_fs(13)),show=show,fg_color=C["inp"],border_color=C["inp_b"],text_color=C["txt"])
            e.pack(pady=(0,12)); return e
        ctk.CTkLabel(frm,text="اسم المستخدم",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self.u=ent("أدخل اسم المستخدم"); self.u.insert(0,"admin")
        ctk.CTkLabel(frm,text="كلمة المرور",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self.p=ent("أدخل كلمة المرور","●")
        ctk.CTkLabel(frm,text="admin/admin123  أو  cashier/1234",font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(pady=(0,4))
        self.err=ctk.CTkLabel(frm,text="",font=(FONT,_fs(11)),text_color=C["danger"]); self.err.pack(pady=(0,8))
        self.btn=ctk.CTkButton(frm,text="تسجيل الدخول  →",width=300,height=48,
            font=(FONT,_fs(14),"bold"),fg_color=C["accent"],hover_color=C["acc_h"],corner_radius=10,command=self._login)
        self.btn.pack()
        self.p.bind("<Return>",lambda _:self._login()); self.u.bind("<Return>",lambda _:self.p.focus())

    def _login(self):
        uname=self.u.get().strip(); pw=self.p.get()
        if not uname or not pw: self.err.configure(text="⚠  أدخل اسم المستخدم وكلمة المرور"); return
        h=hashlib.sha256(pw.encode()).hexdigest()
        user=self.db.q1("SELECT * FROM users WHERE username=? AND password=? AND is_active=1",(uname,h))
        if user:
            self.db.run("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?",(user["id"],))
            self.db.log(user["id"],"LOGIN",uname); self.user=user
            self.btn.configure(text="✓ جاري التحميل...",state="disabled",fg_color=C["success"])
            self.after(700,self._launch)
        else:
            self.err.configure(text="✗  اسم المستخدم أو كلمة المرور غير صحيحة")
            self.p.delete(0,"end"); self.btn.configure(fg_color=C["danger"])
            self.after(900,lambda:self.btn.configure(fg_color=C["accent"]))

    def _launch(self):
        self.withdraw()
        CureERP(self.db,self.user).mainloop()
        self.deiconify()
        self.btn.configure(text="تسجيل الدخول  →",state="normal",fg_color=C["accent"])
        self.u.delete(0,"end"); self.p.delete(0,"end"); self.err.configure(text="")
        self.u.focus()


# ═══════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════
class CureERP(ctk.CTk):
    def __init__(self,db,user):
        super().__init__()
        self.db=db; self.user=user
        global FONT_SCALE, C
        try: FONT_SCALE=float(self.db.setting("font_scale","1.0"))
        except: FONT_SCALE=1.0
        tn=self.db.setting("theme","dawn")
        if tn in THEMES: C.update(THEMES[tn])
        self._bus={}  # event bus: {event_name: [callbacks]}
        nm=self.db.setting("pharmacy_name","صيدلية كيور")
        self.title(f"Cure Enterprise v{VER}  —  {nm}")
        self.state("zoomed")  # fullscreen on Windows
        self.configure(fg_color=C["bg"])
        self._styles(); self._layout()
        self.navigate("dashboard"); self._tick()
        self.protocol("WM_DELETE_WINDOW",self._quit)
        self.after(1000,self._auto_backup)

    def _on(self,event,callback):
        self._bus.setdefault(event,[]).append(callback)

    def _emit(self,event,*a,**kw):
        for cb in self._bus.get(event,[]): cb(*a,**kw)

    # ── Styles ──────────────────────────────
    def _styles(self):
        s=ttk.Style(); s.theme_use("default")
        s.configure("P.Treeview",background=C["card"],foreground=C["txt"],
            fieldbackground=C["card"],rowheight=40,font=(FONT,_fs(12)),borderwidth=0,relief="flat")
        s.configure("P.Treeview.Heading",background=C["surface"],foreground=C["txt_s"],
            font=(FONT,_fs(12),"bold"),relief="flat",borderwidth=0)
        s.map("P.Treeview",background=[("selected",C["accent"])],foreground=[("selected","white")])
        s.layout("P.Treeview",[("P.Treeview.treearea",{"sticky":"nswe"})])

    # ── Layout ──────────────────────────────
    def _layout(self):
        self.sidebar=ctk.CTkFrame(self,width=260,corner_radius=0,
            fg_color=C["bg"],border_width=1,border_color=C["border"])
        self.sidebar.pack(side="right",fill="y"); self.sidebar.pack_propagate(False)
        self.area=ctk.CTkFrame(self,corner_radius=0,fg_color=C["bg"])
        self.area.pack(side="left",fill="both",expand=True)
        self._sidebar(); self._topbar()
        self.cont=ctk.CTkFrame(self.area,corner_radius=0,fg_color=C["bg"])
        self.cont.pack(fill="both",expand=True,padx=20,pady=(0,14))

    def _sidebar(self):
        logo=ctk.CTkFrame(self.sidebar,height=60,corner_radius=0,fg_color=C["surface"])
        logo.pack(fill="x"); logo.pack_propagate(False)
        ctk.CTkLabel(logo,text="💊  CURE",font=(FONT,_fs(18),"bold"),text_color=C["accent"]
                     ).place(relx=0.5,rely=0.5,anchor="center")
        # User card (compact)
        uc=ctk.CTkFrame(self.sidebar,fg_color=C["card"],corner_radius=8,
            border_width=1,border_color=C["border"]); uc.pack(fill="x",padx=10,pady=(8,4))
        rc={"admin":C["accent"],"pharmacist":C["purple"],"cashier":C["success"]}
        ctk.CTkLabel(uc,text=self.user["full_name"],font=(FONT,_fs(12),"bold"),text_color=C["txt"]
                     ).pack(pady=(6,0),padx=8,anchor="e")
        ctk.CTkLabel(uc,text=f"● {ROLES.get(self.user['role'],self.user['role'])}",
            font=(FONT,_fs(10)),text_color=rc.get(self.user["role"],C["txt_s"])
            ).pack(pady=(0,4),padx=8,anchor="e")
        # Scrollable nav area
        nav_scroll=ctk.CTkScrollableFrame(self.sidebar,fg_color="transparent",
            scrollbar_button_color=C["txt_m"],scrollbar_button_hover_color=C["txt_s"])
        nav_scroll.pack(fill="both",expand=True,padx=4,pady=(2,0))
        self._nav={}
        items=[("dashboard","🏠","الرئيسية"),
               ("pos","🛒","البيع")]
        if can(self.user,"expenses") or self.user["role"]=="admin":
            items.append(("expenses","💸","المصروفات"))
        if can(self.user,"credit"):
            items.append(("credit","📋","الآجل"))
        if can(self.user,"inventory"):
            items.append(("inventory","📦","المخزن"))
        if can(self.user,"reports"):
            items.append(("reports","📊","التقارير"))
        if can(self.user,"users"):
            items.append(("users","👥","المستخدمون"))
        if can(self.user,"returns"):
            items.append(("returns","🔄","المرتجعات"))
        if self.user["role"]=="admin":
            items.append(("trash","🗑","المهملات"))
        items.append(("settings","⚙️","الإعدادات"))
        for key,icon,lbl in items:
            b=ctk.CTkButton(nav_scroll,text=f"{icon}  {lbl}",
                font=(FONT,_fs(12)),height=38,anchor="e",
                fg_color="transparent",text_color=C["txt_s"],
                hover_color=C["hover"],corner_radius=6,
                command=lambda k=key:self.navigate(k))
            b.pack(fill="x",padx=6,pady=1); self._nav[key]=b
        self._clk=ctk.CTkLabel(nav_scroll,text="",font=(FONT,_fs(10)),text_color=C["txt_m"])
        self._clk.pack(pady=4)

    def _topbar(self):
        self._tb=ctk.CTkFrame(self.area,height=60,corner_radius=0,
            fg_color=C["surface"],border_width=1,border_color=C["border"])
        self._tb.pack(fill="x"); self._tb.pack_propagate(False)
        self._ttl=ctk.CTkLabel(self._tb,text="",font=(FONT,_fs(19),"bold"),text_color=C["txt"])
        self._ttl.pack(side="right",padx=24,pady=16)
        self._ab=ctk.CTkButton(self._tb,text="🔔",width=42,height=36,
            fg_color=C["card"],hover_color=C["hover"],corner_radius=8,
            font=("Arial",17),text_color=C["txt"],command=self._alert_popup)
        self._ab.pack(side="left",padx=(10,4),pady=12)
        ctk.CTkButton(self._tb,text="🚪 خروج",width=64,height=32,
            fg_color=C["card"],hover_color="#2d0a0a",corner_radius=8,
            font=("Arial",12),text_color=C["danger"],command=self._quit
            ).pack(side="left",padx=(0,4),pady=12)
        self._dl=ctk.CTkLabel(self._tb,text="",font=(FONT,_fs(11)),text_color=C["txt_s"])
        self._dl.pack(side="left",padx=8)

    def _tick(self):
        now=datetime.now(); self._clk.configure(text=now.strftime("%H:%M"))
        self._dl.configure(text=now.strftime("%Y/%m/%d  %H:%M"))
        self._badge(); self.after(30000,self._tick)

    def _badge(self):
        n1=(self.db.q1("SELECT COUNT(*) c FROM medicines WHERE stock<=min_stock AND is_active=1") or {}).get("c",0)
        lim=(datetime.now()+timedelta(days=60)).strftime("%Y-%m-%d")
        n2=(self.db.q1("SELECT COUNT(*) c FROM medicines WHERE expiry<=? AND is_active=1",(lim,)) or {}).get("c",0)
        tot=(n1 or 0)+(n2 or 0)
        if tot: self._ab.configure(text=f"🔔 {tot}",fg_color=C["danger"])
        else:   self._ab.configure(text="🔔",fg_color=C["card"])

    def _alert_popup(self):
        pop=ctk.CTkToplevel(self); pop.title("التنبيهات"); pop.geometry("560x440")
        pop.configure(fg_color=C["surface"]); pop.grab_set()
        ctk.CTkLabel(pop,text="⚠  التنبيهات العاجلة",font=(FONT,_fs(17),"bold"),text_color=C["warning"]).pack(pady=14)
        tf,tree=self._tree(pop,("type","name","val"),("النوع","الدواء","القيمة"))
        tf.pack(fill="both",expand=True,padx=14,pady=(0,14))
        for r in self.db.q("SELECT name,stock FROM medicines WHERE stock<=min_stock AND is_active=1"):
            tree.insert("","end",values=("⚠ نقص مخزون",r["name"],f"{r['stock']} قطعة"))
        lim=(datetime.now()+timedelta(days=60)).strftime("%Y-%m-%d")
        for r in self.db.q("SELECT name,expiry FROM medicines WHERE expiry<=? AND is_active=1",(lim,)):
            tree.insert("","end",values=("⏰ قرب الانتهاء",r["name"],r["expiry"] or "؟"))

    # ── Navigation ──────────────────────────
    def navigate(self,key):
        titles={"dashboard":"لوحة التحكم","pos":"نقطة البيع  POS","credit":"الآجل",
                "inventory":"إدارة المخزن","reports":"التقارير","users":"إدارة المستخدمين",
                "returns":"المرتجعات","trash":"🗑 سلة المهملات","settings":"الإعدادات",
                "expenses":"💸 المصروفات"}
        for k,b in self._nav.items():
            b.configure(fg_color=C["accent"] if k==key else "transparent",
                        text_color="white" if k==key else C["txt_s"])
        self._ttl.configure(text=titles.get(key,""))
        self._clear(); getattr(self,f"_pg_{key}",lambda:None)()

    def _clear(self):
        for w in self.cont.winfo_children(): w.destroy()

    def _quit(self):
        if messagebox.askyesno("خروج","هل تريد تسجيل الخروج؟"):
            self.db.log(self.user["id"],"LOGOUT")
            self.after(100, self._do_quit)

    def _do_quit(self):
        try: self.quit()
        except: pass
        try: self.destroy()
        except: pass

    def _auto_backup(self):
        try:
            bdir=_BASE
            os.makedirs(os.path.join(bdir,"backups"),exist_ok=True)
            src=os.path.join(bdir,"data","cure_v4.db"); dst=os.path.join(bdir,"backups",f"{datetime.now():%Y-%m-%d}.db")
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src,dst)
        except: pass

    # ── Shared helpers ──────────────────────
    def _card(self,parent,title,value,sub="",color=None,icon="",r=0,c=0):
        color=color or C["accent"]
        f=ctk.CTkFrame(parent,corner_radius=14,fg_color=C["card"],border_width=1,border_color=C["border"])
        f.grid(row=r,column=c,padx=8,pady=8,sticky="nsew")
        inn=ctk.CTkFrame(f,fg_color="transparent"); inn.pack(fill="both",expand=True,padx=20,pady=16)
        top=ctk.CTkFrame(inn,fg_color="transparent"); top.pack(fill="x")
        ctk.CTkLabel(top,text=icon,font=("Arial",28)).pack(side="left")
        ctk.CTkLabel(top,text=title,font=(FONT,_fs(13)),text_color=C["txt_s"]).pack(side="right")
        ctk.CTkLabel(inn,text=str(value),font=(FONT,_fs(27),"bold"),text_color=color).pack(anchor="e",pady=4)
        if sub: ctk.CTkLabel(inn,text=sub,font=(FONT,_fs(11)),text_color=C["txt_m"]).pack(anchor="e")

    def _tree(self,parent,cols,heads,rowh=40,widths=None):
        f=ctk.CTkFrame(parent,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        tv=ttk.Treeview(f,columns=cols,show="headings",style="P.Treeview")
        for i,(col,hd) in enumerate(zip(cols,heads)):
            tv.heading(col,text=hd)
            w=widths[i] if widths and i<len(widths) else 100
            tv.column(col,anchor="center",minwidth=w,width=w)
        vsb=ttk.Scrollbar(f,orient="vertical",command=tv.yview)
        tv.configure(yscrollcommand=vsb.set); vsb.pack(side="right",fill="y")
        tv.pack(fill="both",expand=True,padx=1,pady=1)
        return f,tv

    def _ent(self,parent,ph,w=220,show=""):
        return ctk.CTkEntry(parent,placeholder_text=ph,width=w,height=42,
            justify="right",font=(FONT,_fs(13)),show=show,
            fg_color=C["inp"],border_color=C["inp_b"],text_color=C["txt"])

    def _btn(self,parent,text,cmd,color=None,w=130,h=42):
        color=color or C["accent"]
        hmap={C["accent"]:C["acc_h"],C["success"]:"#059669",C["danger"]:"#dc2626",C["warning"]:"#d97706"}
        return ctk.CTkButton(parent,text=text,command=cmd,width=w,height=h,
            font=(FONT,_fs(13),"bold"),fg_color=color,hover_color=hmap.get(color,"#334155"),corner_radius=8)

    def _combo(self,parent,values,w=220):
        return ctk.CTkComboBox(parent,values=values,width=w,height=42,font=(FONT,_fs(13)),
            fg_color=C["inp"],border_color=C["inp_b"],text_color=C["txt"],button_color=C["inp_b"])

    def _sep(self,p):
        ctk.CTkFrame(p,height=1,fg_color=C["border"]).pack(fill="x",padx=14,pady=8)

    # ═══════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════
    def _pg_dashboard(self):
        sc=ctk.CTkScrollableFrame(self.cont,fg_color="transparent"); sc.pack(fill="both",expand=True)
        cur=self.db.setting("currency","SDG")
        today=datetime.now().strftime("%Y-%m-%d")
        yday=(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")
        lim=(datetime.now()+timedelta(days=60)).strftime("%Y-%m-%d")

        ts=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales WHERE (credit_status IS NULL OR credit_status!='pending') AND date(created_at)=?",(today,)) or {}
        ys=self.db.q1("SELECT COALESCE(SUM(total),0) s FROM sales WHERE (credit_status IS NULL OR credit_status!='pending') AND date(created_at)=?",(yday,)) or {}
        ls=self.db.q1("SELECT COUNT(*) c FROM medicines WHERE stock<=min_stock AND is_active=1") or {}
        es=self.db.q1("SELECT COUNT(*) c FROM medicines WHERE expiry<=? AND is_active=1",(lim,)) or {}
        tm=self.db.q1("SELECT COUNT(*) c FROM medicines WHERE is_active=1") or {}

        t_s=ts.get("s") or 0; y_s=ys.get("s") or 0
        diff=t_s-y_s; sign="↑" if diff>=0 else "↓"
        tc=ts.get("c") or 0

        kpi=ctk.CTkFrame(sc,fg_color="transparent"); kpi.pack(fill="x")
        for i in range(4): kpi.columnconfigure(i,weight=1)
        self._card(kpi,"مبيعات اليوم",f"{t_s:,.0f} {cur}",
                   f"{tc} فاتورة  |  {sign} {abs(diff):.0f} عن أمس",C["success"],"💵",0,3)
        self._card(kpi,"تنبيهات المخزن",f"{ls.get('c') or 0} صنف","يحتاج تخزين",C["warning"],"⚠️",0,2)
        self._card(kpi,"قرب الانتهاء",f"{es.get('c') or 0} دواء","خلال 60 يوماً",C["danger"],"⏰",0,1)
        self._card(kpi,"إجمالي الأصناف",f"{tm.get('c') or 0}","صنف نشط",C["accent"],"📦",0,0)

        low=ctk.CTkFrame(sc,fg_color="transparent"); low.pack(fill="both",expand=True,pady=14)
        low.columnconfigure(0,weight=3); low.columnconfigure(1,weight=2)

        sp=ctk.CTkFrame(low,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        sp.grid(row=0,column=0,sticky="nsew",padx=(0,8))
        ctk.CTkLabel(sp,text="آخر المبيعات",font=(FONT,_fs(15),"bold"),text_color=C["txt"]).pack(anchor="e",padx=14,pady=10)
        tf,st=self._tree(sp,("inv","total","method","status","date"),("رقم الفاتورة","الإجمالي","طريقة الدفع","الحالة","التاريخ"))
        tf.pack(fill="both",expand=True,padx=10,pady=(0,10))
        for r in self.db.q("SELECT invoice_no,total,pay_method,credit_status,created_at FROM sales ORDER BY id DESC LIMIT 14"):
            cs=r["credit_status"]
            st_label={"pending":"⏳آجل","approved":"✅آجل","cancelled":"❌ملغي"}.get(cs,"") if cs else ""
            st.insert("","end",values=(r["invoice_no"],f"{r['total']:,.2f}",r["pay_method"],st_label,r["created_at"][:16] if r["created_at"] else ""))

        ap=ctk.CTkFrame(low,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        ap.grid(row=0,column=1,sticky="nsew",padx=(8,0))
        ctk.CTkLabel(ap,text="⚠  تنبيهات عاجلة",font=(FONT,_fs(15),"bold"),text_color=C["warning"]).pack(anchor="e",padx=14,pady=10)
        ai=ctk.CTkScrollableFrame(ap,fg_color="transparent"); ai.pack(fill="both",expand=True,padx=8,pady=(0,10))
        lr=self.db.q("SELECT name,stock,min_stock FROM medicines WHERE stock<=min_stock AND is_active=1 LIMIT 12")
        er=self.db.q("SELECT name,expiry FROM medicines WHERE expiry<=? AND is_active=1 LIMIT 8",(lim,))
        br=self.db.q("SELECT m.name,b.expiry,b.quantity_strips FROM batches b JOIN medicines m ON m.id=b.medicine_id"
            " WHERE b.expiry<=? AND b.quantity_strips>0 LIMIT 8",(lim,))
        if not lr and not er and not br:
            ctk.CTkLabel(ai,text="✓ لا توجد تنبيهات",font=(FONT,_fs(13)),text_color=C["success"]).pack(pady=20)
        for r in lr:
            rf=ctk.CTkFrame(ai,fg_color="#2d1f0a",corner_radius=7); rf.pack(fill="x",pady=2)
            ctk.CTkLabel(rf,text=f"⚠  {r['name']}  —  متبقي: {r['stock']}",font=(FONT,_fs(12)),text_color=C["warning"]).pack(anchor="e",padx=10,pady=7)
        for r in er:
            rf=ctk.CTkFrame(ai,fg_color="#2d0a0a",corner_radius=7); rf.pack(fill="x",pady=2)
            ctk.CTkLabel(rf,text=f"⏰  {r['name']}  —  ينتهي: {r['expiry'] or '؟'}",font=(FONT,_fs(12)),text_color=C["danger"]).pack(anchor="e",padx=10,pady=7)
        for r in br:
            rf=ctk.CTkFrame(ai,fg_color="#2d0a0a",corner_radius=7); rf.pack(fill="x",pady=2)
            ctk.CTkLabel(rf,text=f"📦 دفعة {r['name']}  —  تنتهي: {r['expiry']}  (متبقي {r['quantity_strips']})",
                font=(FONT,_fs(12)),text_color=C["danger"]).pack(anchor="e",padx=10,pady=7)

    # ═══════════════════════════════════════
    #  POS  — نقطة البيع (إعادة تصميم كاملة)
    # ═══════════════════════════════════════
    def _pg_pos(self):
        self._cart=[]  # [{"id","name","price","buy_price","qty","total","unit","max"}]
        cur=self.db.setting("currency","SDG")

        root=ctk.CTkFrame(self.cont,fg_color="transparent"); root.pack(fill="both",expand=True)
        root.columnconfigure(0,weight=5)   # products + search
        root.columnconfigure(1,weight=4)   # cart + checkout
        root.rowconfigure(0,weight=1)

        # ══════════════════════════════════
        #  LEFT: Search + Product results
        # ══════════════════════════════════
        left=ctk.CTkFrame(root,fg_color=C["card"],corner_radius=14,border_width=1,border_color=C["border"])
        left.grid(row=0,column=0,sticky="nsew",padx=(0,8))
        left.rowconfigure(1,weight=1)
        left.columnconfigure(0,weight=1)

        # Search bar with scanner toggle
        sb=ctk.CTkFrame(left,fg_color="transparent"); sb.grid(row=0,column=0,sticky="ew",padx=14,pady=12)
        sb.columnconfigure(2,weight=1)
        ctk.CTkLabel(sb,text="🔍",font=("Arial",22),text_color=C["txt_s"]).grid(row=0,column=0,padx=(0,6))
        self._scanner_var=ctk.BooleanVar(value=False)
        self._scan_btn=ctk.CTkButton(sb,text="📷",width=44,height=44,
            font=("Arial",16),fg_color=C["card"],hover_color=C["hover"],
            text_color=C["txt_s"],corner_radius=8,
            command=self._toggle_scanner)
        self._scan_btn.grid(row=0,column=1,padx=(0,6))
        self._posq=ctk.CTkEntry(sb,placeholder_text="ابحث بالاسم أو الباركود... (Enter للإضافة السريعة)",
            font=(FONT,_fs(14)),height=48,justify="right",
            fg_color=C["inp"],border_color=C["accent"],border_width=2,text_color=C["txt"])
        self._posq.grid(row=0,column=2,sticky="ew")
        self._posq.bind("<KeyRelease>",self._pos_search)
        self._posq.bind("<Return>",self._pos_enter_key)
        self._posq.focus()

        # Results area (scrollable buttons)
        self._res_frame=ctk.CTkScrollableFrame(left,fg_color="transparent",label_text="")
        self._res_frame.grid(row=1,column=0,sticky="nsew",padx=10,pady=(0,10))
        self._res_frame.columnconfigure(0,weight=1)
        self._res_frame.columnconfigure(1,weight=1)

        # Show all products initially
        self._show_products()
        self._on("inventory_changed",self._show_products)

        # ══════════════════════════════════
        #  RIGHT: Cart + Checkout
        # ══════════════════════════════════
        right=ctk.CTkFrame(root,fg_color="transparent"); right.grid(row=0,column=1,sticky="nsew",padx=(8,0))
        right.rowconfigure(0,weight=3); right.rowconfigure(1,weight=2); right.columnconfigure(0,weight=1)

        # Cart panel
        cp=ctk.CTkFrame(right,fg_color=C["card"],corner_radius=14,border_width=1,border_color=C["border"])
        cp.grid(row=0,column=0,sticky="nsew",pady=(0,8))
        cp.rowconfigure(1,weight=1); cp.columnconfigure(0,weight=1)

        # Cart header
        ch=ctk.CTkFrame(cp,fg_color="transparent"); ch.grid(row=0,column=0,sticky="ew",padx=14,pady=10)
        ctk.CTkLabel(ch,text="🛒  السلة",font=(FONT,_fs(15),"bold"),text_color=C["txt"]).pack(side="right")
        self._btn(ch,"🗑 مسح الكل",self._cart_clear,C["danger"],110,36).pack(side="left")

        # Cart table with columns: name, qty controls, price, total
        cart_frm=ctk.CTkFrame(cp,fg_color=C["card"],corner_radius=0); cart_frm.grid(row=1,column=0,sticky="nsew",padx=6,pady=(0,6))
        cart_frm.rowconfigure(0,weight=1); cart_frm.columnconfigure(0,weight=1)

        cols=("name","unit","qty","unit_price","total","_id")
        self._ct=ttk.Treeview(cart_frm,columns=cols,show="headings",style="P.Treeview")
        for col,hd,w in zip(cols,("الدواء","الوحدة","الكمية","السعر","الإجمالي","_"),(160,60,60,80,90,0)):
            self._ct.heading(col,text=hd); self._ct.column(col,anchor="center",width=w,minwidth=w)
        self._ct.column("_id",width=0,minwidth=0,stretch=False)
        vsb=ttk.Scrollbar(cart_frm,orient="vertical",command=self._ct.yview)
        self._ct.configure(yscrollcommand=vsb.set); vsb.pack(side="right",fill="y")
        self._ct.pack(fill="both",expand=True,padx=1,pady=1)
        self._ct.bind("<Double-Button-1>",self._cart_remove)

        # Qty control row (appears when item is selected)
        qc=ctk.CTkFrame(cp,fg_color=C["surface"],corner_radius=8)
        qc.grid(row=2,column=0,sticky="ew",padx=10,pady=(0,8))
        qcin=ctk.CTkFrame(qc,fg_color="transparent"); qcin.pack(padx=10,pady=8)
        ctk.CTkLabel(qcin,text="تعديل كمية الصنف المحدد:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=(0,10))
        self._btn(qcin,"＋",self._qty_up_sel,C["success"],44,38).pack(side="right",padx=2)
        self._qty_sel_lbl=ctk.CTkLabel(qcin,text="—",font=(FONT,_fs(14),"bold"),
            text_color=C["txt"],width=50); self._qty_sel_lbl.pack(side="right")
        self._btn(qcin,"−",self._qty_dn_sel,C["danger"],44,38).pack(side="right",padx=2)
        ctk.CTkLabel(qcin,text="انقر مرتين للحذف",font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(side="left",padx=8)
        self._ct.bind("<<TreeviewSelect>>",self._cart_sel_changed)

        # Checkout panel
        co=ctk.CTkFrame(right,fg_color=C["card"],corner_radius=14,border_width=1,border_color=C["border"])
        co.grid(row=1,column=0,sticky="nsew",pady=(8,0))
        cosc=ctk.CTkScrollableFrame(co,fg_color="transparent"); cosc.pack(fill="both",expand=True)

        ctk.CTkLabel(cosc,text="ملخص الفاتورة",font=(FONT,_fs(15),"bold"),text_color=C["txt"]).pack(anchor="e",padx=14,pady=(12,2))
        self._inv_no=self._gen_inv()
        self._inv_lbl=ctk.CTkLabel(cosc,text=f"رقم: {self._inv_no}",font=(FONT,_fs(10)),text_color=C["txt_m"])
        self._inv_lbl.pack(anchor="e",padx=14)
        self._sep(cosc)

        # Totals
        def kv(title,big=False,color=None):
            rf=ctk.CTkFrame(cosc,fg_color="transparent"); rf.pack(fill="x",padx=14,pady=2)
            sz=20 if big else 13; col=color or (C["success"] if big else C["txt_s"])
            ctk.CTkLabel(rf,text=title,font=(FONT,sz),text_color=col).pack(side="right")
            vl=ctk.CTkLabel(rf,text="0.00",font=(FONT,sz,"bold"),text_color=C["txt"] if not big else C["success"])
            vl.pack(side="left"); return vl

        self._sub_l=kv("المجموع:")
        # Discount row
        dr=ctk.CTkFrame(cosc,fg_color="transparent"); dr.pack(fill="x",padx=14,pady=2)
        ctk.CTkLabel(dr,text="خصم (%):",font=(FONT,_fs(13)),text_color=C["txt_s"]).pack(side="right")
        self._disc=ctk.CTkEntry(dr,width=70,height=36,justify="center",placeholder_text="0",
            fg_color=C["inp"],text_color=C["txt"])
        self._disc.pack(side="left")
        self._disc.bind("<KeyRelease>",lambda _:self._refresh_totals())
        self._sep(cosc)
        self._tot_l=kv("الإجمالي:",big=True)

        # Payment fields in 2 columns
        pf=ctk.CTkFrame(cosc,fg_color="transparent"); pf.pack(fill="x",padx=14,pady=4)
        pf.columnconfigure(0,weight=1); pf.columnconfigure(1,weight=1)
        def prow(r,c,lbl,w):
            f=ctk.CTkFrame(pf,fg_color="transparent"); f.grid(row=r,column=c,padx=4,pady=2,sticky="ew")
            ctk.CTkLabel(f,text=lbl,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
            return f
        f1=prow(0,1,"العميل:",1); self._cust=self._ent(f1,"اسم العميل"); self._cust.pack(fill="x")
        f2=prow(0,0,"طريقة الدفع:",0)
        self._pay=self._combo(f2,["كاش","تحويل بنكي","فيزا","آجل"])
        self._pay.configure(command=self._pay_method_changed)
        self._pay.pack(fill="x")
        f3=prow(1,1,"رقم المرجع:",1); self._ref=self._ent(f3,"رقم العملية"); self._ref.pack(fill="x")
        f4=prow(1,0,"المبلغ المدفوع:",0)
        self._paid=ctk.CTkEntry(f4,width=160,height=42,justify="center",placeholder_text="0.00",
            fg_color=C["inp"],text_color=C["txt"],font=(FONT,_fs(14),"bold"))
        self._paid.pack(fill="x")
        self._paid.bind("<KeyRelease>",lambda _:self._calc_change())
        self._change_l=ctk.CTkLabel(cosc,text="الباقي: 0.00",font=(FONT,_fs(14),"bold"),text_color=C["success"])
        self._change_l.pack(anchor="e",padx=18,pady=2)

        # Print toggle
        prtf=ctk.CTkFrame(cosc,fg_color="transparent"); prtf.pack(fill="x",padx=14,pady=4)
        self._print_v=ctk.BooleanVar(value=True)
        ctk.CTkSwitch(prtf,text="عرض الفاتورة بعد البيع",variable=self._print_v,
            font=(FONT,_fs(12)),text_color=C["txt_s"],progress_color=C["accent"]).pack(side="right")

        # Complete button
        ctk.CTkButton(cosc,text="✓  إتمام البيع  وحفظ الفاتورة",height=54,
            font=(FONT,_fs(15),"bold"),fg_color=C["success"],hover_color="#059669",
            corner_radius=12,command=self._complete_sale).pack(fill="x",padx=14,pady=(6,14))

        # ── Keyboard shortcuts ──
        self._posq.bind("<F2>",lambda _: self._posq.focus())
        root.bind("<F5>",lambda _: (self._show_products(), Toast.show(self,"✓ تحديث","info",800)))
        root.bind("<F12>",lambda _: self._complete_sale())

    # ── Product display helpers ──────────────
    def _show_products(self,search=""):
        self._res_frame.configure(height=1)
        for w in self._res_frame.winfo_children(): w.destroy()
        cur=self.db.setting("currency","SDG")
        if search:
            rows=self.db.q("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines"
                " WHERE (name LIKE ? OR barcode LIKE ? OR generic_name LIKE ? OR manufacturer LIKE ?) AND is_active=1 AND stock>0 LIMIT 24",
                (f"%{search}%",f"%{search}%",f"%{search}%",f"%{search}%"))
        else:
            rows=self.db.q("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines"
                " WHERE is_active=1 AND stock>0 ORDER BY name LIMIT 40")
        if not rows:
            ctk.CTkLabel(self._res_frame,text="لا توجد نتائج",font=(FONT,_fs(14)),
                text_color=C["txt_m"]).grid(row=0,column=0,columnspan=2,pady=30)
            return
        self._last_rows=rows
        self.after(1,lambda: self._render_cards(rows,cur))

    def _render_cards(self,rows,cur):
        for i,med in enumerate(rows):
            row_n,col_n=divmod(i,2)
            btn_f=tk.Frame(self._res_frame,bg="#1e293b",highlightbackground=C["border"],highlightthickness=1)
            btn_f.grid(row=row_n,column=col_n,padx=3,pady=3,sticky="ew")
            btn_f.columnconfigure(0,weight=1)
            stk_col=C["success"] if med["stock"]>10 else C["warning"] if med["stock"]>0 else C["danger"]
            # Name
            tk.Label(btn_f,text=med["name"],font=(FONT,_fs(11),"bold"),fg="#f1f5f9",bg="#1e293b",
                wraplength=170,justify="right").grid(row=0,column=0,sticky="e",padx=8,pady=(6,2))
            # Price + Add button row
            pr_row=tk.Frame(btn_f,bg="#1e293b"); pr_row.grid(row=1,column=0,sticky="ew",padx=6)
            pr_row.columnconfigure(0,weight=1); pr_row.columnconfigure(1,weight=0)
            tk.Label(pr_row,text=f"{med['sell_price']:.2f} {cur}",
                font=(FONT,_fs(12),"bold"),fg=C["accent"],bg="#1e293b",anchor="e"
            ).grid(row=0,column=0,sticky="e")
            add_btn=ctk.CTkButton(pr_row,text="➕",width=34,height=26,
                command=lambda m=med:self._cart_add(m,"box"),fg_color=C["success"],
                hover_color="#059669",corner_radius=6,font=("Arial",12))
            add_btn.grid(row=0,column=1,padx=(4,0))
            # Strip option
            can_strip=med.get("sell_by_strip") and (med.get("strip_price") or 0)>0
            spb=med.get("strips_per_box") or 1
            if can_strip:
                st_row=tk.Frame(btn_f,bg="#1e293b"); st_row.grid(row=2,column=0,sticky="ew",padx=6)
                st_row.columnconfigure(0,weight=1); st_row.columnconfigure(1,weight=0)
                tk.Label(st_row,text=f"شريط: {med['strip_price']:.2f} {cur}",
                    font=(FONT,_fs(11)),fg=C["purple"],bg="#1e293b",anchor="e"
                ).grid(row=0,column=0,sticky="e")
                ctk.CTkButton(st_row,text="➕",width=34,height=26,
                    command=lambda m=med:self._cart_add(m,"strip"),fg_color=C["purple"],
                    hover_color="#7c3aed",corner_radius=6,font=("Arial",12)
                ).grid(row=0,column=1,padx=(4,0))
                stk_info=f"مخزون: {med['stock']//spb}عب +{med['stock']%spb}ش"
            else:
                stk_info=f"مخزون: {med['stock']} {med.get('unit') or 'قطعة'}"
            tk.Label(btn_f,text=stk_info,font=(FONT,_fs(9)),
                fg=stk_col,bg="#1e293b",anchor="e"
            ).grid(row=3 if can_strip else 2,column=0,sticky="e",padx=8,pady=(0,4))

    def _pos_search(self,_=None):
        q=self._posq.get().strip()
        if q:
            # Auto-add on exact barcode match
            med=self.db.q1("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines"
                " WHERE barcode=? AND is_active=1 AND stock>0",(q,))
            if med:
                self._cart_add(med); self._posq.delete(0,"end")
                if self._scanner_var.get(): self.after(100,self._posq.focus)
                return
        self._show_products(q)

    def _toggle_scanner(self):
        self._scanner_var.set(not self._scanner_var.get())
        if self._scanner_var.get():
            self._scan_btn.configure(fg_color=C["success"],text_color="white",text="📷 ⎔")
            Toast.show(self,"وضع المسح نشط — امسح الباركود","info",2000)
        else:
            self._scan_btn.configure(fg_color=C["card"],text_color=C["txt_s"],text="📷")
        self._posq.focus()

    def _pos_enter_key(self,_=None):
        q=self._posq.get().strip()
        if not q: return
        # Try exact barcode match first
        rows=self.db.q("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines"
            " WHERE barcode=? AND is_active=1 AND stock>0",(q,))
        if rows:
            self._cart_add(rows[0]); self._posq.delete(0,"end")
            if self._scanner_var.get(): self.after(100,self._posq.focus)
            return
        # Name search
        rows=self.db.q("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines"
            " WHERE (name LIKE ? OR generic_name LIKE ? OR manufacturer LIKE ?) AND is_active=1 AND stock>0 LIMIT 2",(f"%{q}%",f"%{q}%",f"%{q}%"))
        if len(rows)==1:
            self._cart_add(rows[0]); self._posq.delete(0,"end")
            if self._scanner_var.get(): self.after(100,self._posq.focus)
        elif len(rows)==0 and self._scanner_var.get():
            self._pos_quick_add(q)

    def _pos_quick_add(self,barcode):
        # Check if barcode already exists (including inactive)
        existing=self.db.q1("SELECT * FROM medicines WHERE barcode=? AND is_active=0",(barcode,))
        if existing:
            if messagebox.askyesno("منتج محذوف",f"الباركود '{barcode}' موجود في سلة المهملات ('{existing['name']}').\nهل تريد استرجاعه وإضافة كمية جديدة؟"):
                add_q=simpledialog.askinteger("إضافة كمية","الكمية للإضافة:",initialvalue=1,minvalue=1,parent=self)
                if add_q:
                    self.db.run("UPDATE medicines SET is_active=1,stock=stock+?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(add_q,existing["id"]))
                    self.db.log(self.user["id"],"RESTORE_MED_QR",f"{existing['name']}+{add_q}")
                    Toast.show(self,f"✓ تم استرجاع {existing['name']} وإضافة {add_q}","success")
                    med=self.db.q1("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines WHERE id=?",(existing["id"],))
                    if med: self._cart_add(med); self._posq.delete(0,"end")
                    self._show_products()
                    if self._scanner_var.get(): self.after(100,self._posq.focus)
            return
        # Normal quick add
        dlg=ctk.CTkToplevel(self); dlg.title("منتج جديد — إضافة سريعة"); dlg.geometry("480x520")
        dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks()
        sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"480x520+{(sw-480)//2}+{(sh-520)//2}")
        ctk.CTkLabel(dlg,text=f"📷 الباركود: {barcode}",font=(FONT,_fs(15),"bold"),text_color=C["accent"]).pack(pady=16)
        sc=ctk.CTkScrollableFrame(dlg,fg_color="transparent"); sc.pack(fill="both",expand=True,padx=20)
        fields={}
        for lbl,key in [("اسم الدواء *","name"),("سعر البيع *","sell_price"),("الكمية *","stock"),
                        ("سعر الشراء","buy_price"),("تاريخ الصلاحية (YYYY-MM-DD)","expiry")]:
            ctk.CTkLabel(sc,text=lbl,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",pady=(8,2))
            e=ctk.CTkEntry(sc,width=400,height=42,justify="right",font=(FONT,_fs(13)),
                fg_color=C["inp"],text_color=C["txt"]); e.pack()
            if key=="sell_price": e.insert(0,"0")
            elif key=="stock": e.insert(0,"1")
            fields[key]=e
        def save():
            nm=fields["name"].get().strip(); sp=fields["sell_price"].get().strip(); st=fields["stock"].get().strip()
            if not nm or not sp: Toast.show(dlg,"اسم الدواء وسعر البيع مطلوبان","error"); return
            try: spf=float(sp); sti=int(st or 1)
            except: Toast.show(dlg,"قيم غير صحيحة","error"); return
            self.db.run("INSERT INTO medicines(barcode,name,sell_price,stock,buy_price,expiry,stock_migrated)"
                " VALUES(?,?,?,?,?,?,1)",(barcode,nm,spf,sti,float(fields["buy_price"].get() or 0),
                fields["expiry"].get().strip() or None))
            self.db.log(self.user["id"],"ADD_MED_QR",nm)
            Toast.show(self,f"✓ تمت إضافة {nm}","success")
            med=self.db.q1("SELECT id,name,barcode,sell_price,buy_price,strip_price,sell_by_strip,stock,unit,strips_per_box,image_path FROM medicines WHERE barcode=?",(barcode,))
            if med: self._cart_add(med)
            dlg.destroy(); self._show_products(); self._posq.delete(0,"end")
            if self._scanner_var.get(): self.after(100,self._posq.focus)
        bf=ctk.CTkFrame(sc,fg_color="transparent"); bf.pack(pady=14)
        self._btn(bf,"💾 حفظ وإضافة للسلة",save,C["success"],280,46).pack()

    # ── Cart operations ──────────────────────
    def _cart_add(self,med,sell_mode="box"):
        spb=med.get("strips_per_box") or 1
        price=med["sell_price"] if sell_mode=="box" else (med.get("strip_price") or med["sell_price"])
        buy_p=med.get("buy_price",0)
        # Normalize buy_price to match sell unit: box→per-box, strip→per-strip
        if sell_mode=="strip" and spb>1: buy_p=buy_p/spb
        sell_unit="علبة" if sell_mode=="box" else "شريط"
        max_q=med["stock"] if sell_mode=="strip" else (med["stock"]//spb if spb else med["stock"])
        for item in self._cart:
            if item["id"]==med["id"] and item.get("sell_mode")==sell_mode:
                if item["qty"]>=item["max"]:
                    Toast.show(self,f"المخزون المتاح {item['max']} فقط","error"); return
                item["qty"]+=1; item["total"]=item["qty"]*item["price"]
                self._refresh_cart_ui(); Toast.show(self,f"✓  {med['name']} ({item['qty']})","success",1200); return
        self._cart.append({"id":med["id"],"name":med["name"],"price":price,
            "buy_price":buy_p,"qty":1,"total":price,
            "unit":sell_unit,"max":max_q,"sell_mode":sell_mode,"strips_per_box":spb})
        self._refresh_cart_ui()
        Toast.show(self,f"✓  أُضيف {med['name']} ({sell_unit})","success",1400)

    def _cart_remove(self,_=None):
        sel=self._ct.selection()
        if not sel: return
        mid=self._ct.item(sel[0])["values"][-1]
        self._cart=[c for c in self._cart if c["id"]!=mid]
        self._refresh_cart_ui()

    def _cart_clear(self):
        self._cart=[]; self._refresh_cart_ui()

    def _cart_sel_changed(self,_=None):
        sel=self._ct.selection()
        if not sel: self._qty_sel_lbl.configure(text="—"); return
        mid=self._ct.item(sel[0])["values"][-1]
        for item in self._cart:
            if item["id"]==mid: self._qty_sel_lbl.configure(text=str(item["qty"])); return

    def _qty_up_sel(self):
        sel=self._ct.selection()
        if not sel: return
        mid=self._ct.item(sel[0])["values"][-1]
        for item in self._cart:
            if item["id"]==mid:
                if item["qty"]>=item["max"]:
                    Toast.show(self,f"المخزون المتاح {item['max']} فقط","error"); return
                item["qty"]+=1; item["total"]=item["qty"]*item["price"]
                self._refresh_cart_ui()
                # Reselect the same row
                for row_id in self._ct.get_children():
                    if self._ct.item(row_id)["values"][-1]==mid:
                        self._ct.selection_set(row_id); break
                return

    def _qty_dn_sel(self):
        sel=self._ct.selection()
        if not sel: return
        mid=self._ct.item(sel[0])["values"][-1]
        for item in self._cart:
            if item["id"]==mid:
                if item["qty"]<=1:
                    if messagebox.askyesno("حذف","هل تريد حذف هذا الصنف من السلة؟"):
                        self._cart=[c for c in self._cart if c["id"]!=mid]; self._refresh_cart_ui()
                    return
                item["qty"]-=1; item["total"]=item["qty"]*item["price"]
                self._refresh_cart_ui()
                for row_id in self._ct.get_children():
                    if self._ct.item(row_id)["values"][-1]==mid:
                        self._ct.selection_set(row_id); break
                return

    def _refresh_cart_ui(self):
        for r in self._ct.get_children(): self._ct.delete(r)
        for item in self._cart:
            self._ct.insert("","end",values=(item["name"],item.get("unit",""),
                item["qty"],f"{item['price']:.2f}",f"{item['total']:.2f}",item["id"]))
        self._qty_sel_lbl.configure(text="—")
        self._refresh_totals()

    def _refresh_totals(self):
        sub=sum(i["total"] for i in self._cart)
        try:    dp=max(0,min(100,float(self._disc.get() or 0)))
        except: dp=0
        tot=sub*(1-dp/100); cur=self.db.setting("currency","SDG")
        self._sub_l.configure(text=f"{sub:.2f} {cur}")
        self._tot_l.configure(text=f"{tot:.2f} {cur}")
        self._calc_change()
    def _pay_method_changed(self,choice=None):
        if self._pay.get()=="آجل":
            self._paid.delete(0,"end"); self._paid.insert(0,"0")
            self._paid.configure(state="disabled",fg_color=C["txt_m"])
        else:
            self._paid.configure(state="normal",fg_color=C["inp"])
            self._paid.delete(0,"end")
        self._calc_change()

    def _calc_change(self):
        sub=sum(i["total"] for i in self._cart)
        try:    dp=max(0,min(100,float(self._disc.get() or 0)))
        except: dp=0
        tot=sub*(1-dp/100)
        try:    paid=float(self._paid.get() or 0)
        except: paid=0
        ch=paid-tot
        self._change_l.configure(text=f"الباقي: {ch:.2f}",
            text_color=C["success"] if ch>=0 else C["danger"])

    def _gen_inv(self):
        last=(self.db.q1("SELECT MAX(id) m FROM sales") or {}).get("m") or 0
        return f"INV-{datetime.now().strftime('%y%m%d')}-{last+1:04d}"

    def _complete_sale(self):
        if not self._cart: Toast.show(self,"السلة فارغة!","error"); return
        sub=sum(i["total"] for i in self._cart)
        try:    dp=max(0,min(100,float(self._disc.get() or 0)))
        except: dp=0
        disc_amt=sub*dp/100; tot=sub-disc_amt
        pay_method=self._pay.get(); ref_no=self._ref.get().strip(); customer=self._cust.get().strip()
        is_credit=pay_method=="آجل"
        # For credit, customer name is required and payment is 0
        if is_credit:
            if not customer:
                Toast.show(self,"أدخل اسم العميل للفاتورة الآجلة","error"); return
            paid=0; change=0
            self._paid.delete(0,"end"); self._paid.insert(0,"0")
        else:
            try:    paid=float(self._paid.get() or tot)
            except: paid=tot
            change=paid-tot
            if pay_method=="كاش" and paid<tot:
                Toast.show(self,"المبلغ المدفوع أقل من الإجمالي","error"); return
        try:
            credit_status="pending" if is_credit else None
            sid=self.db.run("INSERT INTO sales(invoice_no,subtotal,discount,total,"
                "pay_method,amount_paid,change_amount,ref_no,customer_name,user_id,credit_status)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (self._inv_no,sub,disc_amt,tot,pay_method,paid,change,ref_no,customer,self.user["id"],credit_status))
            for item in self._cart:
                strip_qty=item.get("strips_per_box",1)*item["qty"] if item.get("sell_mode")=="box" else 0
                self.db.run("INSERT INTO sale_items(sale_id,medicine_id,quantity,unit_price,buy_price,total,strip_qty)"
                    " VALUES(?,?,?,?,?,?,?)",
                    (sid,item["id"],item["qty"],item["price"],item.get("buy_price",0),item["total"],strip_qty))
                ded_qty=strip_qty if strip_qty else item["qty"]
                self.db.run("UPDATE medicines SET stock=stock-? WHERE id=?",(ded_qty,item["id"]))
                # FIFO deduction from batches
                rem=ded_qty
                batches=self.db.q("SELECT id,quantity_strips FROM batches WHERE medicine_id=? AND quantity_strips>0 ORDER BY expiry,id",(item["id"],))
                for b in batches:
                    if rem<=0: break
                    take=min(rem,b["quantity_strips"])
                    self.db.run("UPDATE batches SET quantity_strips=quantity_strips-? WHERE id=?",(take,b["id"]))
                    rem-=take
            # إضافة للخزينة فقط إذا لم تكن آجل
            if not is_credit:
                self.db.run("INSERT INTO ledger(type,amount,category,description,ref_id,user_id)"
                    " VALUES(?,?,?,?,?,?)",("IN",tot,"مبيعات",f"فاتورة {self._inv_no}",sid,self.user["id"]))
            else:
                self.db.log(self.user["id"],"CREDIT_SALE",f"{self._inv_no}={tot:.2f} (آجل)")
            self.db.log(self.user["id"],"SALE",f"{self._inv_no}={tot:.2f}")
            cart_snap=list(self._cart); inv_snap=self._inv_no
            # Reset
            self._cart_clear(); self._disc.delete(0,"end")
            self._paid.configure(state="normal",fg_color=C["inp"])
            self._paid.delete(0,"end"); self._cust.delete(0,"end"); self._ref.delete(0,"end")
            self._pay.set("كاش"); self._pay_method_changed()
            self._inv_no=self._gen_inv(); self._inv_lbl.configure(text=f"رقم: {self._inv_no}")
            self._show_products()
            if is_credit:
                Toast.show(self,f"✓ فاتورة {inv_snap} مسجلة كآجل → بانتظار الموافقة | {tot:.2f}","success",5000)
            elif self._print_v.get():
                self._invoice_dlg(inv_snap,cart_snap,sub,disc_amt,tot,pay_method,paid,change,customer)
            else:
                Toast.show(self,f"✓ فاتورة {inv_snap} | إجمالي: {tot:.2f} | باقي: {change:.2f}","success",4000)
        except Exception as ex:
            Toast.show(self,f"خطأ: {ex}","error",5000)

    # ── Invoice Dialog (احترافية جديدة) ─────
    def _invoice_dlg(self,inv_no,cart,sub,disc,tot,pay_method,paid,change,customer):
        dlg=ctk.CTkToplevel(self); dlg.title(f"فاتورة  {inv_no}")
        dlg.geometry("680x780"); dlg.configure(fg_color="white"); dlg.grab_set()
        dlg.update_idletasks()
        sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"680x780+{(sw-680)//2}+{(sh-780)//2}")
        ph=self.db.setting("pharmacy_name","صيدلية كيور")
        addr=self.db.setting("pharmacy_address","")
        phone=self.db.setting("pharmacy_phone","")
        cur=self.db.setting("currency","SDG")
        now=datetime.now().strftime("%Y-%m-%d  %H:%M")
        cashier=self.user["full_name"]

        sc=ctk.CTkScrollableFrame(dlg,fg_color="transparent"); sc.pack(fill="both",expand=True,padx=24,pady=16)

        # ── Header ──
        hdr=ctk.CTkFrame(sc,fg_color="#f8fafc",corner_radius=10); hdr.pack(fill="x",pady=(0,8))
        hi=ctk.CTkFrame(hdr,fg_color="transparent"); hi.pack(padx=16,pady=12)
        hi.columnconfigure(0,weight=1); hi.columnconfigure(1,weight=2)
        logo_path=self.db.setting("logo_invoice","") or self.db.setting("logo_login","")
        lf=ctk.CTkFrame(hi,fg_color="transparent"); lf.grid(row=0,column=0,sticky="w")
        if logo_path and os.path.exists(logo_path):
            try:
                from PIL import Image
                lf_logo=ctk.CTkImage(Image.open(logo_path),size=(64,64))
                ctk.CTkLabel(lf,text="",image=lf_logo).pack()
            except:
                ctk.CTkLabel(lf,text="💊",font=("Arial",48)).pack()
        else:
            ctk.CTkLabel(lf,text="💊",font=("Arial",48)).pack()
        info_f=ctk.CTkFrame(hi,fg_color="transparent"); info_f.grid(row=0,column=1,sticky="e")
        ctk.CTkLabel(info_f,text=ph,font=("Arial",22,"bold"),text_color="#1e293b").pack(anchor="e")
        if addr: ctk.CTkLabel(info_f,text=addr,font=("Arial",11),text_color="#64748b").pack(anchor="e")
        if phone: ctk.CTkLabel(info_f,text=f"📞 {phone}",font=("Arial",11),text_color="#64748b").pack(anchor="e")

        # ── Accent bar ──
        ctk.CTkFrame(sc,height=4,fg_color="#2563eb",corner_radius=2).pack(fill="x",pady=4)

        # ── Invoice Meta ──
        meta=ctk.CTkFrame(sc,fg_color="white",corner_radius=8,border_width=1,border_color="#e2e8f0")
        meta.pack(fill="x",pady=4)
        mi=ctk.CTkFrame(meta,fg_color="transparent"); mi.pack(padx=16,pady=8)
        mi.columnconfigure(0,weight=1); mi.columnconfigure(1,weight=1)
        def meta_line(parent,row,col,label,val,cc="#2563eb"):
            f=ctk.CTkFrame(parent,fg_color="transparent"); f.grid(row=row,column=col,sticky="ew",pady=1,padx=4)
            ctk.CTkLabel(f,text=label,font=("Arial",10),text_color="#94a3b8").pack(anchor="e")
            ctk.CTkLabel(f,text=val,font=("Arial",11,"bold"),text_color=cc).pack(anchor="e")
        meta_line(mi,0,0,"فاتورة رقم",inv_no)
        meta_line(mi,0,1,"التاريخ",now)
        meta_line(mi,1,0,"الكاشير",cashier)
        meta_line(mi,1,1,"طريقة الدفع",pay_method)
        if customer:
            meta_line(mi,2,0,"العميل",customer)
        meta_line(mi,2,1,"العملة",cur)

        # ── Items Table ──
        ctk.CTkLabel(sc,text="تفاصيل الفاتورة",font=("Arial",12,"bold"),
            text_color="#1e293b").pack(anchor="e",padx=4,pady=(10,4))

        tbl=ctk.CTkFrame(sc,fg_color="transparent",corner_radius=6)
        tbl.pack(fill="x")
        # Header
        hdr_r=ctk.CTkFrame(tbl,fg_color="#1e293b",corner_radius=0,height=32)
        hdr_r.pack(fill="x"); hdr_r.pack_propagate(False)
        for side,w,txt in [("right",170,"البيان"),("right",75,"الإجمالي"),
                            ("right",55,"الكمية"),("right",85,"سعر الوحدة"),("left",40,"")]:
            ctk.CTkLabel(hdr_r,text=txt,font=("Arial",10,"bold"),text_color="white",
                width=w).pack(side=side,padx=2)
        # Items with alternating bg
        for idx,item in enumerate(cart):
            bg="#ffffff" if idx%2==0 else "#f8fafc"
            irow=ctk.CTkFrame(tbl,fg_color=bg,corner_radius=0,height=32)
            irow.pack(fill="x"); irow.pack_propagate(False)
            ctk.CTkFrame(irow,height=1,fg_color="#f1f5f9").pack(fill="x")
            unit_lbl=item.get("unit","")
            ctk.CTkLabel(irow,text=f"{item['total']:.2f}",font=("Arial",11,"bold"),
                text_color="#1e293b",width=75).pack(side="right",padx=2,anchor="center")
            ctk.CTkLabel(irow,text=str(item["qty"]),font=("Arial",11),
                text_color="#1e293b",width=55).pack(side="right",padx=2,anchor="center")
            ctk.CTkLabel(irow,text=f"{item['price']:.2f}",font=("Arial",11),
                text_color="#1e293b",width=85).pack(side="right",padx=2,anchor="center")
            ctk.CTkLabel(irow,text=item["name"],font=("Arial",11),text_color="#1e293b",
                width=170).pack(side="right",padx=2)
            ctk.CTkLabel(irow,text=unit_lbl,font=("Arial",9),text_color="#94a3b8",
                width=35).pack(side="left",padx=2)

        # ── Totals ──
        tot_f=ctk.CTkFrame(sc,fg_color="#f8fafc",corner_radius=8); tot_f.pack(fill="x",pady=(10,4))
        tblock=ctk.CTkFrame(tot_f,fg_color="transparent"); tblock.pack(side="left",padx=12,pady=8)
        def tot_line(t,v,big=False,clr=None):
            r=ctk.CTkFrame(tblock,fg_color="transparent"); r.pack(padx=16,pady=1)
            sz=20 if big else 13
            ctk.CTkLabel(r,text=t,font=("Arial",sz,"bold" if big else "normal"),
                text_color=clr or "#64748b").pack(side="right")
            ctk.CTkLabel(r,text=v,font=("Arial",sz,"bold"),
                text_color="#2563eb" if big else "#1e293b").pack(side="left",padx=(8,0))
        tot_line("الإجمالي الفرعي:",f"{sub:,.2f} {cur}")
        if disc>0: tot_line("الخصم:",f"- {disc:,.2f} {cur}",clr="#f59e0b")
        ctk.CTkFrame(tblock,height=1,fg_color="#cbd5e1").pack(fill="x",padx=16,pady=4)
        tot_line("الإجمالي النهائي:",f"{tot:,.2f} {cur}",big=True)
        ctk.CTkFrame(tblock,height=3,fg_color="#2563eb").pack(fill="x",padx=16,pady=4)
        tot_line("المدفوع:",f"{paid:,.2f} {cur}")
        tot_line("الباقي:",f"{change:,.2f} {cur}",clr="#10b981" if change>0 else "#ef4444")

        # ── Thank you ──
        ctk.CTkFrame(sc,height=1,fg_color="#e2e8f0").pack(fill="x",pady=10)
        ctk.CTkLabel(sc,text="شكراً لزيارتكم  💊  نتمنى لكم الصحة والعافية",
            font=("Arial",13),text_color="#94a3b8").pack(pady=(0,6))

        # ── Buttons ──
        bf=ctk.CTkFrame(dlg,fg_color="#f8fafc",corner_radius=0); bf.pack(fill="x",padx=0,pady=0)
        bfi=ctk.CTkFrame(bf,fg_color="transparent"); bfi.pack(padx=16,pady=10,anchor="e")
        def do_print():
            import subprocess,sys
            lines=["─"*50,f"  {ph}"+(f"  |  {addr}" if addr else ""),
                   f"  هاتف: {phone}" if phone else "","─"*50,
                   f"  فاتورة رقم: {inv_no}     {now}",
                   f"  الكاشير: {cashier}"+(f"     العميل: {customer}" if customer else ""),
                   "─"*50,"  البيان                الكمية   السعر    الإجمالي","─"*50]
            for i in cart:
                u=i.get("unit","")
                lines.append(f"  {i['name'][:25]:25s}  {i['qty']:3d}   {i['price']:7.2f}  {i['total']:9.2f}")
            lines+=["─"*50,f"  الإجمالي الفرعي:              {sub:>10.2f} {cur}"]
            if disc>0: lines.append(f"  الخصم:                        {disc:>10.2f} {cur}")
            lines+=["─"*50,f"  الإجمالي النهائي:             {tot:>10.2f} {cur}",
                    f"  المدفوع:                      {paid:>10.2f} {cur}",
                    f"  الباقي:                       {change:>10.2f} {cur}","─"*50,
                    "  شكراً لزيارتكم 💊  نتمنى لكم الصحة والعافية"]
            text="\n".join(lines)
            inv_dir=os.path.join(app_dir(),"invoices")
            os.makedirs(inv_dir,exist_ok=True)
            fname=os.path.join(inv_dir,f"{inv_no}.txt")
            with open(fname,"w",encoding="utf-8") as f: f.write(text)
            try:
                if sys.platform=="win32": os.startfile(fname,"print")
                elif sys.platform=="darwin": subprocess.call(["lpr",fname])
                else: subprocess.call(["lp",fname])
                Toast.show(self,"✓ أُرسلت للطابعة","success")
            except Exception as e: Toast.show(self,f"تعذّر: {e}","warning",4000)
        def do_save():
            path=filedialog.asksaveasfilename(defaultextension=".txt",
                filetypes=[("Text","*.txt"),("All","*.*")],initialfile=f"{inv_no}.txt")
            if not path: return
            with open(path,"w",encoding="utf-8") as f:
                f.write(f"{ph}\nفاتورة: {inv_no}\n{now}\n")
                for i in cart: f.write(f"{i['name']} ×{i['qty']} = {i['total']:.2f}\n")
                f.write(f"الإجمالي: {tot:.2f} {cur}\n")
            Toast.show(self,"✓ تم الحفظ","success")
        def do_thermal():
            try:
                import win32print
                prn=self.db.setting("thermal_printer","")
                if not prn: Toast.show(self,"اختر طابعة حرارية من الإعدادات أولاً","warning"); return
                lines=[ph.center(40),("فاتورة: "+inv_no).center(40),now.center(40)]
                if addr: lines.append(addr.center(40))
                if phone: lines.append(phone.center(40))
                lines.append("—"*40)
                lines.append(f"{"البيان":25s}  {"ك":3s}  {"السعر":7s}  {"الإجمالي":9s}")
                lines.append("—"*40)
                for i in cart:
                    u=i.get("unit","")
                    lines.append(f"{i['name'][:24]:25s}{i['qty']:3d} {i['price']:7.2f} {i['total']:9.2f}")
                lines.append("—"*40)
                lines.append(f"الإجمالي الفرعي:              {sub:>10.2f} {cur}")
                if disc>0: lines.append(f"الخصم:                        {disc:>10.2f} {cur}")
                lines.append(f"الإجمالي النهائي:             {tot:>10.2f} {cur}")
                lines.append(f"المدفوع:                      {paid:>10.2f} {cur}")
                lines.append(f"الباقي:                       {change:>10.2f} {cur}")
                if customer: lines.append(f"العميل: {customer}")
                lines.append("—"*40)
                lines.append("شكراً لزيارتكم 💊".center(40))
                lines.append("")
                text="\n".join(lines)
                h=win32print.OpenPrinter(prn)
                try:
                    win32print.StartDocPrinter(h,1,("invoice",None,"RAW"))
                    win32print.StartPagePrinter(h)
                    win32print.WritePrinter(h,text.encode("utf-8","replace"))
                    # ESC/POS: cut paper
                    win32print.WritePrinter(h,b"\x1d\x56\x42\x00")
                    win32print.EndPagePrinter(h)
                    win32print.EndDocPrinter(h)
                    Toast.show(self,"✓ طباعة حرارية ناجحة","success",2000)
                finally: win32print.ClosePrinter(h)
            except Exception as e: Toast.show(self,f"خطأ الطباعة: {e}","error",4000)
        self._btn(bfi,"🖨 حراري",do_thermal,"#8b5cf6",100,40).pack(side="right",padx=4)
        self._btn(bfi,"🖨 طباعة",do_print,"#2563eb",130,40).pack(side="right",padx=4)
        self._btn(bfi,"💾 حفظ",do_save,"#475569",100,40).pack(side="right",padx=4)
        self._btn(bfi,"✕ إغلاق",dlg.destroy,"#ef4444",100,40).pack(side="right",padx=4)

    # ═══════════════════════════════════════
    #  INVENTORY
    # ═══════════════════════════════════════
    def _pg_inventory(self):
        if not can(self.user,"inventory"):
            ctk.CTkLabel(self.cont,text="⛔  لا تملك صلاحية الوصول للمخزن",
                font=(FONT,_fs(18),"bold"),text_color=C["danger"]).pack(expand=True); return
        tabs=ctk.CTkTabview(self.cont,fg_color=C["card"],
            segmented_button_fg_color=C["surface"],
            segmented_button_selected_color=C["accent"],
            segmented_button_unselected_hover_color=C["hover"],
            text_color=C["txt"]); tabs.pack(fill="both",expand=True)
        tabs.add("📋 قائمة الأدوية"); tabs.add("➕ إضافة / تعديل"); tabs.add("⚠ تنبيهات")
        self._inv_tabs=tabs
        self._build_inv_list(tabs.tab("📋 قائمة الأدوية"))
        self._build_inv_form(tabs.tab("➕ إضافة / تعديل"))
        self._build_inv_alerts(tabs.tab("⚠ تنبيهات"))

    def _build_inv_list(self,parent):
        tb=ctk.CTkFrame(parent,fg_color="transparent"); tb.pack(fill="x",pady=8,padx=8)
        self._inv_q=self._ent(tb,"ابحث...",250); self._inv_q.pack(side="right",padx=4)
        self._inv_q.bind("<KeyRelease>",self._inv_key_rel)
        self._inv_q.bind("<Return>",self._inv_scan_enter)
        self._inv_scan_btn=ctk.CTkButton(tb,text="📷",width=42,height=42,
            font=("Arial",16),fg_color=C["card"],hover_color=C["hover"],
            text_color=C["txt_s"],corner_radius=8,command=lambda:self._inv_scan_click())
        self._inv_scan_btn.pack(side="right",padx=(0,4))
        cats=["الكل"]+[r["name"] for r in self.db.q("SELECT name FROM categories ORDER BY name")]
        self._inv_cf=self._combo(tb,cats,160); self._inv_cf.pack(side="right",padx=4)
        self._inv_cf.configure(command=lambda _:self._inv_load())
        self._btn(tb,"🏷 باركود",self._inv_print_barcode,C["purple"],90).pack(side="left",padx=3)
        self._btn(tb,"📦 دفعات",self._inv_batches_dlg,C["teal"],90).pack(side="left",padx=3)
        if can(self.user,"delete"):
            self._btn(tb,"🗑 حذف",self._inv_delete,C["danger"],90).pack(side="left",padx=3)
        self._btn(tb,"✏ تعديل",self._inv_edit,C["warning"],100).pack(side="left",padx=3)
        self._btn(tb,"🔄 تحديث",self._inv_load,C["surface"],90).pack(side="left",padx=3)
        tf,self._inv_tv=self._tree(parent,
            ("barcode","name","cat","buy","sell","strip","stock","min","expiry"),
            ("الباركود","الاسم","الفئة","شراء","بيع","ش/عبوة","مخزون","أدنى","الانتهاء"))
        tf.pack(fill="both",expand=True,padx=8,pady=(0,2))
        # Pagination controls
        self._inv_pg_f=ctk.CTkFrame(parent,fg_color="transparent")
        self._inv_pg_f.pack(fill="x",padx=8,pady=(0,8))
        self._inv_pg_lbl=ctk.CTkLabel(self._inv_pg_f,text="",font=(FONT,_fs(11)),text_color=C["txt_s"])
        self._inv_pg_lbl.pack(side="left",padx=6)
        self._inv_pg_prev=ctk.CTkButton(self._inv_pg_f,text="◀ السابق",width=90,height=32,
            command=self._inv_prev_page,font=(FONT,_fs(11)),fg_color=C["surface"],
            hover_color=C["hover"],text_color=C["txt"])
        self._inv_pg_prev.pack(side="right",padx=3)
        self._inv_pg_next=ctk.CTkButton(self._inv_pg_f,text="التالي ▶",width=90,height=32,
            command=self._inv_next_page,font=(FONT,_fs(11)),fg_color=C["surface"],
            hover_color=C["hover"],text_color=C["txt"])
        self._inv_pg_next.pack(side="right",padx=3)
        self._inv_page=0; self._inv_total=0
        self._inv_tv.tag_configure("low",background="#2d1f0a",foreground="#f59e0b")
        self._inv_tv.tag_configure("expired",background="#2d0a0a",foreground="#ef4444")
        self._inv_load()

    def _inv_key_rel(self,ev=None):
        self._inv_load()

    def _inv_scan_enter(self,ev=None):
        q=self._inv_q.get().strip()
        if not q: return
        med=self.db.q1("SELECT * FROM medicines WHERE barcode=? AND is_active=1",(q,))
        if med:
            Toast.show(self,f"✓ {med['name']}","success",1500)
            self._inv_edit_id(med)
        else:
            if messagebox.askyesno("منتج جديد",f"الباركود '{q}' غير موجود.\nهل تريد إضافة منتج جديد بهذا الباركود؟"):
                self._inv_tabs.set("➕ إضافة / تعديل")
                self._inv_clear()
                self._if["barcode"].delete(0,"end"); self._if["barcode"].insert(0,q)
                self._form_hdr.configure(text="📷 إضافة من المسح",text_color=C["accent"])
        self._inv_q.delete(0,"end")

    def _inv_scan_click(self):
        q=simpledialog.askstring("مسح باركود","امسح الباركود أو أدخل الرقم:",parent=self)
        if q: self._inv_q.delete(0,"end"); self._inv_q.insert(0,q); self._inv_scan_enter()

    def _inv_load(self):
        try:
            for r in self._inv_tv.get_children(): self._inv_tv.delete(r)
            q=self._inv_q.get().strip(); cf=self._inv_cf.get()
            if getattr(self,"_inv_last_q",None)!=q or getattr(self,"_inv_last_cf",None)!=cf:
                self._inv_page=0; self._inv_last_q=q; self._inv_last_cf=cf
            ps=50
            base="""SELECT m.id,m.barcode,m.name,c.name cat,
                          m.buy_price,m.sell_price,m.strip_price,m.stock,m.min_stock,m.expiry,
                          m.strips_per_box,m.sell_by_strip
                   FROM medicines m LEFT JOIN categories c ON m.category_id=c.id
                   WHERE m.is_active=1"""
            p=[]
            if q: base+=" AND (m.name LIKE ? OR m.barcode LIKE ? OR m.generic_name LIKE ? OR m.manufacturer LIKE ?)"; p+=[f"%{q}%",f"%{q}%",f"%{q}%",f"%{q}%"]
            if cf and cf!="الكل": base+=" AND c.name=?"; p.append(cf)
            cnt=self.db.q1(f"SELECT COUNT(*) c FROM ({base}) sub",p) or {}
            self._inv_total=cnt.get("c") or 0
            base+=" ORDER BY m.name LIMIT ? OFFSET ?"
            p+=[ps,self._inv_page*ps]
            today=datetime.now().strftime("%Y-%m-%d")
            for r in self.db.q(base,p):
                tag="normal"
                if r["stock"]<=r["min_stock"]: tag="low"
                if r["expiry"] and r["expiry"]<=today: tag="expired"
                sp=r.get("strip_price") or 0
                spb=r.get("strips_per_box") or 1; sbs=r.get("sell_by_strip") or 0
                if sbs and spb>1:
                    boxes=r["stock"]//spb; strips=r["stock"]%spb
                    stk_str=f"{boxes}عب +{strips}ش"
                else:
                    stk_str=str(r["stock"])
                self._inv_tv.insert("","end",iid=r["id"],tags=(tag,),
                    values=(r["barcode"] or "",r["name"],r["cat"] or "",
                        f"{r['buy_price']:.2f}",f"{r['sell_price']:.2f}",
                        f"{sp:.2f}" if sp else "—",
                        stk_str,r["min_stock"],r["expiry"] or ""))
            tp=max(1,self._inv_total)
            pg=max(1,self._inv_page+1); mx=(tp+ps-1)//ps
            self._inv_pg_lbl.configure(text=f"الصفحة {pg} من {mx} | {tp} منتج")
            self._inv_pg_prev.configure(state="normal" if self._inv_page>0 else "disabled")
            self._inv_pg_next.configure(state="normal" if self._inv_page<mx-1 else "disabled")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            Toast.show(self,f"خطأ تحميل المخزن: {ex}","error",8000)

    def _inv_prev_page(self):
        if self._inv_page>0: self._inv_page-=1; self._inv_load()
    def _inv_next_page(self):
        mx=max(1,(self._inv_total+49)//50)
        if self._inv_page<mx-1: self._inv_page+=1; self._inv_load()

    def _inv_print_barcode(self):
        sel=self._inv_tv.selection()
        if not sel: Toast.show(self,"حدّد دواءً أولاً","warning"); return
        med=self.db.q1("SELECT * FROM medicines WHERE id=?",(sel[0],))
        if not med: return
        barcode=med.get("barcode","") or str(med["id"])
        try:
            import win32print
            prn=self.db.setting("thermal_printer","")
            if not prn: Toast.show(self,"اختر طابعة حرارية من الإعدادات أولاً","warning"); return
            data=b""
            data+=b"\x1d\x68\x64"  # GS h 100 (barcode height)
            data+=b"\x1d\x77\x02"  # GS w 2 (barcode width)
            bc=barcode.encode("utf-8")
            data+=b"\x1d\x6b\x49"+bytes([len(bc)])+bc  # GS k m d1...dn (CODE128)
            data+=b"\n\n\n"
            data+=b"\x1d\x56\x42\x00"  # Cut
            h=win32print.OpenPrinter(prn)
            try:
                win32print.StartDocPrinter(h,1,(f"barcode_{barcode}",None,"RAW"))
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h,data)
                win32print.EndPagePrinter(h); win32print.EndDocPrinter(h)
                Toast.show(self,f"✓ تمت طباعة باركود {barcode}","success",2000)
            finally: win32print.ClosePrinter(h)
        except Exception as e: Toast.show(self,f"خطأ طباعة الباركود: {e}","error",4000)

    def _inv_delete(self):
        sel=self._inv_tv.selection()
        if not sel: Toast.show(self,"حدّد دواءً أولاً","warning"); return
        med=self.db.q1("SELECT name FROM medicines WHERE id=?",(sel[0],))
        if med and messagebox.askyesno("تأكيد الحذف",f"هل تريد حذف '{med['name']}'؟"):
            self.db.run("UPDATE medicines SET is_active=0 WHERE id=?",(sel[0],))
            self.db.log(self.user["id"],"DEL_MED",med["name"])
            Toast.show(self,f"تم حذف {med['name']}","success"); self._inv_load(); self._emit("inventory_changed")

    def _inv_batches_dlg(self):
        sel=self._inv_tv.selection()
        if not sel: Toast.show(self,"حدّد دواءً أولاً","warning"); return
        med=self.db.q1("SELECT * FROM medicines WHERE id=?",(sel[0],))
        if not med: return
        dlg=ctk.CTkToplevel(self); dlg.title(f"دفعات — {med['name']}")
        dlg.geometry("500x520"); dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks()
        sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"500x520+{(sw-500)//2}+{(sh-520)//2}")
        ctk.CTkLabel(dlg,text=f"📦  دفعات {med['name']}",
            font=(FONT,_fs(17),"bold"),text_color=C["teal"]).pack(pady=14)
        # Batch table
        tf=ctk.CTkFrame(dlg,fg_color=C["card"]); tf.pack(fill="both",expand=True,padx=12,pady=6)
        cols=("qty","buy","expiry","date")
        hdrs=("الكمية (شريط)","سعر الشراء","تاريخ الصلاحية","تاريخ الإضافة")
        tv=ttk.Treeview(tf,columns=cols,show="headings",height=8,selectmode="browse")
        for c,h in zip(cols,hdrs):
            tv.heading(c,text=h); tv.column(c,width=100,anchor="e")
        tv.pack(fill="both",expand=True,side="right")
        scr=ttk.Scrollbar(tf,orient="vertical",command=tv.yview)
        scr.pack(side="left",fill="y"); tv.configure(yscrollcommand=scr.set)
        def load():
            for r in tv.get_children(): tv.delete(r)
            for b in self.db.q("SELECT * FROM batches WHERE medicine_id=? ORDER BY expiry",(med["id"],)):
                tv.insert("","end",values=(b["quantity_strips"],f"{b['buy_price']:.2f}",b["expiry"] or "-",b["created_at"][:10]))
        load()
        # Add batch form
        af=ctk.CTkFrame(dlg,fg_color="transparent"); af.pack(fill="x",padx=12,pady=12)
        ctk.CTkLabel(af,text="إضافة كمية:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        afi=ctk.CTkFrame(af,fg_color="transparent"); afi.pack(anchor="e")
        b_qty=ctk.CTkEntry(afi,width=80,height=36,justify="right",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"]); b_qty.pack(side="right",padx=2)
        ctk.CTkLabel(afi,text="شريط",font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(side="right",padx=2)
        b_exp=ctk.CTkEntry(afi,width=120,height=36,justify="right",placeholder_text="YYYY-MM-DD",
            font=(FONT,_fs(12)),fg_color=C["inp"],text_color=C["txt"]); b_exp.pack(side="right",padx=2)
        b_buy=ctk.CTkEntry(afi,width=80,height=36,justify="right",placeholder_text="سعر ش",
            font=(FONT,_fs(12)),fg_color=C["inp"],text_color=C["txt"]); b_buy.pack(side="right",padx=2)
        def add_batch():
            try:
                q=int(b_qty.get().strip())
                if q<=0: raise ValueError
            except: Toast.show(self,"كمية صحيحة (عدد صحيح)","error"); return
            exp=b_exp.get().strip() or None
            bp=b_buy.get().strip() or "0"
            try: bp_f=float(bp)
            except: bp_f=0.0
            self.db.run("INSERT INTO batches(medicine_id,quantity_strips,buy_price,expiry) VALUES(?,?,?,?)",
                (med["id"],q,bp_f,exp))
            self.db.run("UPDATE medicines SET stock=stock+?,buy_price=? WHERE id=?",
                (q,bp_f,med["id"]))
            self.db.log(self.user["id"],"ADD_BATCH",f"{med['name']}: +{q}")
            Toast.show(self,f"✓ تمت إضافة {q} شريط","success")
            b_qty.delete(0,"end"); b_exp.delete(0,"end"); b_buy.delete(0,"end")
            load(); self._inv_load(); self._emit("inventory_changed")
        self._btn(af,"➕ إضافة",add_batch,C["success"],120,40).pack(anchor="e",pady=4)
        ctk.CTkLabel(dlg,text="💡 البيع يتم بأقدم تاريخ صلاحية أولاً (FIFO)",
            font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(anchor="e",padx=14)

    def _inv_edit(self):
        sel=self._inv_tv.selection()
        if not sel: Toast.show(self,"حدّد دواءً أولاً","warning"); return
        med=self.db.q1("SELECT * FROM medicines WHERE id=?",(sel[0],))
        if med: self._inv_edit_id(med)

    def _inv_edit_id(self,med):
        self._inv_tabs.set("➕ إضافة / تعديل"); self._edit_id=med["id"]
        sbs=med.get("sell_by_strip") or 0; spb=med.get("strips_per_box") or 1
        mig=med.get("stock_migrated") or 0
        if sbs and spb>1 and mig:
            display_stock=med["stock"]//spb
        else:
            display_stock=med["stock"]
        mp={"barcode":med["barcode"] or "","name":med["name"],
            "generic_name":med["generic_name"] or "","manufacturer":med["manufacturer"] or "",
            "buy_price":str(med["buy_price"]),"sell_price":str(med["sell_price"]),
            "stock":str(display_stock),"min_stock":str(med["min_stock"]),
            "unit":med["unit"] or "قطعة","location":med["location"] or "",
            "strip_price":str(med.get("strip_price") or ""),
            "strips_per_box":str(spb),
            "price_wholesale":str(med.get("price_wholesale") or ""),
            "price_distributor":str(med.get("price_distributor") or "")}
        for k,v in mp.items():
            self._if[k].delete(0,"end"); self._if[k].insert(0,v)
        self._sell_by_strip_var.set(1 if med.get("sell_by_strip") else 0)
        self._inv_notes.delete("1.0","end")
        if med["notes"]: self._inv_notes.insert("1.0",med["notes"])
        if med["category_id"]:
            cat=self.db.q1("SELECT name FROM categories WHERE id=?",(med["category_id"],))
            if cat: self._inv_cat_cb.set(cat["name"])
        img_p=med.get("image_path","") or ""
        if img_p and os.path.exists(img_p):
            self._inv_img_path=img_p
            try:
                from PIL import Image
                img=ctk.CTkImage(Image.open(img_p),size=(60,60))
                self._inv_img_preview.configure(image=img,text="")
            except Exception as _ex: print(f"[IMG] {_ex}")
        self._form_hdr.configure(text="✏  تعديل بيانات الدواء",text_color=C["warning"])

    def _build_inv_form(self,parent):
        sc=ctk.CTkScrollableFrame(parent,fg_color="transparent"); sc.pack(fill="both",expand=True)
        self._form_hdr=ctk.CTkLabel(sc,text="➕  إضافة دواء جديد",font=(FONT,_fs(17),"bold"),text_color=C["success"])
        self._form_hdr.pack(anchor="e",padx=16,pady=(12,6))
        grid=ctk.CTkFrame(sc,fg_color="transparent"); grid.pack(fill="x",padx=16)
        grid.columnconfigure(0,weight=1); grid.columnconfigure(1,weight=1)
        self._if={}
        for key,label,row,col in [
            ("barcode","الباركود",0,0),("name","اسم الدواء  *",0,1),
            ("generic_name","الاسم العلمي",1,0),("manufacturer","الشركة المنتجة",1,1),
            ("buy_price","سعر الشراء",2,0),            ("sell_price","سعر البيع  *",2,1),
            ("stock","عدد العلب / القطع  *",3,0),("min_stock","الحد الأدنى للتنبيه",3,1),
            ("unit","وحدة القياس",4,0),("location","موقع التخزين",4,1),
        ]:
            w=ctk.CTkFrame(grid,fg_color="transparent"); w.grid(row=row,column=col,padx=8,pady=5,sticky="ew")
            ctk.CTkLabel(w,text=label,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
            e=self._ent(w,label,280); e.pack(fill="x"); self._if[key]=e
        # Category
        cw=ctk.CTkFrame(grid,fg_color="transparent"); cw.grid(row=5,column=0,padx=8,pady=5,sticky="ew")
        ctk.CTkLabel(cw,text="الفئة",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        cats=[r["name"] for r in self.db.q("SELECT name FROM categories ORDER BY name")]
        self._inv_cat_cb=self._combo(cw,cats,280); self._inv_cat_cb.pack(fill="x")
        # Expiry
        ew=ctk.CTkFrame(grid,fg_color="transparent"); ew.grid(row=5,column=1,padx=8,pady=5,sticky="ew")
        ctk.CTkLabel(ew,text="تاريخ الانتهاء (YYYY-MM-DD)",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        if HAS_CAL:
            self._inv_exp=DateEntry(ew,width=20,background="darkblue",foreground="white",
                borderwidth=2,date_pattern="yyyy-mm-dd"); self._inv_exp.pack(fill="x",ipady=8)
        else:
            self._inv_exp=self._ent(ew,"YYYY-MM-DD",280); self._inv_exp.pack(fill="x")
        # سعر الشريط (بليستر)
        sw=ctk.CTkFrame(grid,fg_color="transparent"); sw.grid(row=6,column=0,padx=8,pady=5,sticky="ew")
        self._sell_by_strip_var=ctk.IntVar(value=0)
        self._sell_by_strip_cb=ctk.CTkCheckBox(sw,text="يُباع بالشرطة (بليستر)",
            variable=self._sell_by_strip_var,font=(FONT,_fs(12)),text_color=C["txt"],
            fg_color=C["accent"],hover_color=C["acc_h"])
        self._sell_by_strip_cb.pack(anchor="e")
        sw2=ctk.CTkFrame(grid,fg_color="transparent"); sw2.grid(row=6,column=1,padx=8,pady=5,sticky="ew")
        ctk.CTkLabel(sw2,text="سعر الشريط:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self._if["strip_price"]=self._ent(sw2,"سعر الشريط (0 = لا يُباع)",280)
        self._if["strip_price"].pack(fill="x")
        # Multiple pricing (جملة/موزع)
        sw4=ctk.CTkFrame(grid,fg_color="transparent"); sw4.grid(row=7,column=0,padx=8,pady=5,sticky="ew")
        ctk.CTkLabel(sw4,text="سعر الجملة:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self._if["price_wholesale"]=self._ent(sw4,"سعر الجملة (0 = نفس البيع)",280)
        self._if["price_wholesale"].pack(fill="x")
        sw5=ctk.CTkFrame(grid,fg_color="transparent"); sw5.grid(row=7,column=1,padx=8,pady=5,sticky="ew")
        ctk.CTkLabel(sw5,text="سعر الموزع:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self._if["price_distributor"]=self._ent(sw5,"سعر الموزع (0 = نفس الجملة)",280)
        self._if["price_distributor"].pack(fill="x")
        sw3=ctk.CTkFrame(grid,fg_color="transparent"); sw3.grid(row=8,column=0,padx=8,pady=5,sticky="ew")
        ctk.CTkLabel(sw3,text="عدد الشرائط في العبوة:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self._if["strips_per_box"]=self._ent(sw3,"10",280)
        self._if["strips_per_box"].pack(fill="x")
        ctk.CTkLabel(sw3,text="💡 يتم حساب سعر الشريط تلقائياً = سعر العبوة ÷ عدد الشرائط",
            font=(FONT,_fs(9)),text_color=C["txt_m"]).pack(anchor="e")
        def _auto_strip_price(*_):
            try: spb_v=int(self._if["strips_per_box"].get() or 0); sp_v=float(self._if["sell_price"].get() or 0)
            except: return
            if spb_v>0 and sp_v>0:
                self._if["strip_price"].delete(0,"end"); self._if["strip_price"].insert(0,f"{sp_v/spb_v:.2f}")
        self._if["strips_per_box"].bind("<KeyRelease>",_auto_strip_price)
        self._if["sell_price"].bind("<KeyRelease>",_auto_strip_price)
        # صورة المنتج
        imw=ctk.CTkFrame(sc,fg_color="transparent"); imw.pack(fill="x",padx=16,pady=8)
        ctk.CTkLabel(imw,text="صورة المنتج:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e")
        self._inv_img_preview=ctk.CTkLabel(imw,text="",width=60,height=60,corner_radius=8,
            fg_color=C["card"])
        self._inv_img_preview.pack(anchor="e",pady=4)
        self._inv_img_path=""
        self._btn(imw,"🖼 اختيار صورة",self._inv_pick_img,C["surface"],160,34).pack(anchor="e")
        ctk.CTkLabel(sc,text="ملاحظات",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=16,pady=(8,2))
        self._inv_notes=ctk.CTkTextbox(sc,height=76,font=(FONT,_fs(12)),fg_color=C["inp"],text_color=C["txt"])
        self._inv_notes.pack(fill="x",padx=16)
        self._edit_id=None
        bf=ctk.CTkFrame(sc,fg_color="transparent"); bf.pack(pady=14,padx=16,anchor="e")
        self._btn(bf,"💾 حفظ الدواء",self._inv_save,C["success"],160,46).pack(side="right",padx=4)
        self._btn(bf,"🔄 مسح النموذج",self._inv_clear,C["warning"],140,46).pack(side="right",padx=4)

    def _inv_pick_img(self):
        p=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.gif")])
        if p:
            self._inv_img_path=p
            try:
                from PIL import Image
                img=ctk.CTkImage(Image.open(p),size=(60,60))
                self._inv_img_preview.configure(image=img,text="")
            except:
                self._inv_img_preview.configure(text="✓",image="")

    def _inv_save(self):
        name=self._if["name"].get().strip(); sell=self._if["sell_price"].get().strip(); stk=self._if["stock"].get().strip()
        errs=[]
        if not name: errs.append("اسم الدواء")
        try:    sf=float(sell)
        except: sf=None; errs.append("سعر البيع")
        try:    si=int(stk)
        except: si=None; errs.append("الكمية")
        if errs: Toast.show(self,"حقول مطلوبة: "+"، ".join(errs),"error"); return
        cat=self.db.q1("SELECT id FROM categories WHERE name=?",(self._inv_cat_cb.get(),))
        cat_id=cat["id"] if cat else None
        try:    buy=float(self._if["buy_price"].get() or 0)
        except: buy=0.0
        try:    mins=int(self._if["min_stock"].get() or 5)
        except: mins=5
        expiry=(self._inv_exp.get() if HAS_CAL else self._inv_exp.get().strip()) or None
        strip_p=self._sell_by_strip_var.get()
        try:    sp=float(self._if["strip_price"].get() or 0)
        except: sp=0.0
        try:    spb=int(self._if["strips_per_box"].get() or 1)
        except: spb=1
        try:    pw=float(self._if["price_wholesale"].get() or 0)
        except: pw=0.0
        try:    pd=float(self._if["price_distributor"].get() or 0)
        except: pd=0.0
        # Auto-calc strip_price if empty
        if strip_p and sp<=0 and sf>0 and spb>0: sp=sf/spb
        # Convert stock from boxes to strips when selling by strip
        if strip_p and spb>1: si=si*spb
        data=(self._if["barcode"].get().strip() or None,name,cat_id,
            self._if["generic_name"].get().strip(),self._if["manufacturer"].get().strip(),
            buy,sf,si,mins,self._if["unit"].get().strip() or "قطعة",expiry,
            self._if["location"].get().strip(),self._inv_notes.get("1.0","end").strip(),
            sp,strip_p,spb,self._inv_img_path or None,pw,pd)
        try:
            if self._edit_id:
                self.db.run("UPDATE medicines SET barcode=?,name=?,category_id=?,generic_name=?,"
                    "manufacturer=?,buy_price=?,sell_price=?,stock=?,min_stock=?,unit=?,"
                    "expiry=?,location=?,notes=?,strip_price=?,sell_by_strip=?,strips_per_box=?,"
                    "image_path=?,price_wholesale=?,price_distributor=?,stock_migrated=1,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    data+(self._edit_id,))
                self.db.log(self.user["id"],"UPD_MED",name)
                Toast.show(self,f"✓ تم تعديل {name}","success")
            else:
                new_id=self.db.run("INSERT INTO medicines(barcode,name,category_id,generic_name,"
                    "manufacturer,buy_price,sell_price,stock,min_stock,unit,expiry,location,notes,"
                    "strip_price,sell_by_strip,strips_per_box,image_path,price_wholesale,price_distributor,stock_migrated)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",data)
                # Create initial batch if stock > 0
                if si>0:
                    self.db.run("INSERT INTO batches(medicine_id,quantity_strips,buy_price,expiry) VALUES(?,?,?,?)",
                        (new_id,si,buy,expiry))
                self.db.log(self.user["id"],"ADD_MED",name)
                Toast.show(self,f"✓ تمت إضافة {name}","success")
            self._inv_clear(); self._inv_load(); self._inv_tabs.set("📋 قائمة الأدوية")
            self._emit("inventory_changed")
        except sqlite3.IntegrityError as ex:
            Toast.show(self,"الباركود مستخدم مسبقاً" if "barcode" in str(ex) else f"خطأ: {ex}","error")

    def _inv_clear(self):
        for e in self._if.values(): e.delete(0,"end")
        self._if["strips_per_box"].delete(0,"end"); self._if["strips_per_box"].insert(0,"1")
        self._inv_notes.delete("1.0","end"); self._edit_id=None
        self._sell_by_strip_var.set(0)
        self._inv_img_path=""; self._inv_img_preview.configure(image="",text="")
        self._form_hdr.configure(text="➕  إضافة دواء جديد",text_color=C["success"])

    def _build_inv_alerts(self,parent):
        tf,tv=self._tree(parent,("name","stock","min","expiry","reason"),
            ("الدواء","المخزون","الأدنى","الانتهاء","السبب"))
        tf.pack(fill="both",expand=True,padx=8,pady=8)
        tv.tag_configure("low",background="#2d1f0a",foreground="#f59e0b")
        tv.tag_configure("exp",background="#2d0a0a",foreground="#ef4444")
        for r in self.db.q("SELECT name,stock,min_stock,expiry FROM medicines WHERE stock<=min_stock AND is_active=1"):
            tv.insert("","end",tags=("low",),values=(r["name"],r["stock"],r["min_stock"],r["expiry"] or "-","نقص مخزون"))
        lim=(datetime.now()+timedelta(days=60)).strftime("%Y-%m-%d")
        for r in self.db.q("SELECT name,stock,expiry FROM medicines WHERE expiry<=? AND is_active=1",(lim,)):
            tv.insert("","end",tags=("exp",),values=(r["name"],r["stock"],"-",r["expiry"] or "-","قرب الانتهاء"))

    # ═══════════════════════════════════════
    #  LEDGER
    # ═══════════════════════════════════════
    def _pg_ledger(self):
        if not can(self.user,"ledger"):
            ctk.CTkLabel(self.cont,text="⛔  لا تملك صلاحية الوصول للخزينة",
                font=(FONT,_fs(18),"bold"),text_color=C["danger"]).pack(expand=True); return
        cur=self.db.setting("currency","SDG"); today=datetime.now().strftime("%Y-%m-%d")
        def _s(sql,p=()): return (self.db.q1(sql,p) or {}).get("s",0) or 0
        ti=_s("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='IN'")
        to=_s("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='OUT'")
        di=_s("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='IN' AND date(created_at)=?",(today,))
        do_=_s("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='OUT' AND date(created_at)=?",(today,))
        bal=ti-to; net=di-do_

        kpi=ctk.CTkFrame(self.cont,fg_color="transparent"); kpi.pack(fill="x",pady=(0,12))
        for i in range(4): kpi.columnconfigure(i,weight=1)
        self._card(kpi,"الرصيد الكلي",f"{bal:,.2f} {cur}","إجمالي الصندوق",
            C["success"] if bal>=0 else C["danger"],"🏦",0,3)
        self._card(kpi,"مداخيل اليوم",f"{di:,.2f} {cur}","مبيعات + إيرادات",C["success"],"📈",0,2)
        self._card(kpi,"مصاريف اليوم",f"{do_:,.2f} {cur}","مصروفات",C["danger"],"📉",0,1)
        self._card(kpi,"صافي اليوم",f"{net:,.2f} {cur}","ربح / خسارة",
            C["accent"] if net>=0 else C["warning"],"💹",0,0)

        low=ctk.CTkFrame(self.cont,fg_color="transparent"); low.pack(fill="both",expand=True)
        low.columnconfigure(0,weight=1); low.columnconfigure(1,weight=2); low.rowconfigure(0,weight=1)

        fp=ctk.CTkFrame(low,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        fp.grid(row=0,column=0,sticky="nsew",padx=(0,8))
        ctk.CTkLabel(fp,text="إضافة قيد مالي",font=(FONT,_fs(15),"bold"),text_color=C["txt"]).pack(anchor="e",padx=14,pady=12)
        def _l(txt): ctk.CTkLabel(fp,text=txt,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=14,pady=(8,2))
        _l("نوع القيد:")
        self._lt=self._combo(fp,["IN — إيراد","OUT — مصروف"],240); self._lt.pack(anchor="e",padx=14)
        _l("المبلغ:")
        self._la=self._ent(fp,"0.00",240); self._la.pack(anchor="e",padx=14)
        _l("التصنيف:")
        self._lc=self._combo(fp,["مبيعات","مشتريات","رواتب","إيجار","كهرباء","صيانة","مصروفات متنوعة","أخرى"],240)
        self._lc.pack(anchor="e",padx=14)
        _l("الوصف:")
        self._ld=self._ent(fp,"تفاصيل العملية",240); self._ld.pack(anchor="e",padx=14)
        self._btn(fp,"➕ إضافة القيد",self._led_add,C["success"],210,46).pack(pady=20)

        tp=ctk.CTkFrame(low,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        tp.grid(row=0,column=1,sticky="nsew",padx=(8,0))
        ctk.CTkLabel(tp,text="سجل العمليات المالية",font=(FONT,_fs(14),"bold"),text_color=C["txt"]).pack(anchor="e",padx=14,pady=10)
        tf,self._ltv=self._tree(tp,("date","type","cat","amount","desc"),("التاريخ","النوع","التصنيف","المبلغ","الوصف"))
        tf.pack(fill="both",expand=True,padx=10,pady=(0,10))
        self._ltv.tag_configure("IN",foreground=C["success"]); self._ltv.tag_configure("OUT",foreground=C["danger"])
        self._led_load()

    def _led_add(self):
        raw=self._lt.get(); t="IN" if "IN" in raw else "OUT"
        try:    amt=float(self._la.get());    assert amt>0
        except: Toast.show(self,"أدخل مبلغاً صحيحاً أكبر من صفر","error"); return
        self.db.run("INSERT INTO ledger(type,amount,category,description,user_id) VALUES(?,?,?,?,?)",
            (t,amt,self._lc.get(),self._ld.get().strip(),self.user["id"]))
        self.db.log(self.user["id"],f"LEDGER_{t}",str(amt))
        Toast.show(self,"✓ تم تسجيل القيد","success")
        self._la.delete(0,"end"); self._ld.delete(0,"end")
        self._led_load(); self._pg_ledger()

    def _led_load(self):
        for r in self._ltv.get_children(): self._ltv.delete(r)
        for r in self.db.q("SELECT type,category,amount,description,created_at FROM ledger ORDER BY id DESC LIMIT 150"):
            self._ltv.insert("","end",tags=(r["type"],),values=(
                r["created_at"][:16] if r["created_at"] else "",
                "إيراد ✓" if r["type"]=="IN" else "مصروف ✗",
                r["category"],f"{r['amount']:,.2f}",r["description"] or ""))

    # ═══════════════════════════════════════
    #  REPORTS  (صافي الربح الصحيح)
    # ═══════════════════════════════════════
    def _pg_reports(self):
        if not can(self.user,"reports"):
            ctk.CTkLabel(self.cont,text="⛔  لا تملك صلاحية الوصول للتقارير",
                font=(FONT,_fs(18),"bold"),text_color=C["danger"]).pack(expand=True); return
        ctrl=ctk.CTkFrame(self.cont,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        ctrl.pack(fill="x",pady=(0,10))
        ci=ctk.CTkFrame(ctrl,fg_color="transparent"); ci.pack(padx=14,pady=12)
        ctk.CTkLabel(ci,text="من:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=4)
        self._rf=self._ent(ci,"YYYY-MM-DD",130); self._rf.pack(side="right",padx=4)
        self._rf.insert(0,(datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d"))
        ctk.CTkLabel(ci,text="إلى:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=4)
        self._rt=self._ent(ci,"YYYY-MM-DD",130); self._rt.pack(side="right",padx=4)
        self._rt.insert(0,datetime.now().strftime("%Y-%m-%d"))
        self._btn(ci,"📥 PDF",self._rep_export_pdf,C["danger"]).pack(side="right",padx=4)
        self._btn(ci,"📥 Excel",self._rep_export_xlsx,C["success"]).pack(side="right",padx=4)
        self._btn(ci,"📋 X تقرير",self._rep_x_report,C["purple"]).pack(side="right",padx=4)
        self._btn(ci,"📋 Z إغلاق اليوم",self._rep_z_report,C["warning"]).pack(side="right",padx=4)
        self._btn(ci,"🔍 تحديث",self._rep_load,C["accent"]).pack(side="right",padx=10)

        self._rep_kpi=ctk.CTkFrame(self.cont,fg_color="transparent")
        self._rep_kpi.pack(fill="x",pady=6)
        for i in range(4): self._rep_kpi.columnconfigure(i,weight=1)

        # ── Chart ──
        ch=ctk.CTkFrame(self.cont,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        ch.pack(fill="x",pady=6)
        ch_top=ctk.CTkFrame(ch,fg_color="transparent"); ch_top.pack(fill="x",padx=14,pady=6)
        ctk.CTkLabel(ch_top,text="📊 المبيعات اليومية",font=(FONT,_fs(14),"bold"),text_color=C["txt"]).pack(side="right")
        self._ch_btn=ctk.CTkButton(ch_top,text="🔽 إخفاء",command=self._rep_toggle_chart,
            width=70,height=24,font=(FONT,_fs(10)),fg_color=C["border"],hover_color=C["inp_b"],text_color=C["txt"])
        self._ch_btn.pack(side="left")
        self._rep_chart_frame=ctk.CTkFrame(ch,fg_color="transparent")
        self._rep_chart_frame.pack(fill="x",padx=14,pady=(0,10))
        self._rep_canvas=tk.Canvas(self._rep_chart_frame,height=110,bg="#ffffff",highlightthickness=0)
        self._rep_canvas.pack(fill="x")

        trow=ctk.CTkFrame(self.cont,fg_color="transparent"); trow.pack(fill="both",expand=True)
        trow.columnconfigure(0,weight=1); trow.columnconfigure(1,weight=1); trow.rowconfigure(0,weight=1)

        lp=ctk.CTkFrame(trow,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        lp.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        ctk.CTkLabel(lp,text="الأدوية الأكثر مبيعاً",font=(FONT,_fs(14),"bold"),text_color=C["txt"]).pack(anchor="e",padx=14,pady=10)
        tf1,self._top=self._tree(lp,("name","qty","revenue","profit"),("الدواء","الكمية","الإيراد","الربح"),
            widths=(200,70,120,100))
        tf1.pack(fill="both",expand=True,padx=8,pady=(0,8))

        rp2=ctk.CTkFrame(trow,fg_color=C["card"],corner_radius=12,border_width=1,border_color=C["border"])
        rp2.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        ctk.CTkLabel(rp2,text="توزيع طرق الدفع+الآجل",font=(FONT,_fs(14),"bold"),text_color=C["txt"]).pack(anchor="e",padx=14,pady=10)
        tf2,self._pay_tv=self._tree(rp2,("method","count","total"),("الطريقة","العدد","الإجمالي"),
            widths=(130,70,120))
        tf2.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self._rep_load()

    def _rep_toggle_chart(self):
        if self._rep_chart_frame.winfo_viewable():
            self._rep_chart_frame.pack_forget()
            self._ch_btn.configure(text="🔼 إظهار")
        else:
            self._rep_chart_frame.pack(fill="x",padx=14,pady=(0,10))
            self._ch_btn.configure(text="🔽 إخفاء")

    def _rep_load(self):
        fd=self._rf.get().strip(); td=self._rt.get().strip()
        cur=self.db.setting("currency","SDG")
        for w in self._rep_kpi.winfo_children(): w.destroy()

        # استبعاد الآجل المعلق
        r=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales"
            " WHERE (credit_status IS NULL OR credit_status!='pending')"
            " AND date(created_at) BETWEEN ? AND ?",(fd,td)) or {}
        ts=r.get("s") or 0; tc=r.get("c") or 0

        # صافي الربح الحقيقي = مبيعات - تكلفة البضاعة المباعة
        cogs=self.db.q1("""SELECT COALESCE(SUM(si.buy_price*si.quantity),0) s
            FROM sale_items si JOIN sales s ON si.sale_id=s.id
            WHERE (s.credit_status IS NULL OR s.credit_status!='pending')
            AND date(s.created_at) BETWEEN ? AND ?""",(fd,td)) or {}
        total_cogs=cogs.get("s") or 0
        gross_profit=ts-total_cogs

        # صافي الربح = ربح إجمالي - المصاريف التشغيلية (ledger OUT غير المشتريات)
        op_exp=self.db.q1("""SELECT COALESCE(SUM(amount),0) s FROM ledger
            WHERE type='OUT' AND category NOT IN ('مشتريات')
            AND date(created_at) BETWEEN ? AND ?""",(fd,td)) or {}
        net_profit=gross_profit-(op_exp.get("s") or 0)

        qi=(self.db.q1("""SELECT COALESCE(SUM(si.quantity),0) q FROM sale_items si
            JOIN sales s ON si.sale_id=s.id
            WHERE (s.credit_status IS NULL OR s.credit_status!='pending')
            AND date(s.created_at) BETWEEN ? AND ?""",(fd,td)) or {}).get("q") or 0

        self._card(self._rep_kpi,"إجمالي المبيعات",f"{ts:,.2f} {cur}",f"{tc} فاتورة",C["success"],"💵",0,3)
        self._card(self._rep_kpi,"تكلفة البضاعة (COGS)",f"{total_cogs:,.2f} {cur}","سعر الشراء × الكميات",C["warning"],"🏷",0,2)
        self._card(self._rep_kpi,"إجمالي الربح",f"{gross_profit:,.2f} {cur}","مبيعات − تكلفة",
            C["success"] if gross_profit>=0 else C["danger"],"📈",0,1)
        self._card(self._rep_kpi,"صافي الربح",f"{net_profit:,.2f} {cur}","ربح إجمالي − مصاريف",
            C["teal"] if net_profit>=0 else C["danger"],"💹",0,0)

        # ── Draw chart bars ──
        self._rep_canvas.delete("all")
        daily=self.db.q("SELECT date(created_at) d,COALESCE(SUM(total),0) s FROM sales"
            " WHERE (credit_status IS NULL OR credit_status!='pending') AND date(created_at) BETWEEN ? AND ?"
            " GROUP BY d ORDER BY d",(fd,td))
        cw=self._rep_canvas.winfo_width() or 600
        if daily and cw>100:
            max_s=max(r["s"] for r in daily) or 1
            bar_w=max(8,min(40,(cw-80)//len(daily)))
            for i,r in enumerate(daily):
                x=60+i*bar_w
                h=min(85,int(r["s"]/max_s*80))
                color="#2563eb" if r["s"]>0 else "#e2e8f0"
                self._rep_canvas.create_rectangle(x,100-h,x+bar_w-2,98,fill=color,outline="",width=0)
                if bar_w>18:
                    lbl=r["d"][-5:] if r["d"] else ""
                    self._rep_canvas.create_text(x+bar_w//2-1,103,text=lbl,font=("Arial",7),anchor="n",fill="#64748b")

        for r in self._top.get_children(): self._top.delete(r)
        for r in self.db.q("""SELECT m.name,SUM(si.quantity) qty,SUM(si.total) rev,
                SUM((si.unit_price-si.buy_price)*si.quantity) profit
            FROM sale_items si JOIN medicines m ON si.medicine_id=m.id
            JOIN sales s ON si.sale_id=s.id
            WHERE (s.credit_status IS NULL OR s.credit_status!='pending')
            AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY m.id ORDER BY qty DESC LIMIT 14""",(fd,td)):
            self._top.insert("","end",values=(r["name"],r["qty"],f"{r['rev']:.2f}",
                f"{r['profit']:.2f}" if r["profit"] is not None else "0.00"))
        for r in self._pay_tv.get_children(): self._pay_tv.delete(r)
        for r in self.db.q("SELECT pay_method,COUNT(*) c,SUM(total) t FROM sales"
            " WHERE (credit_status IS NULL OR credit_status!='pending')"
            " AND date(created_at) BETWEEN ? AND ? GROUP BY pay_method",(fd,td)):
            self._pay_tv.insert("","end",values=(r["pay_method"],r["c"],f"{r['t']:.2f}"))

    def _rep_x_report(self):
        today=datetime.now().strftime("%Y-%m-%d")
        cur=self.db.setting("currency","SDG")
        data=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales"
            " WHERE (credit_status IS NULL OR credit_status!='pending') AND date(created_at)=?",(today,)) or {}
        ts=data.get("s") or 0; tc=data.get("c") or 0
        cogs=self.db.q1("SELECT COALESCE(SUM(si.buy_price*si.quantity),0) s FROM sale_items si"
            " JOIN sales s ON si.sale_id=s.id"
            " WHERE (s.credit_status IS NULL OR s.credit_status!='pending') AND date(s.created_at)=?",(today,)) or {}
        op_exp=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='OUT' AND date(created_at)=?",(today,)) or {}
        qi=self.db.q1("SELECT COALESCE(SUM(si.quantity),0) q FROM sale_items si JOIN sales s ON si.sale_id=s.id"
            " WHERE (s.credit_status IS NULL OR s.credit_status!='pending') AND date(s.created_at)=?",(today,)) or {}
        gross=ts-(cogs.get("s") or 0); net=gross-(op_exp.get("s") or 0)
        dlg=ctk.CTkToplevel(self); dlg.title(f"X تقرير — {today}")
        dlg.geometry("500x520"); dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks(); sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"500x520+{(sw-500)//2}+{(sh-520)//2}")
        sc=ctk.CTkScrollableFrame(dlg,fg_color=C["card"],corner_radius=12)
        sc.pack(fill="both",expand=True,padx=12,pady=12)
        ctk.CTkLabel(sc,text=f"📋  تقرير X",font=(FONT,_fs(18),"bold"),text_color=C["accent"]).pack(pady=10)
        ctk.CTkLabel(sc,text=f"التاريخ: {today}",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack()
        ctk.CTkFrame(sc,height=1,fg_color=C["border"]).pack(fill="x",padx=20,pady=10)
        items=[("💰 إجمالي المبيعات",f"{ts:,.2f} {cur}"),("🧾 عدد الفواتير",str(tc)),
               ("📦 العناصر المباعة",str(qi.get("q") or 0)),
               ("🏷 COGS (التكلفة)",f"{cogs.get('s') or 0:,.2f} {cur}"),
               ("📈 إجمالي الربح",f"{gross:,.2f} {cur}"),
               ("💸 المصروفات",f"{op_exp.get('s') or 0:,.2f} {cur}"),
               ("💹 صافي الربح",f"{net:,.2f} {cur}")]
        for t,v in items:
            r=ctk.CTkFrame(sc,fg_color="transparent"); r.pack(fill="x",padx=24,pady=2)
            ctk.CTkLabel(r,text=t,font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right")
            ctk.CTkLabel(r,text=v,font=(FONT,_fs(13),"bold"),text_color=C["txt"]).pack(side="left")
        ctk.CTkButton(dlg,text="إغلاق",command=dlg.destroy,width=200,height=40,
            fg_color=C["accent"],font=(FONT,_fs(13),"bold")).pack(pady=12)

    def _rep_z_report(self):
        today=datetime.now().strftime("%Y-%m-%d")
        cur=self.db.setting("currency","SDG")
        data=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales"
            " WHERE (credit_status IS NULL OR credit_status!='pending') AND date(created_at)=?",(today,)) or {}
        ts=data.get("s") or 0; tc=data.get("c") or 0
        cogs=self.db.q1("SELECT COALESCE(SUM(si.buy_price*si.quantity),0) s FROM sale_items si"
            " JOIN sales s ON si.sale_id=s.id"
            " WHERE (s.credit_status IS NULL OR s.credit_status!='pending') AND date(s.created_at)=?",(today,)) or {}
        op_exp=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='OUT' AND date(created_at)=?",(today,)) or {}
        qi=self.db.q1("SELECT COALESCE(SUM(si.quantity),0) q FROM sale_items si JOIN sales s ON si.sale_id=s.id"
            " WHERE (s.credit_status IS NULL OR s.credit_status!='pending') AND date(s.created_at)=?",(today,)) or {}
        gross=ts-(cogs.get("s") or 0); net=gross-(op_exp.get("s") or 0)
        # Payment methods breakdown
        pays=self.db.q("SELECT pay_method,COUNT(*) c,SUM(total) t FROM sales"
            " WHERE (credit_status IS NULL OR credit_status!='pending') AND date(created_at)=? GROUP BY pay_method",(today,))
        dlg=ctk.CTkToplevel(self); dlg.title(f"Z تقرير إغلاق اليوم — {today}")
        dlg.geometry("560x640"); dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks(); sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"560x640+{(sw-560)//2}+{(sh-640)//2}")
        sc=ctk.CTkScrollableFrame(dlg,fg_color=C["card"],corner_radius=12)
        sc.pack(fill="both",expand=True,padx=12,pady=12)
        ctk.CTkLabel(sc,text=f"📋  تقرير Z — إغلاق اليوم",font=(FONT,_fs(18),"bold"),text_color=C["warning"]).pack(pady=10)
        ctk.CTkLabel(sc,text=f"التاريخ: {today}",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack()
        ctk.CTkFrame(sc,height=1,fg_color=C["border"]).pack(fill="x",padx=20,pady=10)
        items=[("💰 إجمالي المبيعات",f"{ts:,.2f} {cur}"),("🧾 عدد الفواتير",str(tc)),
               ("📦 العناصر المباعة",str(qi.get("q") or 0)),
               ("🏷 COGS (التكلفة)",f"{cogs.get('s') or 0:,.2f} {cur}"),
               ("📈 إجمالي الربح",f"{gross:,.2f} {cur}"),
               ("💸 المصروفات",f"{op_exp.get('s') or 0:,.2f} {cur}"),
               ("💹 صافي الربح",f"{net:,.2f} {cur}")]
        for t,v in items:
            r=ctk.CTkFrame(sc,fg_color="transparent"); r.pack(fill="x",padx=24,pady=2)
            ctk.CTkLabel(r,text=t,font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right")
            ctk.CTkLabel(r,text=v,font=(FONT,_fs(13),"bold"),text_color=C["txt"]).pack(side="left")
        # Payment breakdown
        ctk.CTkFrame(sc,height=1,fg_color=C["border"]).pack(fill="x",padx=20,pady=8)
        ctk.CTkLabel(sc,text="طرق الدفع",font=(FONT,_fs(13),"bold"),text_color=C["txt"]).pack(anchor="e",padx=24)
        for p in pays:
            r=ctk.CTkFrame(sc,fg_color="transparent"); r.pack(fill="x",padx=32,pady=1)
            ctk.CTkLabel(r,text=f"{p['pay_method']}",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right")
            ctk.CTkLabel(r,text=f"{p['c']} فاتورة | {p['t']:,.2f} {cur}",font=(FONT,_fs(12),"bold"),text_color=C["txt"]).pack(side="left")
        # Print to thermal
        def do_print_z():
            try:
                import win32print
                prn=self.db.setting("thermal_printer","")
                if not prn: Toast.show(self,"اختر طابعة حرارية من الإعدادات أولاً","warning"); return
                lines=[f"{'Z REPORT':^40s}","─"*40,f"{'إقفال اليوم':^40s}",f"{today:^40s}","─"*40,
                       f"إجمالي المبيعات: {ts:,.2f} {cur}",
                       f"عدد الفواتير: {tc}","─"*40,
                       f"الأصناف المباعة: {qi.get('q') or 0}",
                       f"COGS: {cogs.get('s') or 0:,.2f} {cur}",
                       f"إجمالي الربح: {gross:,.2f} {cur}",
                       f"صافي الربح: {net:,.2f} {cur}","─"*40]
                for p in pays:
                    lines.append(f"{p['pay_method']}: {p['c']} فاتورة = {p['t']:,.2f} {cur}")
                lines+=["─"*40,"نهاية التقرير",""]
                text="\n".join(lines)
                h=win32print.OpenPrinter(prn)
                try:
                    win32print.StartDocPrinter(h,1,("z_report",None,"RAW"))
                    win32print.StartPagePrinter(h)
                    win32print.WritePrinter(h,text.encode("utf-8","replace"))
                    win32print.WritePrinter(h,b"\x1d\x56\x42\x00")
                    win32print.EndPagePrinter(h); win32print.EndDocPrinter(h)
                    Toast.show(self,"✓ تمت طباعة تقرير Z","success",2000)
                finally: win32print.ClosePrinter(h)
            except Exception as e: Toast.show(self,f"خطأ: {e}","error",4000)
        bf=ctk.CTkFrame(dlg,fg_color="transparent"); bf.pack(pady=10)
        ctk.CTkButton(bf,text="🖨 طباعة حرارية",command=do_print_z,width=200,height=40,
            fg_color="#8b5cf6",font=(FONT,_fs(13),"bold")).pack(pady=4)
        ctk.CTkButton(bf,text="إغلاق",command=dlg.destroy,width=200,height=40,
            fg_color=C["accent"],font=(FONT,_fs(13),"bold")).pack(pady=4)

    def _rep_export_xlsx(self):
        try:
            import openpyxl
            fd=self._rf.get().strip(); td=self._rt.get().strip()
            cur=self.db.setting("currency","SDG")
            wb=openpyxl.Workbook()
            ws=wb.active; ws.title="تقرير المبيعات"
            ws.append(["تقرير المبيعات",f"من {fd} إلى {td}"])
            ws.append([])
            # KPI data
            r=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales"
                " WHERE (credit_status IS NULL OR credit_status!='pending')"
                " AND date(created_at) BETWEEN ? AND ?",(fd,td)) or {}
            ws.append(["إجمالي المبيعات",f"{r.get('s') or 0:.2f} {cur}","عدد الفواتير",r.get("c") or 0])
            cogs=self.db.q1("SELECT COALESCE(SUM(si.buy_price*si.quantity),0) s FROM sale_items si"
                " JOIN sales s ON si.sale_id=s.id"
                " WHERE (s.credit_status IS NULL OR s.credit_status!='pending')"
                " AND date(s.created_at) BETWEEN ? AND ?",(fd,td)) or {}
            ws.append(["تكلفة البضاعة",f"{cogs.get('s') or 0:.2f} {cur}"])
            ws.append([])
            # Top products
            ws.append(["الأدوية الأكثر مبيعاً","","",""]); ws.append(["الدواء","الكمية","الإيراد","الربح"])
            for r in self.db.q("SELECT m.name,SUM(si.quantity) qty,SUM(si.total) rev,"
                    "SUM((si.unit_price-si.buy_price)*si.quantity) profit"
                    " FROM sale_items si JOIN medicines m ON si.medicine_id=m.id"
                    " JOIN sales s ON si.sale_id=s.id"
                    " WHERE (s.credit_status IS NULL OR s.credit_status!='pending')"
                    " AND date(s.created_at) BETWEEN ? AND ?"
                    " GROUP BY m.id ORDER BY qty DESC LIMIT 30",(fd,td)):
                ws.append([r["name"],r["qty"],f"{r['rev']:.2f}",f"{r.get('profit') or 0:.2f}"])
            path=filedialog.asksaveasfilename(defaultextension=".xlsx",
                filetypes=[("Excel","*.xlsx")],initialfile=f"تقرير_مبيعات_{fd}_{td}.xlsx")
            if path: wb.save(path); Toast.show(self,f"✓ تم حفظ {path}","success")
        except Exception as e: Toast.show(self,f"خطأ PDF: {e}","error")

    def _rep_export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas
            fd=self._rf.get().strip(); td=self._rt.get().strip()
            cur=self.db.setting("currency","SDG")
            path=filedialog.asksaveasfilename(defaultextension=".pdf",
                filetypes=[("PDF","*.pdf")],initialfile=f"تقرير_مبيعات_{fd}_{td}.pdf")
            if not path: return
            c=canvas.Canvas(path,pagesize=A4)
            w,h=A4; y=h-50
            c.setFont("Helvetica-Bold",18); c.drawString(w//2-80,y,"تقرير المبيعات"); y-=25
            c.setFont("Helvetica",12); c.drawString(50,y,f"من {fd} إلى {td}"); y-=30
            # KPI
            r=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales"
                " WHERE (credit_status IS NULL OR credit_status!='pending')"
                " AND date(created_at) BETWEEN ? AND ?",(fd,td)) or {}
            c.drawString(50,y,f"إجمالي المبيعات: {r.get('s') or 0:.2f} {cur}   الفواتير: {r.get('c') or 0}"); y-=20
            cogs=self.db.q1("SELECT COALESCE(SUM(si.buy_price*si.quantity),0) s FROM sale_items si"
                " JOIN sales s ON si.sale_id=s.id"
                " WHERE (s.credit_status IS NULL OR s.credit_status!='pending')"
                " AND date(s.created_at) BETWEEN ? AND ?",(fd,td)) or {}
            c.drawString(50,y,f"تكلفة البضاعة: {cogs.get('s') or 0:.2f} {cur}"); y-=30
            # Top products
            c.setFont("Helvetica-Bold",14); c.drawString(50,y,"الأدوية الأكثر مبيعاً"); y-=20
            c.setFont("Helvetica-Bold",10)
            c.drawString(50,y,"الدواء"); c.drawString(250,y,"الكمية"); c.drawString(320,y,"الإيراد"); c.drawString(420,y,"الربح")
            y-=15; c.setFont("Helvetica",10)
            for r in self.db.q("SELECT m.name,SUM(si.quantity) qty,SUM(si.total) rev,"
                    "SUM((si.unit_price-si.buy_price)*si.quantity) profit"
                    " FROM sale_items si JOIN medicines m ON si.medicine_id=m.id"
                    " JOIN sales s ON si.sale_id=s.id"
                    " WHERE (s.credit_status IS NULL OR s.credit_status!='pending')"
                    " AND date(s.created_at) BETWEEN ? AND ?"
                    " GROUP BY m.id ORDER BY qty DESC LIMIT 30",(fd,td)):
                c.drawString(50,y,r["name"][:30] if r["name"] else "")
                c.drawString(250,y,str(r["qty"])); c.drawString(320,y,f"{r['rev']:.2f}")
                c.drawString(420,y,f"{r.get('profit') or 0:.2f}")
                y-=15
                if y<50: c.showPage(); y=h-50
            c.save()
            Toast.show(self,f"✓ تم حفظ PDF","success")
        except Exception as e: Toast.show(self,f"خطأ PDF: {e}","error")

    # ═══════════════════════════════════════
    #  CREDIT — إدارة الدفع الآجل
    # ═══════════════════════════════════════
    def _pg_credit(self):
        self._clear()
        cur=self.db.setting("currency","SDG")
        # KPIs
        kpi=ctk.CTkFrame(self.cont,fg_color="transparent"); kpi.pack(fill="x",pady=(0,8))
        for i in range(3): kpi.columnconfigure(i,weight=1)
        pending=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales WHERE credit_status='pending'") or {}
        approved=self.db.q1("SELECT COALESCE(SUM(total),0) s,COUNT(*) c FROM sales WHERE credit_status='approved'") or {}
        collected=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM credit_payments cp JOIN sales s ON cp.sale_id=s.id WHERE s.credit_status='approved'") or {}
        pend_total=pending.get("s") or 0; pend_count=pending.get("c") or 0
        appr_total=approved.get("s") or 0; appr_count=approved.get("c") or 0
        coll_total=collected.get("s") or 0
        remaining=appr_total-coll_total
        self._card(kpi,"معلق (بانتظار الموافقة)",f"{pend_total:,.2f} {cur}",f"{pend_count} فاتورة",C["warning"],"⏳",0,2)
        self._card(kpi,"تمت الموافقة",f"{appr_total:,.2f} {cur}",f"{appr_count} فاتورة",C["success"],"✅",0,1)
        self._card(kpi,"المتبقي للتحصيل",f"{remaining:,.2f} {cur}","إجمالي معتمد − محصل",C["danger"] if remaining>0 else C["success"],"💰",0,0)

        tabs=ctk.CTkTabview(self.cont,fg_color=C["card"],
            segmented_button_fg_color=C["surface"],
            segmented_button_selected_color=C["accent"],
            segmented_button_unselected_hover_color=C["hover"],
            text_color=C["txt"]); tabs.pack(fill="both",expand=True)
        tabs.add("🕐 بانتظار الموافقة"); tabs.add("✅ تمت الموافقة"); tabs.add("📊 إجمالي الآجل")

        # ── Pending tab ──
        pt=tabs.tab("🕐 بانتظار الموافقة")
        pb=ctk.CTkFrame(pt,fg_color="transparent"); pb.pack(fill="x",pady=8)
        self._btn(pb,"✅ موافقة",self._credit_approve,C["success"]).pack(side="right",padx=4)
        self._btn(pb,"❌ رفض",self._credit_reject,C["danger"]).pack(side="right",padx=4)
        tf1,self._pend_tv=self._tree(pt,
            ("id","inv","date","customer","total","created"),
            ("#","الفاتورة","التاريخ","العميل","الإجمالي","تاريخ التسجيل"))
        tf1.pack(fill="both",expand=True,padx=6,pady=6)
        for r in self.db.q("SELECT id,invoice_no,customer_name,total,created_at FROM sales WHERE credit_status='pending' ORDER BY id"):
            self._pend_tv.insert("","end",iid=r["id"],values=(r["id"],r["invoice_no"],
                (r["created_at"] or "")[:10],r["customer_name"] or "",f"{r['total']:,.2f}",
                (r["created_at"] or "")[:16]))

        # ── Approved tab ──
        ap=tabs.tab("✅ تمت الموافقة")
        ab=ctk.CTkFrame(ap,fg_color="transparent"); ab.pack(fill="x",pady=8)
        self._btn(ab,"💰 تسجيل دفعة",self._credit_pay,C["accent"]).pack(side="right",padx=4)
        tf2,self._appr_tv=self._tree(ap,
            ("inv","customer","total","paid","remaining","date"),
            ("الفاتورة","العميل","الإجمالي","المدفوع","المتبقي","تاريخ الاعتماد"))
        tf2.pack(fill="both",expand=True,padx=6,pady=6)
        for r in self.db.q("SELECT s.id,s.invoice_no,s.customer_name,s.total,"
            "COALESCE((SELECT SUM(amount) FROM credit_payments WHERE sale_id=s.id),0) paid,"
            "s.approved_at FROM sales s WHERE s.credit_status='approved' ORDER BY s.id DESC"):
            paid=r["paid"]; rem=r["total"]-paid
            self._appr_tv.insert("","end",iid=r["id"],values=(r["invoice_no"],
                r["customer_name"] or "",f"{r['total']:,.2f}",f"{paid:,.2f}",
                f"{rem:,.2f}",(r["approved_at"] or "")[:10]))

        # ── All credit tab ──
        at=tabs.tab("📊 إجمالي الآجل")
        tf3,self._all_tv=self._tree(at,
            ("inv","customer","total","paid","remaining","status"),
            ("الفاتورة","العميل","الإجمالي","المدفوع","المتبقي","الحالة"))
        tf3.pack(fill="both",expand=True,padx=6,pady=6)
        for r in self.db.q("SELECT s.id,s.invoice_no,s.customer_name,s.total,s.credit_status,"
            "COALESCE((SELECT SUM(amount) FROM credit_payments WHERE sale_id=s.id),0) paid"
            " FROM sales s WHERE s.credit_status IS NOT NULL ORDER BY s.id DESC"):
            paid=r["paid"]; rem=r["total"]-paid
            st={"pending":"⏳ معلق","approved":"✅ معتمد","cancelled":"❌ ملغي"}.get(r["credit_status"],r["credit_status"] or "")
            self._all_tv.insert("","end",iid=r["id"],values=(r["invoice_no"],
                r["customer_name"] or "",f"{r['total']:,.2f}",f"{paid:,.2f}",
                f"{rem:,.2f}",st))

    def _credit_approve(self):
        sel=self._pend_tv.selection()
        if not sel: Toast.show(self,"حدّد فاتورة آجل للموافقة","warning"); return
        sid=int(sel[0])
        s=self.db.q1("SELECT invoice_no,total FROM sales WHERE id=?",(sid,))
        if not s: return
        if messagebox.askyesno("موافقة",f"الموافقة على فاتورة {s['invoice_no']} بقيمة {s['total']:.2f} ؟"):
            self.db.run("UPDATE sales SET credit_status='approved',approved_by=?,approved_at=CURRENT_TIMESTAMP WHERE id=?",(self.user["id"],sid))
            self.db.run("INSERT INTO ledger(type,amount,category,description,ref_id,user_id)"
                " VALUES(?,?,?,?,?,?)",("IN",s["total"],"آجل",f"موافقة {s['invoice_no']}",sid,self.user["id"]))
            self.db.log(self.user["id"],"CREDIT_APPROVE",s["invoice_no"])
            Toast.show(self,f"✓ تمت الموافقة على {s['invoice_no']}","success")
            self._pg_credit()

    def _credit_reject(self):
        sel=self._pend_tv.selection()
        if not sel: Toast.show(self,"حدّد فاتورة آجل للرفض","warning"); return
        sid=int(sel[0])
        s=self.db.q1("SELECT invoice_no,total FROM sales WHERE id=?",(sid,))
        if not s: return
        if messagebox.askyesno("رفض",f"إلغاء فاتورة {s['invoice_no']} بقيمة {s['total']:.2f} ؟"):
            self.db.run("UPDATE sales SET credit_status='cancelled' WHERE id=?",(sid,))
            # Revert stock
            for item in self.db.q("SELECT medicine_id,quantity,strip_qty FROM sale_items WHERE sale_id=?",(sid,)):
                add_qty=item["strip_qty"] if item["strip_qty"] else item["quantity"]
                self.db.run("UPDATE medicines SET stock=stock+? WHERE id=?",(add_qty,item["medicine_id"]))
            self.db.log(self.user["id"],"CREDIT_REJECT",s["invoice_no"])
            Toast.show(self,f"✓ تم إلغاء {s['invoice_no']} وإعادة المخزون","success")
            self._pg_credit()

    def _credit_pay(self):
        sel=self._appr_tv.selection()
        if not sel: Toast.show(self,"حدّد فاتورة معتمدة","warning"); return
        sid=int(sel[0])
        s=self.db.q1("SELECT invoice_no,total FROM sales WHERE id=?",(sid,))
        if not s: return
        paid=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM credit_payments WHERE sale_id=?",(sid,)) or {}
        rem=s["total"]-(paid.get("s") or 0)
        if rem<=0: Toast.show(self,"هذه الفاتورة مسددة بالكامل","info"); return
        dlg=ctk.CTkToplevel(self); dlg.title("تسديد دفعة"); dlg.geometry("400x300")
        dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks()
        sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"400x300+{(sw-400)//2}+{(sh-300)//2}")
        ctk.CTkLabel(dlg,text=f"فاتورة: {s['invoice_no']}",font=(FONT,_fs(15),"bold"),text_color=C["txt"]).pack(pady=12)
        ctk.CTkLabel(dlg,text=f"المتبقي: {rem:.2f}",font=(FONT,_fs(13)),text_color=C["warning"]).pack()
        ctk.CTkLabel(dlg,text="المبلغ:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=30,pady=(14,2))
        amt_e=self._ent(dlg,str(rem),300); amt_e.pack(anchor="e",padx=30)
        ctk.CTkLabel(dlg,text="ملاحظات:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=30,pady=(8,2))
        note_e=self._ent(dlg,"دفعة جديدة",300); note_e.pack(anchor="e",padx=30)
        def do_pay():
            try: amt=float(amt_e.get()); assert amt>0 and amt<=rem
            except: Toast.show(self,"أدخل مبلغاً صحيحاً","error"); return
            self.db.run("INSERT INTO credit_payments(sale_id,amount,notes,user_id) VALUES(?,?,?,?)",
                (sid,amt,note_e.get().strip(),self.user["id"]))
            self.db.log(self.user["id"],"CREDIT_PAY",f"{s['invoice_no']}+{amt:.2f}")
            Toast.show(self,f"✓ تم تسجيل دفعة {amt:.2f}","success")
            dlg.destroy(); self._pg_credit()
        self._btn(dlg,"💾 تسجيل",do_pay,C["success"],240,46).pack(pady=20)

    # ═══════════════════════════════════════
    #  USERS  — إدارة المستخدمين الكاملة
    # ═══════════════════════════════════════
    def _pg_users(self):
        if not can(self.user,"users"):
            ctk.CTkLabel(self.cont,text="⛔  لا تملك صلاحية الوصول لهذه الصفحة",
                font=(FONT,_fs(18),"bold"),text_color=C["danger"]).pack(expand=True); return

        # Toolbar
        tb=ctk.CTkFrame(self.cont,fg_color="transparent"); tb.pack(fill="x",pady=(0,8))
        self._btn(tb,"➕ مستخدم جديد",   self._usr_new,       C["success"]).pack(side="right",padx=4)
        self._btn(tb,"✏ تعديل",          self._usr_edit,      C["warning"]).pack(side="right",padx=4)
        self._btn(tb,"🔄 تفعيل/تعطيل",  self._usr_toggle,    C["accent"]).pack(side="right",padx=4)
        self._btn(tb,"🔑 إعادة كلمة المرور",self._usr_reset_pw,C["purple"]).pack(side="right",padx=4)

        # Permissions info card
        info=ctk.CTkFrame(self.cont,fg_color=C["card"],corner_radius=10,border_width=1,border_color=C["border"])
        info.pack(fill="x",pady=(0,8))
        irow=ctk.CTkFrame(info,fg_color="transparent"); irow.pack(padx=14,pady=10)
        for role,col,perms_txt in [
            ("مدير","#2563eb","جميع الصلاحيات: مبيعات + مخزن + خزينة + تقارير + مستخدمون + إعدادات"),
            ("صيدلاني","#8b5cf6","مبيعات + مخزن + خزينة + تقارير"),
            ("كاشير","#10b981","نقطة البيع فقط"),
        ]:
            rf=ctk.CTkFrame(irow,fg_color="transparent"); rf.pack(side="right",padx=12)
            ctk.CTkLabel(rf,text=f"● {role}",font=(FONT,_fs(12),"bold"),text_color=col).pack(anchor="e")
            ctk.CTkLabel(rf,text=perms_txt,font=(FONT,_fs(10)),text_color=C["txt_s"]).pack(anchor="e")

        # Table
        tf,self._utv=self._tree(self.cont,
            ("uid","username","full_name","role","last_login","status"),
            ("ID","اسم المستخدم","الاسم الكامل","الدور","آخر دخول","الحالة"))
        tf.pack(fill="both",expand=True)
        self._utv.column("uid",width=40,minwidth=40)
        self._utv.column("username",width=120); self._utv.column("full_name",width=160)
        self._utv.column("role",width=120); self._utv.column("last_login",width=140)
        self._utv.column("status",width=80)
        self._usr_load()

    def _usr_load(self):
        for r in self._utv.get_children(): self._utv.delete(r)
        for r in self.db.q("SELECT * FROM users ORDER BY id"):
            self._utv.insert("","end",iid=r["id"],values=(
                r["id"],r["username"],r["full_name"],
                ROLES.get(r["role"],r["role"]),
                r["last_login"][:16] if r["last_login"] else "لم يدخل",
                "✓ نشط" if r["is_active"] else "✗ معطّل"))

    def _usr_toggle(self):
        sel=self._utv.selection()
        if not sel: Toast.show(self,"حدّد مستخدماً أولاً","warning"); return
        uid=int(sel[0])
        if uid==self.user["id"]: Toast.show(self,"لا يمكن تعطيل حسابك الحالي","error"); return
        cur=self.db.q1("SELECT is_active,full_name FROM users WHERE id=?",(uid,))
        if cur:
            nw=0 if cur["is_active"] else 1
            self.db.run("UPDATE users SET is_active=? WHERE id=?",(nw,uid))
            state="تفعيل" if nw else "تعطيل"
            Toast.show(self,f"✓ تم {state} المستخدم {cur['full_name']}","success")
            self._usr_load()

    def _usr_new(self):  self._usr_dlg()
    def _usr_edit(self):
        sel=self._utv.selection()
        if not sel: Toast.show(self,"حدّد مستخدماً أولاً","warning"); return
        user=self.db.q1("SELECT * FROM users WHERE id=?",(int(sel[0]),))
        if user: self._usr_dlg(user)

    def _usr_reset_pw(self):
        sel=self._utv.selection()
        if not sel: Toast.show(self,"حدّد مستخدماً أولاً","warning"); return
        uid=int(sel[0])
        usr=self.db.q1("SELECT username FROM users WHERE id=?",(uid,))
        if not usr: return
        dlg=ctk.CTkToplevel(self); dlg.title("إعادة كلمة المرور"); dlg.geometry("420x320")
        dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks()
        sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"420x320+{(sw-420)//2}+{(sh-320)//2}")
        ctk.CTkLabel(dlg,text=f"🔑  إعادة كلمة مرور: {usr['username']}",
            font=(FONT,_fs(15),"bold"),text_color=C["txt"]).pack(pady=18)
        for lbl in ["كلمة المرور الجديدة:","تأكيد كلمة المرور:"]:
            ctk.CTkLabel(dlg,text=lbl,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=30,pady=(6,1))
            e=ctk.CTkEntry(dlg,width=320,height=44,justify="right",show="●",
                font=(FONT,_fs(13)),fg_color=C["inp"],text_color=C["txt"]); e.pack()
            if lbl.startswith("كلمة"): e1=e
            else: e2=e
        def save():
            p1=e1.get(); p2=e2.get()
            if not p1: Toast.show(self,"أدخل كلمة المرور","error"); return
            if p1!=p2: Toast.show(self,"كلمتا المرور غير متطابقتين","error"); return
            if len(p1)<6: Toast.show(self,"6 أحرف على الأقل","error"); return
            self.db.run("UPDATE users SET password=? WHERE id=?",
                (hashlib.sha256(p1.encode()).hexdigest(),uid))
            Toast.show(self,"✓ تم تغيير كلمة المرور","success"); dlg.destroy()
        self._btn(dlg,"💾 حفظ",save,C["success"],220,46).pack(pady=18)

    def _usr_dlg(self,existing=None):
        edit=existing is not None
        dlg=ctk.CTkToplevel(self)
        dlg.title("تعديل مستخدم" if edit else "مستخدم جديد"); dlg.geometry("550x640")
        dlg.configure(fg_color=C["surface"]); dlg.grab_set()
        dlg.update_idletasks()
        sw=dlg.winfo_screenwidth(); sh=dlg.winfo_screenheight()
        dlg.geometry(f"550x640+{(sw-550)//2}+{(sh-640)//2}")
        ctk.CTkLabel(dlg,
            text="✏  تعديل بيانات المستخدم" if edit else "➕  إنشاء مستخدم جديد",
            font=(FONT,_fs(17),"bold"),
            text_color=C["warning"] if edit else C["success"]).pack(pady=16)
        sc=ctk.CTkScrollableFrame(dlg,fg_color="transparent"); sc.pack(fill="both",expand=True)
        def row(lbl,show=""):
            ctk.CTkLabel(sc,text=lbl,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=28,pady=(6,1))
            e=ctk.CTkEntry(sc,width=360,height=44,justify="right",show=show,
                font=(FONT,_fs(13)),fg_color=C["inp"],text_color=C["txt"]); e.pack(); return e
        u_e=row("اسم المستخدم (username)")
        f_e=row("الاسم الكامل")
        p_e=row("كلمة المرور"+(" (اتركها فارغة للإبقاء)" if edit else ""),"●")
        if edit:
            u_e.insert(0,existing.get("username",""))
            f_e.insert(0,existing.get("full_name",""))
        ctk.CTkLabel(sc,text="الدور الأساسي:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=28,pady=(10,1))
        rb=self._combo(sc,["cashier","pharmacist","admin"],360); rb.pack()
        if edit: rb.set(existing.get("role","cashier"))

        # Custom permissions
        ctk.CTkLabel(sc,text="الصلاحيات المخصصة (اختياري):",font=(FONT,_fs(12),"bold"),text_color=C["accent"]
            ).pack(anchor="e",padx=28,pady=(14,4))
        ctk.CTkLabel(sc,text="اختر صلاحيات إضافية تتجاوز صلاحيات الدور الأساسي",
            font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(anchor="e",padx=28)
        perm_grid=ctk.CTkFrame(sc,fg_color="transparent"); perm_grid.pack(fill="x",padx=28,pady=4)
        perm_grid.columnconfigure(0,weight=1); perm_grid.columnconfigure(1,weight=1)
        all_perms=[("pos","🛒 نقطة البيع"),("inventory","📦 المخزن"),("ledger","💰 الخزينة"),
                   ("reports","📊 التقارير"),("credit","📋 الآجل"),("users","👥 المستخدمون"),
                   ("settings","⚙️ الإعدادات"),("returns","🔄 المرتجعات"),("delete","🗑 حذف"),
                   ("edit_price","✏ تعديل السعر")]
        self._perm_vars={}
        existing_custom=set()
        if edit:
            raw=existing.get("custom_perms","") or ""
            existing_custom=set(c.strip() for c in raw.split(",") if c.strip())
        for i,(pk,plbl) in enumerate(all_perms):
            col=i%2; row_n=i//2
            pv=ctk.IntVar(value=1 if pk in existing_custom else 0)
            cb=ctk.CTkCheckBox(perm_grid,text=plbl,variable=pv,font=(FONT,_fs(11)),text_color=C["txt"],
                fg_color=C["accent"],hover_color=C["acc_h"])
            cb.grid(row=row_n,column=col,sticky="e",padx=4,pady=2)
            self._perm_vars[pk]=pv

        def save():
            uname=u_e.get().strip(); fname=f_e.get().strip()
            pw=p_e.get(); role=rb.get()
            if not uname or not fname: Toast.show(self,"اسم المستخدم والاسم الكامل مطلوبان","error"); return
            if not edit and not pw: Toast.show(self,"كلمة المرور مطلوبة","error"); return
            if pw and len(pw)<6: Toast.show(self,"كلمة المرور 6 أحرف على الأقل","error"); return
            custom_perms=",".join(k for k,v in self._perm_vars.items() if v.get())
            try:
                if edit:
                    if pw:
                        h=hashlib.sha256(pw.encode()).hexdigest()
                        self.db.run("UPDATE users SET username=?,full_name=?,password=?,role=?,custom_perms=? WHERE id=?",
                            (uname,fname,h,role,custom_perms,existing["id"]))
                    else:
                        self.db.run("UPDATE users SET username=?,full_name=?,role=?,custom_perms=? WHERE id=?",
                            (uname,fname,role,custom_perms,existing["id"]))
                    Toast.show(self,f"✓ تم تعديل {uname}","success")
                else:
                    h=hashlib.sha256(pw.encode()).hexdigest()
                    self.db.run("INSERT INTO users(username,full_name,password,role,custom_perms) VALUES(?,?,?,?,?)",
                        (uname,fname,h,role,custom_perms))
                    self.db.log(self.user["id"],"NEW_USER",uname)
                    Toast.show(self,f"✓ تم إنشاء {uname}","success")
                dlg.destroy(); self._usr_load()
            except sqlite3.IntegrityError:
                Toast.show(self,"اسم المستخدم موجود مسبقاً","error")
        self._btn(sc,"💾 حفظ",save,C["success"],320,48).pack(pady=16)

    # ═══════════════════════════════════════
    #  RETURNS — صفحة استرجاع المنتجات
    # ═══════════════════════════════════════
    def _pg_returns(self):
        self._clear()
        cur=self.db.setting("currency","SDG")
        ctk.CTkLabel(self.cont,text="🔄  استرجاع المنتجات",font=(FONT,_fs(18),"bold"),
            text_color=C["txt"]).pack(anchor="e",padx=16,pady=(8,4))

        # Search
        sf=ctk.CTkFrame(self.cont,fg_color=C["card"],corner_radius=10,border_width=1,border_color=C["border"])
        sf.pack(fill="x",padx=8,pady=6)
        si=ctk.CTkFrame(sf,fg_color="transparent"); si.pack(padx=14,pady=10)
        ctk.CTkLabel(si,text="رقم الفاتورة:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=2)
        self._ret_inv=ctk.CTkEntry(si,width=140,height=38,justify="right",font=(FONT,_fs(13)),
            fg_color=C["inp"],text_color=C["txt"]); self._ret_inv.pack(side="right",padx=2)
        ctk.CTkLabel(si,text="من:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=(8,2))
        self._ret_from=self._ent(si,"YYYY-MM-DD",100); self._ret_from.pack(side="right",padx=2)
        self._ret_from.insert(0,(datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d"))
        ctk.CTkLabel(si,text="إلى:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._ret_to=self._ent(si,"YYYY-MM-DD",100); self._ret_to.pack(side="right",padx=2)
        self._ret_to.insert(0,datetime.now().strftime("%Y-%m-%d"))
        self._btn(si,"🔍 بحث",self._ret_search,C["accent"],80,38).pack(side="right",padx=4)
        self._btn(si,"🔄 عرض الكل",self._ret_load_all,C["surface"],100,38).pack(side="right",padx=2)

        # Results area
        self._ret_res=ctk.CTkScrollableFrame(self.cont,fg_color="transparent")
        self._ret_res.pack(fill="both",expand=True,padx=8,pady=(6,8))
        self._ret_load_all()

    def _ret_search(self):
        for w in self._ret_res.winfo_children(): w.destroy()
        inv=self._ret_inv.get().strip(); fd=self._ret_from.get().strip(); td=self._ret_to.get().strip()
        cur=self.db.setting("currency","SDG")
        if inv:
            rows=self.db.q("SELECT s.id,s.invoice_no,s.customer_name,s.total,s.created_at,"
                "s.pay_method FROM sales s WHERE s.invoice_no LIKE ? AND s.credit_status IS DISTINCT FROM 'pending'"
                " ORDER BY s.id DESC LIMIT 10",(f"%{inv}%",))
        else:
            rows=self.db.q("SELECT s.id,s.invoice_no,s.customer_name,s.total,s.created_at,"
                "s.pay_method FROM sales s WHERE date(s.created_at) BETWEEN ? AND ?"
                " AND s.credit_status IS DISTINCT FROM 'pending' ORDER BY s.id DESC LIMIT 30",(fd,td))
        if not rows:
            ctk.CTkLabel(self._ret_res,text="لا توجد فواتير",font=(FONT,_fs(13)),text_color=C["txt_m"]).pack(pady=20); return
        for sale in rows:
            sc=ctk.CTkFrame(self._ret_res,fg_color=C["card"],corner_radius=8,border_width=1,border_color=C["border"])
            sc.pack(fill="x",pady=3)
            si=ctk.CTkFrame(sc,fg_color="transparent"); si.pack(fill="x",padx=12,pady=8)
            items=self.db.q("SELECT si.id,si.medicine_id,m.name,si.quantity,si.unit_price,si.total,si.buy_price,si.strip_qty,si.returned_qty"
                " FROM sale_items si JOIN medicines m ON si.medicine_id=m.id WHERE si.sale_id=? AND si.quantity>COALESCE(si.returned_qty,0)",(sale["id"],))
            if not items: continue
            ctk.CTkLabel(si,text=f"فاتورة: {sale['invoice_no']}",font=(FONT,_fs(13),"bold"),text_color=C["accent"]
                ).pack(anchor="e")
            ctk.CTkLabel(si,text=f"{sale['created_at'][:16] if sale['created_at'] else ''}  |  {sale['customer_name'] or 'عميل نقدي'}  |  {sale['total']:.2f} {cur}",
                font=(FONT,_fs(10)),text_color=C["txt_s"]).pack(anchor="e")
            for item in items:
                rf=ctk.CTkFrame(sc,fg_color=C["surface"],corner_radius=6)
                rf.pack(fill="x",padx=12,pady=2)
                ri=ctk.CTkFrame(rf,fg_color="transparent"); ri.pack(padx=10,pady=4)
                self._btn(ri,"♻ استرجاع",lambda i=item,s=sale:self._ret_do(i,s),
                    C["danger"],90,32).pack(side="left",padx=2)
                ctk.CTkLabel(ri,text=f"{item['total']:.2f} {cur}",
                    font=(FONT,_fs(12),"bold"),text_color=C["txt"]).pack(side="left",padx=4)
                ctk.CTkLabel(ri,text=f"×{item['quantity']}",
                    font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="left",padx=2)
                ctk.CTkLabel(ri,text=item["name"],font=(FONT,_fs(12)),text_color=C["txt"]
                    ).pack(side="right")
            # استرجاع كامل الفاتورة
            all_bf=ctk.CTkFrame(sc,fg_color="#1a0a0a",corner_radius=6)
            all_bf.pack(fill="x",padx=12,pady=(0,6))
            all_bi=ctk.CTkFrame(all_bf,fg_color="transparent"); all_bi.pack(padx=10,pady=4)
            self._btn(all_bi,"♻ استرجاع الكل",lambda s=sale:self._ret_all(s),
                C["danger"],130,34).pack(side="left",padx=2)
            ctk.CTkLabel(all_bi,text="أو استرجع كل أصناف الفاتورة دفعة واحدة",
                font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(side="right")


    def _ret_load_all(self):
        self._ret_inv.delete(0,"end")
        self._ret_from.delete(0,"end"); self._ret_from.insert(0,(datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d"))
        self._ret_to.delete(0,"end"); self._ret_to.insert(0,datetime.now().strftime("%Y-%m-%d"))
        self._ret_search()

    def _ret_do(self,item,sale):
        avail=item["quantity"]-(item.get("returned_qty") or 0)
        if avail<=0: Toast.show(self,"هذا العنصر مسترجع بالكامل","warning"); return
        qty=simpledialog.askinteger("الكمية المرتجعة",
            f"الكمية المتاحة للاسترجاع: {avail}\n{item['name']}\nالفاتورة: {sale['invoice_no']}",
            initialvalue=avail,minvalue=1,maxvalue=avail,parent=self)
        if not qty: return
        if not messagebox.askyesno("تأكيد الاسترجاع",
            f"استرجاع {item['name']}\nالكمية: {qty}\nالقيمة: {item['unit_price']*qty:.2f}؟"): return
        ratio=qty/avail; ret_val=item["total"]*ratio
        add_qty=(item.get("strip_qty",0) or avail)*qty//avail
        self.db.run("UPDATE medicines SET stock=stock+? WHERE id=?",(add_qty,item["medicine_id"]))
        self.db.run("UPDATE sale_items SET returned_qty=COALESCE(returned_qty,0)+? WHERE id=?",(qty,item["id"]))
        self.db.run("INSERT INTO ledger(type,amount,category,description,ref_id,user_id)"
            " VALUES(?,?,?,?,?,?)",("OUT",ret_val,"مرتجعات",
            f"استرجاع {item['name']} ({qty}) من {sale['invoice_no']}",sale["id"],self.user["id"]))
        self.db.log(self.user["id"],"RETURN",f"{item['name']} ({qty}) من {sale['invoice_no']}")
        Toast.show(self,f"✓ تم استرجاع {item['name']} ({qty})","success")
        self._ret_search()

    def _ret_all(self,sale):
        items=self.db.q("SELECT si.id,si.medicine_id,m.name,si.quantity,si.unit_price,si.total,si.buy_price,si.strip_qty,si.returned_qty"
            " FROM sale_items si JOIN medicines m ON si.medicine_id=m.id WHERE si.sale_id=? AND si.quantity>COALESCE(si.returned_qty,0)",(sale["id"],))
        if not items: Toast.show(self,"لا توجد أصناف للاسترجاع","warning"); return
        total_ret=sum((i["total"]/i["quantity"])*max(0,i["quantity"]-(i.get("returned_qty") or 0)) for i in items)
        if not messagebox.askyesno("استرجاع كامل الفاتورة",
            f"استرجاع جميع أصناف فاتورة {sale['invoice_no']}\nالإجمالي: {total_ret:.2f}\nسيتم إعادة الكميات للمخزون."): return
        for item in items:
            avail=item["quantity"]-(item.get("returned_qty") or 0)
            if avail<=0: continue
            ret_val=item["unit_price"]*avail
            add_qty=(item.get("strip_qty",0) or avail)
            self.db.run("UPDATE medicines SET stock=stock+? WHERE id=?",(add_qty,item["medicine_id"]))
            self.db.run("UPDATE sale_items SET returned_qty=COALESCE(returned_qty,0)+? WHERE id=?",(avail,item["id"]))
            self.db.run("INSERT INTO ledger(type,amount,category,description,ref_id,user_id)"
                " VALUES(?,?,?,?,?,?)",("OUT",ret_val,"مرتجعات",
                f"استرجاع {item['name']} ({avail}) من {sale['invoice_no']}",sale["id"],self.user["id"]))
        self.db.log(self.user["id"],"RETURN_ALL",f"{sale['invoice_no']}")
        Toast.show(self,f"✓ تم استرجاع فاتورة {sale['invoice_no']} بالكامل","success")
        self._ret_search()

    # ═══════════════════════════════════════
    #  TRASH (سلة المهملات)
    # ═══════════════════════════════════════
    def _pg_trash(self):
        sc=ctk.CTkScrollableFrame(self.cont,fg_color="transparent"); sc.pack(fill="both",expand=True)
        hdr=ctk.CTkFrame(sc,fg_color="transparent"); hdr.pack(fill="x",padx=18,pady=12)
        ctk.CTkLabel(hdr,text="🗑  سلة المهملات",font=(FONT,_fs(17),"bold"),text_color=C["txt"]).pack(side="right")
        self._btn(hdr,"🗑 تفريغ السلة",self._trash_empty,C["danger"],140,40).pack(side="left",padx=4)
        self._btn(hdr,"🔄 تحديث",self._trash_load,C["surface"],90,40).pack(side="left",padx=4)
        tf,self._trash_tv=self._tree(sc,
            ("barcode","name","buy","sell","stock","deleted_at"),
            ("الباركود","الاسم","سعر الشراء","سعر البيع","آخر مخزون","تاريخ الحذف"))
        tf.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self._trash_tv.bind("<Double-1>",lambda _:self._trash_restore())
        self._trash_load()

    def _trash_load(self):
        for r in self._trash_tv.get_children(): self._trash_tv.delete(r)
        for r in self.db.q("SELECT id,barcode,name,buy_price,sell_price,stock,updated_at"
            " FROM medicines WHERE is_active=0 ORDER BY updated_at DESC"):
            self._trash_tv.insert("","end",iid=r["id"],
                values=(r["barcode"] or "",r["name"],f"{r['buy_price']:.2f}",f"{r['sell_price']:.2f}",
                    r["stock"],r["updated_at"] or ""))

    def _trash_restore(self):
        sel=self._trash_tv.selection()
        if not sel: Toast.show(self,"حدّد دواءً لاسترجاعه","warning"); return
        med=self.db.q1("SELECT name FROM medicines WHERE id=?",(sel[0],))
        if med and messagebox.askyesno("استرجاع",f"إعادة '{med['name']}' للمخزون؟"):
            self.db.run("UPDATE medicines SET is_active=1,updated_at=CURRENT_TIMESTAMP WHERE id=?",(sel[0],))
            self.db.log(self.user["id"],"RESTORE_MED",med["name"])
            Toast.show(self,f"✓ تم استرجاع {med['name']}","success")
            self._trash_load()

    def _trash_empty(self):
        if not messagebox.askyesno("تفريغ السلة","سيتم حذف جميع الأدوية في سلة المهملات نهائياً!\nلا يمكن التراجع."): return
        pw=simpledialog.askstring("تأكيد المدير","أدخل كلمة سر المدير:",show="●",parent=self)
        if not pw: return
        h=hashlib.sha256(pw.encode()).hexdigest()
        admin=self.db.q1("SELECT id FROM users WHERE role='admin' AND password=? AND is_active=1",(h,))
        if not admin: Toast.show(self,"❌ كلمة سر غير صحيحة","error"); return
        cnt=self.db.q1("SELECT COUNT(*) c FROM medicines WHERE is_active=0")["c"]
        self.db.run("DELETE FROM medicines WHERE is_active=0")
        self.db.log(self.user["id"],"TRASH_EMPTY",f"تم حذف {cnt} دواء نهائياً")
        Toast.show(self,f"✓ تم حذف {cnt} دواء نهائياً","success")
        self._trash_load()

    # ═══════════════════════════════════════
    #  EXPENSES + LEDGER  —  مدمجين
    # ═══════════════════════════════════════
    def _pg_expenses(self):
        self._clear()
        cur=self.db.setting("currency","SDG")
        tabs=ctk.CTkTabview(self.cont,fg_color=C["card"],
            segmented_button_fg_color=C["surface"],
            segmented_button_selected_color=C["accent"],
            text_color=C["txt"]); tabs.pack(fill="both",expand=True)
        tabs.add("💸 المصروفات"); tabs.add("💰 الخزينة")
        self._build_expenses_tab(tabs.tab("💸 المصروفات"))
        self._build_ledger_tab(tabs.tab("💰 الخزينة"))

    def _build_expenses_tab(self,parent):
        cur=self.db.setting("currency","SDG")
        # KPI summary
        kpi=ctk.CTkFrame(parent,fg_color="transparent"); kpi.pack(fill="x",padx=8,pady=4)
        for i in range(3): kpi.columnconfigure(i,weight=1)
        self._exp_total_lbl=ctk.CTkLabel(kpi,text=f"إجمالي المصروفات: 0 {cur}",
            font=(FONT,_fs(14),"bold"),text_color=C["danger"])
        self._exp_total_lbl.grid(row=0,column=0,sticky="w",padx=8)
        self._exp_count_lbl=ctk.CTkLabel(kpi,text="0 عملية",
            font=(FONT,_fs(11)),text_color=C["txt_s"])
        self._exp_count_lbl.grid(row=0,column=1,sticky="w",padx=8)
        # Filter bar
        ff=ctk.CTkFrame(parent,fg_color=C["card"],corner_radius=10,border_width=1,border_color=C["border"])
        ff.pack(fill="x",padx=8,pady=4)
        fi=ctk.CTkFrame(ff,fg_color="transparent"); fi.pack(padx=14,pady=8)
        self._exp_period=ctk.StringVar(value="شهري")
        for p in ["يومي","أسبوعي","شهري","سنوي","الكل"]:
            ctk.CTkRadioButton(fi,text=p,variable=self._exp_period,value=p,
                font=(FONT,_fs(11)),text_color=C["txt"],fg_color=C["accent"],
                command=self._exp_load).pack(side="right",padx=6)
        self._btn(fi,"🔄 تحديث",self._exp_load,C["surface"],80,32).pack(side="left",padx=6)
        # Summary cards
        kf=ctk.CTkFrame(parent,fg_color="transparent"); kf.pack(fill="x",padx=8,pady=4)
        self._exp_cards={}
        EX_CATS=["كهرباء","مياه","غاز","ضرائب","مرتبات","إيجار","صيانة","نقل","تسويق","أخرى"]
        for i,cat in enumerate(EX_CATS):
            c=ctk.CTkFrame(kf,fg_color=C["card"],corner_radius=8,border_width=1,border_color=C["border"])
            c.grid(row=i//5,column=i%5,padx=3,pady=3,sticky="ew"); kf.grid_columnconfigure(i%5,weight=1)
            ct=ctk.CTkLabel(c,text=cat,font=(FONT,_fs(10)),text_color=C["txt_s"]); ct.pack(anchor="e",padx=6,pady=(4,0))
            cv=ctk.CTkLabel(c,text=f"0 {cur}",font=(FONT,_fs(12),"bold"),text_color=C["danger"])
            cv.pack(anchor="e",padx=6,pady=(0,4)); self._exp_cards[cat]=cv
        # Table
        tf,tv=self._tree(parent,("date","cat","amount","desc","by"),("التاريخ","الفئة","المبلغ","البيان","بواسطة"))
        tf.pack(fill="both",expand=True,padx=8,pady=4)
        tv.column("desc",width=200)
        self._exp_tv=tv
        # Add form
        af=ctk.CTkFrame(parent,fg_color=C["card"],corner_radius=8,border_width=1,border_color=C["border"])
        af.pack(fill="x",padx=8,pady=4)
        ai=ctk.CTkFrame(af,fg_color="transparent"); ai.pack(padx=14,pady=8)
        ctk.CTkLabel(ai,text="مبلغ:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(0,2))
        self._exp_amt=ctk.CTkEntry(ai,width=90,height=34,justify="right",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"])
        self._exp_amt.pack(side="right",padx=2)
        self._exp_amt.insert(0,"0")
        ctk.CTkLabel(ai,text="فئة:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._exp_cat=ctk.CTkOptionMenu(ai,values=EX_CATS,font=(FONT,_fs(11)),
            fg_color=C["inp"],button_color=C["inp_b"],text_color=C["txt"],width=100,height=34)
        self._exp_cat.pack(side="right",padx=2)
        ctk.CTkLabel(ai,text="تاريخ:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._exp_date=ctk.CTkEntry(ai,width=110,height=34,justify="right",
            placeholder_text="YYYY-MM-DD",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"])
        self._exp_date.pack(side="right",padx=2)
        self._exp_date.insert(0,datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkLabel(ai,text="بيان:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._exp_desc=ctk.CTkEntry(ai,width=160,height=34,justify="right",
            placeholder_text="اختياري",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"])
        self._exp_desc.pack(side="right",padx=2)
        self._btn(ai,"➕ إضافة",self._exp_add,C["danger"],90,34).pack(side="right",padx=4)
        self._exp_load()

    def _build_ledger_tab(self,parent):
        cur=self.db.setting("currency","SDG")
        # KPI
        kpi=ctk.CTkFrame(parent,fg_color="transparent"); kpi.pack(fill="x",padx=8,pady=6)
        for i in range(3): kpi.columnconfigure(i,weight=1)
        q_in=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='IN'") or {}
        q_out=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE type='OUT'") or {}
        tin=q_in.get("s",0); tout=q_out.get("s",0)
        ctk.CTkLabel(kpi,text=f"💰 الإيرادات: {tin:,.2f} {cur}",
            font=(FONT,_fs(14),"bold"),text_color=C["success"]).grid(row=0,column=0,sticky="w",padx=8)
        ctk.CTkLabel(kpi,text=f"💸 المصروفات: {tout:,.2f} {cur}",
            font=(FONT,_fs(14),"bold"),text_color=C["danger"]).grid(row=0,column=1,sticky="w",padx=8)
        bal=tin-tout
        ctk.CTkLabel(kpi,text=f"⚖ الرصيد: {bal:,.2f} {cur}",
            font=(FONT,_fs(14),"bold"),text_color=C["teal"] if bal>=0 else C["danger"]).grid(row=0,column=2,sticky="w",padx=8)
        # Manual entry form
        fp=ctk.CTkFrame(parent,fg_color=C["card"],corner_radius=8,border_width=1,border_color=C["border"])
        fp.pack(fill="x",padx=8,pady=4)
        fi=ctk.CTkFrame(fp,fg_color="transparent"); fi.pack(padx=14,pady=8)
        ctk.CTkLabel(fi,text="نوع القيد:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=2)
        self._lt=ctk.CTkOptionMenu(fi,values=["IN إيراد","OUT مصروف"],
            font=(FONT,_fs(11)),fg_color=C["inp"],button_color=C["inp_b"],text_color=C["txt"],width=110,height=34)
        self._lt.pack(side="right",padx=2)
        ctk.CTkLabel(fi,text="المبلغ:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._la=ctk.CTkEntry(fi,width=90,height=34,font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"]); self._la.pack(side="right",padx=2)
        ctk.CTkLabel(fi,text="التصنيف:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._lc=ctk.CTkEntry(fi,width=130,height=34,font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"],placeholder_text="مبيعات/مرتبات/...")
        self._lc.pack(side="right",padx=2)
        ctk.CTkLabel(fi,text="الوصف:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._ld=ctk.CTkEntry(fi,width=160,height=34,font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"],placeholder_text="اختياري")
        self._ld.pack(side="right",padx=2)
        self._btn(fi,"➕ إضافة القيد",self._led_add,C["success"],130,34).pack(side="right",padx=4)
        # Table
        tf,tv=self._tree(parent,("date","type","cat","amount","desc"),("التاريخ","النوع","التصنيف","المبلغ","الوصف"))
        tf.pack(fill="both",expand=True,padx=8,pady=4)
        self._ltv=tv
        self._ltv.tag_configure("IN",foreground=C["success"]); self._ltv.tag_configure("OUT",foreground=C["danger"])
        self._led_load()
        self._exp_amt=ctk.CTkEntry(ai,width=90,height=34,justify="right",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"])
        self._exp_amt.pack(side="right",padx=2)
        self._exp_amt.insert(0,"0")
        ctk.CTkLabel(ai,text="فئة:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._exp_cat=ctk.CTkOptionMenu(ai,values=EX_CATS,font=(FONT,_fs(11)),
            fg_color=C["inp"],button_color=C["inp_b"],text_color=C["txt"],width=100,height=34)
        self._exp_cat.pack(side="right",padx=2)
        ctk.CTkLabel(ai,text="تاريخ:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._exp_date=ctk.CTkEntry(ai,width=110,height=34,justify="right",
            placeholder_text="YYYY-MM-DD",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"])
        self._exp_date.pack(side="right",padx=2)
        self._exp_date.insert(0,datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkLabel(ai,text="بيان:",font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(side="right",padx=(4,2))
        self._exp_desc=ctk.CTkEntry(ai,width=160,height=34,justify="right",
            placeholder_text="اختياري",font=(FONT,_fs(12)),
            fg_color=C["inp"],text_color=C["txt"])
        self._exp_desc.pack(side="right",padx=2)
        self._btn(ai,"➕ إضافة",self._exp_add,C["danger"],90,34).pack(side="right",padx=4)
        self._exp_tv=tv; self._exp_load()

    def _exp_load(self):
        for r in self._exp_tv.get_children(): self._exp_tv.delete(r)
        cur=self.db.setting("currency","SDG"); period=self._exp_period.get()
        today=datetime.now()
        if period=="يومي":
            sd=today.strftime("%Y-%m-%d")
        elif period=="أسبوعي":
            sd=(today-timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        elif period=="شهري":
            sd=today.replace(day=1).strftime("%Y-%m-%d")
        else: sd=today.replace(month=1,day=1).strftime("%Y-%m-%d")
        for r in self.db.q("SELECT e.*,u.full_name FROM expenses e LEFT JOIN users u ON e.user_id=u.id"
            " WHERE e.expense_date>=? ORDER BY e.expense_date DESC",(sd,)):
            self._exp_tv.insert("","end",values=(r["expense_date"],r["category"],
                f"{r['amount']:.2f}",r["description"] or "",r["full_name"] or ""))
        # Update summary cards
        for cat in self._exp_cards:
            s=self.db.q1("SELECT COALESCE(SUM(amount),0) s FROM expenses"
                " WHERE category=? AND expense_date>=?",(cat,sd)) or {}
            self._exp_cards[cat].configure(text=f"{s.get('s') or 0:.0f} {cur}")

    def _exp_add(self):
        try: amt=float(self._exp_amt.get().strip())
        except: Toast.show(self,"مبلغ صحيح","error"); return
        if amt<=0: Toast.show(self,"المبلغ يجب أن يكون أكبر من صفر","error"); return
        cat=self._exp_cat.get(); date=self._exp_date.get().strip()
        desc=self._exp_desc.get().strip()
        if not date: Toast.show(self,"التاريخ مطلوب","error"); return
        try: datetime.strptime(date,"%Y-%m-%d")
        except: Toast.show(self,"صيغة التاريخ YYYY-MM-DD","error"); return
        self.db.run("INSERT INTO expenses(category,amount,description,expense_date,user_id)"
            " VALUES(?,?,?,?,?)",(cat,amt,desc,date,self.user["id"]))
        # Auto-log to ledger
        self.db.run("INSERT INTO ledger(type,amount,category,description,user_id)"
            " VALUES(?,?,?,?,?)",("OUT",amt,"مصروفات",f"{cat}: {desc or date}",self.user["id"]))
        self.db.log(self.user["id"],"EXPENSE",f"{cat}: {amt:.2f}")
        Toast.show(self,f"✓ تم تسجيل مصروف {cat}: {amt:.2f}","success")
        self._exp_amt.delete(0,"end"); self._exp_amt.insert(0,"0")
        self._exp_desc.delete(0,"end")
        self._exp_date.delete(0,"end"); self._exp_date.insert(0,datetime.now().strftime("%Y-%m-%d"))
        self._exp_load()
        if self.user["role"]=="admin": self._emit("expenses_changed")

    # ═══════════════════════════════════════
    #  SETTINGS
    # ═══════════════════════════════════════
    def _pg_settings(self):
        tabs=ctk.CTkTabview(self.cont,fg_color=C["card"],
            segmented_button_fg_color=C["surface"],
            segmented_button_selected_color=C["accent"],
            text_color=C["txt"]); tabs.pack(fill="both",expand=True)
        tabs.add("🏥 إعدادات الصيدلية"); tabs.add("👤 حسابي")
        self._build_sys_settings(tabs.tab("🏥 إعدادات الصيدلية"))
        self._build_profile(tabs.tab("👤 حسابي"))
        if self.user["role"]=="admin":
            tabs.add("🛡 متقدم")
            self._build_advanced(tabs.tab("🛡 متقدم"))

    def _build_sys_settings(self,parent):
        sc=ctk.CTkScrollableFrame(parent,fg_color="transparent"); sc.pack(fill="both",expand=True)
        ctk.CTkLabel(sc,text="إعدادات الصيدلية",font=(FONT,_fs(16),"bold"),text_color=C["txt"]).pack(anchor="e",padx=18,pady=(14,8))
        self._sf={}
        for k,lbl in [("pharmacy_name","اسم الصيدلية"),("pharmacy_address","العنوان"),
                      ("pharmacy_phone","رقم الهاتف"),("currency","العملة (SDG / EGP / USD)"),("tax_rate","نسبة الضريبة (%)")]:
            row=ctk.CTkFrame(sc,fg_color="transparent"); row.pack(fill="x",padx=18,pady=5)
            ctk.CTkLabel(row,text=lbl,font=(FONT,_fs(12)),text_color=C["txt_s"],width=230).pack(side="right")
            e=self._ent(row,lbl,300); e.pack(side="right",padx=8)
            e.insert(0,self.db.setting(k,"")); self._sf[k]=e
        ctk.CTkLabel(sc,text="شعار التطبيق:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(anchor="e",padx=18,pady=(14,4))
        logo_f=ctk.CTkFrame(sc,fg_color="transparent"); logo_f.pack(fill="x",padx=18)
        self._btn(logo_f,"📁 شعار شاشة الدخول",lambda:self._change_logo("logo_login"),C["surface"],210,42).pack(side="right",padx=4)
        self._btn(logo_f,"📁 شعار الفاتورة",lambda:self._change_logo("logo_invoice"),C["surface"],210,42).pack(side="right",padx=4)
        # Preview
        self._logo_preview=ctk.CTkLabel(sc,text="",font=(FONT,_fs(10)),text_color=C["txt_m"])
        self._logo_preview.pack(anchor="e",padx=18,pady=(4,0))
        self._update_logo_preview()
        # Thermal printer selector
        prn_row=ctk.CTkFrame(sc,fg_color="transparent"); prn_row.pack(fill="x",padx=18,pady=8)
        ctk.CTkLabel(prn_row,text="الطابعة الحرارية:",font=(FONT,_fs(12)),text_color=C["txt_s"],width=230).pack(side="right")
        self._thermal_printer_var=ctk.StringVar(value=self.db.setting("thermal_printer",""))
        printers=[""]; avail=[]
        try:
            import win32print
            for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS):
                printers.append(p[2]); avail.append(p[2])
        except: printers.append("(غير متاح)")
        self._thermal_cb=ctk.CTkOptionMenu(prn_row,values=printers,variable=self._thermal_printer_var,
            font=(FONT,_fs(12)),fg_color=C["inp"],button_color=C["inp_b"],text_color=C["txt"],
            width=300,height=38)
        self._thermal_cb.pack(side="right",padx=8)
        ctk.CTkLabel(sc,text="💡 الطابعة الحرارية تطبع الفواتير مباشرة بزر '🖨 حراري' في نافذة الفاتورة",
            font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(anchor="e",padx=18)
        # Theme selector
        th_row=ctk.CTkFrame(sc,fg_color="transparent"); th_row.pack(fill="x",padx=18,pady=8)
        ctk.CTkLabel(th_row,text="المظهر:",font=(FONT,_fs(12)),text_color=C["txt_s"],width=230).pack(side="right")
        self._theme_labels={"dawn":"🌙 داسك (داكن)","bloom":"☀️ بلوم (فاتح)","emerald":"🌿 زمردي","royal":"💜 ملكي",
            "sandy":"🏜 رملي","neon":"💠 نيون","classic":"🔷 كلاسيك"}
        cur_theme=self.db.setting("theme","dawn")
        self._theme_var=ctk.StringVar(value=self._theme_labels.get(cur_theme,"🌙 داسك (داكن)"))
        self._theme_keys=ctk.StringVar(value=cur_theme)
        def th_changed(choice):
            for k,v in self._theme_labels.items():
                if v==choice: self._theme_keys.set(k); break
        ctk.CTkOptionMenu(th_row,values=list(self._theme_labels.values()),variable=self._theme_var,
            font=(FONT,_fs(12)),fg_color=C["inp"],button_color=C["inp_b"],text_color=C["txt"],
            width=300,height=38,command=th_changed).pack(side="right",padx=8)
        # Font scale
        fs_row=ctk.CTkFrame(sc,fg_color="transparent"); fs_row.pack(fill="x",padx=18,pady=8)
        ctk.CTkLabel(fs_row,text="حجم الخط:",font=(FONT,_fs(12)),text_color=C["txt_s"],width=230).pack(side="right")
        self._font_scale_var=ctk.StringVar(value=self.db.setting("font_scale","1.0"))
        fs_opts=["0.8","0.9","1.0","1.1","1.2","1.3"]
        ctk.CTkOptionMenu(fs_row,values=fs_opts,variable=self._font_scale_var,
            font=(FONT,_fs(12)),fg_color=C["inp"],button_color=C["inp_b"],text_color=C["txt"],
            width=300,height=38).pack(side="right",padx=8)
        self._btn(sc,"💾 حفظ الإعدادات",self._save_sys,C["success"],200,46).pack(pady=18,anchor="e",padx=18)

    def _save_sys(self):
        for k,e in self._sf.items(): self.db.set_setting(k,e.get().strip())
        self.db.set_setting("thermal_printer",self._thermal_printer_var.get())
        new_scale=self._font_scale_var.get()
        old_scale=self.db.setting("font_scale","1.0")
        self.db.set_setting("font_scale",new_scale)
        old_theme=self.db.setting("theme","dawn")
        new_theme=self._theme_keys.get()
        self.db.set_setting("theme",new_theme)
        self.title(f"Cure Enterprise v{VER}  —  {self._sf['pharmacy_name'].get()}")
        needs_restart=(old_theme!=new_theme or old_scale!=new_scale)
        if needs_restart:
            Toast.show(self,"✓ تم الحفظ. أعد تشغيل البرنامج لتطبيق المظهر وحجم الخط.","info",5000)
        else:
            Toast.show(self,"✓ تم حفظ الإعدادات.","success")

    def _change_logo(self,key="logo_login"):
        p=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.ico")])
        if p:
            ad=os.path.join(app_dir(),"assets"); os.makedirs(ad,exist_ok=True)
            ext=os.path.splitext(p)[1]; dest=os.path.join(ad,f"{key}{ext}")
            shutil.copy(p,dest)
            self.db.set_setting(key,dest)
            self._update_logo_preview()
            Toast.show(self,f"✓ تم تحديث {('شاشة الدخول' if key=='logo_login' else 'الفاتورة')}","success")

    def _update_logo_preview(self):
        ll=self.db.setting("logo_login",""); li=self.db.setting("logo_invoice","")
        txt=f"شاشة الدخول: {'✅ موجود' if ll and os.path.exists(ll) else '❌ افتراضي'}  |  "
        txt+=f"الفاتورة: {'✅ موجود' if li and os.path.exists(li) else '❌ افتراضي'}"
        self._logo_preview.configure(text=txt)

    def _build_profile(self,parent):
        sc=ctk.CTkScrollableFrame(parent,fg_color="transparent"); sc.pack(fill="both",expand=True)
        ctk.CTkLabel(sc,text=f"👤  {self.user['full_name']}",font=(FONT,_fs(18),"bold"),text_color=C["txt"]).pack(pady=18)
        ctk.CTkLabel(sc,text=f"الدور: {ROLES.get(self.user['role'],self.user['role'])}",
            font=(FONT,_fs(13)),text_color=C["txt_s"]).pack()
        ctk.CTkLabel(sc,text=f"آخر دخول: {self.user.get('last_login','') or 'غير متاح'}",
            font=(FONT,_fs(12)),text_color=C["txt_m"]).pack(pady=(2,18))
        def _l(t): ctk.CTkLabel(sc,text=t,font=(FONT,_fs(11)),text_color=C["txt_s"]).pack(anchor="e",padx=44,pady=(8,2))
        _l("الاسم الكامل:")
        self._pn=self._ent(sc,"الاسم الكامل",320); self._pn.pack(anchor="e",padx=44)
        self._pn.insert(0,self.user["full_name"])
        _l("كلمة المرور الجديدة (اتركها فارغة للإبقاء):")
        self._pp1=ctk.CTkEntry(sc,show="●",width=320,height=42,justify="right",
            font=(FONT,_fs(13)),fg_color=C["inp"],text_color=C["txt"]); self._pp1.pack(anchor="e",padx=44)
        _l("تأكيد كلمة المرور:")
        self._pp2=ctk.CTkEntry(sc,show="●",width=320,height=42,justify="right",
            font=(FONT,_fs(13)),fg_color=C["inp"],text_color=C["txt"]); self._pp2.pack(anchor="e",padx=44,pady=(0,12))
        self._btn(sc,"📸 تغيير الصورة الشخصية",self._change_pic,C["surface"],240).pack(anchor="e",padx=44,pady=4)
        self._btn(sc,"💾 حفظ التعديلات",self._save_profile,C["success"],200,46).pack(anchor="e",padx=44,pady=16)

    def _save_profile(self):
        name=self._pn.get().strip(); pw1=self._pp1.get(); pw2=self._pp2.get()
        if not name: Toast.show(self,"الاسم لا يمكن أن يكون فارغاً","error"); return
        if pw1:
            if pw1!=pw2: Toast.show(self,"كلمتا المرور غير متطابقتين","error"); return
            if len(pw1)<6: Toast.show(self,"6 أحرف على الأقل","error"); return
            h=hashlib.sha256(pw1.encode()).hexdigest()
            self.db.run("UPDATE users SET full_name=?,password=? WHERE id=?",(name,h,self.user["id"]))
        else:
            self.db.run("UPDATE users SET full_name=? WHERE id=?",(name,self.user["id"]))
        self.user["full_name"]=name; Toast.show(self,"✓ تم تحديث بياناتك","success")

    def _change_pic(self):
        p=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg")])
        if p:
            pd=os.path.join(app_dir(),"profiles"); os.makedirs(pd,exist_ok=True); ext=os.path.splitext(p)[1]
            dest=os.path.join(pd,f"user_{self.user['id']}{ext}"); shutil.copy(p,dest)
            self.db.run("UPDATE users SET photo_path=? WHERE id=?",(dest,self.user["id"]))
            Toast.show(self,"✓ تم تحديث الصورة الشخصية","success")

    def _build_advanced(self,parent):
        sc=ctk.CTkScrollableFrame(parent,fg_color="transparent"); sc.pack(fill="both",expand=True)
        ctk.CTkLabel(sc,text="🛡  إعدادات متقدمة (للمدير فقط)",font=(FONT,_fs(16),"bold"),
            text_color=C["warning"]).pack(anchor="e",padx=18,pady=(14,4))
        self._sep(sc)

        # Backup
        bkf=ctk.CTkFrame(sc,fg_color="transparent"); bkf.pack(fill="x",padx=18,pady=8)
        ctk.CTkLabel(bkf,text="نسخ احتياطي لقاعدة البيانات:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(side="right",padx=8)
        self._btn(bkf,"📦 إنشاء نسخة احتياطية",self._do_backup,C["accent"],200,40).pack(side="right")

        self._sep(sc)

        # Clear history section — intentionally discreet
        clr=ctk.CTkFrame(sc,fg_color="transparent"); clr.pack(fill="x",padx=18,pady=8)
        ctk.CTkLabel(clr,text="مسح السجلات:",font=(FONT,_fs(12)),text_color=C["txt_s"]).pack(anchor="e")
        ctk.CTkLabel(clr,text="الإجراءات أدناه غير قابلة للتراجع. يُطلب كلمة سر المدير للتأكيد.",
            font=(FONT,_fs(10)),text_color=C["txt_m"]).pack(anchor="e",pady=(2,8))

        # Hidden-style buttons (discreet)
        btn_f=ctk.CTkFrame(clr,fg_color="transparent"); btn_f.pack(anchor="e")
        for txt,scope in [("مسح سجل اليوم","day"),("مسح كل السجلات","all")]:
            b=ctk.CTkButton(btn_f,text=txt,font=(FONT,_fs(11)),height=32,
                fg_color="transparent",text_color=C["txt_m"],
                hover_color="#2d0a0a",corner_radius=4,
                command=lambda s=scope:self._clear_history(s))
            b.pack(side="right",padx=6)

    def _do_backup(self):
        import shutil
        try:
            bdir=_BASE
            src=os.path.join(bdir,"data","cure_v4.db")
            if os.path.exists(src):
                ts=datetime.now().strftime("%Y%m%d_%H%M%S")
                dst=os.path.join(bdir,"data",f"backup_cure_{ts}.db")
                shutil.copy2(src,dst)
                Toast.show(self,f"✓ نسخة احتياطية: backup_cure_{ts}.db","success")
        except Exception as e: Toast.show(self,f"خطأ في النسخ: {e}","error")

    def _clear_history(self,scope):
        # Verify admin password
        pw=simpledialog.askstring("تأكيد المدير","أدخل كلمة سر المدير للمتابعة:",show="●",parent=self)
        if not pw: return
        h=hashlib.sha256(pw.encode()).hexdigest()
        admin=self.db.q1("SELECT id FROM users WHERE role='admin' AND password=? AND is_active=1",(h,))
        if not admin:
            Toast.show(self,"❌ كلمة سر المدير غير صحيحة","error"); return
        if not messagebox.askyesno("❗ تأكيد خطير","هذا الإجراء لا يمكن التراجع عنه. هل أنت متأكد تماماً؟"):
            return
        try:
            tables={"day":"activity_log","all":"activity_log,sales,sale_items,ledger,credit_payments"}
            if scope=="day":
                today=datetime.now().strftime("%Y-%m-%d")
                self.db.run("DELETE FROM activity_log WHERE date(created_at)=?",(today,))
                Toast.show(self,f"✓ تم مسح سجل اليوم","success")
            else:
                self.db.con.executescript("""
                    DELETE FROM credit_payments;
                    DELETE FROM sale_items;
                    DELETE FROM sales;
                    DELETE FROM ledger;
                    DELETE FROM activity_log;
                """)
                self.db.log(admin["id"],"CLEAR_ALL","مسح جميع السجلات")
                Toast.show(self,"✓ تم مسح جميع السجلات (باستثناء الأدوية والمستخدمين)","success")
        except Exception as e: Toast.show(self,f"خطأ: {e}","error")


# ═══════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════
if __name__ == "__main__":
    _BASE = os.path.dirname(os.path.abspath(__file__))
    ad=app_dir()
    for d in ("data","assets","profiles","invoices","exports"):
        os.makedirs(os.path.join(ad, d), exist_ok=True)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    LoginWindow().mainloop()
