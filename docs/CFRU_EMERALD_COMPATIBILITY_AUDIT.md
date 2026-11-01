# Auditoria de compatibilidade — CFRU → Lilycove Adoption (Emerald)

Data da auditoria: 2026-11-01

## Fontes verificadas

- CFRU: https://github.com/Skeli789/Complete-Fire-Red-Upgrade
  - Branch analisada: master
  - Commit/tree de referência observado: b637a27898b14e25dd24d0f69a3e302f0069deb8
  - README: o projeto declara um motor de batalha atualizado até Gen 8, com movimentos, habilidades, itens e efeitos até Gen 8.
  - O README exige que usuários do código/assets não monetizem o jogo sem permissão expressa do autor; inclui paywalls e doações.
  - O repositório não declara licença SPDX/GitHub visível (campo license: null). Créditos direcionam à documentação PDF.
- Emerald de destino: https://github.com/Jin27012007/pokeemerald
  - Branch observada: lilycove/development

## Escopo e conclusão

O CFRU não é um pacote de dados simples. É um upgrade profundo de FireRed: dados e tabelas, código C, assembly, battle scripts, hooks para endereços específicos de FireRed, gráficos e ferramentas de inserção/repointing. O README lista Battle Engine Gen 8; não há base no README para afirmar Gen 9 completo.

**Conclusão:** não copiar o CFRU integralmente para Emerald. A arquitetura-base, os símbolos, hooks, offsets e fluxos de inserção são específicos de FireRed. Usar o projeto como referência técnica e fonte de comparação; portar/adaptar apenas componentes isolados cuja necessidade e compatibilidade sejam verificadas. Antes de incorporar qualquer código/assets do CFRU ao fork, esclarecer e cumprir a condição de não monetização/permissão e revisar os créditos/documentação.

## Componentes observados no CFRU

### Dados de espécies
- `include/constants/species.h`
- `src/data/pokemon/species_info.h`
- `assembly/data/species_tables.json`
- Gráficos e recursos de Pokémon estão organizados em subárvores próprias; o recorte de `graphics/Backsprites` encontrado no inventário consultado inclui backs de Brendan/May, não comprova por si só a presença de todos os sprites de espécies.
- Dados de espécies e tabelas de formas/banimentos aparecem em arquivos próprios.

### Movimentos e habilidades
- `include/constants/moves.h`
- `include/constants/abilities.h`
- `src/Tables/battle_moves.c`
- `assembly/data/move_tables.json`
- `assembly/data/ability_tables.json`
- `src/ability_battle_effects.c`, `src/ability_util.c` e `src/battle_script_commands.c`
- O CFRU inclui lógica extensa para novos efeitos; os dados não são suficientes sem handlers, scripts e integração no motor.

### Battle engine e assembly
- `assembly/battle_scripts/`, `assembly/hooks/`, `hooks`, `repoints`, `routinepointers`, `BPRE.ld`, `linker.ld`, `special_inserts.asm`
- Os arquivos de hooks/repoints contêm endereços de funções/tabelas FireRed (endereços 0x08...). Não são endereços compatíveis automaticamente com a ROM Emerald.
- A ferramenta de instalação descrita pelo README usa ROM FireRed BPRE0.gba, devkitPro/DEVKITARM e scripts de inserção. Não é o mesmo fluxo do decompilado Emerald que usa make.

## Estruturas correspondentes no Emerald de destino

A inspeção da branch `lilycove/development` confirmou:
- `include/constants/species.h`
- `include/constants/moves.h`
- `include/constants/pokemon.h` (inclui enumerações/tipos base)
- `include/constants/abilities.h`
- `src/data/pokemon/species_info.h`
- `src/data/pokemon/level_up_learnsets.h`
- `src/battle_script_commands.c`
- `src/battle_main.c`
- `src/pokemon.c`
- `src/pokemon_summary_screen.c`

Isso confirma pontos equivalentes na arquitetura, não compatibilidade binária ou de código. Emerald é uma base decompilada com organização e convenções próprias.

