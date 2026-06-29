import os, sys, json, time, requests, pytz, contextlib, threading, socket, concurrent.futures
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import pandas as pd
import numpy as np
import logging, warnings
from requests.adapters import HTTPAdapter

warnings.filterwarnings("ignore")
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

class DevNull:
    def write(self, msg): pass
    def flush(self): pass

socket.setdefaulttimeout(6)

AYAR = {
    "RSI_ASIRI_ALIM_ESIK": 65, "RSI_ASIRI_SATIM_ESIK": 35, "PUAN_ASIRI_ALIM": -25, "PUAN_ASIRI_SATIM": 20,
    "BASLANGIC_SKOR": 60, "PUAN_TREND_POZITIF": 10, "PUAN_TREND_NEGATIF": -10, "PUAN_MACD_AL": 10,
    "PUAN_HACIMLI_ALIM": 5, "SKOR_MIN": 10, "SKOR_MAKS": 95, "BIST100_DUSUS_ESIK": -1.0,
    "BIST100_DUSUS_PUAN": -15, "BIST100_YUKSELIS_ESIK": 1.5, "BIST100_YUKSELIS_PUAN": 5,
    "RS_ESIK_1": 5, "RS_PUAN_1": 5, "RS_ESIK_2": 10, "RS_PUAN_2": 10,
    "HACIM_ORANI_ESIK_1": 2.0, "HACIM_ORANI_PUAN_1": 5, "HACIM_ORANI_ESIK_2": 2.5, "HACIM_ORANI_PUAN_2": 10,
    "HACIM_ORANI_ESIK_3": 3.5, "HACIM_ORANI_PUAN_3": 15, "DIRENC20_KIRILIM_PUAN": 15,
    "HACIMLI_KIRILIM_HACIM_ORANI_ESIK": 2.0, "HACIMLI_KIRILIM_PUAN": 20,
    "DUSEN_BICAK_TOPLAM_DUSUS_ESIK": -0.12, "DUSEN_BICAK_SKOR_CEZASI": 40,
    "SKOR_GUCLU_AL_ESIK": 80, "SKOR_DIRENC_BEKLE_ESIK": 45,
    "TP_ATR_CARPAN": 2.0, "TP_YUZDE_MIN": 0.05, "TP_YUZDE_MAKS": 0.15,
    "SL_ATR_CARPAN": 1.5, "SL_YUZDE_MIN": 0.03, "SL_YUZDE_MAKS": 0.08,
    "DIBE_YAKINLIK_ESIK": 0.006, "ALIM_INDIRIM_ATR_CARPAN": 0.5, "ALIM_INDIRIM_MIN": 0.007, "ALIM_INDIRIM_MAKS": 0.015,
    "AG_TIMEOUT_SANIYE": 4, "RETRY_DENEME_SAYISI": 2, "RETRY_BEKLEME_SANIYE": 1.5,
    "MAX_WORKERS": 8, "TARAMA_TIMEOUT_SANIYE": 90,
    "SON_2GUN_DUSUS_ESIK": -0.05, "MA10_ALTINDA_CEZA": -15, "MA30_ALTINDA_CEZA": -10,
    "SEKTOR_GUCLU_ESIK": 1.0, "SEKTOR_ZAYIF_ESIK": -1.0,
    "SEKTOR_GUCLU_PUAN": 10, "SEKTOR_ZAYIF_PUAN": -10,
}

VARSAYILAN_HISSELER = ["AEFES","AGHOL","AHGAZ","AKCNS","AKFGY","AKSA","AKSEN","ALARK","ALBRK","ALFAS","ALGYO","ARDYZ","ARENA","ASTOR","BERA","BOBET","BRSAN","BRYAT","BUCIM","CANTE","CATES","CCOLA","CIMSA","CWENE","DEVA","DOAS","ECILC","EGEEN","ENJSA","EUPWR","EURPN","FENER","FORTE","GENIL","GESAN","GLYHO","GSDHO","GUBRF","GWIND","HATSN","HEKTS","INDES","INFO","ISGYO","ISMEN","IZENR","KARSN","KCAER","KONTR","KONYA","KORDS","MAVI","MIATK","MPARK","OYAKC","POLHO","QUAGR","REEDR","RYSAS","SAYAS","SDTTR","SMRTG","SOKM","TSKB","TTRAK","VESBE","VESTL","YEOTK","ZOREN","ADEL","ALCAR","ANHYT","AVOD","AYDEM","BAYRK","BJKAS","CEMTS","CLEBI","COSMO","DAPGM","DESA","DGATE","EDATA","ERBOS","ESCOM","FLAP","FONET","GOODY","HUNER","IHGZT","INVEO","IPEKE","KARTN","KERVT","KLNMA","KRVGD","KUYAS","LIDER","LKMNH","MARTI","MEGAP","MERIT","MTRKS","NATEN","NUHCM","PAPIL","PEKGY","PLTUR","PRZMA","PSGYO","RODRG","RTALB","SANFM","SELGD","SILVR","SMART","SNGYO","TABGD","TDGYO","TGSAS","TMSN","TSPOR","ULKER","UZERB","VERTU","VKING","YATAS","YUNSA"]

