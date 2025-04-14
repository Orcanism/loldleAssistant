import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
from math import log2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LoldleAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistant Loldle Pro++")
        self.root.geometry("1400x900")
        
        try:
            self.load_data()
            if not self.validate_data():
                self.root.destroy()
                return
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")
            self.root.destroy()
            return
        
        # Variables d'état
        self.current_guess = None
        self.remaining_champs = self.champions.copy()
        self.guess_history = []
        self.attribute_feedbacks = {}
        self.weights = {
            'genre': 0.8,
            'role': 1.2, 
            'espece': 1.0,
            'ressource': 0.7,
            'type-de-portee': 0.9,
            'region': 1.1,
            'year': 0.8
        }
        
        # Style
        self.setup_style()
        
        # Interface
        self.create_widgets()
        self.update_display()

    def setup_style(self):
        """Configure le style de l'interface"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10), padding=5)
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Treeview', rowheight=25)
        style.map('TButton', background=[('active', '#e0e0e0')])
        style.configure('Danger.TButton', foreground='white', background='#dc3545')
        style.map('Danger.TButton', 
                background=[('active', '#c82333'), ('disabled', '#f5c6cb')])
    
    def load_data(self):
        """Charge toutes les données nécessaires"""
        try:
            # Charger les champions
            df = pd.read_csv('champions.csv', delimiter=';')
            self.champions = df.to_dict('records')
            self.champion_names = [c['champion'] for c in self.champions]
            
            # Pré-calculer les distributions et probabilités
            self.calculate_distributions()
            self.calculate_all_probabilities()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")
            self.root.destroy()
    
    def validate_data(self):
        """Vérifie la cohérence des données chargées"""
        required_attrs = ['champion', 'genre', 'role', 'espece', 
                         'ressource', 'type-de-portee', 'region', 'year']
        
        for champ in self.champions:
            for attr in required_attrs:
                if attr not in champ:
                    messagebox.showerror("Erreur de données", 
                                      f"Attribut manquant: {attr} pour {champ.get('champion','?')}")
                    return False
        
        # Vérifier les valeurs d'année
        for champ in self.champions:
            try:
                int(champ['year'])
            except (ValueError, KeyError):
                messagebox.showerror("Erreur de données",
                                  f"Année invalide pour {champ['champion']}: {champ.get('year','?')}")
                return False
        
        return True
    
    def calculate_distributions(self):
        """Calcule les distributions des attributs"""
        self.distributions = {}
        attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']
        
        for attr in attributes:
            value_counts = defaultdict(int)
            total = 0
            
            for champion in self.champions:
                values = str(champion[attr]).split(' - ')
                for val in values:
                    val = val.strip()
                    if val:
                        value_counts[val] += 1
                        total += 1
            
            self.distributions[attr] = {
                'values': [],
                'counts': [],
                'percentages': []
            }
            
            for val, count in sorted(value_counts.items(), key=lambda x: -x[1]):
                self.distributions[attr]['values'].append(val)
                self.distributions[attr]['counts'].append(count)
                self.distributions[attr]['percentages'].append(count / total * 100)
    
    def calculate_all_probabilities(self):
        """Calcule les probabilités pour tous les champions"""
        self.probabilities = {}
        attribute_types = {
            'genre': 'boolean',
            'role': 'multi',
            'espece': 'multi',
            'ressource': 'boolean',
            'type-de-portee': 'multi',
            'region': 'multi',
            'year': 'year'
        }
        
        for champion in self.champions:
            self.probabilities[champion['champion']] = self.calculate_champion_probabilities(champion, attribute_types)
    
    def calculate_champion_probabilities(self, champion, attribute_types):
        """Version corrigée du calcul des probabilités"""
        probs = {}
        total_champs = len(self.champions)
        
        for attr, attr_type in attribute_types.items():
            champ_val = str(champion.get(attr, '')).strip()
            attr_probs = {}
            
            if attr_type == 'boolean':
                count = sum(1 for c in self.champions 
                          if str(c.get(attr, '')).strip() == champ_val)
                attr_probs['V'] = count / total_champs
                attr_probs['R'] = 1 - attr_probs['V']
                
            elif attr_type == 'multi':
                values = [v.strip() for v in champ_val.split(' - ') if v.strip()]
                
                # Match exact
                exact_count = sum(1 for c in self.champions 
                                 if str(c.get(attr, '')).strip() == champ_val)
                attr_probs['V'] = exact_count / total_champs
                
                # Match partiel
                partial_count = 0
                for c in self.champions:
                    c_vals = str(c.get(attr, '')).split(' - ')
                    c_vals = [v.strip() for v in c_vals if v.strip()]
                    
                    if any(v in c_vals for v in values) and str(c.get(attr, '')).strip() != champ_val:
                        partial_count += 1
                
                attr_probs['O'] = partial_count / total_champs
                attr_probs['R'] = max(0, 1 - attr_probs['V'] - attr_probs['O'])
                
            elif attr == 'year':
                try:
                    year = int(champion.get('year', 0))
                    same = sum(1 for c in self.champions 
                             if int(c.get('year', 0)) == year)
                    older = sum(1 for c in self.champions 
                              if int(c.get('year', 0)) < year)
                    newer = sum(1 for c in self.champions 
                              if int(c.get('year', 0)) > year)
                    
                    attr_probs['V'] = same / total_champs
                    attr_probs['older'] = older / total_champs
                    attr_probs['newer'] = newer / total_champs
                except (ValueError, TypeError):
                    attr_probs['V'] = 0
                    attr_probs['older'] = 0.5
                    attr_probs['newer'] = 0.5
            
            probs[attr] = attr_probs
        
        return probs
    
    def calculate_entropy(self, champion):
        """Calcule l'entropie avec les poids ajustables"""
        probs = self.probabilities[champion['champion']]
        total_entropy = 0
        
        for attr, attr_probs in probs.items():
            attr_entropy = 0
            for prob in attr_probs.values():
                if prob > 0:
                    attr_entropy -= prob * log2(prob)
            total_entropy += attr_entropy * self.weights.get(attr, 1.0)
        
        return total_entropy
    
    def get_best_guess(self):
        """Détermine le meilleur guess suivant"""
        if not self.remaining_champs:
            return None
            
        best_guess = None
        best_score = -1
        
        for champ in self.remaining_champs:
            entropy = self.calculate_entropy(champ)
            if entropy > best_score:
                best_score = entropy
                best_guess = champ
        
        return best_guess
    
    def create_widgets(self):
        """Crée l'interface"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de gauche
        left_frame = ttk.Frame(main_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        # Suggestions
        suggestion_frame = ttk.LabelFrame(left_frame, text="Top 5 des meilleurs coups", padding=10)
        suggestion_frame.pack(fill=tk.X, pady=5)

        self.suggestion_label = ttk.Label(suggestion_frame, text="Cliquez sur 'Calculer'", font=('Arial', 10))
        self.suggestion_label.pack()

        button_frame = ttk.Frame(suggestion_frame)
        button_frame.pack(pady=5)
        for i in range(5):
            ttk.Button(button_frame, text=f"Choix {i+1}", 
                     command=lambda idx=i: self.select_guess(idx)).grid(row=i, column=1, padx=2)

        ttk.Button(suggestion_frame, text="Calculer", 
                 command=self.update_suggestion).pack(pady=5)
        
        # Historique
        history_frame = ttk.LabelFrame(left_frame, text="Historique", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.history_tree = ttk.Treeview(history_frame, columns=("Guess", "Restants"), show="headings")
        self.history_tree.heading("Guess", text="Guess")
        self.history_tree.heading("Restants", text="Restants")
        self.history_tree.column("Guess", width=200)
        self.history_tree.column("Restants", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de droite
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Feedback
        feedback_frame = ttk.LabelFrame(right_frame, text="Feedback", padding=10)
        feedback_frame.pack(fill=tk.X, pady=5)
        
        self.create_feedback_controls(feedback_frame)
        
        # Visualisation
        viz_frame = ttk.LabelFrame(right_frame, text="Visualisation", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax.set_title("Distribution des champions restants")
        self.ax.bar([], [])
        self.canvas.draw()
    
    def create_feedback_controls(self, parent):
        """Crée les contrôles pour entrer le feedback"""
        attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']
        
        current_frame = ttk.Frame(parent)
        current_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(current_frame, text="Champion testé:").pack(side=tk.LEFT)
        self.current_champ_var = tk.StringVar()
        ttk.Label(current_frame, textvariable=self.current_champ_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        
        self.feedback_vars = {}
        
        for attr in attributes:
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=attr.capitalize(), width=15).pack(side=tk.LEFT)
            
            var = tk.StringVar()
            if attr == 'year':
                ttk.Radiobutton(frame, text="Exact", variable=var, value='V').pack(side=tk.LEFT, padx=5)
                ttk.Radiobutton(frame, text="Plus ancien", variable=var, value='older').pack(side=tk.LEFT, padx=5)
                ttk.Radiobutton(frame, text="Plus récent", variable=var, value='newer').pack(side=tk.LEFT, padx=5)
            elif attr in ['role', 'espece', 'region', 'type-de-portee']:
                ttk.Radiobutton(frame, text="Exact", variable=var, value='V').pack(side=tk.LEFT, padx=5)
                ttk.Radiobutton(frame, text="Partiel", variable=var, value='O').pack(side=tk.LEFT, padx=5)
                ttk.Radiobutton(frame, text="Faux", variable=var, value='R').pack(side=tk.LEFT, padx=5)
            else:
                ttk.Radiobutton(frame, text="Vrai", variable=var, value='V').pack(side=tk.LEFT, padx=5)
                ttk.Radiobutton(frame, text="Faux", variable=var, value='R').pack(side=tk.LEFT, padx=5)
            
            ttk.Radiobutton(frame, text="Non testé", variable=var, value='').pack(side=tk.LEFT, padx=5)
            self.feedback_vars[attr] = var
        
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Appliquer", 
                 command=self.apply_feedback).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Nouvelle Partie", 
                 command=self.new_game, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stats", 
                 command=self.show_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Poids", 
                 command=self.open_weights_editor).pack(side=tk.LEFT, padx=5)
    
    def update_suggestion(self):
        """Met à jour les suggestions"""
        if not self.remaining_champs:
            self.suggestion_label.config(text="Aucun champion restant")
            return
        
        scored_champs = []
        for champ in self.remaining_champs:
            entropy = self.calculate_entropy(champ)
            scored_champs.append((champ, entropy))
        
        scored_champs.sort(key=lambda x: x[1], reverse=True)
        top_5 = scored_champs[:5]
        
        suggestion_text = "Top 5:\n"
        for i, (champ, score) in enumerate(top_5, 1):
            suggestion_text += f"{i}. {champ['champion']} ({score:.2f})\n"
        
        self.suggestion_label.config(text=suggestion_text)
        self.top_guesses = [champ for champ, score in top_5]
    
    def select_guess(self, index):
        """Sélectionne un guess"""
        if hasattr(self, 'top_guesses') and 0 <= index < len(self.top_guesses):
            self.current_guess = self.top_guesses[index]
            self.current_champ_var.set(self.current_guess['champion'])
            for var in self.feedback_vars.values():
                var.set('')
    
    def apply_feedback(self):
        """Applique le feedback"""
        if not self.current_guess:
            messagebox.showwarning("Attention", "Aucun champion sélectionné")
            return

        feedback = {attr: var.get() for attr, var in self.feedback_vars.items() if var.get()}
        
        if not feedback:
            messagebox.showwarning("Attention", "Aucun feedback fourni")
            return

        new_remaining = []
        for champ in self.remaining_champs:
            keep = True
            for attr, fb_val in feedback.items():
                champ_val = str(champ.get(attr, '')).strip()
                guess_val = str(self.current_guess.get(attr, '')).strip()
                
                if not champ_val or not guess_val:
                    continue
                    
                if fb_val == 'V':
                    if champ_val != guess_val:
                        keep = False
                        break
                        
                elif fb_val == 'O':
                    champ_vals = set(v.strip() for v in champ_val.split(' - ') if v.strip())
                    guess_vals = set(v.strip() for v in guess_val.split(' - ') if v.strip())
                    if not champ_vals & guess_vals:
                        keep = False
                        break
                        
                elif fb_val == 'R':
                    champ_vals = set(v.strip() for v in champ_val.split(' - ') if v.strip())
                    guess_vals = set(v.strip() for v in guess_val.split(' - ') if v.strip())
                    if champ_vals & guess_vals:
                        keep = False
                        break
                        
                elif fb_val == 'older':
                    try:
                        if int(champ.get('year', 0)) >= int(self.current_guess.get('year', 0)):
                            keep = False
                            break
                    except ValueError:
                        continue
                        
                elif fb_val == 'newer':
                    try:
                        if int(champ.get('year', 0)) <= int(self.current_guess.get('year', 0)):
                            keep = False
                            break
                    except ValueError:
                        continue
            
            if keep:
                new_remaining.append(champ)

        self.remaining_champs = new_remaining
        self.guess_history.append((self.current_guess['champion'], len(self.remaining_champs)))
        self.update_display()
        
        if len(self.remaining_champs) == 0:
            messagebox.showwarning("Erreur", "Aucun champion ne correspond")
        elif len(self.remaining_champs) == 1:
            messagebox.showinfo("Félicitations", f"Trouvé: {self.remaining_champs[0]['champion']}")
    
    def update_display(self):
        """Met à jour l'affichage"""
        self.update_suggestion()
        self.update_history()
        self.update_visualization()
    
    def update_history(self):
        """Met à jour l'historique"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        for i, (guess, remaining) in enumerate(self.guess_history, 1):
            self.history_tree.insert("", "end", values=(guess, remaining))
    
    def update_visualization(self):
        """Met à jour la visualisation"""
        self.ax.clear()
        
        if not self.remaining_champs:
            self.ax.set_title("Aucun champion restant")
            self.canvas.draw()
            return
        
        regions = defaultdict(int)
        for champ in self.remaining_champs:
            for region in str(champ.get('region', '')).split(' - '):
                regions[region.strip()] += 1
        
        if regions:
            labels, values = zip(*sorted(regions.items(), key=lambda x: -x[1]))
            self.ax.bar(labels, values)
            self.ax.set_title(f"Champions restants ({len(self.remaining_champs)})")
            self.ax.tick_params(axis='x', rotation=45)
            self.figure.tight_layout()
            self.canvas.draw()
    
    def new_game(self):
        """Nouvelle partie"""
        self.remaining_champs = self.champions.copy()
        self.guess_history = []
        self.current_guess = None
        self.current_champ_var.set("")
        for var in self.feedback_vars.values():
            var.set('')
        self.update_display()
        messagebox.showinfo("Nouvelle partie", "Partie réinitialisée!")
    
    def show_stats(self):
        """Affiche les statistiques"""
        if not self.remaining_champs:
            messagebox.showinfo("Stats", "Aucun champion restant")
            return
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistiques")
        stats_window.geometry("600x400")
        
        notebook = ttk.Notebook(stats_window)
        
        for attr in ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=attr.capitalize())
            
            value_counts = defaultdict(int)
            for champ in self.remaining_champs:
                vals = str(champ.get(attr, '')).split(' - ')
                for val in vals:
                    value_counts[val.strip()] += 1
            
            tree = ttk.Treeview(frame, columns=("Valeur", "Count", "%"), show="headings")
            tree.heading("Valeur", text="Valeur")
            tree.heading("Count", text="Count")
            tree.heading("%", text="%")
            
            for val, count in sorted(value_counts.items(), key=lambda x: -x[1]):
                perc = count / len(self.remaining_champs) * 100
                tree.insert("", "end", values=(val, count, f"{perc:.1f}%"))
            
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        notebook.pack(fill=tk.BOTH, expand=True)
    
    def open_weights_editor(self):
        """Ouvre l'éditeur de poids"""
        weights_window = tk.Toplevel(self.root)
        weights_window.title("Éditeur de poids")
        weights_window.geometry("400x500")
        
        main_frame = ttk.Frame(weights_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Ajustez les poids des attributs:").pack(pady=10)
        
        self.weight_vars = {}
        for attr in self.weights:
            frame = ttk.Frame(main_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{attr}:", width=15).pack(side=tk.LEFT)
            
            var = tk.DoubleVar(value=self.weights[attr])
            spin = ttk.Spinbox(frame, from_=0.1, to=2.0, increment=0.1, 
                             textvariable=var, width=5)
            spin.pack(side=tk.LEFT)
            self.weight_vars[attr] = var
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="Appliquer", 
                  command=lambda: self.save_weights(weights_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", 
                  command=weights_window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Par défaut", 
                  command=self.reset_weights).pack(side=tk.LEFT, padx=5)
    
    def save_weights(self, window):
        """Sauvegarde les nouveaux poids"""
        for attr, var in self.weight_vars.items():
            try:
                self.weights[attr] = float(var.get())
            except ValueError:
                messagebox.showerror("Erreur", f"Valeur invalide pour {attr}")
                return
        
        window.destroy()
        messagebox.showinfo("Succès", "Poids mis à jour")
        self.update_suggestion()
    
    def reset_weights(self):
        """Réinitialise les poids"""
        self.weights = {
            'genre': 0.8,
            'role': 1.2, 
            'espece': 1.0,
            'ressource': 0.7,
            'type-de-portee': 0.9,
            'region': 1.1,
            'year': 0.8
        }
        for attr, var in self.weight_vars.items():
            var.set(self.weights[attr])
        messagebox.showinfo("Succès", "Poids réinitialisés")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoldleAssistant(root)
    root.mainloop()