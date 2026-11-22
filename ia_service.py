import os
import sys

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
os.environ["HADOOP_HOME"] = r"D:\hadoop"
os.environ["hadoop.home.dir"] = r"D:\hadoop"

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassificationModel

spark = SparkSession.builder \
    .appName("IA_Medicale") \
    .config("spark.hadoop.io.nativeio.enabled", "false") \
    .getOrCreate()

modeles = {}

def charger_modeles():
    global modeles
    try:
        # Modèle Hypertension
        modeles["hypertension"] = RandomForestClassificationModel.load(r"D:\health_project\models\hypertension_model")
        print("✅ Modèle Hypertension chargé.")
        
        # Modèle Diabète (à décommenter quand vous aurez entraîné le modèle)
        modeles["diabete"] = RandomForestClassificationModel.load(r"D:\health_project\models\diabetes_model")
        print("✅ Modèle Diabète chargé.")
    except Exception as e:
        print(f"❌ Erreur chargement modèles : {e}")

charger_modeles()

def predire_maladie(maladie: str, data_dict: dict):
    if maladie not in modeles:
        return {"erreur": f"Modèle pour {maladie} non disponible."}
    
    # --- HYPERTENSION ---
    if maladie == "hypertension":
        try:
            data = [(data_dict['age'], data_dict['gender'], data_dict['systolic_bp'], data_dict['glucose'], data_dict['heart_rate'])]
            cols = ["age", "gender", "systolic_bp", "glucose", "heart_rate"]
            df = spark.createDataFrame(data, cols)
            
            indexer = StringIndexer(inputCol="gender", outputCol="gender_index", handleInvalid="keep")
            df = indexer.fit(df).transform(df)
            
            assembler = VectorAssembler(
                inputCols=["age", "systolic_bp", "glucose", "heart_rate", "gender_index"],
                outputCol="features"
            )
            df = assembler.transform(df)
            
            prediction = modeles[maladie].transform(df)
            result = prediction.select("prediction", "probability").collect()[0]
            
            return {"probabilite": float(result["probability"][1]), "maladie": maladie}
        except Exception as e:
            return {"erreur": f"Erreur Spark : {str(e)}"}
    
    # --- DIABÈTE ---
    elif maladie == "diabete":
        try:
            print("=== DÉBUT PRÉDICTION DIABÈTE ===")
            print(f"Données reçues : {data_dict}")  # <-- AJOUTEZ CECI
            
            data = [(data_dict['age'], data_dict['glucose'], data_dict['bmi'], data_dict['blood_pressure'])]
            cols = ["age", "glucose", "bmi", "blood_pressure"]
            df = spark.createDataFrame(data, cols)
            
            assembler = VectorAssembler(inputCols=cols, outputCol="features")
            df = assembler.transform(df)
            
            prediction = modeles[maladie].transform(df)
            result = prediction.select("prediction", "probability").collect()[0]
            
            return {"probabilite": float(result["probability"][1]), "maladie": maladie}
        except Exception as e:
            print(f"❌ ERREUR DIABÈTE : {str(e)}")  # <-- AJOUTEZ CECI
            import traceback
            traceback.print_exc()  # <-- ET CECI
            return {"erreur": f"Erreur Spark Diabète : {str(e)}"}
    
    else:
        return {"erreur": f"Logique non implémentée pour {maladie}."}