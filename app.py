import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(layout="wide") # App nutzt die ganze Bildschirmbreite
st.title("🌱 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# 1. Registerkarten erstellen
tab1, tab2 = st.tabs(["Gießen & Status", "Alle Pflanzen & Infos"])

with tab1:
    st.subheader("Fällige Pflanzen")
    # SQL für Fälligkeit
    query = """
    SELECT p.name_deutsch, 
           MAX(g.datum_gegossen) as letztes_giessen,
           (MAX(g.datum_gegossen) + (p.giessintervall_tage || ' days')::interval)::date AS faellig_am
    FROM pflanzen p
    JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    ORDER BY faellig_am ASC;
    """
    df_status = pd.read_sql(query, conn)
    st.dataframe(df_status, use_container_width=True)

    # Gießen-Funktion für mehrere Pflanzen
    st.subheader("Gießvorgang erfassen")
    pflanzen_liste = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)
    auswahl = st.multiselect("Welche Pflanzen hast du heute gegossen?", pflanzen_liste['name_deutsch'])
    
    if st.button("Ausgewählte Pflanzen als gegossen markieren"):
        for name in auswahl:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.success(f"Gieß-Historie aktualisiert für: {', '.join(auswahl)}")

with tab2:
    st.subheader("Alle Pflanzen im Überblick")
    df_alle = pd.read_sql("SELECT name_deutsch, name_botanisch, standort_ideal, vermehrung FROM pflanzen", conn)
    st.table(df_alle)
