import streamlit as st
import psycopg2
import pandas as pd

# Design-Anpassungen (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #fdfdfd; }
    h1 { color: #2d5a27 !important; }
    div.stButton > button { border-radius: 15px; background-color: #e8f5e9; border: 1px solid #c8e6c9; }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Mein Pflanzen-Dashboard", layout="wide")
st.title("🌿 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# Tabs erstellen
tab1, tab2, tab3 = tab1, tab2, tab3 = st.tabs(["💧 Gießen", "🧪 Düngen", "📖 Übersicht"])

# --- TAB 1: GIESSEN ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        temp = st.slider("Aktuelle Temperatur (°C)", 0, 40, 20)
    
    abzug = 3 if temp > 28 else (1 if temp > 22 else (-2 if temp < 15 else 0))
        
    query_giessen = f"""
    SELECT p.name_deutsch, MAX(g.datum_gegossen) as zuletzt,
           (MAX(g.datum_gegossen) + ((p.giessintervall_tage - {abzug}) || ' days')::interval)::date AS faellig
    FROM pflanzen p
    LEFT JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    ORDER BY faellig ASC;
    """
    df_giessen = pd.read_sql(query_giessen, conn)
    st.dataframe(df_giessen, use_container_width=True, hide_index=True)

    pflanzen_liste = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)
    auswahl_giessen = st.multiselect("Heute gegossen?", pflanzen_liste['name_deutsch'], key="g")
    if st.button("Gießen speichern"):
        for name in auswahl_giessen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

# --- TAB 2: DÜNGEN ---
with tab2:
    st.subheader("Dünge-Historie")
    query_duenge = "SELECT p.name_deutsch, MAX(d.datum_geduengt) as zuletzt FROM pflanzen p LEFT JOIN duenge_historie d ON p.id = d.pflanze_id GROUP BY p.name_deutsch"
    st.dataframe(pd.read_sql(query_duenge, conn), use_container_width=True, hide_index=True)
    
    auswahl_duengen = st.multiselect("Heute gedüngt?", pflanzen_liste['name_deutsch'], key="d")
    if st.button("Düngen speichern"):
        for name in auswahl_duengen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO duenge_historie (pflanze_id, datum_geduengt) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

# --- TAB 3: ÜBERSICHT ---
with tab3:
    st.subheader("Pflanzen-Lexikon")
    df_alle = pd.read_sql("SELECT name_deutsch, name_botanisch, standort_ideal, duengen, vertraegt_staunaesse FROM pflanzen", conn)
    st.dataframe(df_alle, use_container_width=True, hide_index=True)
