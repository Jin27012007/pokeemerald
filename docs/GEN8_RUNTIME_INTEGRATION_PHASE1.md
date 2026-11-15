# Integração Gen 8 — fase 1: ledger de compatibilidade SpeciesInfo

## Objetivo

Esta fase conecta cada SpeciesInfo das gerações 4–8 ao domínio de enums de Emerald por símbolo, preservando os IDs numéricos originais da Expansion em campos separados. O resultado é um ledger de compatibilidade revisável, não uma tabela de runtime.

O gerador consome os cinco lotes SpeciesInfo e as auditorias de dependências geradas por `tools/gen8_build_pending_tables.py`. Para cada uma das 512 espécies, registra os valores de stats, EVs, tipos, grupos de ovos, crescimento, três slots de habilidade e itens segurados, incluindo os IDs da fonte e os IDs-alvo quando existem.

## Correção do catálogo de itens

O auditor anterior tratava `include/constants/items.h` como se os itens fossem macros numéricas `#define`. O arquivo declara o namespace principal em um `enum`; por isso, a busca antiga retornava um catálogo-alvo vazio e marcava itens já existentes como ausentes.

A função `target_item_constant_catalog` agora lê os membros da enum com o parser de enums já usado pelo conversor. Os testes cobrem o cálculo dos valores implícitos e conferem símbolos reais do Emerald, como `ITEM_ASPEAR_BERRY` e `ITEM_BIG_MUSHROOM`, além de um item introduzido depois da terceira geração que não deve existir no alvo. O CI vai regenerar os relatórios de itens com essa correção; a contagem antiga de itens ausentes não deve ser reutilizada.

## Incompatibilidades de layout confirmadas

- **Habilidades ocultas:** 409 das 512 espécies têm um terceiro slot de habilidade diferente de `NONE`. O `struct SpeciesInfo` de Emerald possui apenas dois slots. O ledger conserva o slot oculto, mas marca que ele não cabe na estrutura atual.
- **Experiência base:** 105 espécies têm `expYield` acima de 255. O campo correspondente no `struct SpeciesInfo` atual é `u8`. Copiar esses valores diretamente causaria perda por truncamento; a integração precisa decidir uma representação maior e revisar os consumidores.
- **Tipo Fairy:** 49 slots de tipo nos registros novos usam `FAIRY`, sem enum-alvo em Emerald. Não basta adicionar um identificador: o cálculo e a tabela de efetividade de tipos também precisam ser adaptados.
- **Enums de habilidades e itens:** os IDs da Expansion não são IDs de Emerald. Habilidades sem constante-alvo, itens sem constante ou sem registro de dados e comportamentos ainda não auditados permanecem como lacunas explícitas.
- **EVs:** os valores fornecidos estão dentro do limite de 2 bits do struct atual. Quando um EV não é declarado na fonte, o valor de inicialização é registrado como zero, que é o valor padrão de um campo omitido em um inicializador C.

Os números deste documento descrevem o conjunto de dados analisado no artefato Gen 8 validado. A auditoria de dependências de itens será recalculada pelo CI após a correção do parser.

## Saídas e limites

O CI gera:

- `data/pokemon/gen8_species_info_runtime_mapping.json`: mapeamento por espécie, com IDs de origem e destino separados.
- `reports/gen8-conversion/species_info_runtime_mapping_audit.json`: cobertura, lacunas de enum, limites de campos e pendências semânticas.

O ledger permanece marcado como `explicit_symbol_mapping_staging_only`. Não é incluído em `gSpeciesInfo`, não aloca IDs internos, não altera `NUM_SPECIES`, não modifica tabelas de evolução/learnsets e não muda saves. Os IDs de produção das 386 espécies existentes permanecem intocados.

## Próximas etapas de integração

1. Fechar a implementação e os testes das habilidades ausentes, do terceiro slot e do comportamento dos itens.
2. Definir a representação de `expYield` acima de 255 e auditar todos os consumidores antes de alterar o layout.
3. Implementar Fairy de ponta a ponta, incluindo efetividade de tipos, mensagens e interações de batalha.
4. Integrar assets gráficos, ícones e cries e adaptar movimentos, efeitos de batalha e métodos/condições de evolução.
5. Só então preparar a promoção dos 512 IDs e o plano de migração de todos os registros persistentes — party, PC, daycare e demais campos — com testes de compatibilidade e recuperação de saves interrompidos.

O critério de segurança desta fase é manter o runtime atual compilável e tornar cada incompatibilidade explícita. A conclusão do ledger não significa que as espécies estejam jogáveis.
