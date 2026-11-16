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
- Os oito itens possuem constantes, registros, descrições e entradas no estoque de Lilycove. Black Sludge, Metronome e Honey receberam lógica de batalha/campo; Oval Stone tem o método de evolução diurna; Lagging Tail e Wide Lens já afetam batalha; Electirizer e Magmarizer usam a evolução por troca com item segurado.
- Os seis Evolution Stones e os oito itens Gen 4 foram adicionados ao balcão esquerdo do 2F da loja de Lilycove. Os ícones dos oito itens ainda usam a interrogação genérica até a importação de arte própria.
- As 107 espécies ainda não têm ID interno de produção.
- As 107 espécies ainda não têm assets gráficos completos no formato do Emerald nem entrada de cry integrada.
- As evoluções envolvendo a Geração 4 precisam de revisão de condições como gênero, amizade, horário, movimento conhecido, item segurado, região e espécie presente na equipe.

Os números de bloqueios são uma fotografia da branch e devem ser atualizados conforme cada dependência for resolvida.

## Ordem de integração

1. Integrar os 137 movimentos ausentes em lotes de efeitos, com categorias físicas/especiais corretas, alvos, prioridades, flags, textos e animações.
2. Implementar os efeitos especiais de movimento que não existem no Emerald; não substituir movimentos com comportamento próprio por golpes genéricos.
3. Implementar e testar as condições evolutivas da Geração 4, incluindo evoluções de espécies antigas para espécies novas.
4. Importar front/back sprites, animações, ícones, footprints e paletas no formato e limites gráficos da GBA; integrar os cries.
5. Auditar o comportamento real de todas as habilidades atribuídas às espécies.
6. Só depois, concluir a revisão dos consumidores de índices de espécie e a migração de save. Então será possível alocar IDs e ativar as espécies no runtime.

## Mecânicas integradas nesta etapa

- O motor agora aceita categoria física, especial ou status por movimento. Registros antigos sem categoria explícita continuam usando a regra do Emerald baseada no tipo.
- Black Sludge cura Pokémon Poison em 1/16 do HP máximo por turno e causa dano de 1/8 aos demais tipos.
- O item Metronome aumenta em 20% o poder do mesmo movimento repetido em sequência, até +100%.
- Honey é consumido ao ser usado e ativa o aumento de encontros selvagens, reaproveitando a flag do White Flute.
- Oval Stone permite evolução por nível durante o dia enquanto o Pokémon a segura. Electirizer e Magmarizer usam o caminho existente de evolução por troca com item segurado.
- Lagging Tail e Wide Lens mantêm seus efeitos de prioridade e precisão.

A camada física/especial e os itens estão integrados ao código-fonte nesta etapa; a validação final de compilação e comportamento segue no CI e nos testes de batalha.

## Segurança

Não alterar `NUM_SPECIES`, `SPECIES_EGG`, o intervalo calculado de Unown ou o formato do save durante esta etapa. A auditoria global anterior encontrou consumidores de índices que ainda precisam de revisão. National Dex #387–#493 não deve ser usado como índice direto em `gSpeciesInfo` ou em outras tabelas legadas.

O relatório produzido por `tools/audit_gen4_species_readiness.py` é um gate de preparação, não uma declaração de que os Pokémon da Geração 4 já são jogáveis.
