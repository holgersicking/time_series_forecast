import streamlit as st
import pandas as pd
from neuralprophet import NeuralProphet
import matplotlib.pyplot as plt
from io import BytesIO

# Page configuration for wider layout
st.set_page_config(page_title="Zeitreihen-Prognose mit NeuralProphet", layout="centered")

# Custom CSS to match Österreich Werbung design
st.markdown(
    """
    <style>
    .main {
        background-color: #FFFFFF;  /* Weißer Hintergrund */
    }
    h1 {
        color: #E60000;  /* Österreich Werbung Rot */
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        font-size: 2.5em;
        margin-bottom: 20px;
    }
    footer {
        visibility: hidden;
    }
    .css-1v3fvcr {
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton button {
        background-color: #E60000;  /* Rot für Buttons */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stDownloadButton {
        text-align: center;
    }
    .stSlider .st-ba {
        background: linear-gradient(90deg, #E60000, #ff6666);  /* Roter Slider */
    }
    .css-10trblm {  /* Textfarbe im Header */
        color: white;
        background-color: #E60000;
        padding: 10px;
        border-radius: 0px 0px 10px 10px;
    }
    .stMarkdown h3 {
        color: #333333;
    }
    </style>
    """, unsafe_allow_html=True
)

# Header im Stil von Österreich Werbung
st.markdown("<div class='css-10trblm'><h1>Zeitreihen-Prognose mit NeuralProphet</h1></div>", unsafe_allow_html=True)
# Introduction section with instructions
st.markdown("""
Willkommen bei deinem Tool für **Zeitreihenprognosen**! 🎉

Lade deine Zeitreihendaten hoch (CSV oder Excel), und wir erstellen eine Prognose mit **NeuralProphet**. 
Lass uns beginnen!
""")

# File upload section
uploaded_file = st.file_uploader("📁 Wähle eine CSV- oder Excel-Datei", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Check the file type
    if uploaded_file.name.endswith('csv'):
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_excel(uploaded_file)

    # Display the first few rows
    st.markdown("### 📊 Hochgeladene Daten")
    st.write(data.head())

    # Erkennung, ob 'ds' Jahreswerte enthält (z. B. 1973, 1974, ...)
    def detect_year_column(column):
        if pd.api.types.is_numeric_dtype(column):
            # Prüfen, ob alle Werte im Bereich von plausiblen Jahreszahlen liegen
            if column.between(1800, 2100).all():
                return True
        return False

    # Wenn 'ds' Jahreszahlen enthält, in ein Datumsformat konvertieren
    if detect_year_column(data['ds']):
        st.write("Jahresangaben erkannt! Konvertiere in Datumsformat (1. Januar jedes Jahres).")
        data['ds'] = pd.to_datetime(data['ds'], format='%Y')  # Konvertiere Jahr in Datum
    else:
        st.write("Die Spalte 'ds' enthält keine Jahresangaben. Nutze die ursprünglichen Daten.")

    # Weiterer Code wie zuvor
    def detect_frequency(df):
        df = df.sort_values(by='ds').reset_index(drop=True)
        diffs = df['ds'].diff().dropna().dt.days
        avg_diff = diffs.mean()
        
        if avg_diff <= 1.5:
            return 'D'  # Daily
        elif avg_diff <= 8:
            return 'W'  # Weekly
        elif avg_diff <= 32:
            return 'M'  # Monthly
        else:
            return 'Y'  # Yearly

    # Detect and rename columns
    date_col, value_col = 'ds', 'y'  # Assuming these are the correct columns

    # Detect frequency automatically
    detected_freq = detect_frequency(data)
    st.markdown(f"### 🕒 Automatisch erkannte Frequenz der Daten: **{detected_freq}**")

    # Define slider limits and default values based on frequency
    if detected_freq == 'D':
        period_label = "Tage"
        period_max = 365
        period_default = 200
    elif detected_freq == 'W':
        period_label = "Wochen"
        period_max = 52
        period_default = 4
    elif detected_freq == 'M':
        period_label = "Monate"
        period_max = 36
        period_default = 24
    elif detected_freq == 'Y':
        period_label = "Jahre"
        period_max = 10
        period_default = 3

    # NeuralProphet Model
    st.write("⏳ NeuralProphet Modell wird trainiert...")
    # model = NeuralProphet()
    model = NeuralProphet(
            yearly_seasonality=True,   # Jährliche Saisonalität (z. B. Sommer/Winter)
            weekly_seasonality=True,   # Wöchentliche Saisonalität (falls relevant)
            daily_seasonality=False    # Deaktivieren, falls tägliche Muster nicht relevant sind
        )
    model.fit(data, freq=detected_freq)

    # Forecast future data
    periods = st.slider(f"Wähle die Anzahl der {period_label} für die Prognose", 1, period_max, period_default)
    future = model.make_future_dataframe(data, periods=periods)
    forecast = model.predict(future)

    # Combine the original data with the forecast
    combined_data = pd.concat([data, forecast[['ds', 'yhat1']]], ignore_index=True)
    combined_data = combined_data.rename(columns={'yhat1': 'Forecast'})

    # Visualize the Results
    st.markdown("### 📉 Vorhersage-Diagramm")
    fig, ax = plt.subplots()
    ax.plot(data['ds'], data['y'], label='Originaldaten', color='#E60000')  # Rot für Originaldaten
    ax.plot(forecast['ds'], forecast['yhat1'], label='Vorhersage', color='#50E3C2')  # Grün für Vorhersage
    ax.legend()
    st.pyplot(fig)

    # Save the combined data to an Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        combined_data.to_excel(writer, index=False, sheet_name='Forecast')
        writer.close()

    # Option to download the forecast
    st.markdown("### 📥 Prognose herunterladen")
    st.download_button(
        label="📄 Prognose als Excel herunterladen", 
        data=output.getvalue(), 
        file_name="forecast.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.write("⚠️ Bitte stelle sicher, dass die Datei eine Datumsspalte und eine Wertspalte enthält.")

# Footer im Stil von Österreich Werbung
st.markdown("<div style='text-align: center; color: #E60000;'>Zeitreihen-Prognose mit Neuralprophet | © Österreich Werbung</div>", unsafe_allow_html=True)
