import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="BIST Smart Radar Pro", page_icon="🤖", layout="wide")

# Koyu/Açık tema otomatik
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: white; }
    .card { background-color: #161b22; border-radius: 12px; padding: 20px; margin: 10px 0; border: 1px solid #30363d; }
    .skor-yuksek { color: #00d2ff; font-weight: bold; font-size: 24px; }
    .skor-orta { color: #ffd93d; font-weight: bold; font-size: 24px; }
    .skor-dusuk { color: #ff6b6b; font-weight: bold; font-size: 24px; }
    .sektor-baslik { font-size: 18px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 BIST Smart Radar Pro Dashboard")

VERI_DOSYASI = "dashboard_veri.json"

if os.path.exists(VERI_DOSYASI):
    with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
        veri = json.load(f)
    
    # Üst bilgi çubuğu
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"### 🏛️ BIST 100: {veri.get('bist100_durum', 'Veri Yok')}")
    with col2:
        guclu = veri.get('en_guclu_sektor', ['-', 0])
        zayif = veri.get('en_zayif_sektor', ['-', 0])
        st.markdown(f"### 🟢 En Güçlü Sektör: {guclu[0]} ({guclu[1]})")
        st.markdown(f"### 🔴 En Zayıf Sektör: {zayif[0]} ({zayif[1]})")
    with col3:
        st.markdown(f"🕐 {veri.get('son_guncelleme', '')}")
        if st.button("🔄 Yenile"):
            st.rerun()
    
    st.divider()
    
    # Sektör performansı tablosu
    sektorler = veri.get('sektor_ortalamalar', {})
    if sektorler:
        with st.expander("📊 Sektör Performansları", expanded=False):
            sektor_df = pd.DataFrame(list(sektorler.items()), columns=['Sektör', 'Ortalama Skor'])
            sektor_df = sektor_df.sort_values('Ortalama Skor', ascending=False)
            st.dataframe(sektor_df, use_container_width=True)
    
    # Hisse verileri
    hisseler = veri.get("hisseler", [])
    if hisseler:
        df = pd.DataFrame(hisseler)
        
        # Filtreler
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            arama = st.text_input("🔍 Hisse Ara", placeholder="Hisse kodu...")
        with col2:
            min_skor = st.slider("Min Skor", 0, 100, 60)
        with col3:
            sektorler_liste = ["Tümü"] + sorted(set(HISSE_SEKTOR.get(h, "Diger") for h in df['hisse']))
            secili_sektor = st.selectbox("Sektör", sektorler_liste)
        with col4:
            siralama = st.selectbox("Sırala", ["Skor ▼", "Skor ▲", "Fiyat ▼", "Fiyat ▲"])
        
        # Filtreleme
        if arama: df = df[df['hisse'].str.contains(arama.upper())]
        if secili_sektor != "Tümü":
            df = df[df['hisse'].apply(lambda h: HISSE_SEKTOR.get(h, "Diger")) == secili_sektor]
        df = df[df['skor'] >= min_skor]
        
        if "Skor" in siralama:
            df = df.sort_values('skor', ascending="▲" in siralama)
        else:
            df = df.sort_values('fiyat', ascending="▲" in siralama)
        
        # Kartlar
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
        st.warning("Henüz veri bulunmuyor.")
else:
    st.warning("Veri dosyası bulunamadı.")
