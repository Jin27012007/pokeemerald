# Geração 4 — preparação de integração runtime

## Escopo

A Geração 4 ocupa a faixa National Dex #387–#493: 107 espécies. Os dados-fonte estão disponíveis no snapshot fixado do `pokeemerald-expansion` em `c460a8661dfa0598ae25d42a968c690ecbf489c6`. O pipeline já converte os registros para um lote independente em `data/pokemon/gen8_species_info_batches/gen4_species_info.json`.

O lote é staging: ele preserva os dados e a identidade National Dex, mas não atribui IDs internos de produção e não é compilado como espécies jogáveis.

## Auditoria inicial

A auditoria Generation 4-only verifica o lote SpeciesInfo, a tabela de learnsets Gen 8, o catálogo de evoluções, o mapeamento de habilidades/itens e as referências de gráficos e cries.

Baseline aferido pelo CI:

- 107/107 registros SpeciesInfo presentes, com os campos-base exigidos preenchidos.
- 107/107 learnsets presentes; 1.675 entradas de movimentos e 380 movimentos distintos.
- 137 movimentos distintos usados nesses learnsets ainda não possuem registros de batalha no Emerald.
- Os oito itens pendentes agora têm constantes, registros, descrições e entradas de ícone temporárias. Lagging Tail e Wide Lens receberam efeitos de batalha; Black Sludge, Electirizer, Honey, Magmarizer, Metronome e Oval Stone continuam sem comportamento completo.
- Os seis Evolution Stones e os oito itens Gen 4 foram adicionados ao balcão esquerdo do 2F da loja de Lilycove. Os ícones dos oito itens ainda usam a interrogação genérica até a importação de arte própria.
- As 107 espécies ainda não têm ID interno de produção.
- As 107 espécies ainda não têm assets gráficos completos no formato do Emerald nem entrada de cry integrada.
- As evoluções envolvendo a Geração 4 precisam de revisão de condições como gênero, amizade, horário, movimento conhecido, item segurado, região e espécie presente na equipe.

Os números de bloqueios são uma fotografia da branch e devem ser atualizados conforme cada dependência for resolvida.

## Ordem de integração

1. Fechar os 137 movimentos usados pelas 107 espécies, incluindo efeitos de batalha e dados de Contest quando exigidos.
2. Finalizar os seis comportamentos de itens ainda pendentes: Black Sludge, Electirizer, Honey, Magmarizer, Metronome e Oval Stone; adicionar testes de regressão.
3. Implementar e testar as condições evolutivas da Geração 4, incluindo evoluções de espécies antigas para espécies novas.
4. Importar front/back sprites, animações, ícones, footprints e paletas no formato e limites gráficos da GBA; integrar os cries.
5. Auditar o comportamento real de todas as habilidades atribuídas às espécies.
6. Só depois, concluir a revisão dos consumidores de índices de espécie e a migração de save. Então será possível alocar IDs e ativar as espécies no runtime.

## Segurança

Não alterar `NUM_SPECIES`, `SPECIES_EGG`, o intervalo calculado de Unown ou o formato do save durante esta etapa. A auditoria global anterior encontrou consumidores de índices que ainda precisam de revisão. National Dex #387–#493 não deve ser usado como índice direto em `gSpeciesInfo` ou em outras tabelas legadas.

O relatório produzido por `tools/audit_gen4_species_readiness.py` é um gate de preparação, não uma declaração de que os Pokémon da Geração 4 já são jogáveis.
