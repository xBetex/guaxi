# 🦝 Guaxinim Tempo Real

Ambiente pixel-art animado que sincroniza com o **clima real** da sua cidade.

Disponível em duas versões:

---

## 🌐 Versão Web (`index.html`)

Abra `index.html` diretamente no navegador — sem servidor necessário.

**Funcionalidades:**
- Animação pixel-art com sol, lua, nuvens, montanhas e árvores
- Guaxinim animado que reage ao clima
- Clima em tempo real via wttr.in
- Ciclo dia/noite e estações do ano
- Fogueira noturna, vaga-lumes, pássaros, estrelas cadentes

---

## 🐍 Versão Desktop — Pygame (`guaxinin_pygame/`)

Port completo em Python/Pygame com recursos extras.

**Destaques:**
- Lua pixel-art com craters e fases precisas
- Aurora boreal, chuva de meteoros
- Câmera PIP (skycam, citycam, forestcam)
- Painéis de info ocultáveis (`I`)
- Calendário integrado (`F3`)
- Controles de velocidade e tempo manual

**Executar:**
```powershell
cd guaxinin_pygame
.\run.ps1
```

Veja [`guaxinin_pygame/README.md`](guaxinin_pygame/README.md) para instruções completas.

---

## 🌍 Cidade padrão

**Julio de Castilhos, RS, Brasil**

---

## 📁 Estrutura do repositório

```
/
├── index.html              # Versão web principal
├── index_year.html         # Visualização anual
├── script.js               # Lógica principal da versão web
├── style.css               # Estilos
├── assets/                 # Sprites compartilhados (PNG)
├── guaxinin_pygame/        # Port Pygame (Python)
│   ├── main.py
│   ├── run.ps1
│   └── ...
└── js/                     # Módulos JS auxiliares
```

---

## 🔧 Tecnologias

| Versão | Tecnologias |
|---|---|
| Web | HTML5 Canvas, Vanilla JS, CSS |
| Desktop | Python 3, Pygame, Requests |
| API clima | wttr.in (sem chave) |
