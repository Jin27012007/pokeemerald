# Mapa técnico do código — Pokémon Emerald / Lilycove

> Documento de navegação e método de trabalho. Não contém alterações de gameplay. Os arquivos reais da branch são sempre a fonte de verdade.

## Objetivo

Este documento registra onde procurar e como raciocinar ao implementar uma funcionalidade. Não significa que cada linha dos 13 mil arquivos esteja simultaneamente carregada em memória: quando uma tarefa for definida, os arquivos e dependências relevantes serão consultados diretamente no GitHub antes de qualquer mudança.

## Estado do projeto

- Base: decompilação `pret/pokeemerald`.
- Branch de trabalho: `lilycove/development`.
- Escopo geral: projeto com foco em Lilycove; a proposta de gameplay ainda será definida pelo usuário.
- Build de referência: GitHub Actions **Build Pokémon Emerald** completou com sucesso em 23/10/2026. A execução manual ocorreu na branch `master`, commit `2110bd8c0c1b8b326b6f88ff9e3bd5e206c2c410`; produziu o artefato `pokeemerald-modern-rom`. Isso comprova compilação e geração do arquivo, não teste de gameplay em emulador.
- Até este documento, não há mudanças de gameplay feitas por este projeto.

## Como trabalhar em qualquer pedido

1. Especificar o comportamento esperado em termos observáveis: o que o jogador faz, o que acontece, quando acontece e quando não deve acontecer.
2. Localizar a implementação existente e ler o contexto, não somente a linha que a busca encontrou.
3. Traçar dependências: mapa/evento, script/label, flags e variáveis, dados de gameplay, código C, gráficos/sons e regras de build — apenas as áreas implicadas pela tarefa.
4. Fazer a menor mudança possível na branch `lilycove/development`; preservar comportamento não relacionado.
5. Revisar o diff e procurar colisões de IDs, estados incompletos, caminhos de saída e efeitos colaterais.
6. Compilar com `bash scripts/build-modern.sh` ou GitHub Actions.
7. Testar a ROM num emulador. Para eventos, validar também os diferentes estados de história/flags; para recursos globais, testar caminhos adjacentes.

## Mapa de arquivos por tipo de tarefa

| Tipo de tarefa | Começar por | Procurar também |
|---|---|---|
| NPC, diálogo, item recebido, treinador, placa ou evento local | `data/maps/<Mapa>/map.json` e `data/maps/<Mapa>/scripts.inc` | `include/constants/flags.h`, `include/constants/vars.h`, `data/scripts/` |
| Mudança de terreno, passagem ou colisão | layout em `data/layouts/<Layout>/map.bin` e dados do tileset | `data/layouts/layouts.json`, assets em `data/tilesets/`, atributos de metatile, eventos e warps |
| Entrada/saída de prédio | `warp_events` nos `map.json` de origem e destino | IDs dos mapas, warps do interior, condições que escondem/bloqueiam passagens |
| Evento dependente da história | script local e referências de flags/vars | definições de `include/constants/flags.h`, `include/constants/vars.h`, scripts compartilhados |
| Sistema novo ou regra global | buscar a implementação existente em `src/` e protótipos em `include/` | dados em `data/`, comandos de script, persistência/save, interface e testes de fluxo |
| Pokémon, movimentos, habilidades, encontros ou treinadores | pesquisar a tabela/dado atual em `src/data/`, `data/` e `include/constants/` | código que consome esses dados; índices/IDs e compatibilidade |
| Itens, lojas e inventário | dados de itens/lojas e scripts do mapa | `src/item.c`, `src/item_use.c`, `src/item_menu.c`, `src/shop.c` |
| Equipe e caixas | `src/party_menu.c`, `src/pokemon_storage_system.c` | `src/pokemon.c`, dados e estruturas relacionadas |
| Batalha/IA/comando de movimento | `src/battle_main.c`, `src/battle_script_commands.c`, `src/battle_ai_script_commands.c` | `include/battle*.h`, scripts de batalha em `data/`, animações e mensagens |
| Sprite/interface/arte | arquivos em `graphics/` e dados que os referenciam | regras em `graphics_file_rules.mk`, paletas, dimensões e conversores |
| Música/efeito sonoro | referências em scripts/dados e fontes em `sound/` | `audio_rules.mk`, voicegroups, regras do `Makefile` |
| Salvar/carregar estado | `src/save.c`, `src/load_save.c`, estruturas relacionadas | `include/global.h`, tamanhos/layout do save; risco transversal alto |
| Compilação ou arquivo gerado | `Makefile`, `INSTALL.md`, regras `*_rules.mk` | ferramentas em `tools/`, workflow e logs de build |

Os nomes acima são pontos de partida verificados no repositório, não uma garantia de que toda a funcionalidade esteja concentrada num só arquivo. Sempre seguir referências, chamadas, macros e dados efetivamente usados.

