# Guia de Instalação - Guaxinim Tempo Real (Pygame)

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Passo a Passo

### 1. Verificar instalação do Python

Abra o terminal (CMD ou PowerShell) e execute:

```bash
python --version
```

Se aparecer algo como "Python 3.x.x", você está pronto!

### 2. Criar ambiente virtual (Recomendado)

No diretório do projeto:

```bash
python -m venv venv
```

### 3. Ativar o ambiente virtual

**Windows (CMD):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

Isso instalará:
- pygame (motor de jogos)
- requests (para buscar dados do clima)

### 5. Executar o jogo

**Opção 1 - Usando Python diretamente:**
```bash
python main.py
```

**Opção 2 - Usando o script batch (Windows):**
```bash
run.bat
```

## Solução de Problemas

### Erro: "pygame não encontrado"

```bash
pip install pygame --upgrade
```

### Erro: "requests não encontrado"

```bash
pip install requests --upgrade
```

### Erro de rede ao buscar clima

- Verifique sua conexão com a internet
- Algumas redes corporativas podem bloquear as APIs
- O jogo funcionará em "modo simulação" sem dados reais

### Performance baixa

- Feche outros programas
- Reduza o FPS no arquivo `constants.py` (linha com `FPS = 60`)
- Verifique drivers da placa de vídeo

## Configuração Opcional

### Mudar cidade padrão

Edite `main.py`, linha 31:
```python
self.current_city = "Sua Cidade Aqui"
```

### Ajustar resolução

Edite `constants.py`:
```python
WINDOW_WIDTH = 1280  # Largura
WINDOW_HEIGHT = 720  # Altura
```

### Ajustar FPS

Edite `constants.py`:
```python
FPS = 60  # Quadros por segundo (30-60 recomendado)
```

## Recursos do Sistema

**Mínimo:**
- CPU: Dual-core 2.0 GHz
- RAM: 2 GB
- GPU: Qualquer com suporte OpenGL

**Recomendado:**
- CPU: Quad-core 2.5 GHz+
- RAM: 4 GB+
- GPU: Dedicada com 512 MB+

## Suporte

Para problemas ou dúvidas:
1. Verifique se todas as dependências estão instaladas
2. Confirme que está usando Python 3.8+
3. Tente reinstalar as dependências: `pip install -r requirements.txt --force-reinstall`
