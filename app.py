import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌱 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# 1. Warnung oben (Gießen)
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
tab1, tab2, tab3 = st.tabs(["💧 Gießen", "🧪 Düngen", "📋 Alle Pflanzen"])

with tab1:
    st.subheader("Gießen Status")
    query_giessen = """
    SELECT p.name_deutsch, 
           MAX(g.datum_gegossen) as zuletzt_gegossen,
           (MAX(g.datum_gegossen) + (p.giessintervall_tage || ' days')::interval)::date AS faellig_am
    FROM pflanzen p
    JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    ORDER BY faellig_am ASC;
    """
    st.dataframe(pd.read_sql(query_giessen, conn), use_container_width=True)

    pflanzen_liste = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)
    auswahl_giessen = st.multiselect("Welche Pflanzen hast du heute gegossen?", pflanzen_liste['name_deutsch'])
    if st.button("Markiere Gießen"):
        for name in auswahl_giessen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

with tab2:
    st.subheader("Düngen Status")
    query_duengen = """
    SELECT p.name_deutsch, 
           MAX(d.datum_geduengt) as zuletzt_geduengt,
           (MAX(d.datum_geduengt) + (p.duenge_abstand_wochen * 7 || ' days')::interval)::date AS duengen_faellig
    FROM pflanzen p
    JOIN duenge_historie d ON p.id = d.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.duenge_abstand_wochen
    ORDER BY duengen_faellig ASC;
    """
    st.dataframe(pd.read_sql(query_duengen, conn), use_container_width=True)

    auswahl_duengen = st.multiselect("Welche Pflanzen hast du heute gedüngt?", pflanzen_liste['name_deutsch'])
    if st.button("Markiere Düngen"):
        for name in auswahl_duengen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO duenge_historie (pflanze_id, datum_geduengt) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

with tab3:
    st.subheader("Filter & Übersicht")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Nur Empfindliche"): st.session_state.filter = "Nein"
    with col2:
        if st.button("🔄 Alle anzeigen"): st.session_state.filter = "Alle"
    
    df_alle = pd.read_sql("SELECT * FROM pflanzen", conn)
    if 'filter' in st.session_state and st.session_state.filter == "Nein":
        df_alle = df_alle[df_alle['vertraegt_staunaesse'] == 'Nein']
        
    st.dataframe(df_alle, use_container_width=True)
