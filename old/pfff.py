import pandas as pd
import numpy as np

# Charger les données avec le bon encodage
try:
    data = pd.read_csv('loldle entropy.csv', sep=';', header=None, encoding='latin1')
except UnicodeDecodeError:
    data = pd.read_csv('loldle entropy.csv', sep=';', header=None, encoding='cp1252')

# Extraire les noms des champions et les probabilités
champions = data.iloc[0].values
probabilities = data.iloc[1:].values.astype(float)

# Fonction pour calculer l'entropie
def calculate_entropy(prob_series):
    prob_series = prob_series[prob_series > 0]  # Éviter log(0)
    return -np.sum(prob_series * np.log2(prob_series))

# Calculer l'entropie pour chaque champion
entropies = [calculate_entropy(probabilities[:, i]) for i in range(len(champions))]

# Créer et trier les résultats
results = sorted(zip(champions, entropies), key=lambda x: x[1], reverse=True)

# Écrire les résultats dans un fichier texte
with open('champions_entropy_ranking.txt', 'w', encoding='utf-8') as f:
    f.write("Classement des champions par entropie (du plus imprévisible au plus prévisible):\n")
    f.write("="*70 + "\n")
    f.write("{:<5} {:<25} {:<15}\n".format("Rang", "Champion", "Entropie"))
    f.write("-"*50 + "\n")
    
    for rank, (champ, entropy) in enumerate(results, 1):
        f.write("{:<5} {:<25} {:<15.4f}\n".format(rank, champ, entropy))

print("Les résultats ont été enregistrés dans 'champions_entropy_ranking.txt'")