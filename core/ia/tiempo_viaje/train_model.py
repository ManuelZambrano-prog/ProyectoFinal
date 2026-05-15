import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset_limpio.csv")
MODEL_PATH = os.path.join(BASE_DIR, "modelo_tiempo_100arboles.pkl")
ENCODERS_PATH = os.path.join(BASE_DIR, "label_encoders.pkl")
COLUMNS_PATH = os.path.join(BASE_DIR, "columnas_modelo.pkl")


def cargar_dataset(path):
    df = pd.read_csv(path, low_memory=False)
    return df


def entrenar_modelo(df):
    if "HORAS_VIAJE" not in df.columns:
        raise ValueError("El dataset no contiene la columna objetivo HORAS_VIAJE")

    df = df.dropna(subset=["HORAS_VIAJE"]).copy()

    tiempo_df = df.copy()
    tiempo_df = tiempo_df.drop(columns=[
        "HORAS_VIAJE",
        "VALOR_PAGADO",
        "VALOR_PACTADO",
        "FECHASALIDACARGUE",
        "FECHALLEGADADESCARGUE",
    ], errors="ignore")

    le_dict = {}
    for col in tiempo_df.select_dtypes(include="object").columns:
        le = LabelEncoder()
        tiempo_df[col] = le.fit_transform(tiempo_df[col].astype(str))
        le_dict[col] = le

    X = tiempo_df
    y = df["HORAS_VIAJE"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    modelo = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=1,
    )
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    return modelo, le_dict, list(X.columns), y_test, y_pred


def guardar_artifacts(modelo, le_dict, columnas):
    temp_model = MODEL_PATH + ".tmp"
    temp_encoders = ENCODERS_PATH + ".tmp"
    temp_columns = COLUMNS_PATH + ".tmp"

    joblib.dump(modelo, temp_model, compress=3)
    joblib.dump(le_dict, temp_encoders)
    joblib.dump(columnas, temp_columns)

    os.replace(temp_model, MODEL_PATH)
    os.replace(temp_encoders, ENCODERS_PATH)
    os.replace(temp_columns, COLUMNS_PATH)

    print(f"Modelo guardado en: {MODEL_PATH}")
    print(f"Encoders guardados en: {ENCODERS_PATH}")
    print(f"Columnas guardadas en: {COLUMNS_PATH}")


def imprimir_metricas(y_test, y_pred):
    print("R²:", r2_score(y_test, y_pred))
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("RMSE:", mean_squared_error(y_test, y_pred, squared=False))


if __name__ == '__main__':
    df = cargar_dataset(DATASET_PATH)
    modelo, le_dict, columnas, y_test, y_pred = entrenar_modelo(df)
    guardar_artifacts(modelo, le_dict, columnas)
    imprimir_metricas(y_test, y_pred)
