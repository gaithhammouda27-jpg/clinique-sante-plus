import csv
import random
import os

output_path = os.path.join("data", "raw", "diabetes_data_1000.csv")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["age", "glucose", "bmi", "blood_pressure", "has_diabetes"])

    for _ in range(1000):
        age = random.randint(20, 80)
        glucose = round(random.gauss(5.5, 1.5), 1)
        bmi = round(random.gauss(25, 5), 1)
        bp = random.randint(60, 100)
        
        # Règle médicale simplifiée
        has_diabetes = 0
        if glucose >= 7.0 or (glucose >= 6.0 and bmi >= 30):
            has_diabetes = 1
            
        # Ajout de bruit
        if random.random() < 0.1:
            has_diabetes = 1 - has_diabetes

        writer.writerow([age, glucose, bmi, bp, has_diabetes])

print(f"✅ 1000 lignes de données diabète générées dans {output_path}")