import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, font
from collections import defaultdict
from math import log2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from wordcloud import WordCloud
from PIL import Image, ImageTk
import io

class DarkLoldleAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Dark Loldle Assistant")
        self.root.geometry("1600x900")
        
        # Configuration du thème sombre
        self.bg_color = "#121212"
        self.fg_color = "#ffffff"
        self.accent_color = "#1e88e5"
        self.secondary_color = "#424242"
        self.success_color = "#43a047"
        self.warning_color = "#fb8c00"
        self.error_color = "#e53935"
        
        self.root.configure(bg=self.bg_color)
        
        # Chargement des données
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
        self.weights = {
            'genre': 0.8,
            'role': 1.2, 
            'espece': 1.0,
            'ressource': 0.7,
            'type-de-portee': 0.9,
            'region': 1.1,
            'year': 0.8
        }
        
        # Configuration de la police
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=10)
        self.bold_font = font.Font(weight="bold", size=10)
        self.title_font = font.Font(size=12, weight="bold")
        
        # Création de l'interface
        self.create_widgets()
        self.update_display()
    
    def load_data(self):
        """Charge les données depuis le fichier CSV"""
        df = pd.read_csv('champions.csv', delimiter=';')
        self.champions = df.to_dict('records')
        self.champion_names = [c['champion'] for c in self.champions]
        
        # Pré-calculs
        self.calculate_all_probabilities()

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
    
    def set_feedback(self, attribute, value):
        """Définit le feedback pour un attribut"""
        for (attr, val), btn in self.feedback_buttons.items():
            if attr == attribute:
                if val == value:
                    btn.config(relief=tk.SUNKEN)
                else:
                    btn.config(relief=tk.RAISED)
        self.feedback_vars[attribute].set(value)

    def on_champ_click(self, event):
        """Gère le clic sur un champion"""
        item = self.champ_tree.identify_row(event.y)
        if item:
            champ_name = self.champ_tree.item(item, "text")
            self.current_guess = next(c for c in self.champions if c['champion'] == champ_name)
            self.current_champ_var.set(f"Testé: {champ_name}")
            
            # Réinitialiser les feedbacks
            for (attr, val), btn in self.feedback_buttons.items():
                btn.config(relief=tk.RAISED)
            for var in self.feedback_vars.values():
                var.set('')
    
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
    
    def update_wordcloud(self):
        """Met à jour le nuage de mots des champions restants"""
        # Supprimer le widget existant s'il y en a un
        for widget in self.wordcloud_frame.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'remaining_champs') or not self.remaining_champs:
            tk.Label(self.wordcloud_frame, text="Aucun champion restant",
                    bg=self.bg_color, fg=self.fg_color).pack(expand=True)
            return
        
        try:
            # Création du nuage de mots
            text = " ".join([champ['champion'] for champ in self.remaining_champs])
            wordcloud = WordCloud(
                width=480,
                height=600,
                background_color=self.bg_color,
                colormap="viridis",
                max_words=100
            ).generate(text)
            
            # Affichage avec matplotlib
            fig = plt.figure(figsize=(4.8, 6), facecolor=self.bg_color)
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")
            plt.tight_layout()
            
            # Intégration dans Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.wordcloud_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Erreur WordCloud: {e}")
            tk.Label(self.wordcloud_frame, text="Erreur de génération",
                    bg=self.bg_color, fg=self.error_color).pack(expand=True)
    
    def create_widgets(self):
        """Crée l'interface utilisateur"""
        # Frame principale
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Colonne de gauche - Liste des champions avec entropie
        left_frame = tk.Frame(main_frame, bg=self.bg_color, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        tk.Label(left_frame, text="Champions", font=self.title_font,
                bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        
        # Treeview amélioré
        self.champ_tree = ttk.Treeview(left_frame, columns=("Entropie", "Statut"), 
                                    show="headings", selectmode="browse", height=30)
        self.champ_tree.heading("#0", text="Champion")
        self.champ_tree.heading("Entropie", text="Entropie")
        self.champ_tree.heading("Statut", text="Statut")
        self.champ_tree.column("#0", width=250, anchor="w")
        self.champ_tree.column("Entropie", width=80, anchor="center")
        self.champ_tree.column("Statut", width=70, anchor="center")
        
        # Style pour les lignes
        style = ttk.Style()
        style.configure("Treeview", 
                    background=self.secondary_color, 
                    foreground=self.fg_color,
                    rowheight=25)
        style.map("Treeview", background=[('selected', self.accent_color)])
        
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.champ_tree.yview)
        self.champ_tree.configure(yscrollcommand=scrollbar.set)
        
        self.champ_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Lier le double-clic
        self.champ_tree.bind("<Double-1>", self.on_champ_double_click)
        
        # Frame centrale - Feedback et suggestions
        center_frame = tk.Frame(main_frame, bg=self.bg_color)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Section de feedback
        feedback_frame = tk.LabelFrame(center_frame, text=" Feedback ", font=self.title_font,
                                     bg=self.bg_color, fg=self.fg_color)
        feedback_frame.pack(fill=tk.X, pady=5)
        
        # Affichage du champion sélectionné
        self.current_champ_var = tk.StringVar()
        tk.Label(feedback_frame, textvariable=self.current_champ_var, 
                font=self.bold_font, bg=self.bg_color, fg=self.accent_color).pack(pady=5)
        
        # Feedback par attribut (horizontal)
        self.feedback_buttons = {}
        feedback_grid = tk.Frame(feedback_frame, bg=self.bg_color)
        feedback_grid.pack(pady=10)

        attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year']
        for i, attr in enumerate(attributes):
            frame = tk.Frame(feedback_grid, bg=self.bg_color)
            frame.grid(row=0, column=i, padx=5)
            
            tk.Label(frame, text=attr.capitalize(), bg=self.bg_color, 
                    fg=self.fg_color, font=self.bold_font).pack(pady=5)
            
            if attr == 'year':
                options = [('Exact', 'V', self.success_color),
                        ('+ Ancien', 'older', self.warning_color),
                        ('+ Récent', 'newer', self.warning_color)]
            elif attr in ['role', 'espece', 'region', 'type-de-portee']:
                options = [('Exact', 'V', self.success_color),
                        ('Partiel', 'O', self.warning_color),
                        ('Faux', 'R', self.error_color)]
            else:
                options = [('Vrai', 'V', self.success_color),
                        ('Faux', 'R', self.error_color)]
            
            for text, value, color in options:
                btn = tk.Button(frame, text=text, command=lambda a=attr, v=value: self.set_feedback(a, v),
                            bg=color, fg=self.fg_color, bd=0, padx=5, pady=2,
                            activebackground=color, activeforeground=self.fg_color)
                btn.pack(fill=tk.X, pady=2)
                self.feedback_buttons[(attr, value)] = btn
        
        # Boutons de contrôle
        control_frame = tk.Frame(feedback_frame, bg=self.bg_color)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Appliquer Feedback", command=self.apply_feedback,
                 bg=self.secondary_color, fg=self.fg_color, bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Nouvelle Partie", command=self.new_game,
                 bg=self.error_color, fg=self.fg_color, bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Modifier Poids", command=self.open_weights_editor,
                 bg=self.secondary_color, fg=self.fg_color, bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Section des suggestions
        suggestion_frame = tk.LabelFrame(center_frame, text=" Suggestions ", font=self.title_font,
                                       bg=self.bg_color, fg=self.fg_color)
        suggestion_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.suggestion_canvas = tk.Canvas(suggestion_frame, bg=self.bg_color, highlightthickness=0)
        self.suggestion_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Colonne de droite - Nuage de mots des champions restants
        right_frame = tk.Frame(main_frame, bg=self.bg_color, width=500)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

        tk.Label(right_frame, text="Nuage de mots", font=self.title_font,
                bg=self.bg_color, fg=self.fg_color).pack(pady=5)

        self.wordcloud_frame = tk.Frame(right_frame, bg=self.bg_color)
        self.wordcloud_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialiser le nuage de mots
        self.update_wordcloud()
    
    def on_champ_double_click(self, event):
        """Gère le double-clic sur un champion"""
        item = self.champ_tree.selection()[0]
        champ_name = self.champ_tree.item(item, "text")
        self.current_guess = next(c for c in self.champions if c['champion'] == champ_name)
        self.current_champ_var.set(f"Testé: {champ_name}")
        
        # Réinitialiser les feedbacks
        for var in self.feedback_vars.values():
            var.set('')
    
    def apply_feedback(self):
        """Applique le feedback pour filtrer les champions"""
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
            messagebox.showwarning("Incohérence", "Aucun champion ne correspond à ces critères")
        elif len(self.remaining_champs) == 1:
            messagebox.showinfo("Félicitations", f"Champion trouvé : {self.remaining_champs[0]['champion']}")
    
    def update_display(self):
        """Met à jour toute l'interface"""
        # Mettre à jour la liste des champions avec leurs entropies
        self.update_champ_list()
        
        # Mettre à jour le nuage de mots
        self.update_wordcloud()
        
        # Mettre à jour les suggestions
        self.update_suggestions()
    
    def update_champ_list(self):
        """Met à jour la liste des champions avec leurs entropies"""
        for item in self.champ_tree.get_children():
            self.champ_tree.delete(item)
        
        for champ in self.champions:
            entropy = self.calculate_entropy(champ)
            self.champ_tree.insert("", "end", text=champ['champion'], values=(f"{entropy:.2f}",))
    
    def update_suggestions(self):
        """Met à jour les suggestions visuelles"""
        self.suggestion_canvas.delete("all")
        
        if not self.remaining_champs:
            self.suggestion_canvas.create_text(150, 50, text="Aucun champion restant", 
                                             fill=self.fg_color, font=self.title_font)
            return
        
        # Calculer les meilleurs guesses
        scored_champs = []
        for champ in self.remaining_champs:
            entropy = self.calculate_entropy(champ)
            scored_champs.append((champ, entropy))
        
        scored_champs.sort(key=lambda x: x[1], reverse=True)
        top_5 = scored_champs[:5]
        
        # Afficher les suggestions sous forme de cartes colorées
        for i, (champ, score) in enumerate(top_5):
            x0, y0 = 20, 20 + i*100
            x1, y1 = 280, 100 + i*100
            
            # Couleur en fonction du score
            hue = min(120, int(score * 40))  # Vert plus intense pour les meilleurs scores
            color = f"#{hue:02x}{60:02x}00"
            
            # Dessiner la carte
            self.suggestion_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=self.secondary_color)
            self.suggestion_canvas.create_text(x0+10, y0+20, text=champ['champion'], 
                                             anchor="w", fill=self.fg_color, font=self.bold_font)
            self.suggestion_canvas.create_text(x0+10, y0+50, text=f"Score: {score:.2f}", 
                                             anchor="w", fill=self.fg_color)
            
            # Bouton cliquable
            btn_id = self.suggestion_canvas.create_rectangle(x1-80, y1-30, x1-10, y1-10, 
                                                           fill=self.accent_color, outline=self.accent_color)
            self.suggestion_canvas.create_text(x1-45, y1-20, text="Choisir", fill=self.fg_color)
            
            # Lier le clic
            self.suggestion_canvas.tag_bind(btn_id, "<Button-1>", 
                                          lambda e, c=champ: self.select_champion(c))
    
    def select_champion(self, champion):
        """Sélectionne un champion depuis les suggestions"""
        self.current_guess = champion
        self.current_champ_var.set(f"Testé: {champion['champion']}")
        
        # Réinitialiser les feedbacks
        for var in self.feedback_vars.values():
            var.set('')
    
    def new_game(self):
        """Réinitialise la partie"""
        self.remaining_champs = self.champions.copy()
        self.guess_history = []
        self.current_guess = None
        self.current_champ_var.set("")
        
        for var in self.feedback_vars.values():
            var.set('')
        
        self.update_display()
        messagebox.showinfo("Nouvelle partie", "Partie réinitialisée!")
    
    def open_weights_editor(self):
        """Ouvre l'éditeur de poids"""
        editor = tk.Toplevel(self.root)
        editor.title("Éditeur de poids")
        editor.geometry("400x500")
        editor.configure(bg=self.bg_color)
        
        tk.Label(editor, text="Ajustez les poids des attributs", font=self.title_font,
                bg=self.bg_color, fg=self.fg_color).pack(pady=10)
        
        self.weight_vars = {}
        for attr, weight in self.weights.items():
            frame = tk.Frame(editor, bg=self.bg_color)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(frame, text=attr.capitalize(), width=15, 
                    bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
            
            var = tk.DoubleVar(value=weight)
            tk.Scale(frame, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                    variable=var, bg=self.bg_color, fg=self.fg_color, 
                    highlightthickness=0).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.weight_vars[attr] = var
        
        btn_frame = tk.Frame(editor, bg=self.bg_color)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Appliquer", command=lambda: self.save_weights(editor),
                 bg=self.accent_color, fg=self.fg_color, bd=0, padx=15, pady=5).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Annuler", command=editor.destroy,
                 bg=self.secondary_color, fg=self.fg_color, bd=0, padx=15, pady=5).pack(side=tk.LEFT, padx=10)
    
    def save_weights(self, window):
        """Sauvegarde les nouveaux poids"""
        for attr, var in self.weight_vars.items():
            self.weights[attr] = var.get()
        
        window.destroy()
        self.update_display()
        messagebox.showinfo("Succès", "Poids mis à jour avec succès")

if __name__ == "__main__":
    root = tk.Tk()
    app = DarkLoldleAssistant(root)
    root.mainloop()