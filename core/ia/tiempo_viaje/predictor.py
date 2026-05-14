import pandas as pd
import joblib
import os

# Ruta de la carpeta actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Modelo
modelo = joblib.load(
    os.path.join(BASE_DIR, 'modelo_tiempo_100arboles.pkl')
)

# Encoders
label_encoders = joblib.load(
    os.path.join(BASE_DIR, 'label_encoders.pkl')
)

# Columnas originales
columnas_modelo = joblib.load(
    os.path.join(BASE_DIR, 'columnas_modelo.pkl')
)


def preparar_datos(datos):

    df = pd.DataFrame([datos])

    # Aplicar LabelEncoder
    for col, le in label_encoders.items():

        if col in df.columns:

            valor = str(df[col].iloc[0])

            # Si aparece una categoría nueva
            if valor not in le.classes_:
                valor = le.classes_[0]

            df[col] = le.transform([valor])

    # Mantener exactamente las columnas del entrenamiento
    df = df.reindex(columns=columnas_modelo, fill_value=0)

    return df


def predecir_tiempo(datos):

    datos_preparados = preparar_datos(datos)

    prediccion = modelo.predict(datos_preparados)

    return round(float(prediccion[0]), 2)