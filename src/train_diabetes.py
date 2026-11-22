import os
import sys

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
os.environ["HADOOP_HOME"] = r"D:\hadoop"
os.environ["hadoop.home.dir"] = r"D:\hadoop"

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark = SparkSession.builder \
    .appName("TrainDiabetesModel") \
    .config("spark.hadoop.io.nativeio.enabled", "false") \
    .getOrCreate()

# 1. Lecture des données
file_path = os.path.join("data", "raw", "diabetes_data_1000.csv")
df = spark.read.csv(file_path, header=True, inferSchema=True)

# 2. Assemblage des features
assembler = VectorAssembler(
    inputCols=["age", "glucose", "bmi", "blood_pressure"],
    outputCol="features"
)
data = assembler.transform(df)

# 3. Séparation entraînement / test
train_data, test_data = data.randomSplit([0.8, 0.2], seed=42)
print(f"Taille entraînement : {train_data.count()} lignes")
print(f"Taille test : {test_data.count()} lignes")

# 4. Entraînement
rf = RandomForestClassifier(featuresCol="features", labelCol="has_diabetes", numTrees=50)
model = rf.fit(train_data)

# 5. Évaluation
predictions = model.transform(test_data)
evaluator = BinaryClassificationEvaluator(labelCol="has_diabetes")
auc = evaluator.evaluate(predictions)
print(f"\n--- Performance du modèle Diabète (AUC) : {auc:.4f} ---")

# 6. Sauvegarde
model_path = os.path.join("models", "diabetes_model")
model.write().overwrite().save(model_path)
print(f"✅ Modèle sauvegardé dans : {model_path}")

spark.stop()