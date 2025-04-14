class LoldleAssistant {
    constructor() {
        this.champions = [];
        this.remainingChamps = [];
        this.guessHistory = [];
        this.currentGuess = null;
        this.topGuesses = [];
        this.weights = {
            'genre': 0.8,
            'role': 1.2, 
            'espece': 1.0,
            'ressource': 0.7,
            'type-de-portee': 0.9,
            'region': 1.1,
            'year': 0.8
        };
        
        this.distributions = {};
        this.probabilities = {};
        
        this.chart = null;
        
        this.initElements();
        this.loadData();
    }
    
    initElements() {
        // Main elements
        this.suggestionText = document.getElementById('suggestionText');
        this.suggestionList = document.getElementById('suggestionList');
        this.calculateBtn = document.getElementById('calculateBtn');
        this.historyBody = document.getElementById('historyBody');
        this.currentGuessElement = document.getElementById('currentGuess');
        this.feedbackControls = document.getElementById('feedbackControls');
        this.applyFeedbackBtn = document.getElementById('applyFeedbackBtn');
        this.newGameBtn = document.getElementById('newGameBtn');
        this.statsBtn = document.getElementById('statsBtn');
        this.weightsBtn = document.getElementById('weightsBtn');
        
        // Modals
        this.statsModal = document.getElementById('statsModal');
        this.closeStatsBtn = document.getElementById('closeStatsBtn');
        this.statsTabs = document.getElementById('statsTabs');
        this.statsContent = document.getElementById('statsContent');
        
        this.weightsModal = document.getElementById('weightsModal');
        this.closeWeightsBtn = document.getElementById('closeWeightsBtn');
        this.weightsContainer = document.getElementById('weightsContainer');
        this.saveWeightsBtn = document.getElementById('saveWeightsBtn');
        this.cancelWeightsBtn = document.getElementById('cancelWeightsBtn');
        this.resetWeightsBtn = document.getElementById('resetWeightsBtn');
        
        // Chart
        const chartCtx = document.getElementById('distributionChart').getContext('2d');
        this.chart = new Chart(chartCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Champions restants',
                    data: [],
                    backgroundColor: 'rgba(74, 111, 165, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribution des champions restants'
                    }
                }
            }
        });
        
        // Event listeners
        this.calculateBtn.addEventListener('click', () => this.updateSuggestions());
        this.applyFeedbackBtn.addEventListener('click', () => this.applyFeedback());
        this.newGameBtn.addEventListener('click', () => this.newGame());
        this.statsBtn.addEventListener('click', () => this.showStats());
        this.weightsBtn.addEventListener('click', () => this.openWeightsEditor());
        
        this.closeStatsBtn.addEventListener('click', () => this.statsModal.style.display = 'none');
        this.closeWeightsBtn.addEventListener('click', () => this.weightsModal.style.display = 'none');
        this.cancelWeightsBtn.addEventListener('click', () => this.weightsModal.style.display = 'none');
        
        this.saveWeightsBtn.addEventListener('click', () => this.saveWeights());
        this.resetWeightsBtn.addEventListener('click', () => this.resetWeights());
        
        // Create feedback controls
        this.createFeedbackControls();
    }
    
    async loadData() {
        try {
            const response = await fetch('champions.csv');
            const csvData = await response.text();
            
            Papa.parse(csvData, {
                header: true,
                delimiter: ';',
                skipEmptyLines: true,
                complete: (results) => {
                    this.champions = results.data;
                    this.championNames = this.champions.map(c => c.champion);
                    
                    if (this.validateData()) {
                        this.calculateDistributions();
                        this.calculateAllProbabilities();
                        this.newGame();
                    }
                },
                error: (error) => {
                    this.showError(`Impossible de charger les données: ${error.message}`);
                }
            });
        } catch (error) {
            this.showError(`Impossible de charger le fichier: ${error.message}`);
        }
    }
    
    validateData() {
        const requiredAttrs = ['champion', 'genre', 'role', 'espece', 
                             'ressource', 'type-de-portee', 'region', 'year'];
        
        for (const champ of this.champions) {
            for (const attr of requiredAttrs) {
                if (!(attr in champ)) {
                    this.showError(`Attribut manquant: ${attr} pour ${champ.champion || '?'}`);
                    return false;
                }
            }
            
            // Vérifier les valeurs d'année
            try {
                parseInt(champ.year);
            } catch (error) {
                this.showError(`Année invalide pour ${champ.champion}: ${champ.year || '?'}`);
                return false;
            }
        }
        
        return true;
    }
    
    calculateDistributions() {
        this.distributions = {};
        const attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year'];
        
        for (const attr of attributes) {
            const valueCounts = {};
            let total = 0;
            
            for (const champion of this.champions) {
                const values = String(champion[attr]).split(' - ');
                for (const val of values) {
                    const trimmedVal = val.trim();
                    if (trimmedVal) {
                        valueCounts[trimmedVal] = (valueCounts[trimmedVal] || 0) + 1;
                        total++;
                    }
                }
            }
            
            this.distributions[attr] = {
                values: [],
                counts: [],
                percentages: []
            };
            
            const sortedEntries = Object.entries(valueCounts).sort((a, b) => b[1] - a[1]);
            
            for (const [val, count] of sortedEntries) {
                this.distributions[attr].values.push(val);
                this.distributions[attr].counts.push(count);
                this.distributions[attr].percentages.push(count / total * 100);
            }
        }
    }
    
    calculateAllProbabilities() {
        this.probabilities = {};
        const attributeTypes = {
            'genre': 'boolean',
            'role': 'multi',
            'espece': 'multi',
            'ressource': 'boolean',
            'type-de-portee': 'multi',
            'region': 'multi',
            'year': 'year'
        };
        
        for (const champion of this.champions) {
            this.probabilities[champion.champion] = this.calculateChampionProbabilities(champion, attributeTypes);
        }
    }
    
    calculateChampionProbabilities(champion, attributeTypes) {
        const probs = {};
        const totalChamps = this.champions.length;
        
        for (const [attr, attrType] of Object.entries(attributeTypes)) {
            const champVal = String(champion[attr]).trim();
            const attrProbs = {};
            
            if (attrType === 'boolean') {
                const count = this.champions.filter(c => String(c[attr]).trim() === champVal).length;
                attrProbs['V'] = count / totalChamps;
                attrProbs['R'] = 1 - attrProbs['V'];
                
            } else if (attrType === 'multi') {
                const values = champVal.split(' - ').map(v => v.trim()).filter(v => v);
                
                // Match exact
                const exactCount = this.champions.filter(c => String(c[attr]).trim() === champVal).length;
                attrProbs['V'] = exactCount / totalChamps;
                
                // Match partiel
                let partialCount = 0;
                for (const c of this.champions) {
                    const cVals = String(c[attr]).split(' - ').map(v => v.trim()).filter(v => v);
                    
                    if (cVals.some(v => values.includes(v)) && String(c[attr]).trim() !== champVal) {
                        partialCount++;
                    }
                }
                
                attrProbs['O'] = partialCount / totalChamps;
                attrProbs['R'] = Math.max(0, 1 - attrProbs['V'] - attrProbs['O']);
                
            } else if (attr === 'year') {
                try {
                    const year = parseInt(champion.year);
                    const same = this.champions.filter(c => parseInt(c.year) === year).length;
                    const older = this.champions.filter(c => parseInt(c.year) < year).length;
                    const newer = this.champions.filter(c => parseInt(c.year) > year).length;
                    
                    attrProbs['V'] = same / totalChamps;
                    attrProbs['older'] = older / totalChamps;
                    attrProbs['newer'] = newer / totalChamps;
                } catch (error) {
                    attrProbs['V'] = 0;
                    attrProbs['older'] = 0.5;
                    attrProbs['newer'] = 0.5;
                }
            }
            
            probs[attr] = attrProbs;
        }
        
        return probs;
    }
    
    calculateEntropy(champion) {
        const probs = this.probabilities[champion.champion];
        let totalEntropy = 0;
        
        for (const [attr, attrProbs] of Object.entries(probs)) {
            let attrEntropy = 0;
            for (const prob of Object.values(attrProbs)) {
                if (prob > 0) {
                    attrEntropy -= prob * Math.log2(prob);
                }
            }
            totalEntropy += attrEntropy * this.weights[attr];
        }
        
        return totalEntropy;
    }
    
    getBestGuess() {
        if (this.remainingChamps.length === 0) {
            return null;
        }
        
        let bestGuess = null;
        let bestScore = -1;
        
        for (const champ of this.remainingChamps) {
            const entropy = this.calculateEntropy(champ);
            if (entropy > bestScore) {
                bestScore = entropy;
                bestGuess = champ;
            }
        }
        
        return bestGuess;
    }
    
    createFeedbackControls() {
        const attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year'];
        this.feedbackVars = {};
        
        for (const attr of attributes) {
            const frame = document.createElement('div');
            frame.className = 'feedback-attribute';
            
            const label = document.createElement('div');
            label.className = 'attribute-name';
            label.textContent = attr.charAt(0).toUpperCase() + attr.slice(1);
            frame.appendChild(label);
            
            const radioGroup = document.createElement('div');
            radioGroup.className = 'radio-group';
            
            const varName = `feedback_${attr}`;
            this.feedbackVars[attr] = varName;
            
            if (attr === 'year') {
                this.createRadioOption(radioGroup, varName, 'V', 'Vrai');
                this.createRadioOption(radioGroup, varName, 'older', 'Plus ancien');
                this.createRadioOption(radioGroup, varName, 'newer', 'Plus récent');
            } else if (['role', 'espece', 'region', 'type-de-portee'].includes(attr)) {
                this.createRadioOption(radioGroup, varName, 'V', 'Vrai');
                this.createRadioOption(radioGroup, varName, 'O', 'Partiel');
                this.createRadioOption(radioGroup, varName, 'R', 'Faux');
            } else {
                this.createRadioOption(radioGroup, varName, 'V', 'Vrai');
                this.createRadioOption(radioGroup, varName, 'R', 'Faux');
            }
            
            frame.appendChild(radioGroup);
            this.feedbackControls.appendChild(frame);
        }
    }
    
    createRadioOption(container, name, value, label, checked = false) {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'radio-option';
        
        const input = document.createElement('input');
        input.type = 'radio';
        input.name = name;
        input.value = value;
        input.id = `${name}_${value}`;
        if (checked) input.checked = true;
        
        const labelEl = document.createElement('label');
        labelEl.htmlFor = `${name}_${value}`;
        labelEl.textContent = label;
        
        optionDiv.appendChild(input);
        optionDiv.appendChild(labelEl);
        container.appendChild(optionDiv);
    }
    
    updateSuggestions() {
        if (this.remainingChamps.length === 0) {
            this.suggestionText.textContent = "Aucun champion restant";
            this.suggestionList.innerHTML = '';
            return;
        }
        
        const scoredChamps = this.remainingChamps.map(champ => ({
            champ,
            score: this.calculateEntropy(champ)
        }));
        
        scoredChamps.sort((a, b) => b.score - a.score);
        const top5 = scoredChamps;
        
        this.suggestionText.textContent = '';
        
        // Update suggestion list
        this.suggestionList.innerHTML = '';
        this.topGuesses = top5.map(item => item.champ);
        
        top5.forEach((item, index) => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.textContent = `${index+1}. ${item.champ.champion} (${item.score.toFixed(2)})`;
            suggestionItem.addEventListener('click', () => this.selectGuess(index));
            this.suggestionList.appendChild(suggestionItem);
        });
    }
    
    selectGuess(index) {
        if (this.topGuesses && index >= 0 && index < this.topGuesses.length) {
            this.currentGuess = this.topGuesses[index];
            this.currentGuessElement.textContent = this.currentGuess.champion;
            
            // Reset all feedback radios
            document.querySelectorAll('input[type="radio"]').forEach(radio => {
                if (radio.value === '') radio.checked = true;
                else radio.checked = false;
            });
            
            for (let i = 0; i < document.getElementsByClassName('suggestion-item').length; i++) {
                document.getElementsByClassName('suggestion-item')[i].style.backgroundColor='#f0f0f0';
                document.getElementsByClassName('suggestion-item')[i].style.color='black';
                if (document.getElementsByClassName('suggestion-item')[i].textContent.includes(this.currentGuess.champion)) {
                    document.getElementsByClassName('suggestion-item')[i].style.backgroundColor='#4a6fa5';
                    document.getElementsByClassName('suggestion-item')[i].style.color='white';
                }
            }
        }
    }
    
    applyFeedback() {
        if (!this.currentGuess) {
            this.showAlert("Attention", "Aucun champion sélectionné");
            return;
        }
        
        const feedback = {};
        let hasFeedback = false;
        
        for (const attr in this.feedbackVars) {
            const selectedRadio = document.querySelector(`input[name="${this.feedbackVars[attr]}"]:checked`);
            if (selectedRadio && selectedRadio.value !== '') {
                feedback[attr] = selectedRadio.value;
                hasFeedback = true;
            }
        }
        
        if (!hasFeedback) {
            this.showAlert("Attention", "Aucun feedback fourni");
            return;
        }
        
        const newRemaining = [];
        for (const champ of this.remainingChamps) {
            let keep = true;
            
            for (const [attr, fbVal] of Object.entries(feedback)) {
                const champVal = String(champ[attr]).trim();
                const guessVal = String(this.currentGuess[attr]).trim();
                
                if (!champVal || !guessVal) continue;
                
                if (fbVal === 'V') {
                    if (champVal !== guessVal) {
                        keep = false;
                        break;
                    }
                } else if (fbVal === 'O') {
                    const champVals = new Set(champVal.split(' - ').map(v => v.trim()).filter(v => v));
                    const guessVals = new Set(guessVal.split(' - ').map(v => v.trim()).filter(v => v));
                    
                    let hasCommon = false;
                    for (const val of champVals) {
                        if (guessVals.has(val)) {
                            hasCommon = true;
                            break;
                        }
                    }
                    
                    if (!hasCommon) {
                        keep = false;
                        break;
                    }
                } else if (fbVal === 'R') {
                    const champVals = new Set(champVal.split(' - ').map(v => v.trim()).filter(v => v));
                    const guessVals = new Set(guessVal.split(' - ').map(v => v.trim()).filter(v => v));
                    
                    let hasCommon = false;
                    for (const val of champVals) {
                        if (guessVals.has(val)) {
                            hasCommon = true;
                            break;
                        }
                    }
                    
                    if (hasCommon) {
                        keep = false;
                        break;
                    }
                } else if (fbVal === 'older') {
                    try {
                        if (parseInt(champ.year) >= parseInt(this.currentGuess.year)) {
                            keep = false;
                            break;
                        }
                    } catch (error) {
                        continue;
                    }
                } else if (fbVal === 'newer') {
                    try {
                        if (parseInt(champ.year) <= parseInt(this.currentGuess.year)) {
                            keep = false;
                            break;
                        }
                    } catch (error) {
                        continue;
                    }
                }
            }
            
            if (keep) {
                newRemaining.push(champ);
            }
        }
        
        this.remainingChamps = newRemaining;
        this.guessHistory.push({
            guess: this.currentGuess.champion,
            remaining: this.remainingChamps.length
        });
        
        this.updateDisplay();
        
        if (this.remainingChamps.length === 0) {
            this.showAlert("Erreur", "Aucun champion ne correspond");
        } else if (this.remainingChamps.length === 1) {
            this.showAlert("Félicitations", `Trouvé: ${this.remainingChamps[0].champion}`);
        }
    }
    
    updateDisplay() {
        this.updateSuggestions();
        this.updateHistory();
        this.updateVisualization();
    }
    
    updateHistory() {
        this.historyBody.innerHTML = '';
        
        this.guessHistory.forEach(item => {
            const row = document.createElement('tr');
            
            const guessCell = document.createElement('td');
            guessCell.textContent = item.guess;
            row.appendChild(guessCell);
            
            const remainingCell = document.createElement('td');
            remainingCell.textContent = item.remaining;
            row.appendChild(remainingCell);
            
            this.historyBody.appendChild(row);
        });
    }
    
    updateVisualization() {
        if (this.remainingChamps.length === 0) {
            this.chart.data.labels = [];
            this.chart.data.datasets[0].data = [];
            this.chart.options.plugins.title.text = "Aucun champion restant";
            this.chart.update();
            return;
        }
        
        const regions = {};
        for (const champ of this.remainingChamps) {
            const regionVals = String(champ.region).split(' - ');
            for (const region of regionVals) {
                const trimmedRegion = region.trim();
                if (trimmedRegion) {
                    regions[trimmedRegion] = (regions[trimmedRegion] || 0) + 1;
                }
            }
        }
        
        const sortedRegions = Object.entries(regions).sort((a, b) => b[1] - a[1]);
        
        this.chart.data.labels = sortedRegions.map(item => item[0]);
        this.chart.data.datasets[0].data = sortedRegions.map(item => item[1]);
        this.chart.options.plugins.title.text = `Champions restants (${this.remainingChamps.length})`;
        this.chart.update();
    }
    
    newGame() {
        this.remainingChamps = [...this.champions];
        this.guessHistory = [];
        this.currentGuess = null;
        this.currentGuessElement.textContent = "Aucun champion sélectionné";
        
        // Reset all feedback radios
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            if (radio.value === '') radio.checked = true;
            else radio.checked = false;
        });
        
        this.updateDisplay();
        this.showAlert("Nouvelle partie", "Partie réinitialisée!");
    }
    
    showStats() {
        if (this.remainingChamps.length === 0) {
            this.showAlert("Stats", "Aucun champion restant");
            return;
        }
        
        // Clear previous content
        this.statsTabs.innerHTML = '';
        this.statsContent.innerHTML = '';
        
        const attributes = ['genre', 'role', 'espece', 'ressource', 'type-de-portee', 'region', 'year'];
        
        // Create tabs
        attributes.forEach((attr, index) => {
            const tab = document.createElement('div');
            tab.className = `tab ${index === 0 ? 'active' : ''}`;
            tab.textContent = attr.charAt(0).toUpperCase() + attr.slice(1);
            tab.addEventListener('click', () => this.switchStatsTab(index));
            this.statsTabs.appendChild(tab);
        });
        
        // Create tab content
        attributes.forEach((attr, index) => {
            const tabContent = document.createElement('div');
            tabContent.className = `tab-content ${index === 0 ? 'active' : ''}`;
            
            const valueCounts = {};
            for (const champ of this.remainingChamps) {
                const vals = String(champ[attr]).split(' - ').map(v => v.trim()).filter(v => v);
                for (const val of vals) {
                    valueCounts[val] = (valueCounts[val] || 0) + 1;
                }
            }
            
            const table = document.createElement('table');
            table.className = 'stats-table';
            
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            ['Valeur', 'Count', '%'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            const tbody = document.createElement('tbody');
            const sortedValues = Object.entries(valueCounts).sort((a, b) => b[1] - a[1]);
            
            sortedValues.forEach(([val, count]) => {
                const perc = (count / this.remainingChamps.length * 100).toFixed(1);
                const row = document.createElement('tr');
                
                const valCell = document.createElement('td');
                valCell.textContent = val;
                row.appendChild(valCell);
                
                const countCell = document.createElement('td');
                countCell.textContent = count;
                row.appendChild(countCell);
                
                const percCell = document.createElement('td');
                percCell.textContent = `${perc}%`;
                row.appendChild(percCell);
                
                tbody.appendChild(row);
            });
            
            table.appendChild(tbody);
            tabContent.appendChild(table);
            this.statsContent.appendChild(tabContent);
        });
        
        this.statsModal.style.display = 'flex';
    }
    
    switchStatsTab(index) {
        document.querySelectorAll('.tab').forEach((tab, i) => {
            tab.classList.toggle('active', i === index);
        });
        
        document.querySelectorAll('.tab-content').forEach((content, i) => {
            content.classList.toggle('active', i === index);
        });
    }
    
    openWeightsEditor() {
        this.weightsContainer.innerHTML = '';
        
        for (const [attr, weight] of Object.entries(this.weights)) {
            const weightItem = document.createElement('div');
            weightItem.className = 'weight-item';
            
            const label = document.createElement('div');
            label.className = 'weight-name';
            label.textContent = attr.charAt(0).toUpperCase() + attr.slice(1);
            weightItem.appendChild(label);
            
            const input = document.createElement('input');
            input.type = 'number';
            input.className = 'weight-input';
            input.step = '0.1';
            input.min = '0.1';
            input.max = '2.0';
            input.value = weight;
            input.dataset.attr = attr;
            weightItem.appendChild(input);
            
            this.weightsContainer.appendChild(weightItem);
        }
        
        this.weightsModal.style.display = 'flex';
    }
    
    saveWeights() {
        const inputs = this.weightsContainer.querySelectorAll('.weight-input');
        let hasError = false;
        
        inputs.forEach(input => {
            const attr = input.dataset.attr;
            try {
                const value = parseFloat(input.value);
                if (isNaN(value) || value < 0.1 || value > 2.0) {
                    throw new Error('Valeur invalide');
                }
                this.weights[attr] = value;
            } catch (error) {
                hasError = true;
                this.showError(`Valeur invalide pour ${attr}`);
            }
        });
        
        if (!hasError) {
            this.weightsModal.style.display = 'none';
            this.showAlert("Succès", "Poids mis à jour");
            this.updateSuggestions();
        }
    }
    
    resetWeights() {
        this.weights = {
            'genre': 0.8,
            'role': 1.2, 
            'espece': 1.0,
            'ressource': 0.7,
            'type-de-portee': 0.9,
            'region': 1.1,
            'year': 0.8
        };
        
        const inputs = this.weightsContainer.querySelectorAll('.weight-input');
        inputs.forEach(input => {
            const attr = input.dataset.attr;
            input.value = this.weights[attr];
        });
        
        this.showAlert("Succès", "Poids réinitialisés");
    }
    
    showAlert(title, message) {
        alert(`${title}\n\n${message}`);
    }
    
    showError(message) {
        alert(`Erreur\n\n${message}`);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new LoldleAssistant();
    document.querySelector('.searchBar input').addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        document.querySelectorAll('.suggestion-item').forEach(el => {
            const text = el.textContent.toLowerCase();
            el.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });
});

