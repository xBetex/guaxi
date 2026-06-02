# Guaxinim Tempo Real — Pygame Port

Um simulador de céu, paisagem e clima em tempo real com um guaxinim animado, fases da lua, estações do ano e efeitos atmosféricos dinâmicos.

---

## Características

- **Clima em tempo real** — Busca dados meteorológicos de qualquer cidade via [Open-Meteo](https://open-meteo.com/) e [wttr.in](https://wttr.in/)
- **Ciclo dia/noite** — Sol e Lua percorrem o céu baseados no horário local real ou manual
- **Fases da lua** — Renderização precisa das fases (algoritmo de Jean Meeus) com textura de crateras
- **Estações do ano** — Calculadas corretamente para ambos os hemisférios (Sul e Norte)
- **Aurora boreal** — Aparece automaticamente em noites de inverno ou pode ser forçada via teclado
- **Efeitos atmosféricos** — Chuva, neve, neblina, relâmpagos, arco-íris, estrelas cadentes, vaga-lumes
- **Pássaros (revoada)** — Bando animado que aparece durante o dia
- **Modos de câmera** — Vistas alternativas: céu, cidade e floresta em picture-in-picture
- **Slider de linha do tempo** — Arraste ou use o teclado para percorrer qualquer dia do ano
- **Calendário interativo** — Navegue até qualquer data via GUI (F3)

---

## Instalação

**Pré-requisitos:** Python 3.8+

```bash
pip install -r requirements.txt
```

Dependências:
- `pygame >= 2.5.0`
- `requests >= 2.31.0`

---

## Como executar

```bash
python main.py
```

**Windows (atalhos alternativos):**
```bash
run.bat
```
```powershell
.\run.ps1
```

---

## Controles

### Tempo e simulação

| Tecla | Ação |
|-------|------|
| `Space` | Pausar / Retomar simulação |
| `T` | Alternar modo tempo real ↔ manual |
| `←` / `↑` | Recuar no tempo |
| `→` / `↓` | Avançar no tempo |
| `+` / `=` | Aumentar velocidade da simulação |
| `-` | Diminuir velocidade da simulação |
| `G` | Pular 6 horas à frente |
| `F` | Ativar/desativar Fast-Forward (10×) |

### Clima e efeitos

| Tecla | Ação |
|-------|------|
| `R` | Ligar/desligar chuva |
| `B` | Disparar relâmpago |
| `N` | Chuva de meteoros (5 segundos) |
| `A` | Alternar aurora boreal |

### Interface

| Tecla | Ação |
|-------|------|
| `I` | Mostrar/ocultar painéis de clima e HUD |
| `S` | Mostrar/ocultar barra de controles |
| `H` | Mostrar/ocultar ajuda |
| `V` | Alternar modo de câmera (normal / cidade / floresta / telescópio) |
| `F2` | Mostrar/ocultar painel de depuração |
| `F3` | Abrir/fechar calendário |
| `F11` | Alternar tela cheia |
| `ESC` | Cancelar edição de cidade |

### Mouse

| Ação | Efeito |
|------|--------|
| Clicar no nome da cidade | Editar cidade |
| Clicar em `[S]` / `[N]` | Alternar hemisfério |
| Clicar no céu noturno | Disparar estrela cadente na posição |
| Scroll do mouse | Ajustar dia no slider |

---

## Estrutura do projeto

```
guaxinin_pygame/
├── main.py              # Loop principal, eventos, orquestração
├── celestial.py         # Sol, Lua, estrelas, aurora, fases lunares
├── landscape.py         # Gradiente de céu, montanhas, cidade ao fundo
├── scenery.py           # Árvores, guaxinim, fogueira, terreno
├── controls.py          # Slider, botões, painéis, debug overlay, ajuda
├── weather.py           # Sistema de clima (chuva, neve, relâmpagos, arco-íris)
├── live_weather.py      # Integração com wttr.in para clima em tempo real
├── weather_api.py       # Integração alternativa via Open-Meteo
├── calendar_ui.py       # Widget de calendário interativo
├── birds.py             # Simulação de revoada de pássaros
├── fireflies.py         # Vaga-lumes noturnos animados
├── cityscape.py         # Renderização da paisagem urbana (modo câmera)
├── trees.py             # Árvores procedurais para o modo floresta
├── sprites.py           # Sprites e utilitários gráficos (Gfx)
├── data.py              # Tabelas de cores, estações, nomes dos meses
├── constants.py         # Constantes globais
├── assets/              # Imagens, sprites e árvores PNG por estação
├── run.bat              # Script de inicialização (Windows CMD)
├── run.ps1              # Script de inicialização (PowerShell)
└── requirements.txt     # Dependências Python
```

---

## APIs utilizadas

| Serviço | Uso |
|---------|-----|
| [wttr.in](https://wttr.in/) | Dados meteorológicos em tempo real (temperatura, chuva, vento, etc.) |
| [Open-Meteo](https://open-meteo.com/) | API alternativa de previsão do tempo |
| [Nominatim (OpenStreetMap)](https://nominatim.org/) | Geocodificação de cidades |
| Algoritmo de Jean Meeus | Cálculo preciso das fases da lua |

---

## Configuração

### Cidade padrão

Edite `main.py`, linha 127:
```python
city_name = "Sua Cidade Aqui"
```

### Resolução e FPS

Edite `main.py`:
```python
WIDTH, HEIGHT = 1280, 720
```

Ou ajuste `FPS` em `constants.py`.

---

## Futuras melhorias

- [ ] Menu de configurações in-game
- [ ] Salvar preferências do usuário
- [ ] Efeitos sonoros e música ambiente
- [ ] Mais animações do guaxinim
- [ ] Suporte para múltiplos guaxinins
- [ ] Exibição de temperatura no HUD

---

## Diferenças da versão web (`index.html` / `script.js`)

Esta é uma reimplementação em Pygame da versão JavaScript original:

| Aspecto | Web | Pygame |
|---------|-----|--------|
| Entrada | Navegador | Janela nativa |
| Renderização | Canvas 2D | `pygame.Surface` |
| Clima | Open-Meteo | wttr.in + Open-Meteo |
| Fases da lua | Aproximação | Jean Meeus |
| Efeitos extras | — | Aurora, pássaros, vaga-lumes, câmeras |
