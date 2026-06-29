import streamlit as st
import pandas as pd
import time
import requests
import contextlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import numpy as np
from requests.adapters import HTTPAdapter

st.set_page_config(page_title="BIST Radar", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: white; }
    .card { background-color: #161b22; border-radius: 12px; padding: 20px; margin: 10px 0; border: 1px solid #30363d; }
    .skor-yuksek { color: #00d2ff; font-weight: bold; font-size: 24px; }
    .skor-orta { color: #ffd93d; font-weight: bold; font-size: 24px; }
    .skor-dusuk { color: #ff6b6b; font-weight: bold; font-size: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 BIST Smart Radar Pro")

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
    for _ in range(3):
        try:
            with contextlib.redirect_stderr(DevNull()), contextlib.redirect_stdout(DevNull()):
                h = obj.history(**kw)
            if h is not None and not h.empty: return h
        except: time.sleep(0.5)
    return pd.DataFrame()

HISSE_SEKTOR = {
    "AEFES": "Gida", "AGHOL": "Holding", "AHGAZ": "Enerji", "AKCNS": "Cimento", "AKFGY": "Gyo", "AKSA": "Kimya", "AKSEN": "Enerji", "ALARK": "Holding", "ALBRK": "Banka", "ALFAS": "Enerji", "ALGYO": "Gyo", "ARDYZ": "Teknoloji", "ARENA": "Teknoloji", "ASTOR": "Enerji", "BERA": "Gida", "BOBET": "Kimya", "BRSAN": "DemirCelik", "BRYAT": "DemirCelik", "BUCIM": "Cimento", "CANTE": "Cimento", "CATES": "Enerji", "CCOLA": "Gida", "CIMSA": "Cimento", "CWENE": "Enerji", "DEVA": "Ilac", "DOAS": "Otomotiv", "ECILC": "DemirCelik", "EGEEN": "Tekstil", "ENJSA": "Enerji", "EUPWR": "Enerji", "EURPN": "Tekstil", "FENER": "Spor", "FORTE": "Teknoloji", "GENIL": "Enerji", "GESAN": "Enerji", "GLYHO": "Gyo", "GSDHO": "Holding", "GUBRF": "Kimya", "GWIND": "Enerji", "HATSN": "Teknoloji", "HEKTS": "Teknoloji", "INDES": "Teknoloji", "INFO": "Teknoloji", "ISGYO": "Gyo", "ISMEN": "Gyo", "IZENR": "Enerji", "KARSN": "Otomotiv", "KCAER": "DemirCelik", "KONTR": "Savunma", "KONYA": "Cimento", "KORDS": "Tekstil", "MAVI": "Tekstil", "MIATK": "Teknoloji", "MPARK": "Saglik", "OYAKC": "Cimento", "POLHO": "Kimya", "QUAGR": "Gida", "REEDR": "Teknoloji", "RYSAS": "Teknoloji", "SAYAS": "Enerji", "SDTTR": "Savunma", "SMRTG": "Teknoloji", "SOKM": "Perakende", "TSKB": "Banka", "TTRAK": "Otomotiv", "VESBE": "Otomotiv", "VESTL": "BeyazEsya", "YEOTK": "Enerji", "ZOREN": "Enerji", "ADEL": "Kimya", "ALCAR": "Otomotiv", "ANHYT": "Sigorta", "AVOD": "Gida", "AYDEM": "Enerji", "BAYRK": "Tekstil", "BJKAS": "Spor", "CEMTS": "Cimento", "CLEBI": "Ulastirma", "COSMO": "Teknoloji", "DAPGM": "Gida", "DESA": "Tekstil", "DGATE": "Teknoloji", "EDATA": "Teknoloji", "ERBOS": "DemirCelik", "ESCOM": "Teknoloji", "FLAP": "Enerji", "FONET": "Teknoloji", "GOODY": "Gida", "HUNER": "Teknoloji", "IHGZT": "Medya", "INVEO": "Gida", "IPEKE": "Teknoloji", "KARTN": "Kagit", "KERVT": "Gida", "KLNMA": "Kimya", "KRVGD": "Teknoloji", "KUYAS": "DemirCelik", "LIDER": "Teknoloji", "LKMNH": "Kimya", "MARTI": "Turizm", "MEGAP": "Enerji", "MERIT": "Savunma", "MTRKS": "Teknoloji", "NATEN": "Enerji", "NUHCM": "Cimento", "PAPIL": "Savunma", "PEKGY": "Gyo", "PLTUR": "Ulastirma", "PRZMA": "Enerji", "PSGYO": "Gyo", "RODRG": "Enerji", "RTALB": "Gida", "SANFM": "Enerji", "SELGD": "Gida", "SILVR": "Teknoloji", "SMART": "Teknoloji", "SNGYO": "Gyo", "TABGD": "Gida", "TDGYO": "Gyo", "TGSAS": "Kimya", "TMSN": "DemirCelik", "TSPOR": "Spor", "ULKER": "Gida", "UZERB": "Gida", "VERTU": "Enerji", "VKING": "Enerji", "YATAS": "Tekstil", "YUNSA": "Tekstil"
}
HISSE_LISTESI = list(HISSE_SEKTOR.keys())

def bist100_durumu():
    try:
        e = yf.Ticker("XU100.IS", session=YF)
        h = _cek(e, period="5d")
        if h.empty or len(h) < 2: return "Veri Yok ⚪"
        s = float(h['Close'].iloc[-1]); o = float(h['Close'].iloc[-2])
        d = ((s-o)/o)*100
        if d > 0.15: return f"YÜKSELİŞ 📈 (%{d:+.2f})"
        elif d < -0.15: return f"DÜŞÜŞ 📉 (%{d:+.2f})"
        else: return f"NÖTR ⚪ (%{d:+.2f})"
    except: return "Veri Yok ⚪"

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
        if skor>=80: karar="GÜÇLÜ AL 🔥"
        elif skor>=60: karar="KADEMELİ AL 📈"
        else: karar="DİRENÇTE BEKLE 🛑"
        if rv>65: rd=f"Aşırı Alım 🔴 (RSI: {rv:.1f})"
        elif rv<35: rd=f"Aşırı Satım 🟢 (RSI: {rv:.1f})"
        else: rd=f"Nötr ⚪ (RSI: {rv:.1f})"
        return {"hisse":kod,"fiyat":round(f,2),"skor":skor,"robot_karari":karar,"rsi_durumu":rd,"ideal_alim":round(f*0.985,2),"tp":round(f*1.08,2),"sl":round(f*0.95,2),"s1":s1,"r1":r1,"direnc20":round(d20,2),"ma10":round(ma10,2),"ma30":round(ma30,2)}
    except: return None

# Session state ile yenileme kontrolü
if 'son_guncelleme' not in st.session_state:
    st.session_state.son_guncelleme = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
if 'veri' not in st.session_state:
    st.session_state.veri = None

if st.button("🔄 Verileri Anlık Çek", use_container_width=True):
    st.session_state.son_guncelleme = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    st.session_state.veri = None  # Cache'i temizle
    st.rerun()

# Veri yoksa veya butona basıldıysa yeniden çek
if st.session_state.veri is None:
    with st.spinner('📡 BIST hisseleri taranıyor...'):
        bist100 = bist100_durumu()
        sonuclar = []
        with ThreadPoolExecutor(max_workers=8) as ex:
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
            "bist100": bist100,
            "sonuclar": sonuclar,
            "sektor_ort": sektor_ort,
            "sirali": sirali
        }

veri = st.session_state.veri

col1, col2, col3 = st.columns([2,2,1])
with col1: st.markdown(f"### 🏛️ BIST 100: {veri['bist100']}")
with col2:
    g = veri['sirali'][0] if veri['sirali'] else ("-",0)
    z = veri['sirali'][-1] if veri['sirali'] else ("-",0)
    st.markdown(f"### 🟢 {g[0]} ({g[1]})")
    st.markdown(f"### 🔴 {z[0]} ({z[1]})")
with col3: st.markdown(f"🕐 {st.session_state.son_guncelleme}")
st.divider()

if veri['sektor_ort']:
    with st.expander("📊 Sektör Performansları", expanded=False):
        sdf = pd.DataFrame(list(veri['sektor_ort'].items()), columns=['Sektör','Skor'])
        st.dataframe(sdf.sort_values('Skor', ascending=False), use_container_width=True)

if veri['sonuclar']:
    df = pd.DataFrame(veri['sonuclar'])
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    with c1: ara = st.text_input("🔍 Hisse Ara")
    with c2: ms = st.slider("Min Skor",0,100,60)
    with c3:
        sl = ["Tümü"] + sorted(set(HISSE_SEKTOR.get(h,"Diger") for h in df['hisse']))
        ss = st.selectbox("Sektör", sl)
    with c4: sir = st.selectbox("Sırala",["Skor ▼","Skor ▲","Fiyat ▼","Fiyat ▲"])
    if ara: df = df[df['hisse'].str.contains(ara.upper())]
    if ss != "Tümü": df = df[df['hisse'].apply(lambda h: HISSE_SEKTOR.get(h,"Diger")) == ss]
    df = df[df['skor'] >= ms]
    if "Skor" in sir: df = df.sort_values('skor', ascending="▲" in sir)
    else: df = df.sort_values('fiyat', ascending="▲" in sir)
    for _, r in df.iterrows():
        sk = r['skor']; sc = "skor-yuksek" if sk>=80 else ("skor-orta" if sk>=60 else "skor-dusuk")
        em = "🔥" if sk>=80 else ("📈" if sk>=60 else "📉")
        st.markdown(f"""<div class="card"><div style="display:flex;justify-content:space-between"><div><h3>#{r['hisse']} {em} <small>({HISSE_SEKTOR.get(r['hisse'],'Diger')})</small></h3><p>💰 {r['fiyat']} TL | 🤖 {r['robot_karari']}</p><p>📊 {r['rsi_durumu']} | 🎯 Alım: {r['ideal_alim']} TL</p></div><div style="text-align:right"><span class="{sc}">{sk}/100</span><p>TP: {r['tp']} | SL: {r['sl']}</p><p>S1: {r['s1']} | R1: {r['r1']}</p></div></div></div>""", unsafe_allow_html=True)
else: st.warning("Veri çekilemedi.")
