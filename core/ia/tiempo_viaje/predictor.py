import base64
import difflib
import json
import os
import pickle
import re
import unicodedata

import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELO_PATH = os.path.join(BASE_DIR, 'modelo_tiempo_100arboles.pkl')
MODELO_JSON_PATH = os.path.join(BASE_DIR, 'modelo_tiempo.json')
ENCODERS_PATH = os.path.join(BASE_DIR, 'label_encoders.pkl')
ENCODERS_JSON_PATH = os.path.join(BASE_DIR, 'label_encoders.json')
DATASET_PATH = os.path.join(BASE_DIR, 'dataset_limpio.csv')


def cargar_recurso(path, default=None):
    try:
        if path.endswith('.json'):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, dict):
                payload = data.get('payload') or data.get('data') or data.get('content')
                if isinstance(payload, str):
                    try:
                        return pickle.loads(base64.b64decode(payload))
                    except Exception:
                        pass

                if data.get('type') == 'dict':
                    return {k: v for k, v in data.items() if k != 'type'}

            return data

        return joblib.load(path)
    except Exception as exc:
        print(f"Advertencia: no se pudo cargar '{path}': {exc}")
        return default


def normalizar_texto(texto):
    if texto is None:
        return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"\s+", " ", texto)
    return texto


def coincidencia_inexacta(valor, candidatos, cutoff=0.75):
    if not valor or not candidatos:
        return ""

    valor_norm = normalizar_texto(valor)
    mapa = {normalizar_texto(str(c)): c for c in candidatos if c is not None}

    if valor_norm in mapa:
        return mapa[valor_norm]

    for clave, original in mapa.items():
        if clave.startswith(valor_norm) or valor_norm.startswith(clave) or valor_norm in clave or clave in valor_norm:
            return original

    mejores = difflib.get_close_matches(valor_norm, list(mapa.keys()), n=1, cutoff=cutoff)
    if mejores:
        return mapa[mejores[0]]

    return ""


modelo = None
label_encoders = None
dataset = None


def cargar_recursos():
    global modelo, label_encoders, dataset

    if modelo is None:
        if os.path.exists(MODELO_JSON_PATH):
            modelo = cargar_recurso(MODELO_JSON_PATH, default=None)
        elif os.path.exists(MODELO_PATH):
            modelo = cargar_recurso(MODELO_PATH, default=None)

    if label_encoders is None:
        if os.path.exists(ENCODERS_JSON_PATH):
            label_encoders = cargar_recurso(ENCODERS_JSON_PATH, default={})
        elif os.path.exists(ENCODERS_PATH):
            label_encoders = cargar_recurso(ENCODERS_PATH, default={})

    if dataset is None:
        try:
            dataset = pd.read_csv(DATASET_PATH)
        except Exception as exc:
            print(f"Advertencia: no se pudo cargar '{DATASET_PATH}': {exc}")
            dataset = pd.DataFrame()


def obtener_opciones():
    cargar_recursos()

    opciones = {
        "tipos_carga": [],
        "origenes": [],
        "destinos": []
    }

    if isinstance(label_encoders, dict):
        opciones["tipos_carga"] = list(label_encoders["NATURALEZA"].classes_) if "NATURALEZA" in label_encoders else []
        opciones["origenes"] = list(label_encoders["CARGUE"].classes_) if "CARGUE" in label_encoders else []
        opciones["destinos"] = list(label_encoders["DESCARGUE"].classes_) if "DESCARGUE" in label_encoders else []

    if opciones["tipos_carga"] == [] and not dataset.empty:
        opciones["tipos_carga"] = sorted(dataset["NATURALEZA"].dropna().unique()) if "NATURALEZA" in dataset.columns else []
    if opciones["origenes"] == [] and not dataset.empty:
        opciones["origenes"] = sorted(dataset["CARGUE"].dropna().unique()) if "CARGUE" in dataset.columns else []
    if opciones["destinos"] == [] and not dataset.empty:
        opciones["destinos"] = sorted(dataset["DESCARGUE"].dropna().unique()) if "DESCARGUE" in dataset.columns else []

    return opciones


