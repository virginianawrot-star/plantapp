import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(layout="wide")
st.title("🌱 Mein Pflanzen-Dashboard")

conn = psycopg2.connect(st.secrets["DATABASE_URL"])

# Tabs erstellen
tab1, tab2, tab3 = st.tabs(["💧 Gießen", "🧪 Düngen", "📋 Alle Pflanzen"])

with tab1:
    st.subheader("Gießen Status")
    query_giessen = """
    SELECT p.name_deutsch, 
           MAX(g.datum_gegossen) as zuletzt,
           (MAX(g.datum_gegossen) + (p.giessintervall_tage || ' days')::interval)::date AS faellig_am
    FROM pflanzen p
    JOIN giess_historie g ON p.id = g.pflanze_id
    GROUP BY p.id, p.name_deutsch, p.giessintervall_tage
    ORDER BY faellig_am ASC;
    """
    st.dataframe(pd.read_sql(query_giessen, conn), use_container_width=True)

with tab2:
    st.subheader("Dünge-Plan")
    st.info("Hier siehst du, wie oft gedüngt werden muss. Notiere dir das Datum im Kalender!")
    df_duengen = pd.read_sql("SELECT name_deutsch, duengen FROM pflanzen", conn)
    st.table(df_duengen)

with tab3:
    st.subheader("Pflanzen-Filter")
    # Große Buttons statt kleiner Lupe
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Staunässe-empfindlich anzeigen"):
            st.session_state.filter = "Nein"
    with col2:
        if st.button("🔄 Alle anzeigen"):
            st.session_state.filter = "Alle"
    
    query_alle = "SELECT * FROM pflanzen"
    df_alle = pd.read_sql(query_alle, conn)
    
    if 'filter' in st.session_state and st.session_state.filter == "Nein":
        df_alle = df_alle[df_alle['vertraegt_staunaesse'] == 'Nein']
        
    st.dataframe(df_alle, use_container_width=True)
