import pandas as pd
import numpy as np
from collections import defaultdict
from tqdm import tqdm

# Charger les données
df = pd.read_csv('champions.csv', delimiter=';')
champions = df.to_dict('records')
attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']

# Calculer les distributions initiales pour chaque attribut
attribute_distributions = {}
for attr in attributes:
    values = []
    for c in champions:
        vals = str(c[attr]).split(' - ')
        values.extend(vals)
    unique, counts = np.unique(values, return_counts=True)
    attribute_distributions[attr] = {u: c/len(champions) for u, c in zip(unique, counts)}

def calculate_feedback_prob(guess, attr, mystery):
    g_val = str(guess[attr]).strip()
    m_val = str(mystery[attr]).strip()
    
    if g_val == m_val:
        return 'V'
    elif any(x in m_val.split(' - ') for x in g_val.split(' - ')):
        return 'O'
    else:
        return 'R'

def expected_remaining(guess):
    # Pré-calculer toutes les probabilités de feedback
    feedback_probs = defaultdict(float)
    feedback_counts = defaultdict(int)
    
    for mystery in champions:
        feedback = tuple(calculate_feedback_prob(guess, attr, mystery) for attr in attributes)
        feedback_probs[feedback] += 1/len(champions)
        feedback_counts[feedback] += 1
    
    # Calculer l'espérance
    expectation = 0
    for feedback in feedback_probs:
        prob = feedback_probs[feedback]
        count = feedback_counts[feedback]
        
        # Poids basé sur la probabilité réelle du feedback
        weight = 1
        for i, attr in enumerate(attributes):
            val = str(guess[attr]).split(' - ')[0]
            if feedback[i] == 'V':
                weight *= attribute_distributions[attr].get(val, 0.01)
            elif feedback[i] == 'O':
                # Probabilité qu'au moins une sous-valeur corresponde
                sub_vals = str(guess[attr]).split(' - ')
                p_O = sum(attribute_distributions[attr].get(x,0) for x in sub_vals)
                weight *= max(0.01, p_O - attribute_distributions[attr].get(val, 0))
            else:
                sub_vals = str(guess[attr]).split(' - ')
                p_R = 1 - sum(attribute_distributions[attr].get(x,0) for x in sub_vals)
                weight *= max(0.01, p_R)
        
        expectation += weight * count
    
    return expectation

# Trouver le meilleur guess
best_guess = None
best_score = float('inf')

print("Calcul précis en cours (avec distributions réelles)...")
for champion in tqdm(champions[:50]):  # On teste les 50 premiers pour l'exemple
    current_score = expected_remaining(champion)
    if current_score < best_score:
        best_score = current_score
        best_guess = champion

print(f"\nMEILLEUR PREMIER GUESS: {best_guess['champion']}")
print(f"Espérance de champions restants: {best_score:.1f}")

# Affichage des distributions pour vérification
print("\nDistributions des attributs clés:")
for attr in ['genre', 'role', 'espece']:
    print(f"\n{attr}:")
    for val, prob in sorted(attribute_distributions[attr].items(), key=lambda x: -x[1]):
        print(f"  {val}: {prob:.1%}")