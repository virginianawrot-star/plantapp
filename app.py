import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌱 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# Tabs erstellen
tab1, tab2, tab3 = st.tabs(["Gießen", "Düngen", "Alle Infos"])

# --- TAB 1: GIESSEN ---
with tab1:
    st.subheader("Gieß-Status")
    # Warnung nur für Gießen
    query_warnung_g = """
    SELECT p.name_deutsch 
    FROM pflanzen p
    JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    HAVING (MAX(g.datum_gegossen) + (p.giessintervall_tage || ' days')::interval)::date <= CURRENT_DATE;
    """
    df_warn_g = pd.read_sql(query_warnung_g, conn)
    if not df_warn_g.empty:
        st.error(f"⚠️ Gieß-Alarm: {', '.join(df_warn_g['name_deutsch'].tolist())}")
    else:
        st.success("✅ Alles bestens beim Gießen!")

    query_giessen = """
    SELECT p.name_deutsch, MAX(g.datum_gegossen) as zuletzt_giessen,
           (MAX(g.datum_giessen) + (p.giessintervall_tage || ' days')::interval)::date AS faellig_am
    FROM pflanzen p JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage ORDER BY faellig_am ASC;
    """
    # (HINWEIS: Hier im SQL ggf. auf 'datum_gegossen' achten, falls es beim Kopieren kurz klemmte)
    df_giessen = pd.read_sql("SELECT p.name_deutsch, MAX(g.datum_gegossen) as letztes_giessen FROM pflanzen p JOIN giess_historie g ON p.id = g.pflanze_id GROUP BY p.name_deutsch ORDER BY letztes_giessen ASC", conn)
    st.dataframe(df_giessen, use_container_width=True)

    pflanzen_liste = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)
    auswahl_giessen = st.multiselect("Heute gegossen?", pflanzen_liste['name_deutsch'], key="g")
    if st.button("Speichern Gießen"):
        for name in auswahl_giessen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

# --- TAB 2: DÜNGEN ---
with tab2:
    st.subheader("Dünge-Status")
    # Hier prüfen wir z.B. auf 30 Tage (Standardintervall)
    query_warnung_d = """
    SELECT p.name_deutsch 
    FROM pflanzen p
    JOIN duenge_historie d ON p.id = d.pflanze_id
    GROUP BY p.id, p.name_deutsch
    HAVING MAX(d.datum_geduengt) <= CURRENT_DATE - INTERVAL '30 days';
    """
    df_warn_d = pd.read_sql(query_warnung_d, conn)
    if not df_warn_d.empty:
        st.error(f"⚠️ Dünge-Alarm: {', '.join(df_warn_d['name_deutsch'].tolist())} ist seit 30 Tagen nicht gedüngt!")
    else:
        st.success("✅ Alles bestens beim Düngen!")

    query_duenge_status = "SELECT p.name_deutsch, MAX(d.datum_geduengt) as zuletzt_geduengt FROM pflanzen p LEFT JOIN duenge_historie d ON p.id = d.pflanze_id GROUP BY p.name_deutsch ORDER BY zuletzt_geduengt DESC"
    st.dataframe(pd.read_sql(query_duenge_status, conn), use_container_width=True)

    auswahl_duengen = st.multiselect("Heute gedüngt?", pflanzen_liste['name_deutsch'], key="d")
    if st.button("Speichern Düngen"):
        for name in auswahl_duengen:
            p_id = pflanzen_liste[pflanzen_liste['name_deutsch'] == name]['id'].iloc[0]
            conn.cursor().execute("INSERT INTO duenge_historie (pflanze_id, datum_geduengt) VALUES (%s, CURRENT_DATE)", (int(p_id),))
            conn.commit()
        st.rerun()

# --- TAB 3: ALLE INFOS ---
with tab3:
    st.dataframe(pd.read_sql("SELECT * FROM pflanzen", conn), use_container_width=True)
