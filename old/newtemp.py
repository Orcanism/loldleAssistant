import pandas as pd
from collections import defaultdict
from itertools import product
import math

# Charger les données
df = pd.read_csv('champions.csv', delimiter=';')
champions = df.to_dict('records')

attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']
feedback_types = {
    'genre': ['V', 'R'],
    'role': ['V', 'O', 'R'],
    'espece': ['V', 'O', 'R'],
    'ressource': ['V', 'R'],
    'type-de-portee': ['V', 'R'],
    'region': ['V', 'O', 'R'],
    'year': ['V', 'older', 'newer']
}

# Calcul théorique du nombre total de patterns possibles
total_possible_patterns = 1
for attr in attributes:
    total_possible_patterns *= len(feedback_types[attr])
print(f"Nombre théorique de patterns possibles: {total_possible_patterns} (2×3×3×2×2×3×3 = 648)")

def calculate_all_patterns(champion):
    patterns = defaultdict(float)
    total = len(champions)
    
    for mystery in champions:
        pattern = []
        for attr in attributes:
            champ_val = str(champion[attr]).strip()
            myst_val = str(mystery[attr]).strip()
            
            if attr == 'year':
                if int(myst_val) == int(champ_val):
                    pattern.append('V')
                elif int(myst_val) < int(champ_val):
                    pattern.append('older')
                else:
                    pattern.append('newer')
            else:
                if champ_val == myst_val:
                    pattern.append('V')
                elif attr in ['role', 'espece', 'region']:
                    champ_vals = set(champ_val.split(' - '))
                    myst_vals = set(myst_val.split(' - '))
                    if champ_vals & myst_vals:
                        pattern.append('O')
                    else:
                        pattern.append('R')
                else:
                    pattern.append('R')
        
        patterns[tuple(pattern)] += 1/total
    
    return patterns

# Calcul pour Aatrox
aatrox = next(c for c in champions if c['champion'] == 'Aatrox')
aatrox_patterns = calculate_all_patterns(aatrox)

print(f"\nNombre réel de patterns observés pour Aatrox: {len(aatrox_patterns)}")
print("Quelques exemples avec leur probabilité:")
for pattern, prob in sorted(aatrox_patterns.items(), key=lambda x: -x[1])[:10]:
    print(f"{pattern}: {prob:.4%}")

# Export COMPLET vers un fichier
with open('loldle_ALL_patterns.txt', 'w', encoding='utf-8') as f:
    for name in [c['champion'] for c in champions]:
        champ = next(c for c in champions if c['champion'] == name)
        patterns = calculate_all_patterns(champ)
        
        f.write(f"\n{name} - {len(patterns)} patterns uniques:\n")
        f.write("="*60 + "\n")
        
        # Trier par probabilité décroissante
        sorted_patterns = sorted(patterns.items(), key=lambda x: -x[1])
        
        for pattern, prob in sorted_patterns:
            f.write(f"{pattern}: {prob:.6f} ({prob:.4%})\n")
            
print("\nExport COMPLET terminé dans 'loldle_ALL_patterns.txt'")