## Fluxo dos mapas e scripts

- `data/maps/<Mapa>/map.json` descreve o mapa, conexões, objetos, warps, gatilhos por coordenadas e eventos de fundo.
- `data/maps/<Mapa>/scripts.inc` associa rótulos e comandos aos objetos/eventos daquele mapa.
- `include/constants/flags.h` e `include/constants/vars.h` guardam estados de progresso; conferir definições e usos existentes para não duplicar identificadores.
- `data/scripts/` contém lógica compartilhada que pode ser usada por mais de um mapa.
- `map_data_rules.mk` mostra como `map.json` alimenta os includes e constantes gerados. Alterações devem ser feitas na fonte apropriada, não num arquivo gerado, sem primeiro rastrear sua origem.
- `data/layouts/<Layout>/map.bin` e `border.bin` são dados binários do layout. Para mudanças visuais ou de passagem é necessário identificar o layout certo e estudar o tileset/atributos usados.

## Lilycove: pontos de entrada

Mapa principal:
- Arquivo de mapa: `data/maps/LilycoveCity/map.json`
- Scripts: `data/maps/LilycoveCity/scripts.inc`
- ID: `MAP_LILYCOVE_CITY`
- Layout: `LAYOUT_LILYCOVE_CITY`
- Música: `MUS_LILYCOVE`
- Tipo: `MAP_TYPE_CITY`
- Conexões existentes: `left: MAP_ROUTE121 (offset 10)`, `right: MAP_ROUTE124 (offset -10)`.
- Eventos listados no JSON: 22 object events, 14 warps, 0 coordinate events, 13 background events.
- O arquivo `scripts.inc` tem 66 rótulos locais no snapshot consultado. Isso não é uma lista exaustiva de toda lógica que afeta Lilycove, porque scripts comuns e mapas interiores ficam em outros lugares.

Outros locais com mapas e scripts independentes incluem Contest Hall e Lobby, Cove Lily Motel, Department Store (andares, elevador e terraço), porto, casas, Museu, Move Deleter's House, Pokémon Center, Trainer Fan Club e Unused Mart. Uma mudança que envolva um interior deve localizar o mapa interior real e verificar os warps dos dois lados.

## Sistemas centrais que costumam ser relevantes

- Exploração e transições: `src/overworld.c`.
- Movimento de objetos e NPCs: `src/event_object_movement.c`.
- Mapa/terreno e controle do avatar: `src/fieldmap.c`, `src/field_player_avatar.c`, `src/field_control_avatar.c`.
- Batalha e IA: `src/battle_main.c`, `src/battle_script_commands.c`, `src/battle_ai_script_commands.c`.
- Dados e operações de Pokémon: `src/pokemon.c` e dados/tabelas relacionados em `src/data/` e `data/`.
- Itens, uso e lojas: `src/item.c`, `src/item_use.c`, `src/item_menu.c`, `src/shop.c`.
- Equipe e PC: `src/party_menu.c`, `src/pokemon_storage_system.c`.
- Persistência: `src/save.c`, `src/load_save.c` e estruturas em `include/`.
- Gráficos e som: `graphics/` e `sound/`, com conversões/regras definidas nos arquivos make correspondentes.

## Build, verificação e limites

- `make modern` é o target usado pelo workflow e gera `pokeemerald_modern.gba`.
- `bash scripts/build-modern.sh` verifica ferramentas necessárias e executa a compilação.
- `.github/workflows/build.yml` gera um artefato com retenção de sete dias para teste.
- Uma build verde não garante que o jogo inicia, que um evento funciona, nem que saves antigos são compatíveis. Testar no emulador e verificar o caminho feliz, estados alternativos e regressões próximas.
- Não mexer em `master` para implementação do mod; usar `lilycove/development` até a proposta ficar clara.
- Nenhum comportamento de gameplay deve ser alterado antes de o usuário especificar a proposta.

## Snapshot de referências estudadas

Hashes abaixo ajudam a perceber quando esses arquivos mudarem e precisarem ser relidos:
- `map.json` de Lilycove: `2eff099ab98c5d0c7fd30f548d273aa13b9444fd`
- `scripts.inc` de Lilycove: `534acdec76082533c9ee2278fb131b00b91f4baa`
- `layouts.json`: `b8d841f72bcc198d1721aad12e46c20b184bd16f`
- `include/constants/flags.h`: `74b10cdfbc7372eb0054f4a0964cb515669ea528`
- `Makefile`: `ed46644b7bde3fd2223ae8f5d07b5e95effa7f4d`

**Regra final:** em cada pedido, consultar novamente o código atual, buscar chamadas e usos, conferir o diff e compilar/testar. Este mapa acelera a navegação; não substitui a leitura contextual dos arquivos implicados.
