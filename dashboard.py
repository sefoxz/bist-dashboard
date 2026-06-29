import streamlit as st
import pandas as pd
import time
import requests
import contextlib
import pytz
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import numpy as np
from requests.adapters import HTTPAdapter

st.set_page_config(page_title="BIST Radar Pro", page_icon="📈", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0b0f19 0%, #0d1525 100%); color: #e0e6f0; }
    .top-band { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
    .metric-box {
        background: #111827; border: 1px solid #1e293b; border-radius: 14px;
        padding: 14px 22px; flex: 1; min-width: 130px; text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: 0.2s;
    }
    .metric-box:hover { border-color: #3b82f6; box-shadow: 0 0 18px rgba(59,130,246,0.15); }
    .metric-label { font-size: 12px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 22px; font-weight: 700; color: #f1f5f9; margin: 4px 0; }
    .metric-change { font-size: 13px; font-weight: 500; }
    .change-up { color: #10b981; }
    .change-down { color: #ef4444; }
    .update-time { font-size: 13px; color: #64748b; text-align: right; }
    .stock-card {
        background: #111827; border: 1px solid #1e293b; border-radius: 16px;
        padding: 18px 22px; margin: 8px 0;
        border-left: 4px solid #3b82f6;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2); transition: 0.2s;
    }
    .stock-card:hover { border-color: #3b82f6; box-shadow: 0 4px 16px rgba(59,130,246,0.2); }
    .stock-card.skor-80 { border-left-color: #3b82f6; }
    .stock-card.skor-60 { border-left-color: #f59e0b; }
    .stock-card.skor-diger { border-left-color: #6b7280; }
    .stock-name { font-size: 18px; font-weight: 700; color: #f1f5f9; }
    .stock-sector { font-size: 12px; color: #64748b; margin-left: 8px; }
    .stock-details { font-size: 13px; color: #94a3b8; line-height: 1.6; }
    .stock-score { font-size: 28px; font-weight: 700; }
    .score-high { color: #3b82f6; }
    .score-mid { color: #f59e0b; }
    .score-low { color: #6b7280; }
    .stButton > button {
        background: #1e293b; color: #e0e6f0; border: 1px solid #334155; border-radius: 10px;
        font-weight: 600; padding: 10px 24px; transition: 0.2s;
    }
    .stButton > button:hover { background: #334155; border-color: #3b82f6; }
    .stDataFrame { background: #111827; border: 1px solid #1e293b; border-radius: 12px; }
    .stDataFrame th { background: #1e293b; color: #94a3b8; font-weight: 600; }
    .stDataFrame td { color: #e0e6f0; }
    .stSlider > div > div > div { background: #3b82f6; }
    .stRadio > div { gap: 10px; }
    .stRadio label { color: #94a3b8; }
    .stTextInput > div > div > input { background: #111827; color: white; border: 1px solid #1e293b; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

class DevNull:
    def write(self, msg): pass
    def flush(self): pass

YF = requests.Session()
YF.headers.update({"User-Agent": "Mozilla/5.0"})

class TA(HTTPAdapter):
    def send(self, r, **k):
        k['timeout'] = 5
        return super().send(r, **k)
YF.mount("https://", TA())

def _cek(obj, **kw):
    for _ in range(2):
        try:
            with contextlib.redirect_stderr(DevNull()), contextlib.redirect_stdout(DevNull()):
                h = obj.history(**kw)
            if h is not None and not h.empty: return h
        except: time.sleep(0.3)
    return pd.DataFrame()

HISSE_SEKTOR = {
    "AEFES": "Gida", "AGHOL": "Holding", "AHGAZ": "Enerji", "AKCNS": "Cimento", "AKFGY": "Gyo", "AKSA": "Kimya", "AKSEN": "Enerji", "ALARK": "Holding", "ALBRK": "Banka", "ALFAS": "Enerji", "ALGYO": "Gyo", "ARDYZ": "Teknoloji", "ARENA": "Teknoloji", "ASTOR": "Enerji", "BERA": "Gida", "BOBET": "Kimya", "BRSAN": "DemirCelik", "BRYAT": "DemirCelik", "BUCIM": "Cimento", "CANTE": "Cimento", "CATES": "Enerji", "CCOLA": "Gida", "CIMSA": "Cimento", "CWENE": "Enerji", "DEVA": "Ilac", "DOAS": "Otomotiv", "ECILC": "DemirCelik", "EGEEN": "Tekstil", "ENJSA": "Enerji", "EUPWR": "Enerji", "EURPN": "Tekstil", "FENER": "Spor", "FORTE": "Teknoloji", "GENIL": "Enerji", "GESAN": "Enerji", "GLYHO": "Gyo", "GSDHO": "Holding", "GUBRF": "Kimya", "GWIND": "Enerji", "HATSN": "Teknoloji", "HEKTS": "Teknoloji", "INDES": "Teknoloji", "INFO": "Teknoloji", "ISGYO": "Gyo", "ISMEN": "Gyo", "IZENR": "Enerji", "KARSN": "Otomotiv", "KCAER": "DemirCelik", "KONTR": "Savunma", "KONYA": "Cimento", "KORDS": "Tekstil", "MAVI": "Tekstil", "MIATK": "Teknoloji", "MPARK": "Saglik", "OYAKC": "Cimento", "POLHO": "Kimya", "QUAGR": "Gida", "REEDR": "Teknoloji", "RYSAS": "Teknoloji", "SAYAS": "Enerji", "SDTTR": "Savunma", "SMRTG": "Teknoloji", "SOKM": "Perakende", "TSKB": "Banka", "TTRAK": "Otomotiv", "VESBE": "Otomotiv", "VESTL": "BeyazEsya", "YEOTK": "Enerji", "ZOREN": "Enerji", "ADEL": "Kimya", "ALCAR": "Otomotiv", "ANHYT": "Sigorta", "AVOD": "Gida", "AYDEM": "Enerji", "BAYRK": "Tekstil", "BJKAS": "Spor", "CEMTS": "Cimento", "CLEBI": "Ulastirma", "COSMO": "Teknoloji", "DAPGM": "Gida", "DESA": "Tekstil", "DGATE": "Teknoloji", "EDATA": "Teknoloji", "ERBOS": "DemirCelik", "ESCOM": "Teknoloji", "FLAP": "Enerji", "FONET": "Teknoloji", "GOODY": "Gida", "HUNER": "Teknoloji", "IHGZT": "Medya", "INVEO": "Gida", "IPEKE": "Teknoloji", "KARTN": "Kagit", "KERVT": "Gida", "KLNMA": "Kimya", "KRVGD": "Teknoloji", "KUYAS": "DemirCelik", "LIDER": "Teknoloji", "LKMNH": "Kimya", "MARTI": "Turizm", "MEGAP": "Enerji", "MERIT": "Savunma", "MTRKS": "Teknoloji", "NATEN": "Enerji", "NUHCM": "Cimento", "PAPIL": "Savunma", "PEKGY": "Gyo", "PLTUR": "Ulastirma", "PRZMA": "Enerji", "PSGYO": "Gyo", "RODRG": "Enerji", "RTALB": "Gida", "SANFM": "Enerji", "SELGD": "Gida", "SILVR": "Teknoloji", "SMART": "Teknoloji", "SNGYO": "Gyo", "TABGD": "Gida", "TDGYO": "Gyo", "TGSAS": "Kimya", "TMSN": "DemirCelik", "TSPOR": "Spor", "ULKER": "Gida", "UZERB": "Gida", "VERTU": "Enerji", "VKING": "Enerji", "YATAS": "Tekstil", "YUNSA": "Tekstil"
}
HISSE_LISTESI = list(HISSE_SEKTOR.keys())

def tr_saat():
    return datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M:%S')

def bist100_durumu():
    try:
        e = yf.Ticker("XU100.IS", session=YF)
        h = _cek(e, period="5d")
        if h.empty or len(h) < 2: return None, None
        s = float(h['Close'].iloc[-1]); o = float(h['Close'].iloc[-2])
        return s, ((s-o)/o)*100
    except: return None, None

def dolar_kuru():
    try:
        e = yf.Ticker("USDTRY=X", session=YF)
        h = _cek(e, period="2d")
        if h.empty or len(h) < 2: return None, None
        s = float(h['Close'].iloc[-1]); o = float(h['Close'].iloc[-2])
        return s, ((s-o)/o)*100
    except: return None, None

def euro_kuru():
    try:
        e = yf.Ticker("EURTRY=X", session=YF)
        h = _cek(e, period="2d")
        if h.empty or len(h) < 2: return None, None
        s = float(h['Close'].iloc[-1]); o = float(h['Close'].iloc[-2])
        return s, ((s-o)/o)*100
    except: return None, None

def gram_altin():
    # 1. Deneme: yfinance ile gram altın (GAUTRY=X)
    try:
        e = yf.Ticker("GAUTRY=X", session=YF)
        h = _cek(e, period="2d")
        if not h.empty and len(h) >= 2:
            s = float(h['Close'].iloc[-1]); o = float(h['Close'].iloc[-2])
            return s, ((s-o)/o)*100
    except: pass

    # 2. Deneme: yfinance ons altın ve USD/TRY ile hesaplama
    try:
        ons = yf.Ticker("GC=F", session=YF)
        h_ons = _cek(ons, period="2d")
        usd = yf.Ticker("USDTRY=X", session=YF)
        h_usd = _cek(usd, period="2d")
        if not h_ons.empty and len(h_ons) >= 2 and not h_usd.empty and len(h_usd) >= 2:
            ons_f = float(h_ons['Close'].iloc[-1]); usd_f = float(h_usd['Close'].iloc[-1])
            ons_o = float(h_ons['Close'].iloc[-2]); usd_o = float(h_usd['Close'].iloc[-2])
            gram_f = (ons_f * usd_f) / 31.1035
            gram_o = (ons_o * usd_o) / 31.1035
            return gram_f, ((gram_f - gram_o) / gram_o) * 100
    except: pass

    # 3. Deneme: GenelPara API (ücretsiz, anlık veri)
    try:
        r = requests.get("https://api.genelpara.com/embed/para-birimleri.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if "GA" in data:
                gram_f = float(data["GA"]["satis"])
                # API anlık veri verdiği için önceki günü bilmiyoruz, değişim %0.00
                return gram_f, 0.0
    except: pass

    return None, None

def analiz_et(kod):
    t = f"{kod}.IS"
    try:
        o = yf.Ticker(t, session=YF)
        h = _cek(o, period="3mo")
        if h.empty or len(h) < 30: return None
        f = float(h['Close'].iloc[-1])
        ph = float(h['High'].iloc[-2]); pl = float(h['Low'].iloc[-2]); pc = float(h['Close'].iloc[-2])
        pv = (ph+pl+pc)/3; s1 = round((pv*2)-ph,2); r1 = round((pv*2)-pl,2)
        tr = pd.concat([h['High']-h['Low'], (h['High']-h['Close'].shift()).abs(), (h['Low']-h['Close'].shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1]) if len(tr)>=14 else f*0.03
        delta = h['Close'].diff(); gain = delta.where(delta>0,0).rolling(14).mean(); loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain/loss.replace(0,0.00001); rsi = 100-(100/(1+rs)); rv = float(rsi.iloc[-1])
        ma10 = float(h['Close'].rolling(10).mean().iloc[-1]); ma20 = float(h['Close'].rolling(20).mean().iloc[-1]); ma30 = float(h['Close'].rolling(30).mean().iloc[-1])
        hv = float(h['Volume'].iloc[-1]); oh = float(h['Volume'].rolling(20).mean().iloc[-1]); ho = hv/oh if oh>0 else 0
        e12 = h['Close'].ewm(span=12, adjust=False).mean(); e26 = h['Close'].ewm(span=26, adjust=False).mean()
        macd = e12-e26; sig = macd.ewm(span=9, adjust=False).mean(); ma = macd.iloc[-1] > sig.iloc[-1]
        d20 = float(h['High'].iloc[:-1].tail(20).max()) if not h['High'].iloc[:-1].tail(20).empty else float(h['High'].iloc[-1])
        skor=60
        if rv>65: skor-=25
        elif rv<35: skor+=20
        if f>ma20: skor+=10
        else: skor-=10
        if f<=ma10: skor-=15
        if f<=ma30: skor-=10
        if ma: skor+=10
        if ho>=2.0: skor+=5
        if f>d20: skor+=15
        skor=max(10,min(95,skor))
        if skor>=80: karar="GÜÇLÜ AL"
        elif skor>=60: karar="KADEMELİ AL"
        else: karar="BEKLE"
        if rv>65: rd=f"RSI {rv:.1f} 🔴"
        elif rv<35: rd=f"RSI {rv:.1f} 🟢"
        else: rd=f"RSI {rv:.1f} ⚪"
        return {"hisse":kod,"fiyat":round(f,2),"skor":skor,"karar":karar,"rsi_durum":rd,"ideal":round(f*0.985,2),"tp":round(f*1.08,2),"sl":round(f*0.95,2),"s1":s1,"r1":r1,"d20":round(d20,2),"ma10":round(ma10,2),"ma30":round(ma30,2),"hacim":round(ho,1)}
    except: return None

# ==========================================
# ARAYÜZ
# ==========================================
col_title, col_time = st.columns([3, 1])
with col_title: st.title("📊 BIST Radar Pro")
with col_time: st.markdown(f'<div class="update-time">🕐 Son güncelleme:<br><b>{st.session_state.get("son_guncelleme", tr_saat())}</b></div>', unsafe_allow_html=True)

if 'son_guncelleme' not in st.session_state: st.session_state.son_guncelleme = tr_saat()
if 'veri' not in st.session_state: st.session_state.veri = None

col_btn, col_empty = st.columns([1, 3])
with col_btn:
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.session_state.son_guncelleme = tr_saat()
        st.session_state.veri = None
        st.rerun()

if st.session_state.veri is None:
    with st.spinner('📡 Piyasa verileri alınıyor...'):
        bist_f, bist_d = bist100_durumu()
        usd_f, usd_d = dolar_kuru()
        eur_f, eur_d = euro_kuru()
        alt_f, alt_d = gram_altin()
        sonuclar = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            fs = {ex.submit(analiz_et, k): k for k in HISSE_LISTESI}
            for f in fs:
                try:
                    a = f.result()
                    if a: sonuclar.append(a)
                except: pass
        sonuclar.sort(key=lambda x: x["skor"], reverse=True)
        skorlar, sayilar = {}, {}
        for a in sonuclar:
            s = HISSE_SEKTOR.get(a["hisse"],"Diger")
            skorlar[s] = skorlar.get(s,0)+a["skor"]
            sayilar[s] = sayilar.get(s,0)+1
        sektor_ort = {s: round(skorlar[s]/sayilar[s],1) for s in skorlar}
        sirali = sorted(sektor_ort.items(), key=lambda x: x[1], reverse=True)
        st.session_state.veri = {
            "bist_f": bist_f, "bist_d": bist_d,
            "usd_f": usd_f, "usd_d": usd_d,
            "eur_f": eur_f, "eur_d": eur_d,
            "alt_f": alt_f, "alt_d": alt_d,
            "sonuclar": sonuclar, "sektor_ort": sektor_ort, "sirali": sirali
        }

veri = st.session_state.veri

# Üst bant
st.markdown('<div class="top-band">', unsafe_allow_html=True)
metrics = [
    ("BIST 100", veri['bist_f'], veri['bist_d'], "📈"),
    ("USD/TRY", veri['usd_f'], veri['usd_d'], "💵"),
    ("EUR/TRY", veri['eur_f'], veri['eur_d'], "💶"),
    ("Gram Altın", veri['alt_f'], veri['alt_d'], "🥇"),
]
for label, deger, degisim, ikon in metrics:
    if deger is None:
        st.markdown(f'<div class="metric-box"><div class="metric-label">{ikon} {label}</div><div class="metric-value">---</div></div>', unsafe_allow_html=True)
    else:
        change_class = "change-up" if degisim >= 0 else "change-down"
        change_sign = "+" if degisim >= 0 else ""
        fmt = f"{deger:,.2f}"
        st.markdown(f'<div class="metric-box"><div class="metric-label">{ikon} {label}</div><div class="metric-value">{fmt}</div><div class="metric-change {change_class}">{change_sign}{degisim:.2f}%</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Manuel hisse sorgulama
st.divider()
col_man, col_btn_man = st.columns([3, 1])
with col_man:
    manuel_hisse = st.text_input("🔍 Harici hisse sorgula (örn: THYAO, GARAN)", placeholder="Hisse kodu yazın ve butona basın...").upper().strip()
with col_btn_man:
    st.write("")
    if st.button("🔎 Sorgula", use_container_width=True) and manuel_hisse:
        with st.spinner(f'{manuel_hisse} analiz ediliyor...'):
            analiz = analiz_et(manuel_hisse)
            if analiz:
                sk = analiz['skor']
                border_class = "skor-80" if sk>=80 else ("skor-60" if sk>=60 else "skor-diger")
                score_class = "score-high" if sk>=80 else ("score-mid" if sk>=60 else "score-low")
                emoji = "🔥" if sk>=80 else ("📈" if sk>=60 else "📉")
                st.markdown(f'''<div class="stock-card {border_class}">
                    <div>
                        <span class="stock-name">#{analiz['hisse']}</span>
                        <div class="stock-details">💰 {analiz['fiyat']} TL | 🎯 Alım: {analiz['ideal']} | TP: {analiz['tp']} | SL: {analiz['sl']}</div>
                        <div class="stock-details">📊 {analiz['rsi_durum']} | Hacim: {analiz['hacim']}x | S1: {analiz['s1']} | R1: {analiz['r1']}</div>
                    </div>
                    <div style="text-align:right">
                        <div class="stock-score {score_class}">{sk}</div>
                        <div style="color:#94a3b8; font-size:13px;">{analiz['karar']} {emoji}</div>
                    </div>
                </div>''', unsafe_allow_html=True)
            else:
                st.error(f"{manuel_hisse} için veri bulunamadı.")

st.divider()
gorunum = st.radio("Görünüm", ["Kart", "Tablo"], horizontal=True)

# Sektör performansı - expander yok, her zaman görünür
st.subheader("📊 Sektör Performansları")
if veri['sektor_ort']:
    sdf = pd.DataFrame(list(veri['sektor_ort'].items()), columns=['Sektör','Ort. Skor'])
    st.dataframe(sdf.sort_values('Ort. Skor', ascending=False), use_container_width=True)

st.divider()

if veri['sonuclar']:
    df = pd.DataFrame(veri['sonuclar'])
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: ara = st.text_input("🔍 Listede ara", placeholder="Kod yazın...")
    with col2: ms = st.slider("Minimum skor", 0, 100, 60)
    with col3:
        sl = ["Tümü"] + sorted(set(HISSE_SEKTOR.get(h,"Diger") for h in df['hisse']))
        ss = st.selectbox("Sektör", sl)
    if ara: df = df[df['hisse'].str.contains(ara.upper())]
    if ss != "Tümü": df = df[df['hisse'].apply(lambda h: HISSE_SEKTOR.get(h,"Diger")) == ss]
    df = df[df['skor'] >= ms]
    df = df.sort_values('skor', ascending=False)
    
    if gorunum == "Kart":
        for _, r in df.iterrows():
            sk = r['skor']
            if sk >= 80: border_class = "skor-80"; score_class = "score-high"; emoji = "🔥"
            elif sk >= 60: border_class = "skor-60"; score_class = "score-mid"; emoji = "📈"
            else: border_class = "skor-diger"; score_class = "score-low"; emoji = "📉"
            sektor = HISSE_SEKTOR.get(r['hisse'], 'Diger')
            st.markdown(f'''<div class="stock-card {border_class}">
                <div>
                    <span class="stock-name">#{r['hisse']}</span><span class="stock-sector">{sektor}</span>
                    <div class="stock-details">💰 {r['fiyat']} TL | 🎯 İdeal Alım: {r['ideal']} | TP: {r['tp']} | SL: {r['sl']}</div>
                    <div class="stock-details">📊 {r['rsi_durum']} | Hacim: {r['hacim']}x | S1: {r['s1']} | R1: {r['r1']}</div>
                </div>
                <div style="text-align:right">
                    <div class="stock-score {score_class}">{sk}</div>
                    <div style="color:#94a3b8; font-size:13px;">{r['karar']} {emoji}</div>
                </div>
            </div>''', unsafe_allow_html=True)
    else:
        display_df = df[['hisse', 'fiyat', 'skor', 'karar', 'ideal', 'tp', 'sl', 'rsi_durum', 'hacim']].copy()
        display_df.columns = ['Hisse', 'Fiyat', 'Skor', 'Karar', 'Alım', 'TP', 'SL', 'RSI', 'Hacim']
        st.dataframe(display_df, use_container_width=True, height=600)
else:
    st.warning("Veri çekilemedi, lütfen yenileyin.")
