import csv
import random
import os

# Chemin de sauvegarde
output_path = os.path.join("data", "raw", "health_data_1000.csv")

# Créer le dossier s'il n'existe pas
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["age", "gender", "systolic_bp", "glucose", "heart_rate", "has_hypertension"])

    for _ in range(1000):
        age = random.randint(20, 80)
        gender = random.choice(["M", "F"])
        
        # Tension simulée (augmente avec l'âge)
        base_bp = 110 + (age - 20) * 0.5
        systolic_bp = int(random.gauss(base_bp, 15))
        
        # Glycémie et fréquence cardiaque
        glucose = round(random.gauss(5.5, 1.0), 1)
        heart_rate = int(random.gauss(72, 10))
        
        # Règle médicale simplifiée
        has_hypertension = 0
        if systolic_bp >= 140 or (systolic_bp >= 130 and glucose >= 7.0) or (age >= 60 and systolic_bp >= 135):
            has_hypertension = 1
            
        # Ajout de 15% de bruit (cas réels atypiques)
        if random.random() < 0.15:
            has_hypertension = 1 - has_hypertension

        writer.writerow([age, gender, systolic_bp, glucose, heart_rate, has_hypertension])

print(f"✅ 1000 lignes de données générées avec succès dans {output_path}")