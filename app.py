import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌱 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# --- TAB 1: GIESSEN ---
tab1, tab2, tab3 = st.tabs(["Gießen", "Düngen", "Alle Infos"])

with tab1:
    st.subheader("Gieß-Status")
    
    # Der Hitze-Regler
    hitze_level = st.select_slider("Wie ist das Wetter heute?", 
                                   options=["Kühl", "Normal", "Heiß"], 
                                   value="Normal")
    
    # Logik: Heiß = Intervall wird um 2 Tage verkürzt
    abzug = 2 if hitze_level == "Heiß" else 0
    
    query_giessen = f"""
    SELECT p.name_deutsch, 
           MAX(g.datum_gegossen) as zuletzt_giessen,
           (MAX(g.datum_gegossen) + ((p.giessintervall_tage - {abzug}) || ' days')::interval)::date AS faellig_am
    FROM pflanzen p
    LEFT JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    ORDER BY faellig_am ASC NULLS FIRST;
    """
    df_giessen = pd.read_sql(query_giessen, conn)
    
    # Warnung nur wenn fällig
    fällige_pflanzen = df_giessen[df_giessen['faellig_am'] <= pd.to_datetime('today').date()]
    if not fällige_pflanzen.empty:
        st.error(f"⚠️ Gieß-Alarm: {', '.join(fällige_pflanzen['name_deutsch'].tolist())}")
    else:
        st.success("✅ Alles bestens!")
        
    st.dataframe(df_giessen, use_container_width=True)

    pflanzen_liste = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)
    auswahl_giessen = st.multiselect("Heute gegossen?", pflanzen_liste['name_deutsch'], key="g")
    
    if st.button("Speichern Gießen"):
        for name in auswahl_giessen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

# --- TAB 2: DÜNGEN (Unverändert) ---
with tab2:
    st.subheader("Dünge-Status")
    query_duenge_status = "SELECT p.name_deutsch, MAX(d.datum_geduengt) as zuletzt_geduengt FROM pflanzen p LEFT JOIN duenge_historie d ON p.id = d.pflanze_id GROUP BY p.name_deutsch ORDER BY zuletzt_geduengt DESC NULLS FIRST"
    st.dataframe(pd.read_sql(query_duenge_status, conn), use_container_width=True)
    auswahl_duengen = st.multiselect("Heute gedüngt?", pflanzen_liste['name_deutsch'], key="d")
    if st.button("Speichern Düngen"):
        for name in auswahl_duengen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO duenge_historie (pflanze_id, datum_geduengt) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

# --- TAB 3: ALLE INFOS (Unverändert) ---
with tab3:
    st.dataframe(pd.read_sql("SELECT * FROM pflanzen", conn), use_container_width=True)