HISSE_SEKTOR = {
    "AEFES": "Gida", "AGHOL": "Holding", "AHGAZ": "Enerji", "AKCNS": "Cimento", "AKFGY": "Gyo", "AKSA": "Kimya", "AKSEN": "Enerji", "ALARK": "Holding", "ALBRK": "Banka", "ALFAS": "Enerji", "ALGYO": "Gyo", "ARDYZ": "Teknoloji", "ARENA": "Teknoloji", "ASTOR": "Enerji", "BERA": "Gida", "BOBET": "Kimya", "BRSAN": "DemirCelik", "BRYAT": "DemirCelik", "BUCIM": "Cimento", "CANTE": "Cimento", "CATES": "Enerji", "CCOLA": "Gida", "CIMSA": "Cimento", "CWENE": "Enerji", "DEVA": "Ilac", "DOAS": "Otomotiv", "ECILC": "DemirCelik", "EGEEN": "Tekstil", "ENJSA": "Enerji", "EUPWR": "Enerji", "EURPN": "Tekstil", "FENER": "Spor", "FORTE": "Teknoloji", "GENIL": "Enerji", "GESAN": "Enerji", "GLYHO": "Gyo", "GSDHO": "Holding", "GUBRF": "Kimya", "GWIND": "Enerji", "HATSN": "Teknoloji", "HEKTS": "Teknoloji", "INDES": "Teknoloji", "INFO": "Teknoloji", "ISGYO": "Gyo", "ISMEN": "Gyo", "IZENR": "Enerji", "KARSN": "Otomotiv", "KCAER": "DemirCelik", "KONTR": "Savunma", "KONYA": "Cimento", "KORDS": "Tekstil", "MAVI": "Tekstil", "MIATK": "Teknoloji", "MPARK": "Saglik", "OYAKC": "Cimento", "POLHO": "Kimya", "QUAGR": "Gida", "REEDR": "Teknoloji", "RYSAS": "Teknoloji", "SAYAS": "Enerji", "SDTTR": "Savunma", "SMRTG": "Teknoloji", "SOKM": "Perakende", "TSKB": "Banka", "TTRAK": "Otomotiv", "VESBE": "Otomotiv", "VESTL": "BeyazEsya", "YEOTK": "Enerji", "ZOREN": "Enerji", "ADEL": "Kimya", "ALCAR": "Otomotiv", "ANHYT": "Sigorta", "AVOD": "Gida", "AYDEM": "Enerji", "BAYRK": "Tekstil", "BJKAS": "Spor", "CEMTS": "Cimento", "CLEBI": "Ulastirma", "COSMO": "Teknoloji", "DAPGM": "Gida", "DESA": "Tekstil", "DGATE": "Teknoloji", "EDATA": "Teknoloji", "ERBOS": "DemirCelik", "ESCOM": "Teknoloji", "FLAP": "Enerji", "FONET": "Teknoloji", "GOODY": "Gida", "HUNER": "Teknoloji", "IHGZT": "Medya", "INVEO": "Gida", "IPEKE": "Teknoloji", "KARTN": "Kagit", "KERVT": "Gida", "KLNMA": "Kimya", "KRVGD": "Teknoloji", "KUYAS": "DemirCelik", "LIDER": "Teknoloji", "LKMNH": "Kimya", "MARTI": "Turizm", "MEGAP": "Enerji", "MERIT": "Savunma", "MTRKS": "Teknoloji", "NATEN": "Enerji", "NUHCM": "Cimento", "PAPIL": "Savunma", "PEKGY": "Gyo", "PLTUR": "Ulastirma", "PRZMA": "Enerji", "PSGYO": "Gyo", "RODRG": "Enerji", "RTALB": "Gida", "SANFM": "Enerji", "SELGD": "Gida", "SILVR": "Teknoloji", "SMART": "Teknoloji", "SNGYO": "Gyo", "TABGD": "Gida", "TDGYO": "Gyo", "TGSAS": "Kimya", "TMSN": "DemirCelik", "TSPOR": "Spor", "ULKER": "Gida", "UZERB": "Gida", "VERTU": "Enerji", "VKING": "Enerji", "YATAS": "Tekstil", "YUNSA": "Tekstil"
}

