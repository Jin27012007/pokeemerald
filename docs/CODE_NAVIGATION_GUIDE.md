# Mapa técnico do código — Pokémon Emerald / Lilycove

> Documento de navegação e método de trabalho. Não contém alterações de gameplay. Os arquivos reais da branch são sempre a fonte de verdade.

## Objetivo

O objetivo é desenvolver familiaridade prática com onde cada tipo de mudança vive, que dependências costumam existir e como validar uma modificação. Isso não equivale a manter literalmente todos os arquivos carregados ao mesmo tempo; para cada tarefa, o conteúdo atual dos arquivos relevantes será consultado diretamente antes de editar.

## Estado verificado

- Base: decompilação `pret/pokeemerald`.
- Branch de trabalho: `lilycove/development`.
- O projeto tem foco em Lilycove, mas ainda não recebeu uma proposta de gameplay.
- Build de referência: [workflow 40037449537](https://github.com/Jin27012007/pokeemerald/actions/runs/40037449537) concluiu com sucesso em 23/10/2026 sobre `master`, commit `2110bd8c0c1b8b326b6f88ff9e3bd5e206c2c410`. Artefato `pokeemerald-modern-rom` foi criado; teste no emulador ainda não confirmado.
- Este guia e o plano técnico são documentação, não alterações de sistemas ou conteúdo do jogo.

## Escala e organização do repositório

No snapshot inspecionado da branch havia 13.407 entradas no Git tree, incluindo diretórios. Foram identificados 518 `map.json`, 468 `scripts.inc` de mapa, 310 arquivos C em `src/` e 329 headers em `include/`. Há muito mais recursos binários e gerados; por isso, uma busca direcionada e o rastreamento de referências é mais seguro do que tentar ler tudo linearmente.

### Fonte, dados, recursos e geração

- `src/`: lógica executável em C e assembly.
- `include/`: estruturas, interfaces, macros e constantes declaradas.
- `src/data/` e `data/`: tabelas e configurações de gameplay, diálogos, encontros, mapas e outras bases de dados.
- `data/maps/<Mapa>/map.json`: metadados do mapa e eventos; `scripts.inc`: scripts que realizam interações.
- `data/layouts/<Layout>/`: arquivo binário da grade e borda; `data/layouts/layouts.json`: catálogo que associa layout e recursos.
- `graphics/`, `sound/`: imagens, paletas, sprites, músicas e efeitos.
- `tools/`: utilitários usados pela compilação, como `mapjson`, `jsonproc`, `gbagfx`, `mid2agb`, `preproc` e conversores relacionados.
- `Makefile` e `*_rules.mk`: dependências e transformações dos dados/fontes em recursos usados pelo build.

## Como trabalhar em qualquer solicitação

1. Transformar o pedido em comportamento observável: ação do jogador, resultado desejado, condições, estados de história relevantes e o que não deve mudar.
2. Encontrar a implementação existente por busca de símbolo, texto, chamada, constante e arquivo de dados; ler o contexto completo.
3. Seguir referências dos dados para os scripts, scripts para comandos/specials, comandos para a implementação C, e referências para UI/arte/áudio/save quando aplicável.
4. Identificar se a mudança é só dado, é script/evento, ou exige nova lógica C e APIs/constantes. Preferir a menor mudança que resolva o pedido.
5. Conferir IDs únicos, flags/vars, nomes de símbolo, includes, tipos, dimensões dos assets, regras de geração e estados alternativos.
6. Revisar o diff na branch `lilycove/development`; não editar a `master` para trabalho experimental.
7. Compilar com `bash scripts/build-modern.sh` ou GitHub Actions.
8. Testar a ROM num emulador e exercitar o recurso na prática. Relatar build e teste de gameplay separadamente.

## Mapa por tipo de mudança

| Pedido | Arquivos iniciais | Dependências que precisam ser rastreadas |
|---|---|---|
| NPC, diálogo, item, treinador, placa ou evento local | `data/maps/<Mapa>/map.json`, `data/maps/<Mapa>/scripts.inc` | label/chamadas, flags/vars, scripts compartilhados, recompensas e condições |
| Evento de história/uma única vez | scripts locais ou `data/scripts/` | `include/constants/flags.h`, `include/constants/vars.h`, todos os usos desses estados e comportamento ao reentrar |
| Porta, prédio, ferry ou transição | `warp_events` nos dois `map.json` | destino, índice/ID dos warps, bloqueios e condições de história |
| Terreno, rota, passagem ou colisão | `data/layouts/<Layout>/map.bin`, `border.bin` e layout catalogado | tileset, metatile e atributos de comportamento, coordenadas de objetos, warps e conexões |
| Novo comando de script | `src/scrcmd.c`, `src/script.c`, `include/script.h`, `include/event_scripts.h` | tabela de despacho/registro do comando, codificação do script e fluxos que o chamam |
| Sistema global | símbolo em `src/`, interfaces em `include/` | estruturas, dados em `data/`, UI, flags/vars, save, mensagens e efeitos colaterais |
| Pokémon, atributos, evoluções ou movimentos aprendidos | `src/data/pokemon/species_info.h`, `level_up_learnsets.h`, `tmhm_learnsets.h`, `tutor_learnsets.h`, `evolution.h` | consumidores em `src/pokemon.c`, dados de golpes, constantes de espécies/movimentos, evolução, aprendizagem, interface |
| Encontros selvagens | `src/data/wild_encounters.json` e dados associados | `src/wild_encounter.c`, mapas/áreas, constantes e regras JSON |
| Treinadores e equipes | `src/data/trainers.h`, `src/data/trainer_parties.h`, arquivos relacionados | scripts de treinador, classes/gráficos, níveis, espécies, movesets e regras de batalha |
| Itens e uso de itens | `src/data/items.h`, `src/item.c`, `src/item_use.c` | `src/item_menu.c`, efeitos, uso em campo/batalha, mensagens e dados de mochila |
| Lojas | `src/shop.c` e scripts/dados da loja do mapa | estoque, IDs de item, preço, flags de acesso e fluxo de compra |
| Batalha, efeitos de golpe ou IA | `src/battle_main.c`, `src/battle_script_commands.c`, `src/battle_ai_script_commands.c` | scripts de batalha, efeitos, constantes, textos, animações, estados de turnos e casos multi/alvos |
| Equipe/PC/party | `src/party_menu.c`, `src/pokemon_storage_system.c` | `src/pokemon.c`, estruturas de Pokémon, slots vazios, party/box, UI e save |
| Save/load ou persistência | `src/save.c`, `src/load_save.c`, estruturas em `include/` | inicialização, serialize/deserialize, tamanhos e offsets, compatibilidade com saves antigos |
| Sprite ou interface gráfica | arquivo em `graphics/` e tabela/referência consumidora | `graphics_file_rules.mk`, paleta, tamanho, compressão, animações e dependências de build |
| Música/efeito sonoro | arquivos de referência e fontes em `sound/` | `audio_rules.mk`, voicegroups, conversores, dados e ponto de reprodução |
| Novo tipo de dado JSON | JSON de origem e regras existentes | `json_data_rules.mk`, template, ferramenta de geração, constantes e todos os consumidores gerados |

Esta tabela é um mapa inicial, não uma afirmação de que cada função esteja isolada nesses arquivos. O símbolo e a versão atual da branch decidem o caminho real.

## Fluxo de mapas e eventos

1. `map.json` define identificador, layout, conexões, música/clima/tipo e arrays de eventos (`object_events`, `warp_events`, `coord_events`, `bg_events`).
2. Campos de script levam a rótulos em `scripts.inc`; estes podem chamar scripts compartilhados em `data/scripts/`, comandos registrados ou funções `special`.
3. `src/script.c` controla execução; `src/scrcmd.c` implementa muitos comandos. Não são a mesma camada.
4. `src/event_data.c` oferece a lógica de dados/estado relacionada; definições de flags e vars ficam em `include/constants/flags.h` e `include/constants/vars.h`.
5. Para qualquer estado de evento, verificar inicialização, condição de leitura, gravação, limpeza, persistência e comportamento após reentrar no mapa.
6. Para conexões entre interiores, checar os warps nos mapas de origem e destino, e se condições/flags permitem chegar a cada um.

## Movimento, terreno e comportamento no overworld

- `src/overworld.c`: coordena fluxo do overworld e transições em nível geral.
- `src/field_control_avatar.c` e `src/field_player_avatar.c`: entrada/controle e estados do avatar/jogador.
- `src/fieldmap.c`: leitura/consultas do mapa e comportamento relacionado ao fieldmap.
- `src/event_object_movement.c`: movimento de objetos/NPCs.
- Para uma mudança de colisão, não basta olhar coordenadas de personagem; o tile precisa ter o comportamento esperado e o evento precisa continuar alcançável.

## Dados de Pokémon, itens e batalha

- Dados de espécie estão distribuídos: `species_info.h`, `evolution.h`, `level_up_learnsets.h`, `tmhm_learnsets.h`, `tutor_learnsets.h`, `egg_moves.h`, tabelas de experiência e entradas da Pokédex.
- Para alterar um valor, localizar a definição e os consumidores. Uma espécie/forma pode ter dados associados adicionais além de atributos básicos.
- Treinadores usam tabelas e party data; encounters têm seu JSON e consumidor; itens têm definições, efeitos e caminhos de uso/loja.
- Batalha costuma atravessar C, scripts e dados: acompanhar despacho do comando, execução do efeito, mensagens/animações, seleção de alvo, fim de turno e interações com habilidades/status. Testar alvos simples/múltiplos quando o efeito for relacionado a batalha.
- Alterações de dados não requerem necessariamente C, mas isso deve ser confirmado inspecionando o caminho consumidor.

## Mudanças persistentes e sistemas globais

Mudanças em estruturas de save ou no fluxo de load/save podem afetar saves existentes e muitos sistemas. Antes de qualquer alteração, rastrear o bloco e seus campos, inicialização de um novo jogo, carga, salvamento, cópias/backups e versões/validações de save no código atual. Não usar uma flag/var já existente sem procurar todos os seus usos e sem conferir se seu significado pode conflitar.

## Recursos visuais e sonoros

Os recursos devem ser seguidos da fonte até o consumidor: asset → tabela/JSON/include/referência → conversor/regra make → dado compilado. Em gráficos, confirmar dimensão, paleta, transparência, animações e compressão. Em áudio, confirmar conversão, voicegroup/instrumentos e o identificador usado para reproduzir a música ou efeito.

## Geração e build

- `Makefile`: targets e orquestração; `make modern` gera `pokeemerald_modern.gba`.
- `map_data_rules.mk`: `map.json` e layouts geram headers/includes e constantes de mapas/eventos.
- `json_data_rules.mk`: JSON gera C/includes via `jsonproc`.
- `graphics_file_rules.mk`: regras dos assets gráficos.
- `audio_rules.mk`: regras de áudio.
- `scripts/build-modern.sh`: valida ferramentas e executa a build.
- `.github/workflows/build.yml`: build e artifact de teste.
- Evitar editar saídas geradas até comprovar que o arquivo é de fato uma fonte editável.

## Checklist antes de concluir uma alteração

- [ ] O comportamento pedido está definido e estados não desejados foram identificados.
- [ ] As referências e implementações atuais foram lidas na branch correta.
- [ ] O diff está limitado ao escopo solicitado.
- [ ] IDs, labels, flags, vars, índices, dimensões e destinos são válidos e sem colisão.
- [ ] Caminho positivo, condições alternativas, reentrada e casos de progressão relevantes foram considerados.
- [ ] Compilação concluiu com sucesso.
- [ ] Teste no emulador foi realizado e seu resultado foi informado separadamente.
- [ ] Não se afirma que algo foi testado quando foi apenas compilado.

## Snapshot dos arquivos-chave consultados

Hashes SHA de blobs do snapshot examinado (servem para detectar alterações e saber quando reler):
- `src/scrcmd.c`: `9c75a625cc62d030a3801ed038b2018fef97cf4e`
- `src/script.c`: `a953ff1e75fcdb0ed8579ad2b830388c39061868`
- `src/event_data.c`: `e3ee3dedb2dd049121daedc987abc721ebf0eee4`
- `src/fieldmap.c`: `258947a03edf7b1741f17f8100dcb5ec0979889b`
- `src/field_player_avatar.c`: `5b22ff74c38fefbc3606945ac7f35f3bec303b3c`
- `src/field_control_avatar.c`: `ed96a8772598908442f9a0e7d84dbcd86df594ec`
- `src/event_object_movement.c`: consultar novamente antes de mudança relacionada
- `src/pokemon.c`: `4b5c197140eb7b21f4fb3377d4cbe3d1a4c01eb0`
- `src/data/pokemon/species_info.h`: `fbd3bcba2a209a8447430ea2c05e862bd9b8ef50`
- `src/data/pokemon/level_up_learnsets.h`: `212b969a70e0dd454be2be71615f59496388bfb2`
- `src/data/pokemon/tmhm_learnsets.h`: `4357cdd1a30a65b29f35ecb1031da40b2ca4ea0d`
- `src/data/pokemon/evolution.h`: `c9b0cf716d6e25cfa054e988115af60f61bd206e`
- `src/item.c`: `a3095c32d7a34caed28011b142c247914807d908`
- `src/item_use.c`: `1884801d69f341abba8cff6f2699e503f0ccc8c8`
- `src/item_menu.c`: `86b1bf941dea6e5a41ade0d99d6387dd92aa6974`
- `src/shop.c`: `c6e78817eb3263af3a35b8778353ca492324772c`
- `src/save.c`: `3f519fb98d5943cd20844225f582dc5f0db264ef`
- `src/load_save.c`: `117ba3e27c8d6284a164e04492a55e4303c2374e`
- `src/battle_script_commands.c`: `3af09ec7a281b99508f5e0170bb15f535d11df47`
- `src/battle_main.c`: `11fc168603f80a099134bc30e363dcc4c143d696`
- `src/battle_ai_script_commands.c`: `5cb0a60a6d6cdccf7f6278981a929e5f5ea84c5c`
- `src/data/wild_encounters.json`: consultar novamente antes de mudança relacionada
- `src/data/trainers.h`: consultar novamente antes de mudança relacionada
- `src/data/trainer_parties.h`: consultar novamente antes de mudança relacionada
- `data/maps/LilycoveCity/map.json`: `2eff099ab98c5d0c7fd30f548d273aa13b9444fd`
- `data/maps/LilycoveCity/scripts.inc`: `534acdec76082533c9ee2278fb131b00b91f4baa`
- `data/layouts/layouts.json`: `b8d841f72bcc198d1721aad12e46c20b184bd16f`
- `include/constants/flags.h`: `74b10cdfbc7372eb0054f4a0964cb515669ea528`
- `include/constants/vars.h`: `1b7113459359fba0f47c1d26f87e461babe08f54`
- `Makefile`: `ed46644b7bde3fd2223ae8f5d07b5e95effa7f4d`
- `map_data_rules.mk`: `cad0531689b0114b16157c78584ce0ceb23c307d`
- `json_data_rules.mk`: `16d9dad392ce124bea873b5739bbb19e959718f0`
- `graphics_file_rules.mk`: `0123417c2da94daf5b8dea2ca4b9551833f98d07`
- `audio_rules.mk`: `dcf08b352bea1c67ab9eafee0a3979172d5afe28`

**Regra final:** este índice acelera a navegação e registra investigação preliminar, mas o código atual da branch prevalece. Antes de implementar qualquer mudança, consultar novamente fontes, usos e dependências específicas.

## Verified implementation details from source inspection

This section records specific source patterns already inspected, so future changes can start from the correct boundary.

### Script execution and command registration

- `src/script.c` defines `RunScriptCommand` and `ScriptContext_RunScript`; the script context can be in bytecode or native mode.
- `include/script.h` declares `struct ScriptContext`, `ScrCmdFunc`, and script-context entry points.
- `data/script_cmd_table.inc` is a generated/assembly-style table that maps opcode constants (for example `SCR_OP_SETVAR`, `SCR_OP_SETFLAG`, `SCR_OP_MESSAGE`, `SCR_OP_SPECIAL`) to C handlers such as `ScrCmd_setvar`, `ScrCmd_setflag`, `ScrCmd_message`, and `ScrCmd_special`.
- `src/scrcmd.c` implements those handlers. The inspected `ScrCmd_setflag` calls `FlagSet(ScriptReadHalfword(ctx))`; `ScrCmd_setvar` reads a variable/value and writes via `GetVarPointer`; `ScrCmd_message` reads a message pointer and calls `ShowFieldMessage`; `ScrCmd_special` indexes `gSpecials` and invokes that function. Therefore, a new script behavior should first be expressed using existing commands/specials if possible. A genuinely new opcode needs consistent opcode definition, dispatch-table entry, C handler, script encoder/preprocessor compatibility and validation.
- A `special` is not the same as a script opcode implementation: `special` dispatches an already registered C function through the specials table. If an existing special can provide the behavior, it may avoid adding an opcode, but its own effects/dependencies must still be examined.
- The scripts are macro/opcode-based input that ultimately compile through preprocessors/assembler rules; textual command names are not arbitrary C function calls. Follow how the current command table and build generate output before changing a command.

### Flags, variables, and persistent state

- `src/event_data.c` includes logic that clears temporary flags and temporary variables and calls `FlagSet`, `FlagClear`, `VarSet`, and `VarGet` from other flow paths.
- `include/constants/flags.h` and `include/constants/vars.h` are extensive registries. Before adding a state identifier, search definitions AND all uses, distinguish temporary from persistent flags/vars, and check initialization/clearing and save/load behavior.
- A story/event flag should be checked in each branch of the event and on map re-entry; a variable is appropriate only when the requirement needs a value/state rather than a simple on/off. The final choice depends on existing conventions in the surrounding code.

### Data-driven items and trainer teams

- `src/data/items.h` defines the `gItems[]` table. Each item can contain user-visible fields such as name, price, description, pocket, item type and a field-use callback, plus other effect-related values. For an item change, inspect the exact item entry and the consuming path before touching general item logic.
- `src/item.c`, `src/item_use.c`, `src/item_menu.c` and `src/shop.c` split item access, use behavior, menu/bag UI and shop transactions. A new/modified item may involve one or several of these layers depending on the requested behavior.
- `src/data/trainers.h` defines `gTrainers[]`, including trainer class, encounter presentation/music, name and party flags. Team members are represented separately in `src/data/trainer_parties.h`. A trainer change must check the map's trainer event/script reference plus trainer constants, party data and battle-start flow; editing the display record alone does not define the team.
- The inspected Pokémon data sources include `src/data/pokemon/species_info.h`, `level_up_learnsets.h`, `tmhm_learnsets.h`, `tutor_learnsets.h`, `egg_moves.h`, `experience_tables.h`, and `evolution.h`. The correct file depends on whether a request concerns base species data, learnsets, evolution, egg moves, or another table.

### Map generation and event validity

- `map_data_rules.mk` consumes source map JSON and layout metadata to generate map includes and constants such as map groups/layouts/event IDs. That means the editable source for object placement and warps is ordinarily the appropriate `data/maps/<Map>/map.json`, not generated headers/includes.
- The map entry and its local script form a pair: an event can compile yet be unusable if its script label is missing, its trigger is absent/unreachable, its graphics/object ID is invalid, or its flag logic is wrong.
- For terrain edits, the correct source layout is resolved through the map's `layout` value and `data/layouts/layouts.json`; the binary layout itself must be treated as binary data and inspected through suitable map/tileset tooling rather than hand-editing as text.

### Known current-state caveat

The guide documents file roles and verified interfaces, not a promise that every subsystem has been fully reverse-engineered. For a concrete future request, reopen the affected files at the then-current branch SHA, search usages/callers, inspect related build rules, make the minimal edit and validate it. Do not infer function signatures, command operands, or save compatibility from filenames alone.


## Lilycove event audit snapshot

This is a basic structural inventory from the current source, not gameplay validation. Recheck the source before implementation.

- Main map definition: `data/maps/LilycoveCity/map.json`.
- ID/layout/music: `MAP_LILYCOVE_CITY`, `LAYOUT_LILYCOVE_CITY`, `MUS_LILYCOVE`.
- The JSON currently lists 22 object events, 14 warps, 0 coordinate events and 13 background events.
- Connected routes in this JSON: left → MAP_ROUTE121 (offset 10); right → MAP_ROUTE124 (offset -10).
- Since warp events are references into other map data, an edit affecting entrances/exits must inspect the target map JSONs and not only this map.
- The map contains a transition script and a load script. These can adjust story flags, map metatiles and rival graphics; changing the entry lifecycle should therefore be done only after tracing callers and the state assumptions of each script.

## Completion standard for technical readiness

“Ready” means a reliable implementation workflow and navigation map are in place, not that every feature or every line of the game has been exhaustively reverse-engineered. Once the proposed feature is known, do a focused deep dive on all affected systems and create an implementation plan with exact files, symbols, state and test cases before changing gameplay.
