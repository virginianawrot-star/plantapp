import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌱 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# 1. Warnung oben (Erinnerung)
query_warnung = """
SELECT p.name_deutsch 
FROM pflanzen p
JOIN giess_historie g ON p.id = g.pflanze_id
GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
HAVING (MAX(g.datum_gegossen) + (p.giessintervall_tage || ' days')::interval)::date <= CURRENT_DATE;
"""
df_warnung = pd.read_sql(query_warnung, conn)

if not df_warnung.empty:
    st.error(f"⚠️ Achtung! Diese Pflanzen müssen dringend gegossen werden: {', '.join(df_warnung['name_deutsch'].tolist())}")
else:
    st.success("✅ Alles im grünen Bereich – keine Pflanze braucht aktuell Wasser.")

# 2. Tabs erstellen
tab1, tab2, tab3 = st.tabs(["Gießen", "Düngen", "Alle Infos"])

# --- TAB 1: GIESSEN ---
with tab1:
    st.subheader("Gieß-Status")
    query_giessen = """
    SELECT p.name_deutsch, 
           MAX(g.datum_gegossen) as letztes_giessen,
           (MAX(g.datum_gegossen) + (p.giessintervall_tage || ' days')::interval)::date AS faellig_am
    FROM pflanzen p
    JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    ORDER BY faellig_am ASC;
    """
    df_giessen = pd.read_sql(query_giessen, conn)
    st.dataframe(df_giessen, use_container_width=True)

    pflanzen_liste = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)
    auswahl_giessen = st.multiselect("Welche Pflanzen hast du heute gegossen?", pflanzen_liste['name_deutsch'], key="g")
    
    if st.button("Ausgewählte als gegossen markieren"):
        for name in auswahl_giessen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.success("Gieß-Historie aktualisiert!")
        st.rerun()

# --- TAB 2: DÜNGEN ---
with tab2:
    st.subheader("Dünge-Status")
    query_duenge_status = """
    SELECT p.name_deutsch, MAX(d.datum_geduengt) as zuletzt_geduengt
    FROM pflanzen p
    LEFT JOIN duenge_historie d ON p.id = d.pflanze_id
    GROUP BY p.name_deutsch
    ORDER BY zuletzt_geduengt DESC;
    """
    df_duenge = pd.read_sql(query_duenge_status, conn)
    st.dataframe(df_duenge, use_container_width=True)

    auswahl_duengen = st.multiselect("Welche Pflanzen hast du heute gedüngt?", pflanzen_liste['name_deutsch'], key="d")
    
    if st.button("Ausgewählte als gedüngt markieren"):
        for name in auswahl_duengen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO duenge_historie (pflanze_id, datum_geduengt) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.success("Dünge-Historie aktualisiert!")
        st.rerun()

# --- TAB 3: ALLE INFOS ---
with tab3:
    st.subheader("Filter & Details")
    col1, col2 = st.columns(2)
    
    if "filter" not in st.session_state: st.session_state.filter = "Alle"
    
    if col1.button("🚫 Keine Staunässe", use_container_width=True): st.session_state.filter = "Staunässe_Nein"
    if col2.button("Alle anzeigen", use_container_width=True): st.session_state.filter = "Alle"
            
    query_alle = "SELECT name_deutsch, name_botanisch, standort_ideal, duengen, vertraegt_staunaesse FROM pflanzen"
    if st.session_state.filter == "Staunässe_Nein":
        query_alle += " WHERE vertraegt_staunaesse = 'Nein'"
            
    df = pd.read_sql(query_alle, conn)
    st.dataframe(df, use_container_width=True)