YF_OTURUMU = requests.Session()
YF_OTURUMU.headers.update({"User-Agent": "Mozilla/5.0","Accept-Language": "tr-TR,tr;q=0.9"})

class ZamanAsimiAdaptoru(HTTPAdapter):
    def send(self, request, **kwargs):
        kwargs['timeout'] = 4
        return super().send(request, **kwargs)

YF_OTURUMU.mount("https://", ZamanAsimiAdaptoru())

def _veri_cek_retry(ticker_obj, **kwargs):
    for _ in range(3):
        try:
            with contextlib.redirect_stderr(DevNull()), contextlib.redirect_stdout(DevNull()):
                h = ticker_obj.history(**kwargs)
            if h is not None and not h.empty: return h
        except: pass
        time.sleep(1)
    return pd.DataFrame()

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

def hisse_analiz_et(ticker_sembol):
    ticker = f"{ticker_sembol}.IS" if not ticker_sembol.endswith(".IS") else ticker_sembol
    try:
        obj = yf.Ticker(ticker, session=YF_OTURUMU)
        hist = _veri_cek_retry(obj, period="3mo", timeout=4)
        if hist.empty or len(hist) < 30: return None
        
        guncel_fiyat = float(hist['Close'].iloc[-1])
        gunun_en_yuksegi = float(hist['High'].iloc[-1])
        gunun_en_dusugu = float(hist['Low'].iloc[-1])
        guncel_hacim = float(hist['Volume'].iloc[-1])
        
        if len(hist) > 1:
            prev_high = float(hist['High'].iloc[-2])
            prev_low = float(hist['Low'].iloc[-2])
            prev_close = float(hist['Close'].iloc[-2])
            pivot = (prev_high + prev_low + prev_close) / 3
            s1 = round((pivot * 2) - prev_high, 2)
            r1 = round((pivot * 2) - prev_low, 2)
        else: s1 = r1 = guncel_fiyat

        high_low = hist['High'] - hist['Low']
        high_cp = (hist['High'] - hist['Close'].shift()).abs()
        low_cp = (hist['Low'] - hist['Close'].shift()).abs()
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        atr = float(tr.rolling(window=14).mean().iloc[-1]) if len(tr) >= 14 else guncel_fiyat * 0.03

        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss.replace(0, 0.00001)
        rsi = 100 - (100 / (1 + rs))
        guncel_rsi = float(rsi.iloc[-1])

        ma10 = hist['Close'].rolling(window=10).mean().iloc[-1]
        ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        ma30 = hist['Close'].rolling(window=30).mean().iloc[-1]
        
        ortalama_hacim = hist['Volume'].rolling(window=20).mean().iloc[-1]
        hacim_orani = guncel_hacim / ortalama_hacim if ortalama_hacim > 0 else 0

        exp12 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_al = macd.iloc[-1] > signal.iloc[-1]

        onceki_yirmi_gun_high = hist['High'].iloc[:-1].tail(20)
        direnc20 = float(onceki_yirmi_gun_high.max()) if not onceki_yirmi_gun_high.empty else gunun_en_yuksegi

        skor = AYAR["BASLANGIC_SKOR"]
        if guncel_rsi > AYAR["RSI_ASIRI_ALIM_ESIK"]: skor += AYAR["PUAN_ASIRI_ALIM"]
        elif guncel_rsi < AYAR["RSI_ASIRI_SATIM_ESIK"]: skor += AYAR["PUAN_ASIRI_SATIM"]
        
        if guncel_fiyat > ma20: skor += AYAR["PUAN_TREND_POZITIF"]
        else: skor += AYAR["PUAN_TREND_NEGATIF"]
        if guncel_fiyat <= ma10: skor += AYAR["MA10_ALTINDA_CEZA"]
        if guncel_fiyat <= ma30: skor += AYAR["MA30_ALTINDA_CEZA"]
        if macd_al: skor += AYAR["PUAN_MACD_AL"]
        if hacim_orani >= 2.0 and guncel_fiyat > ma20: skor += AYAR["PUAN_HACIMLI_ALIM"]
        if guncel_fiyat > direnc20: skor += AYAR["DIRENC20_KIRILIM_PUAN"]
        if guncel_fiyat > direnc20 and hacim_orani >= 2.0: skor += AYAR["HACIMLI_KIRILIM_PUAN"]

        skor = max(10, min(95, skor))

        if skor >= 80: robot_karari = "GÜÇLÜ AL 🔥"
        elif skor >= 60: robot_karari = "KADEMELİ AL 📈"
        else: robot_karari = "DİRENÇTE BEKLE 🛑"

        if guncel_rsi > 65: rsi_durumu = f"Aşırı Alım 🔴 (RSI: {guncel_rsi:.1f})"
        elif guncel_rsi < 35: rsi_durumu = f"Aşırı Satım 🟢 (RSI: {guncel_rsi:.1f})"
        else: rsi_durumu = f"Nötr ⚪ (RSI: {guncel_rsi:.1f})"

        tp_yuzde = max(0.05, min(0.15, (2.0 * atr) / guncel_fiyat))
        sl_yuzde = max(0.03, min(0.08, (1.5 * atr) / guncel_fiyat))
        tp_seviyesi = round(guncel_fiyat * (1 + tp_yuzde), 2)
        sl_seviyesi = round(guncel_fiyat * (1 - sl_yuzde), 2)
        ideal_alim = round(guncel_fiyat * 0.985, 2)

        return {
            "hisse": ticker_sembol, "fiyat": round(guncel_fiyat, 2),
            "skor": skor, "robot_karari": robot_karari, "rsi_durumu": rsi_durumu,
            "ideal_alim": ideal_alim, "tp": tp_seviyesi, "sl": sl_seviyesi,
            "s1": s1, "r1": r1, "direnc20": round(direnc20, 2),
            "ma10": round(ma10, 2), "ma30": round(ma30, 2),
            "rsi_deger": round(guncel_rsi, 1), "hacim_orani": round(hacim_orani, 1)
        }
    except: return None

