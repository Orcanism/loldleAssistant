import pandas as pd
from collections import defaultdict

# Charger les données
df = pd.read_csv('champions.csv', delimiter=';')
champions = df.to_dict('records')

# Pré-calcul des distributions globales
distributions = {}
attribute_types = {
    'genre': 'boolean',
    'role': 'multi',
    'espece': 'multi',
    'ressource': 'boolean',
    'type-de-portee': 'multi',
    'region': 'multi',
    'year': 'year'
}

# Calculer les distributions
for attr, attr_type in attribute_types.items():
    counts = defaultdict(int)
    for champ in champions:
        val = str(champ[attr]).strip()
        if attr_type == 'multi':
            for v in val.split(' - '):
                counts[v.strip()] += 1
        else:
            counts[val] += 1
    distributions[attr] = dict(counts)

def calculate_probabilities(champion):
    probs = {}
    total_champs = len(champions)
    
    for attr, attr_type in attribute_types.items():
        champ_val = str(champion[attr]).strip()
        attr_probs = {}
        
        if attr_type == 'boolean':
            # Genre, ressource, type-de-portee
            count = distributions[attr].get(champ_val, 0)
            attr_probs['V'] = count / total_champs
            attr_probs['R'] = 1 - attr_probs['V']
            attr_probs['O'] = 0.0
            
        elif attr_type == 'multi':
            # Role, espece, region
            values = [v.strip() for v in champ_val.split(' - ')]
            
            # Calcul V (match exact)
            exact_count = sum(1 for c in champions if str(c[attr]).strip() == champ_val)
            attr_probs['V'] = exact_count / total_champs
            
            # Calcul O (au moins une valeur commune mais pas exact match)
            partial_count = 0
            for c in champions:
                c_vals = [v.strip() for v in str(c[attr]).split(' - ')]
                if set(values) & set(c_vals) and str(c[attr]).strip() != champ_val:
                    partial_count += 1
            attr_probs['O'] = partial_count / total_champs
            
            # Calcul R (aucune valeur commune)
            attr_probs['R'] = 1 - attr_probs['V'] - attr_probs['O']
            
        elif attr == 'year':
            # Traitement spécial pour l'année
            year = int(champion['year'])
            same = sum(1 for c in champions if int(c['year']) == year)
            older = sum(1 for c in champions if int(c['year']) < year)
            newer = sum(1 for c in champions if int(c['year']) > year)
            
            attr_probs['V'] = same / total_champs
            attr_probs['older'] = older / total_champs
            attr_probs['newer'] = newer / total_champs
        
        probs[attr] = attr_probs
    
    return probs

# Recalcul pour tous les champions
champion_probs = {c['champion']: calculate_probabilities(c) for c in champions}

# Vérification pour Aatrox
aatrox_probs = champion_probs['Aatrox']
print(f"\nVérification pour Aatrox:")
print(f"Genre (Masculin): V={aatrox_probs['genre']['V']:.1%}, R={aatrox_probs['genre']['R']:.1%}")
print(f"Rôle (Haut): V={aatrox_probs['role']['V']:.1%}, O={aatrox_probs['role']['O']:.1%}, R={aatrox_probs['role']['R']:.1%}")
print(f"Espèce (Darkin): V={aatrox_probs['espece']['V']:.1%}, O={aatrox_probs['espece']['O']:.1%}, R={aatrox_probs['espece']['R']:.1%}")
print(f"Année (2013): V={aatrox_probs['year']['V']:.1%}, older={aatrox_probs['year']['older']:.1%}, newer={aatrox_probs['year']['newer']:.1%}")

# Export des résultats
with open('loldle_probabilities_corrected.txt', 'w', encoding='utf-8') as f:
    for name, probs in champion_probs.items():
        champ = next(c for c in champions if c['champion'] == name)
        f.write(f"\nProbabilités pour {name}:\n")
        f.write("="*50 + "\n")
        
        for attr in attribute_types:
            val = champ[attr]
            attr_probs = probs[attr]
            if attr == 'year':
                f.write(f"Année ({val}):\n")
                f.write(f"  Exact: {attr_probs['V']:.1%}\n")
                f.write(f"  Plus ancien: {attr_probs['older']:.1%}\n")
                f.write(f"  Plus récent: {attr_probs['newer']:.1%}\n")
            else:
                f.write(f"{attr} ({val}):\n")
                f.write(f"  Vrai: {attr_probs['V']:.1%}\n")
                if attribute_types[attr] == 'multi':
                    f.write(f"  Partiel: {attr_probs['O']:.1%}\n")
                f.write(f"  Faux: {attr_probs['R']:.1%}\n")
            f.write("-"*40 + "\n")

print("\nRésultats corrigés sauvegardés dans 'loldle_probabilities_corrected.txt'")