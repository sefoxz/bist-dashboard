import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="BIST Smart Radar", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    h1, h2, h3, p, span, div { color: white; }
    .card { background-color: #161b22; border-radius: 10px; padding: 15px; margin: 10px 0; border: 1px solid #30363d; }
    .skor-yuksek { color: #00d2ff; font-weight: bold; font-size: 20px; }
    .skor-orta { color: #ffd93d; font-weight: bold; font-size: 20px; }
    .skor-dusuk { color: #ff6b6b; font-weight: bold; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 BIST Smart Radar Dashboard")

VERI_DOSYASI = "dashboard_veri.json"

if os.path.exists(VERI_DOSYASI):
    with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
        veri = json.load(f)
    
    bist_durum = veri.get("bist100_durum", "Veri Yok")
    son_guncelleme = veri.get("son_guncelleme", "Bilinmiyor")
    
    col1, col2 = st.columns([2, 1])
    with col1: st.markdown(f"### 🏛️ BIST 100: {bist_durum}")
    with col2: st.markdown(f"🕐 Son Güncelleme: {son_guncelleme}")
    st.divider()
    
    hisseler = veri.get("hisseler", [])
    if hisseler:
        df = pd.DataFrame(hisseler)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: arama = st.text_input("🔍 Hisse Ara", placeholder="Hisse kodu...")
        with col2: min_skor = st.slider("Minimum Skor", 0, 100, 60)
        with col3: siralama = st.selectbox("Sırala", ["Skor (Yüksekten)", "Skor (Düşükten)", "Fiyat (Yüksekten)", "Fiyat (Düşükten)"])
        
        if arama: df = df[df['hisse'].str.contains(arama.upper())]
        df = df[df['skor'] >= min_skor]
        
        if "Skor" in siralama:
            df = df.sort_values('skor', ascending="Düşükten" in siralama)
        else:
            df = df.sort_values('fiyat', ascending="Düşükten" in siralama)
        
        for _, row in df.head(30).iterrows():
            skor = row['skor']
            skor_class = "skor-yuksek" if skor >= 80 else ("skor-orta" if skor >= 60 else "skor-dusuk")
            emoji = "🔥" if skor >= 80 else ("📈" if skor >= 60 else "📉")
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3>#{row['hisse']} {emoji}</h3>
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
    st.warning("Veri dosyası bulunamadı. GitHub Actions'ın çalışmasını bekleyin.")