VERI_DOSYASI = "dashboard_veri.json"
MAX_HISSE = 30

def veri_guncelle():
    print(f"🔄 Güncelleniyor... {datetime.now().strftime('%H:%M:%S')}")
    bist100 = bist100_durumu_getir()
    tum = []
    executor = ThreadPoolExecutor(max_workers=8)
    try:
        futures = {executor.submit(hisse_analiz_et, h): h for h in VARSAYILAN_HISSELER[:MAX_HISSE]}
        for f in futures:
            try:
                a = f.result()
                if a: tum.append(a)
            except: pass
    finally: executor.shutdown(wait=False)
    tum.sort(key=lambda x: x["skor"], reverse=True)
    
    # Sektör bazlı ortalama skor hesapla
    sektor_skorlar = {}
    sektor_sayilar = {}
    for h in tum:
        sektor = HISSE_SEKTOR.get(h["hisse"], "Diger")
        sektor_skorlar[sektor] = sektor_skorlar.get(sektor, 0) + h["skor"]
        sektor_sayilar[sektor] = sektor_sayilar.get(sektor, 0) + 1
    
    sektor_ortalamalar = {}
    for s in sektor_skorlar:
        sektor_ortalamalar[s] = round(sektor_skorlar[s] / sektor_sayilar[s], 1)
    
    # En güçlü ve en zayıf sektörleri bul
    sirali_sektorler = sorted(sektor_ortalamalar.items(), key=lambda x: x[1], reverse=True)
    
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump({
            "son_guncelleme": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "bist100_durum": bist100,
            "toplam_hisse": len(tum),
            "hisseler": tum[:MAX_HISSE],
            "sektor_ortalamalar": sektor_ortalamalar,
            "en_guclu_sektor": sirali_sektorler[0] if sirali_sektorler else ("-", 0),
            "en_zayif_sektor": sirali_sektorler[-1] if sirali_sektorler else ("-", 0)
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(tum)} hisse güncellendi. En güçlü sektör: {sirali_sektorler[0] if sirali_sektorler else '-'}")

if __name__ == "__main__":
    veri_guncelle()
