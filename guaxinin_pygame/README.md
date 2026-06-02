# Guaxinim Tempo Real - Pygame Port

Um ambiente interativo do guaxinim que sincroniza com o clima real, agora em Pygame!

## Características

- **Clima em tempo real**: Busca dados climáticos reais de qualquer cidade via Open-Meteo API
- **Ciclo dia/noite**: Baseado no horário real ou manual
- **Estações do ano**: Calculadas corretamente baseadas no hemisfério (CORRIGIDO!)
- **Animações**: Guaxinim com IA simples, estrelas cadentes, vaga-lumes, neve, chuva
- **Fases da lua**: Renderização precisa das fases lunares
- **Comportamento do guaxinim**: 
  - Anda livremente durante tempo bom
  - Se esconde na árvore durante chuva/tempestade/neve
  - Se esconde aleatoriamente para dormir

## Instalação

```bash
pip install -r requirements.txt
```

## Como executar

```bash
python main.py
```

## Controles

- **ESC**: Sair do jogo
- **F**: Atualizar dados do clima
- **T**: Alternar tempo manual/automático
- **S**: Alternar estação manual/automática
- **W**: Alternar clima manual/automático
- **← →**: Ajustar hora (quando tempo manual ativo)

## Diferenças da versão JavaScript

Esta é uma reimplementação completa em Pygame que mantém a mesma sensação e características da versão web:

1. **Estações corrigidas**: A lógica de estações agora funciona corretamente baseada no hemisfério
2. **Performance**: Melhor desempenho com renderização nativa do Pygame
3. **Mesmos assets**: Utiliza os mesmos sprites pixel art da versão original
4. **Física similar**: Mantém o mesmo comportamento do guaxinim e partículas

## Adicionando assets customizados

Para adicionar imagens customizadas do guaxinim ou árvores:
1. Coloque os arquivos PNG na pasta `assets/`
2. Atualize as referências no código conforme necessário

## API's utilizadas

- **Open-Meteo**: Dados meteorológicos
- **Nominatim (OpenStreetMap)**: Geocodificação de cidades
- **Cálculo lunar**: Algoritmo de Jean Meeus para fases da lua

## Estrutura do projeto

```
guaxinin_pygame/
├── main.py           # Loop principal do jogo
├── constants.py      # Constantes, cores e sprites
├── weather_api.py    # Integração com APIs de clima
├── renderer.py       # Funções de renderização
├── assets/           # Imagens e sprites
└── requirements.txt  # Dependências Python
```

## Futuras melhorias

- [ ] Carregar sprites de imagens PNG
- [ ] Menu de configurações no jogo
- [ ] Salvar preferências do usuário
- [ ] Efeitos sonoros
- [ ] Mais animações do guaxinim
- [ ] Suporte para múltiplos guaxinins