def preparar_datos(datos):
    cargar_recursos()
    df = pd.DataFrame([datos])

    if isinstance(label_encoders, dict):
        for col, le in label_encoders.items():
            if col in df.columns:
                valor = str(df[col].iloc[0])
                if valor not in le.classes_:
                    valor = le.classes_[0]
                df[col] = le.transform([valor])

    columnas_path = os.path.join(BASE_DIR, 'columnas_modelo.pkl')
    if os.path.exists(columnas_path):
        columnas_modelo = cargar_recurso(columnas_path, default=list(df.columns))
    else:
        columnas_modelo = list(df.columns)

    df = df.reindex(columns=columnas_modelo, fill_value=0)
    return df


def buscar_coincidencias(datos):
    origen = datos.get("origen", "")
    destino = datos.get("destino", "")
    tipo = datos.get("tipo_carga", "")

    opciones = obtener_opciones()
    origen_real = coincidencia_inexacta(origen, opciones.get("origenes", []))
    destino_real = coincidencia_inexacta(destino, opciones.get("destinos", []))
    tipo_real = coincidencia_inexacta(tipo, opciones.get("tipos_carga", []))

    return origen_real, destino_real, tipo_real


def predecir_por_reglas(datos):
    cargar_recursos()
    if dataset.empty:
        return 0.0

    df = dataset.copy()
    origen_real, destino_real, tipo_real = buscar_coincidencias(datos)
    peso = float(datos.get("peso_kg") or 0)

    if "CARGUE" in df.columns:
        df["CARGUE_N"] = df["CARGUE"].astype(str).apply(normalizar_texto)
    if "DESCARGUE" in df.columns:
        df["DESCARGUE_N"] = df["DESCARGUE"].astype(str).apply(normalizar_texto)
    if "NATURALEZA" in df.columns:
        df["NATURALEZA_N"] = df["NATURALEZA"].astype(str).apply(normalizar_texto)

    origen_norm = normalizar_texto(origen_real)
    destino_norm = normalizar_texto(destino_real)
    tipo_norm = normalizar_texto(tipo_real)

    mask = pd.Series([True] * len(df))
    if origen_norm and "CARGUE_N" in df.columns:
        mask &= df["CARGUE_N"] == origen_norm
    if destino_norm and "DESCARGUE_N" in df.columns:
        mask &= df["DESCARGUE_N"] == destino_norm
    if tipo_norm and "NATURALEZA_N" in df.columns:
        mask &= df["NATURALEZA_N"] == tipo_norm

    if peso > 0 and "CANTIDAD" in df.columns:
        lower = peso * 0.5
        upper = peso * 1.5
        mask &= df["CANTIDAD"].between(lower, upper)

    candidatos = df[mask]
    if not candidatos.empty:
        return candidatos["HORAS_VIAJE"].mean()

    # Intento menos estricto por rutas y tipo
    if origen_norm and destino_norm and "CARGUE_N" in df.columns and "DESCARGUE_N" in df.columns:
        candidatos = df[
            (df["CARGUE_N"] == origen_norm) &
            (df["DESCARGUE_N"] == destino_norm)
        ]
        if not candidatos.empty:
            return candidatos["HORAS_VIAJE"].mean()

    if origen_norm and tipo_norm and "CARGUE_N" in df.columns and "NATURALEZA_N" in df.columns:
        candidatos = df[
            (df["CARGUE_N"] == origen_norm) &
            (df["NATURALEZA_N"] == tipo_norm)
        ]
        if not candidatos.empty:
            return candidatos["HORAS_VIAJE"].mean()

    if destino_norm and tipo_norm and "DESCARGUE_N" in df.columns and "NATURALEZA_N" in df.columns:
        candidatos = df[
            (df["DESCARGUE_N"] == destino_norm) &
            (df["NATURALEZA_N"] == tipo_norm)
        ]
        if not candidatos.empty:
            return candidatos["HORAS_VIAJE"].mean()

    if "HORAS_VIAJE" in df.columns:
        return df["HORAS_VIAJE"].mean()

    return 0.0


