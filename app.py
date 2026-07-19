import streamlit as st
import psycopg2
import pandas as pd

# Verbindung zu Neon
def get_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

st.title("🌱 Mein Pflanzen-Tracker")

conn = get_connection()
# Pflanzen laden
df = pd.read_sql("SELECT id, name_deutsch FROM pflanzen", conn)

# Auswahl-Box
pflanze_id = st.selectbox("Welche Pflanze hast du gegossen?", options=df['id'], format_func=lambda x: df[df['id'] == x]['name_deutsch'].values[0])

if st.button("Jetzt gegossen!"):
    cur = conn.cursor()
    cur.execute("INSERT INTO giess_historie (pflanze_id, datum_gegossen) VALUES (%s, CURRENT_DATE)", (int(pflanze_id),))
    conn.commit()
    st.success("Erledigt! Gieß-Historie wurde aktualisiert.")

# Anzeige der Historie
st.subheader("Letzte Gießvorgänge")
hist = pd.read_sql("SELECT p.name_deutsch, g.datum_gegossen FROM giess_historie g JOIN pflanzen p ON g.pflanze_id = p.id ORDER BY g.datum_gegossen DESC LIMIT 5", conn)
st.table(hist)

