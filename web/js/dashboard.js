/**
 * AgroVision AI - Dashboard Controller
 * Lógica do dashboard com simulação em tempo real
 */

class AgroVisionDashboard {
    constructor() {
        // Estado da aplicação
        this.state = {
            animals: [],
            detections: [],
            sessionStart: Date.now(),
            isRunning: false,
            fps: 30,
            frameCount: 0,
            lastFpsUpdate: Date.now()
        };

        // Elementos DOM
        this.elements = {};

        // Configurações
        this.config = {
            maxAnimals: 8,
            minAnimals: 2,
            detectionInterval: 2000, // ms
            updateInterval: 100, // ms
            simulationSpeed: 1
        };

        // Inicialização
        this.init();
    }

    /**
     * Inicializa o dashboard
     */
    init() {
        this.cacheElements();
        this.bindEvents();
        this.startSimulation();
        this.log('Sistema iniciado. Iniciando simulação...', 'success');
    }

    /**
     * Cache dos elementos DOM
     */
    cacheElements() {
        this.elements = {
            // Stats
            totalAnimals: document.getElementById('total-animals'),
            avgWeight: document.getElementById('avg-weight'),
            behaviorStatus: document.getElementById('behavior-status'),
            animalsChange: document.getElementById('animals-change'),
            sessionTime: document.getElementById('session-time'),
            fpsDisplay: document.getElementById('fps-display'),
            detectionCount: document.getElementById('detection-count'),

            // Layers SVG
            animalsLayer: document.getElementById('animals-layer'),
            detectionLayer: document.getElementById('detection-layer'),
            infoLayer: document.getElementById('info-layer'),

            // Listas
            animalList: document.getElementById('animal-list'),
            logContainer: document.getElementById('log-container'),

            // Loading
            loadingOverlay: document.getElementById('loading-overlay')
        };
    }