def _predecir_por_reglas_col(datos, columna):
    """Predice una columna numérica basada en promedios del dataset por coincidencias.
    Usa la misma lógica que `predecir_por_reglas` pero devuelve la media de `columna`.
    """
    cargar_recursos()
    if dataset.empty:
        return 0.0

    df = dataset.copy()
    origen_real, destino_real, tipo_real = buscar_coincidencias(datos)
    peso = float(datos.get("peso_kg") or 0)

    if "CARGUE" in df.columns:
        df["CARGUE_N"] = df["CARGUE"].astype(str).apply(normalizar_texto)
    if "DESCARGUE" in df.columns:
        df["DESCARGUE_N"] = df["DESCARGUE"].astype(str).apply(normalizar_texto)
    if "NATURALEZA" in df.columns:
        df["NATURALEZA_N"] = df["NATURALEZA"].astype(str).apply(normalizar_texto)

    origen_norm = normalizar_texto(origen_real)
    destino_norm = normalizar_texto(destino_real)
    tipo_norm = normalizar_texto(tipo_real)

    mask = pd.Series([True] * len(df))
    if origen_norm and "CARGUE_N" in df.columns:
        mask &= df["CARGUE_N"] == origen_norm
    if destino_norm and "DESCARGUE_N" in df.columns:
        mask &= df["DESCARGUE_N"] == destino_norm
    if tipo_norm and "NATURALEZA_N" in df.columns:
        mask &= df["NATURALEZA_N"] == tipo_norm

    if peso > 0 and "CANTIDAD" in df.columns:
        lower = peso * 0.5
        upper = peso * 1.5
        mask &= df["CANTIDAD"].between(lower, upper)

    candidatos = df[mask]
    if not candidatos.empty and columna in candidatos.columns:
        return round(float(candidatos[columna].mean()), 2)

    # Intentos menos estrictos
    if origen_norm and destino_norm and "CARGUE_N" in df.columns and "DESCARGUE_N" in df.columns and columna in df.columns:
        candidatos = df[(df["CARGUE_N"] == origen_norm) & (df["DESCARGUE_N"] == destino_norm)]
        if not candidatos.empty:
            return round(float(candidatos[columna].mean()), 2)

    if origen_norm and tipo_norm and "CARGUE_N" in df.columns and "NATURALEZA_N" in df.columns and columna in df.columns:
        candidatos = df[(df["CARGUE_N"] == origen_norm) & (df["NATURALEZA_N"] == tipo_norm)]
        if not candidatos.empty:
            return round(float(candidatos[columna].mean()), 2)

    if destino_norm and tipo_norm and "DESCARGUE_N" in df.columns and "NATURALEZA_N" in df.columns and columna in df.columns:
        candidatos = df[(df["DESCARGUE_N"] == destino_norm) & (df["NATURALEZA_N"] == tipo_norm)]
        if not candidatos.empty:
            return round(float(candidatos[columna].mean()), 2)

    if columna in df.columns:
        return round(float(df[columna].mean()), 2)

    return 0.0


def predecir_espera_carga(datos):
    """Predice las horas de espera en cargue usando reglas sobre el dataset."""
    try:
        # Si hay un modelo específico para este target futuramente, se puede usar aquí
        return _predecir_por_reglas_col(datos, "HORAS_ESPERA_CARGUE")
    except Exception:
        return 0.0


def predecir_espera_descarga(datos):
    """Predice las horas de espera en descargue usando reglas sobre el dataset."""
    try:
        return _predecir_por_reglas_col(datos, "HORAS_ESPERA_DESCARGUE")
    except Exception:
        return 0.0


def recomendar_tipo_por_peso(datos):
    """Recomienda el `NATURALEZA` (tipo de carga) más frecuente para pesos similares en el dataset.
    Busca filas con `CANTIDAD` en un rango 0.5x-1.5x del peso dado y devuelve la moda de `NATURALEZA`.
    """
    cargar_recursos()
    if dataset.empty or "CANTIDAD" not in dataset.columns or "NATURALEZA" not in dataset.columns:
        return ""

    try:
        peso = float(datos.get("peso_kg") or 0)
    except Exception:
        peso = 0.0

    if peso <= 0:
        return ""

    lower = peso * 0.5
    upper = peso * 1.5
    candidatos = dataset[dataset["CANTIDAD"].between(lower, upper)]
    if candidatos.empty:
        # fallback a todo el dataset
        candidatos = dataset

    modos = candidatos["NATURALEZA"].dropna()
    if modos.empty:
        return ""

    modo = modos.mode()
    if modo.empty:
        return ""

    return str(modo.iloc[0])


def predecir_tiempo(datos):
    cargar_recursos()

    if modelo is not None:
        try:
            datos_preparados = preparar_datos(datos)
            prediccion = modelo.predict(datos_preparados)
            return round(float(prediccion[0]), 2)
        except Exception as exc:
            print(f"Advertencia: no se pudo predecir con el modelo, usando reglas de datos ({exc})")

    return round(float(predecir_por_reglas(datos)), 2)
