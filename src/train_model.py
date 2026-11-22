import os
os.environ["HADOOP_HOME"] = r"D:\hadoop"
os.environ["hadoop.home.dir"] = r"D:\hadoop"
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import os

spark = SparkSession.builder \
    .appName("TrainModel") \
    .config("spark.hadoop.io.nativeio.enabled", "false") \
    .getOrCreate()

# 1. Lecture des données
file_path = os.path.join("data", "raw", "health_data_1000.csv")
df = spark.read.csv(file_path, header=True, inferSchema=True)

# 2. Encodage de la variable catégorielle "gender"
indexer = StringIndexer(inputCol="gender", outputCol="gender_index")
df = indexer.fit(df).transform(df)

# 3. Assemblage des caractéristiques
assembler = VectorAssembler(
    inputCols=["age", "systolic_bp", "glucose", "heart_rate", "gender_index"],
    outputCol="features"
)
data = assembler.transform(df)

# 4. Séparation entraînement / test
train_data, test_data = data.randomSplit([0.8, 0.2], seed=42)
print(f"Taille de l'ensemble d'entraînement : {train_data.count()} lignes")
print(f"Taille de l'ensemble de test : {test_data.count()} lignes")

# 5. Entraînement du modèle (Random Forest)
rf = RandomForestClassifier(featuresCol="features", labelCol="has_hypertension", numTrees=50)
model = rf.fit(train_data)

# 6. Évaluation
predictions = model.transform(test_data)
evaluator = BinaryClassificationEvaluator(labelCol="has_hypertension")
auc = evaluator.evaluate(predictions)
print(f"\n--- Performance du modèle (AUC) : {auc:.4f} ---")

# 7. Sauvegarde du modèle
model_path = os.path.join("models", "hypertension_model")
model.write().overwrite().save(model_path)
print(f"✅ Modèle sauvegardé avec succès dans le dossier : {model_path}")

spark.stop()