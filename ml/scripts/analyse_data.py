from pyspark.sql import SparkSession
import os
ML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dossier ml/

# Initialisation de Spark
spark = SparkSession.builder.appName("HealthDataAnalysis").getOrCreate()

# Lecture des données
file_path = os.path.join(ML_DIR, "data", "raw", "health_data_1000.csv")
df = spark.read.csv(file_path, header=True, inferSchema=True)

print("\n--- 1. Aperçu des données ---")
df.show(5)

print("\n--- 2. Statistiques descriptives ---")
df.describe("age", "systolic_bp", "glucose").show()

print("\n--- 3. Répartition des diagnostics ---")
df.groupBy("has_hypertension").count().show()

print("\n--- 4. Tension moyenne selon le diagnostic ---")
df.groupBy("has_hypertension").avg("systolic_bp").show()

spark.stop()