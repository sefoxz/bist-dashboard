import streamlit as st
import pandas as pd
import json
import os
import time
import requests
import contextlib
import threading
import concurrent.futures
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import numpy as np
from requests.adapters import HTTPAdapter

# Streamlit sayfa ayarları
st.set_page_config(page_title="BIST Smart Radar Pro", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: white; }
    .card { background-color: #161b22; border-radius: 12px; padding: 20px; margin: 10px 0; border: 1px solid #30363d; }
    .skor-yuksek { color: #00d2ff; font-weight: bold; font-size: 24px; }
    .skor-orta { color: #ffd93d; font-weight: bold; font-size: 24px; }
    .skor-dusuk { color: #ff6b6b; font-weight: bold; font-size: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 BIST Smart Radar Pro Dashboard")

# ==========================================
# VERİ ÇEKME FONKSİYONLARI
# ==========================================
class DevNull:
    def write(self, msg): pass
    def flush(self): pass

YF_OTURUMU = requests.Session()
YF_OTURUMU.headers.update({"User-Agent": "Mozilla/5.0", "Accept-Language": "tr-TR"})

class ZamanAsimiAdaptoru(HTTPAdapter):
    def send(self, request, **kwargs):
        kwargs['timeout'] = 4
        return super().send(request, **kwargs)

YF_OTURUMU.mount("https://", ZamanAsimiAdaptoru())

def _veri_cek_retry(ticker_obj, **kwargs):
    for _ in range(2):
        try:
            with contextlib.redirect_stderr(DevNull()), contextlib.redirect_stdout(DevNull()):
                h = ticker_obj.history(**kwargs)
            if h is not None and not h.empty: return h
        except: pass
        time.sleep(0.5)
    return pd.DataFrame()

HISSE_SEKTOR = {
    "AEFES": "Gida", "AGHOL": "Holding", "AHGAZ": "Enerji", "AKCNS": "Cimento", "AKFGY": "Gyo", "AKSA": "Kimya", "AKSEN": "Enerji", "ALARK": "Holding", "ALBRK": "Banka", "ALFAS": "Enerji", "ALGYO": "Gyo", "ARDYZ": "Teknoloji", "ARENA": "Teknoloji", "ASTOR": "Enerji", "BERA": "Gida", "BOBET": "Kimya", "BRSAN": "DemirCelik", "BRYAT": "DemirCelik", "BUCIM": "Cimento", "CANTE": "Cimento", "CATES": "Enerji", "CCOLA": "Gida", "CIMSA": "Cimento", "CWENE": "Enerji", "DEVA": "Ilac", "DOAS": "Otomotiv", "ECILC": "DemirCelik", "EGEEN": "Tekstil", "ENJSA": "Enerji", "EUPWR": "Enerji", "EURPN": "Tekstil", "FENER": "Spor", "FORTE": "Teknoloji", "GENIL": "Enerji", "GESAN": "Enerji", "GLYHO": "Gyo", "GSDHO": "Holding", "GUBRF": "Kimya", "GWIND": "Enerji", "HATSN": "Teknoloji", "HEKTS": "Teknoloji", "INDES": "Teknoloji", "INFO": "Teknoloji", "ISGYO": "Gyo", "ISMEN": "Gyo", "IZENR": "Enerji", "KARSN": "Otomotiv", "KCAER": "DemirCelik", "KONTR": "Savunma", "KONYA": "Cimento", "KORDS": "Tekstil", "MAVI": "Tekstil", "MIATK": "Teknoloji", "MPARK": "Saglik", "OYAKC": "Cimento", "POLHO": "Kimya", "QUAGR": "Gida", "REEDR": "Teknoloji", "RYSAS": "Teknoloji", "SAYAS": "Enerji", "SDTTR": "Savunma", "SMRTG": "Teknoloji", "SOKM": "Perakende", "TSKB": "Banka", "TTRAK": "Otomotiv", "VESBE": "Otomotiv", "VESTL": "BeyazEsya", "YEOTK": "Enerji", "ZOREN": "Enerji", "ADEL": "Kimya", "ALCAR": "Otomotiv", "ANHYT": "Sigorta", "AVOD": "Gida", "AYDEM": "Enerji", "BAYRK": "Tekstil", "BJKAS": "Spor", "CEMTS": "Cimento", "CLEBI": "Ulastirma", "COSMO": "Teknoloji", "DAPGM": "Gida", "DESA": "Tekstil", "DGATE": "Teknoloji", "EDATA": "Teknoloji", "ERBOS": "DemirCelik", "ESCOM": "Teknoloji", "FLAP": "Enerji", "FONET": "Teknoloji", "GOODY": "Gida", "HUNER": "Teknoloji", "IHGZT": "Medya", "INVEO": "Gida", "IPEKE": "Teknoloji", "KARTN": "Kagit", "KERVT": "Gida", "KLNMA": "Kimya", "KRVGD": "Teknoloji", "KUYAS": "DemirCelik", "LIDER": "Teknoloji", "LKMNH": "Kimya", "MARTI": "Turizm", "MEGAP": "Enerji", "MERIT": "Savunma", "MTRKS": "Teknoloji", "NATEN": "Enerji", "NUHCM": "Cimento", "PAPIL": "Savunma", "PEKGY": "Gyo", "PLTUR": "Ulastirma", "PRZMA": "Enerji", "PSGYO": "Gyo", "RODRG": "Enerji", "RTALB": "Gida", "SANFM": "Enerji", "SELGD": "Gida", "SILVR": "Teknoloji", "SMART": "Teknoloji", "SNGYO": "Gyo", "TABGD": "Gida", "TDGYO": "Gyo", "TGSAS": "Kimya", "TMSN": "DemirCelik", "TSPOR": "Spor", "ULKER": "Gida", "UZERB": "Gida", "VERTU": "Enerji", "VKING": "Enerji", "YATAS": "Tekstil", "YUNSA": "Tekstil"
}

VARSAYILAN_HISSELER = list(HISSE_SEKTOR.keys())

def bist100_durumu_getir():
    try:
        endeks = yf.Ticker("XU100.IS", session=YF_OTURUMU)
        hist = _veri_cek_retry(endeks, period="5d", timeout=4)
        if hist.empty or len(hist) < 2: return "Veri Yok ⚪"
        son = float(hist['Close'].iloc[-1])
        onceki = float(hist['Close'].iloc[-2])
        d = ((son - onceki) / onceki) * 100
        if d > 0.15: return f"YÜKSELİŞ 📈 (%{d:+.2f})"
        elif d < -0.15: return f"DÜŞÜŞ 📉 (%{d:+.2f})"
        else: return f"NÖTR ⚪ (%{d:+.2f})"
    except: return "Veri Yok ⚪"

@st.cache_data(ttl=300)
def tum_hisseleri_tara():
    """Tüm hisseleri tarar ve sonuçları döndürür (5 dk cache)."""
    bist100 = bist100_durumu_getir()
    tum = []
    executor = ThreadPoolExecutor(max_workers=6)
    try:
        futures = {}
        for h in VARSAYILAN_HISSELER:
            futures[executor.submit(hisse_analiz_et, h)] = h
        for f in futures:
            try:
                a = f.result()
                if a: tum.append(a)
            except: pass
    finally: executor.shutdown(wait=False)
    tum.sort(key=lambda x: x["skor"], reverse=True)
    
    sektor_skorlar = {}
    sektor_sayilar = {}
    for h in tum:
        s = HISSE_SEKTOR.get(h["hisse"], "Diger")
        sektor_skorlar[s] = sektor_skorlar.get(s, 0) + h["skor"]
        sektor_sayilar[s] = sektor_sayilar.get(s, 0) + 1
    
    sektor_ort = {s: round(sektor_skorlar[s]/sektor_sayilar[s], 1) for s in sektor_skorlar}
    sirali = sorted(sektor_ort.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "son_guncelleme": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "bist100_durum": bist100,
        "hisseler": tum[:30],
        "sektor_ortalamalar": sektor_ort,
        "en_guclu_sektor": sirali[0] if sirali else ("-", 0),
        "en_zayif_sektor": sirali[-1] if sirali else ("-", 0)
    }

def hisse_analiz_et(ticker_sembol):
    ticker = f"{ticker_sembol}.IS"
    try:
        obj = yf.Ticker(ticker, session=YF_OTURUMU)
        hist = _veri_cek_retry(obj, period="3mo", timeout=4)
        if hist.empty or len(hist) < 30: return None
        
        fiyat = float(hist['Close'].iloc[-1])
        yuksek = float(hist['High'].iloc[-1])
        dusuk = float(hist['Low'].iloc[-1])
        
        prev_high = float(hist['High'].iloc[-2])
        prev_low = float(hist['Low'].iloc[-2])
        prev_close = float(hist['Close'].iloc[-2])
        pivot = (prev_high + prev_low + prev_close) / 3
        s1 = round((pivot * 2) - prev_high, 2)
        r1 = round((pivot * 2) - prev_low, 2)

        tr = pd.concat([hist['High']-hist['Low'], (hist['High']-hist['Close'].shift()).abs(), (hist['Low']-hist['Close'].shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else fiyat * 0.03

        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss.replace(0, 0.00001)
        rsi = 100 - (100 / (1 + rs))
        rsi_val = float(rsi.iloc[-1])

        ma10 = float(hist['Close'].rolling(10).mean().iloc[-1])
        ma20 = float(hist['Close'].rolling(20).mean().iloc[-1])
        ma30 = float(hist['Close'].rolling(30).mean().iloc[-1])
        
        hacim = float(hist['Volume'].iloc[-1])
        ortalama_hacim = float(hist['Volume'].rolling(20).mean().iloc[-1])
        hacim_orani = hacim / ortalama_hacim if ortalama_hacim > 0 else 0

        exp12 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_al = macd.iloc[-1] > signal.iloc[-1]

        onceki_high = hist['High'].iloc[:-1].tail(20)
        direnc20 = float(onceki_high.max()) if not onceki_high.empty else yuksek

        skor = 60
        if rsi_val > 65: skor -= 25
        elif rsi_val < 35: skor += 20
        if fiyat > ma20: skor += 10
        else: skor -= 10
        if fiyat <= ma10: skor -= 15
        if fiyat <= ma30: skor -= 10
        if macd_al: skor += 10
        if hacim_orani >= 2.0: skor += 5
        if fiyat > direnc20: skor += 15
        skor = max(10, min(95, skor))

        if skor >= 80: karar = "GÜÇLÜ AL 🔥"
        elif skor >= 60: karar = "KADEMELİ AL 📈"
        else: karar = "DİRENÇTE BEKLE 🛑"

        if rsi_val > 65: rsi_durum = f"Aşırı Alım 🔴 (RSI: {rsi_val:.1f})"
        elif rsi_val < 35: rsi_durum = f"Aşırı Satım 🟢 (RSI: {rsi_val:.1f})"
        else: rsi_durum = f"Nötr ⚪ (RSI: {rsi_val:.1f})"

        tp = round(fiyat * 1.08, 2)
        sl = round(fiyat * 0.95, 2)
        ideal = round(fiyat * 0.985, 2)

        return {
            "hisse": ticker_sembol, "fiyat": round(fiyat, 2),
            "skor": skor, "robot_karari": karar, "rsi_durumu": rsi_durum,
            "ideal_alim": ideal, "tp": tp, "sl": sl,
            "s1": s1, "r1": r1, "direnc20": round(direnc20, 2),
            "ma10": round(ma10, 2), "ma30": round(ma30, 2),
            "rsi_deger": round(rsi_val, 1), "hacim_orani": round(hacim_orani, 1)
        }
    except: return None

# ==========================================
# DASHBOARD ARAYÜZÜ
# ==========================================
if st.button("🔄 Verileri Yenile", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

try:
    veri = tum_hisseleri_tara()
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"### 🏛️ BIST 100: {veri.get('bist100_durum', 'Veri Yok')}")
    with col2:
        guclu = veri.get('en_guclu_sektor', ['-', 0])
        zayif = veri.get('en_zayif_sektor', ['-', 0])
        st.markdown(f"### 🟢 En Güçlü Sektör: {guclu[0]} ({guclu[1]})")
        st.markdown(f"### 🔴 En Zayıf Sektör: {zayif[0]} ({zayif[1]})")
    with col3:
        st.markdown(f"🕐 Son Güncelleme: {veri.get('son_guncelleme', '')}")
    
    st.divider()
    
    sektorler = veri.get('sektor_ortalamalar', {})
    if sektorler:
        with st.expander("📊 Sektör Performansları", expanded=False):
            sektor_df = pd.DataFrame(list(sektorler.items()), columns=['Sektör', 'Ortalama Skor'])
            sektor_df = sektor_df.sort_values('Ortalama Skor', ascending=False)
            st.dataframe(sektor_df, use_container_width=True)
    
    hisseler = veri.get("hisseler", [])
    if hisseler:
        df = pd.DataFrame(hisseler)
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1: arama = st.text_input("🔍 Hisse Ara", placeholder="Hisse kodu...")
        with col2: min_skor = st.slider("Min Skor", 0, 100, 60)
        with col3:
            sektorler_liste = ["Tümü"] + sorted(set(HISSE_SEKTOR.get(h, "Diger") for h in df['hisse']))
            secili_sektor = st.selectbox("Sektör", sektorler_liste)
        with col4: siralama = st.selectbox("Sırala", ["Skor ▼", "Skor ▲", "Fiyat ▼", "Fiyat ▲"])
        
        if arama: df = df[df['hisse'].str.contains(arama.upper())]
        if secili_sektor != "Tümü": df = df[df['hisse'].apply(lambda h: HISSE_SEKTOR.get(h, "Diger")) == secili_sektor]
        df = df[df['skor'] >= min_skor]
        
        if "Skor" in siralama: df = df.sort_values('skor', ascending="▲" in siralama)
        else: df = df.sort_values('fiyat', ascending="▲" in siralama)
        
        for _, row in df.iterrows():
            skor = row['skor']
            skor_class = "skor-yuksek" if skor >= 80 else ("skor-orta" if skor >= 60 else "skor-dusuk")
            emoji = "🔥" if skor >= 80 else ("📈" if skor >= 60 else "📉")
            sektor = HISSE_SEKTOR.get(row['hisse'], "Diger")
            
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3>#{row['hisse']} {emoji} <span style="font-size: 14px; color: #888;">({sektor})</span></h3>
                        <p>💰 {row['fiyat']} TL | 🤖 {row['robot_karari']}</p>
                        <p>📊 {row['rsi_durumu']} | 🎯 Alım: {row['ideal_alim']} TL</p>
                    </div>
                    <div style="text-align: right;">
                        <span class="{skor_class}">{skor}/100</span>
                        <p>TP: {row['tp']} TL | SL: {row['sl']} TL</p>
                        <p>S1: {row['s1']} | R1: {row['r1']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Veri çekilemedi, lütfen yenileyin.")
except Exception as e:
    st.error(f"Bir hata oluştu: {e}")
