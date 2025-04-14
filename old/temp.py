import pandas as pd
import numpy as np
from collections import defaultdict

# Charger les données
df = pd.read_csv('champions.csv', delimiter=';')
champions = df.to_dict('records')
attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']

# Dictionnaire pour stocker les distributions
distributions = {}

for attr in attributes:
    # Initialiser le compteur
    value_counts = defaultdict(int)
    total = 0
    
    # Compter chaque occurrence (y compris les multi-valeurs)
    for champion in champions:
        values = str(champion[attr]).split(' - ')
        for val in values:
            val = val.strip()
            if val:  # Ignorer les chaînes vides
                value_counts[val] += 1
                total += 1
    
    # Calculer les pourcentages
    distributions[attr] = {
        'values': [],
        'counts': [],
        'percentages': []
    }
    
    for val, count in sorted(value_counts.items(), key=lambda x: -x[1]):
        distributions[attr]['values'].append(val)
        distributions[attr]['counts'].append(count)
        distributions[attr]['percentages'].append(count / total * 100)

# Affichage des résultats
for attr in attributes:
    print(f"\nDistribution de l'attribut: {attr.upper()}")
    print("-" * 40)
    print(f"{'Valeur':<25} | {'Count':<6} | {'%':<5}")
    print("-" * 40)
    
    for val, count, perc in zip(distributions[attr]['values'],
                               distributions[attr]['counts'],
                               distributions[attr]['percentages']):
        print(f"{val:<25} | {count:<6} | {perc:.1f}%")
    
    print(f"\nTotal unique values: {len(distributions[attr]['values'])}")
    print(f"Total occurrences: {sum(distributions[attr]['counts'])}")
    print("-" * 40)

# Export vers un fichier texte
with open('loldle_distributions.txt', 'w', encoding='utf-8') as f:
    for attr in attributes:
        f.write(f"\nDistribution de l'attribut: {attr.upper()}\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'Valeur':<25} | {'Count':<6} | {'%':<5}\n")
        f.write("-" * 40 + "\n")
        
        for val, count, perc in zip(distributions[attr]['values'],
                                   distributions[attr]['counts'],
                                   distributions[attr]['percentages']):
            f.write(f"{val:<25} | {count:<6} | {perc:.1f}%\n")
        
        f.write(f"\nTotal unique values: {len(distributions[attr]['values'])}\n")
        f.write(f"Total occurrences: {sum(distributions[attr]['counts'])}\n")
        f.write("-" * 40 + "\n\n")

print("\nLes distributions ont été sauvegardées dans 'loldle_distributions.txt'")