    /**
     * Bind de eventos
     */
    bindEvents() {
        // Controles do painel de vídeo
        document.querySelectorAll('.control-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const parent = e.currentTarget.parentElement;
                parent.querySelectorAll('.control-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');

                if (e.currentTarget.title === 'Pausar') {
                    this.toggleSimulation(false);
                } else if (e.currentTarget.title === 'Play') {
                    this.toggleSimulation(true);
                }
            });
        });
    }

    /**
     * Inicia a simulação
     */
    startSimulation() {
        this.state.isRunning = true;

        // Gerar animais iniciais
        this.generateInitialAnimals();

        // Loop de atualização
        this.runUpdateLoop();

        // Loop de detecções
        this.runDetectionLoop();

        // Atualizar tempo de sessão
        setInterval(() => this.updateSessionTime(), 1000);

        // Atualizar FPS
        setInterval(() => this.updateFps(), 1000);
    }

    /**
     * Toggle da simulação
     */
    toggleSimulation(running) {
        this.state.isRunning = running;
        if (running) {
            this.log('Simulação retomada', 'info');
        } else {
            this.log('Simulação pausada', 'warning');
        }
    }

    /**
     * Gera animais iniciais para simulação
     */
    generateInitialAnimals() {
        const numAnimals = this.randomInt(this.config.minAnimals, this.config.maxAnimals);

        for (let i = 0; i < numAnimals; i++) {
            this.addAnimal();
        }

        this.updateStats();
    }

    /**
     * Adiciona um animal à simulação
     */
    addAnimal() {
        const id = Date.now() - this.state.sessionStart + this.state.animals.length;
        const animal = {
            id: id,
            x: this.randomInt(100, 700),
            y: this.randomInt(350, 500),
            vx: this.randomFloat(-0.5, 0.5),
            vy: this.randomFloat(-0.3, 0.3),
            width: this.randomInt(60, 100),
            height: this.randomInt(50, 70),
            weight: this.randomInt(100, 200),
            behavior: this.randomBehavior(),
            color: this.randomColor(),
            direction: Math.random() > 0.5 ? 1 : -1
        };

        this.state.animals.push(animal);
        this.renderAnimal(animal);
        this.log(`Animal #${id} detectado`, 'success');
    }

    /**
     * Remove um animal da simulação
     */
    removeAnimal(index) {
        if (this.state.animals.length > 0) {
            const animal = this.state.animals.splice(index, 1)[0];
            this.removeAnimalElement(animal.id);
            this.log(`Animal #${animal.id} saiu do campo de visão`, 'info');
        }
    }

    /**
     * Renderiza um animal no SVG
     */
    renderAnimal(animal) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'animal-group');
        group.setAttribute('id', `animal-${animal.id}`);

        // Corpo do animal (estilo simplificado)
        const body = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        body.setAttribute('class', 'animal-body');
        body.setAttribute('cx', animal.x);
        body.setAttribute('cy', animal.y);
        body.setAttribute('rx', animal.width / 2);
        body.setAttribute('ry', animal.height / 2);
        body.setAttribute('fill', animal.color);
        body.setAttribute('stroke', '#2a2a2a');
        body.setAttribute('stroke-width', '2');

        // Cabeça
        const head = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        head.setAttribute('class', 'animal-head');
        head.setAttribute('cx', animal.x + (30 * animal.direction));
        head.setAttribute('cy', animal.y - 20);
        head.setAttribute('r', '15');
        head.setAttribute('fill', animal.color);

        // Olho
        const eye = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        eye.setAttribute('class', 'animal-eye');
        eye.setAttribute('cx', animal.x + (35 * animal.direction));
        eye.setAttribute('cy', animal.y - 22);
        eye.setAttribute('r', '3');
        eye.setAttribute('fill', '#000');

        // Patas
        const leg1 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        leg1.setAttribute('class', 'animal-leg');
        leg1.setAttribute('x', animal.x - 20);
        leg1.setAttribute('y', animal.y + 20);
        leg1.setAttribute('width', '8');
        leg1.setAttribute('height', '25');
        leg1.setAttribute('fill', '#3a3a3a');
        leg1.setAttribute('rx', '4');

        const leg2 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        leg2.setAttribute('class', 'animal-leg');
        leg2.setAttribute('x', animal.x + 12);
        leg2.setAttribute('y', animal.y + 20);
        leg2.setAttribute('width', '8');
        leg2.setAttribute('height', '25');
        leg2.setAttribute('fill', '#3a3a3a');
        leg2.setAttribute('rx', '4');

        group.appendChild(body);
        group.appendChild(head);
        group.appendChild(eye);
        group.appendChild(leg1);
        group.appendChild(leg2);

        this.elements.animalsLayer.appendChild(group);
    }

    /**
     * Remove elemento de animal do DOM
     */
    removeAnimalElement(id) {
        const element = document.getElementById(`animal-${id}`);
        if (element) {
            element.remove();
        }
    }

    /**
     * Renderiza bounding box de detecção
     */
    renderDetection(animal) {
        const bbox = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bbox.setAttribute('class', 'detection-bbox');
        bbox.setAttribute('x', animal.x - animal.width / 2 - 5);
        bbox.setAttribute('y', animal.y - animal.height / 2 - 25);
        bbox.setAttribute('width', animal.width + 10);
        bbox.setAttribute('height', animal.height + 50);

        // Label com informações
        const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        labelGroup.setAttribute('class', 'info-label-group');
        labelGroup.setAttribute('id', `label-${animal.id}`);

        const labelBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        labelBg.setAttribute('class', 'info-label-bg');
        labelBg.setAttribute('x', animal.x - animal.width / 2 - 5);
        labelBg.setAttribute('y', animal.y - animal.height / 2 - 45);
        labelBg.setAttribute('width', '80');
        labelBg.setAttribute('height', '20');
        labelBg.setAttribute('rx', '4');

        const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        labelText.setAttribute('class', 'info-label');
        labelText.setAttribute('x', animal.x - animal.width / 2);
        labelText.setAttribute('y', animal.y - animal.height / 2 - 30);
        labelText.textContent = `#${animal.id} ${animal.weight}kg`;

        labelGroup.appendChild(labelBg);
        labelGroup.appendChild(labelText);

        this.elements.detectionLayer.appendChild(bbox);
        this.elements.infoLayer.appendChild(labelGroup);
    }

    /**
     * Atualiza posições dos animais
     */
    updateAnimals() {
        this.state.animals.forEach(animal => {
            // Atualizar posição
            animal.x += animal.vx * animal.direction * this.config.simulationSpeed;
            animal.y += animal.vy * this.config.simulationSpeed;

            // Colisão com bordas
            if (animal.x <= 100 || animal.x >= 700) {
                animal.direction *= -1;
                animal.vx *= -1;
            }

            // Atualizar DOM
            const group = document.getElementById(`animal-${animal.id}`);
            if (group) {
                const body = group.querySelector('.animal-body');
                const head = group.querySelector('.animal-head');
                const eye = group.querySelector('.animal-eye');

                if (body) {
                    body.setAttribute('cx', animal.x);
                    body.setAttribute('cy', animal.y);
                }
                if (head) {
                    head.setAttribute('cx', animal.x + (30 * animal.direction));
                }
                if (eye) {
                    eye.setAttribute('cx', animal.x + (35 * animal.direction));
                }

                // Atualizar bounding box
                const bbox = document.getElementById(`bbox-${animal.id}`);
                if (bbox) {
                    bbox.setAttribute('x', animal.x - animal.width / 2 - 5);
                    bbox.setAttribute('y', animal.y - animal.height / 2 - 25);
                }

                // Atualizar label
                const label = document.getElementById(`label-${animal.id}`);
                if (label) {
                    const text = label.querySelector('text');
                    if (text) {
                        text.textContent = `#${animal.id} ${animal.weight}kg`;
                    }
                    const bg = label.querySelector('rect');
                    if (bg) {
                        bg.setAttribute('x', animal.x - animal.width / 2 - 5);
                        bg.setAttribute('y', animal.y - animal.height / 2 - 45);
                    }
                }
            }
        });

        // Renderizar detections
        this.renderDetections();
    }

    /**
     * Renderiza todas as detecções
     */
    renderDetections() {
        // Limpar layer anterior
        this.elements.detectionLayer.innerHTML = '';
        this.elements.infoLayer.innerHTML = '';

        this.state.animals.forEach(animal => {
            const bbox = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bbox.setAttribute('class', 'detection-bbox confirmed');
            bbox.setAttribute('x', animal.x - animal.width / 2 - 5);
            bbox.setAttribute('y', animal.y - animal.height / 2 - 25);
            bbox.setAttribute('width', animal.width + 10);
            bbox.setAttribute('height', animal.height + 50);
            bbox.setAttribute('id', `bbox-${animal.id}`);

            this.elements.detectionLayer.appendChild(bbox);

            // Label
            const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            labelGroup.setAttribute('id', `label-${animal.id}`);

            const labelBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            labelBg.setAttribute('class', 'info-label-bg');
            labelBg.setAttribute('x', animal.x - animal.width / 2 - 5);
            labelBg.setAttribute('y', animal.y - animal.height / 2 - 45);
            labelBg.setAttribute('width', '80');
            labelBg.setAttribute('height', '20');
            labelBg.setAttribute('rx', '4');

            const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            labelText.setAttribute('class', 'info-label');
            labelText.setAttribute('x', animal.x - animal.width / 2);
            labelText.setAttribute('y', animal.y - animal.height / 2 - 30);
            labelText.textContent = `#${animal.id} ${animal.weight}kg ${animal.behavior}`;
            labelText.setAttribute('fill', '#10b981');

            labelGroup.appendChild(labelBg);
            labelGroup.appendChild(labelText);
            this.elements.infoLayer.appendChild(labelGroup);
        });

        // Atualizar contador
        this.elements.detectionCount.textContent = `${this.state.animals.length} detecções`;
    }

    /**
     * Atualiza lista de animais no painel lateral
     */
    updateAnimalList() {
        if (!this.elements.animalList) return;

        this.elements.animalList.innerHTML = '';

        this.state.animals.forEach(animal => {
            const item = document.createElement('div');
            item.className = 'animal-item';
            item.innerHTML = `
                <span class="animal-id">#${animal.id}</span>
                <div class="animal-info">
                    <span class="animal-name">Vaca ${animal.id}</span>
                    <div class="animal-details">
                        <span>${animal.weight} kg</span>
                        <span class="animal-status ${animal.behavior}">${animal.behavior}</span>
                    </div>
                </div>
            `;
            this.elements.animalList.appendChild(item);
        });

        if (this.state.animals.length === 0) {
            this.elements.animalList.innerHTML = `
                <div class="animal-item placeholder">
                    <span class="animal-info">Aguardando detecções...</span>
                </div>
            `;
        }
    }

    /**
     * Atualiza estatísticas do dashboard
     */
    updateStats() {
        const totalAnimals = this.state.animals.length;
        const avgWeight = totalAnimals > 0
            ? Math.round(this.state.animals.reduce((sum, a) => sum + a.weight, 0) / totalAnimals)
            : 0;
        const dominantBehavior = this.getDominantBehavior();

        // Animar números
        this.animateValue(this.elements.totalAnimals, parseInt(this.elements.totalAnimals.textContent) || 0, totalAnimals, 500);
        this.animateValue(this.elements.avgWeight, parseInt(this.elements.avgWeight.textContent) || 0, avgWeight, 500, 'kg');

        this.elements.behaviorStatus.textContent = dominantBehavior;
        this.elements.behaviorStatus.className = `behavior-value ${dominantBehavior.toLowerCase()}`;
    }

    /**
     * Obtém comportamento dominante
     */
    getDominantBehavior() {
        const behaviors = this.state.animals.map(a => a.behavior);
        const counts = behaviors.reduce((acc, b) => {
            acc[b] = (acc[b] || 0) + 1;
            return acc;
        }, {});

        return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Calmo';
    }

    /**
     * Loop principal de atualização
     */
    runUpdateLoop() {
        const update = () => {
            if (this.state.isRunning) {
                this.updateAnimals();
                this.state.frameCount++;
            }
            requestAnimationFrame(update);
        };
        update();

        // Atualizações periódicas
        setInterval(() => {
            if (this.state.isRunning) {
                this.updateStats();
                this.updateAnimalList();
                this.maybeAddOrRemoveAnimal();
                this.maybeChangeBehavior();
            }
        }, this.config.updateInterval);
    }

    /**
     * Loop de detecções simuladas
     */
    runDetectionLoop() {
        setInterval(() => {
            if (this.state.isRunning) {
                // Simular nova detecção ocasionalmente
                if (Math.random() < 0.3 && this.state.animals.length < this.config.maxAnimals) {
                    this.addAnimal();
                }
            }
        }, this.config.detectionInterval);
    }

    /**
     * Adicional ou remove animais baseado no estado
     */
    maybeAddOrRemoveAnimal() {
        if (this.state.animals.length < this.config.minAnimals && Math.random() < 0.3) {
            this.addAnimal();
        } else if (this.state.animals.length > this.config.maxAnimals) {
            this.removeAnimal(0);
        }
    }

    /**
     * Muda comportamento aleatoriamente
     */
    maybeChangeBehavior() {
        this.state.animals.forEach(animal => {
            if (Math.random() < 0.05) {
                animal.behavior = this.randomBehavior();
            }
        });
    }

    /**
     * Atualiza tempo de sessão
     */
    updateSessionTime() {
        const elapsed = Math.floor((Date.now() - this.state.sessionStart) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        this.elements.sessionTime.textContent = `${minutes}:${seconds}`;
    }

    /**
     * Atualiza display de FPS
     */
    updateFps() {
        const now = Date.now();
        const delta = now - this.state.lastFpsUpdate;
        this.state.fps = Math.round((this.state.frameCount * 1000) / delta);
        this.elements.fpsDisplay.textContent = this.state.fps;
        this.state.frameCount = 0;
        this.state.lastFpsUpdate = now;
    }

    /**
     * Adiciona entrada ao log
     */
    log(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;

        const time = new Date().toLocaleTimeString('pt-BR');
        entry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-badge ${type}">${type.toUpperCase()}</span>
            <span class="log-message">${message}</span>
        `;

        this.elements.logContainer.appendChild(entry);
        this.elements.logContainer.scrollTop = this.elements.logContainer.scrollHeight;

        // Manter apenas últimas 50 entradas
        while (this.elements.logContainer.children.length > 50) {
            this.elements.logContainer.removeChild(this.elements.logContainer.firstChild);
        }
    }

    /**
     * Animação de valor numérico
     */
    animateValue(element, start, end, duration, suffix = '') {
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease-out quadratic
            const eased = 1 - (1 - progress) * (1 - progress);

            const value = Math.round(start + (end - start) * eased);
            element.textContent = value + (suffix ? ` ${suffix}` : '');

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    // Utilitários
    randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    randomFloat(min, max) {
        return Math.random() * (max - min) + min;
    }

    randomBehavior() {
        const behaviors = ['calmo', 'calmo', 'calmo', 'alimentando', 'caminhando', 'agitado'];
        return behaviors[this.randomInt(0, behaviors.length - 1)];
    }

    randomColor() {
        const colors = ['#4a4a4a', '#5a5a5a', '#6a6a6a', '#3a3a3a', '#505040'];
        return colors[this.randomInt(0, colors.length - 1)];
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AgroVisionDashboard();
});