## Matriz preliminar de portabilidade

| Componente CFRU | Estratégia recomendada | Risco |
|---|---|---|
| Nomes/espécies e ordem Pokédex | Extrair como dados de referência e mapear IDs para as convenções Emerald | Médio |
| Estatísticas, tipos, gênero, captura, experiência, ovos, crescimento | Converter registros para a estrutura Emerald; validar tamanhos/limites/índices | Médio |
| Learnsets e evoluções | Converter dados e métodos, validar IDs de movimentos/itens e métodos de evolução | Médio |
| Sprites/ícones/paletas | Converter formatos e tabelas de gráficos do Emerald; validar paletas, dimensões e compressão | Médio |
| Novos movimentos e habilidades | Portar individualmente efeito por efeito para scripts/rotinas Emerald | Alto |
| Divisão físico/especial por movimento | Verificar já existente na base Emerald e preservar; não assumir que precisa vir do CFRU | Baixo/Médio |
| Tipo Fada e tabela de efetividade | Comparar com Emerald; integrar apenas se ausente ou incompleto | Médio |
| Mega/Z-Moves/Dynamax/Ultra Burst | Não importar em bloco; decidir separadamente e projetar integração nativa | Muito alto |
| AI avançada e battle scripts CFRU | Referência de comportamento, reimplementação/adaptação necessária | Muito alto |
| Hooks/repoints/endereço FireRed | Não copiar como estão | Incompatível diretamente |
| DexNav, armazenamento expandido, calendário e recursos de campo | Avaliar separadamente contra a arquitetura Emerald e contra o escopo Lilycove | Alto |

## Plano de integração sugerido

1. Fechar e preservar uma versão Emerald de referência compilável, com hash e commit.
2. Criar branch isolada de integração, sem substituir `lilycove/development`.
3. Fazer inventário de capacidades Emerald já presentes (tipo Fada, split físico/especial, total de espécies/movimentos/habilidades, formas, limites de armazenamento e gráficos).
4. Definir um primeiro recorte de espécies para Lilycove Adoption; a proposta original favorece uma Pokédex selecionada, então não habilitar automaticamente todo o catálogo CFRU.
5. Prototipar os dados de espécies com uma amostra pequena e representativa (incluindo espécie de Gen 4+ e uma forma alternativa), atualizar dados, gráficos, ícones, Pokédex, encontros, evolução, aprendizagem e armazenamento.
6. Compilar, executar testes de captura, party, PC, resumo, evolução, learnset, salvamento/recarregamento.
7. Depois disso, portar novas mecânicas de batalha uma a uma, com testes de interação e IA.
8. Manter concursos e adoção fora do escopo das primeiras mudanças, mas verificar regressões de IV/EV, nature, felicidade, ribbons, metadados de captura e armazenamento.

## Questões não comprovadas nesta auditoria

- O README do CFRU declara Gen 8; não confirma suporte integral à Gen 9.
- A auditoria não compilou nem executou o CFRU.
- Não foi realizada transferência de código/assets CFRU para o Emerald.
- A compatibilidade de cada espécie/forma individual e de cada efeito de movimento ainda precisa ser testada.
- A documentação completa do CFRU (PDF/DOCX) foi identificada no repositório, mas não foi extraída nesta auditoria.

## Referências principais

- CFRU README: https://github.com/Skeli789/Complete-Fire-Red-Upgrade#readme
- CFRU species data: https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/master/assembly/data/species_tables.json
- CFRU move tables: https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/master/assembly/data/move_tables.json
- CFRU ability tables: https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/master/assembly/data/ability_tables.json
- Emerald species info: https://github.com/Jin27012007/pokeemerald/blob/lilycove/development/src/data/pokemon/species_info.h
- Emerald learnsets: https://github.com/Jin27012007/pokeemerald/blob/lilycove/development/src/data/pokemon/level_up_learnsets.h
