"""Service de prédiction IA (Spark MLlib, Random Forest).

- La session Spark et les modèles sont chargés paresseusement au premier appel,
  ce qui permet de démarrer l'API sans Java/Spark (les autres routes marchent).
- Les chemins des modèles sont relatifs au dépôt (ml/models), plus de chemin
  codé en dur du type D:\\health_project.
"""

import os
import sys
import threading

from backend.config import MODELS_DIR

os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

# Sous Windows, Spark a besoin de winutils.exe : on respecte HADOOP_HOME s'il est
# déjà défini, sinon on tente D:\hadoop (configuration d'origine du projet).
if os.name == "nt" and "HADOOP_HOME" not in os.environ and os.path.isdir(r"D:\hadoop"):
    os.environ["HADOOP_HOME"] = r"D:\hadoop"

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.ml.feature import VectorAssembler  # noqa: E402
from pyspark.ml.classification import RandomForestClassificationModel  # noqa: E402

# Encodage du sexe identique à celui de l'entraînement : StringIndexer
# (frequencyDesc) sur health_data_1000.csv => F (509) = 0.0, M (491) = 1.0.
# L'ancien code ré-entraînait un StringIndexer sur la seule ligne reçue,
# ce qui encodait TOUJOURS le patient à 0.0 (= femme).
GENDER_INDEX = {"F": 0.0, "M": 1.0}

MODEL_DIRS = {
    "hypertension": "hypertension_model",
    "diabete": "diabetes_model",
}

_lock = threading.Lock()
_spark = None
_modeles = {}


def _get_spark():
    global _spark
    if _spark is None:
        _spark = (
            SparkSession.builder
            .appName("IA_Medicale")
            .config("spark.hadoop.io.nativeio.enabled", "false")
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
    return _spark


def _get_modele(maladie: str):
    with _lock:
        if maladie not in _modeles:
            _get_spark()
            chemin = MODELS_DIR / MODEL_DIRS[maladie]
            _modeles[maladie] = RandomForestClassificationModel.load(str(chemin))
            print(f"✅ Modèle {maladie} chargé depuis {chemin}")
        return _modeles[maladie]


def _predire(maladie: str, ligne: tuple, colonnes: list):
    modele = _get_modele(maladie)
    df = _get_spark().createDataFrame([ligne], colonnes)
    df = VectorAssembler(inputCols=colonnes, outputCol="features").transform(df)
    resultat = modele.transform(df).select("probability").collect()[0]
    return {"probabilite": float(resultat["probability"][1]), "maladie": maladie}


def predire_maladie(maladie: str, data_dict: dict):
    if maladie not in MODEL_DIRS:
        return {"erreur": f"Modèle pour {maladie} non disponible."}

    try:
        if maladie == "hypertension":
            requis = ["age", "gender", "systolic_bp", "glucose", "heart_rate"]
            manquants = [c for c in requis if data_dict.get(c) is None]
            if manquants:
                return {"erreur": f"Paramètres manquants : {', '.join(manquants)}"}

            gender = str(data_dict["gender"]).strip().upper()[:1]
            if gender not in GENDER_INDEX:
                return {"erreur": "Sexe invalide (attendu : M ou F)."}

            # Même ordre de colonnes que ml/scripts/train_model.py
            colonnes = ["age", "systolic_bp", "glucose", "heart_rate", "gender_index"]
            ligne = (
                float(data_dict["age"]), float(data_dict["systolic_bp"]),
                float(data_dict["glucose"]), float(data_dict["heart_rate"]),
                GENDER_INDEX[gender],
            )
            return _predire(maladie, ligne, colonnes)

        # Diabète — même ordre que ml/scripts/train_diabetes.py
        colonnes = ["age", "glucose", "bmi", "blood_pressure"]
        manquants = [c for c in colonnes if data_dict.get(c) is None]
        if manquants:
            return {"erreur": f"Paramètres manquants : {', '.join(manquants)}"}
        ligne = tuple(float(data_dict[c]) for c in colonnes)
        return _predire(maladie, ligne, colonnes)

    except Exception as e:  # erreurs Spark / Java
        texte = str(e)
        if "NativeIO" in texte or "winutils" in texte.lower() or "HADOOP_HOME" in texte:
            return {"erreur": (
                "Spark ne trouve pas Hadoop pour Windows : installez winutils.exe et "
                "hadoop.dll dans <HADOOP_HOME>\\bin puis définissez HADOOP_HOME (voir README)."
            )}
        if "JAVA_GATEWAY_EXITED" in texte or "Java gateway" in texte:
            return {"erreur": "Java introuvable : installez Java 17 et définissez JAVA_HOME."}
        # Une trace Java fait plusieurs Ko : on ne renvoie que la première ligne utile.
        premiere_ligne = next((l for l in texte.splitlines() if l.strip()), texte)
        return {"erreur": f"Erreur Spark ({maladie}) : {premiere_ligne[:300]}"}
