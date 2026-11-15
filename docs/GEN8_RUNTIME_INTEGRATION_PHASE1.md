# Integração Gen 8 — fase 1: ledger de compatibilidade SpeciesInfo

## Objetivo

Esta fase conecta cada SpeciesInfo das gerações 4–8 ao domínio de enums de Emerald por símbolo, preservando os IDs numéricos originais da Expansion em campos separados. O resultado é um ledger de compatibilidade revisável, não uma tabela de runtime.

O gerador consome os cinco lotes SpeciesInfo e as auditorias de dependências geradas por `tools/gen8_build_pending_tables.py`. Para cada uma das 512 espécies, registra os valores de stats, EVs, tipos, grupos de ovos, crescimento, três slots de habilidade e itens segurados, incluindo os IDs da fonte e os IDs-alvo quando existem.

## Correção do catálogo de itens

O auditor anterior tratava `include/constants/items.h` como se os itens fossem macros numéricas `#define`. O arquivo declara o namespace principal em um `enum`; por isso, a busca antiga retornava um catálogo-alvo vazio e marcava itens já existentes como ausentes.

A função `target_item_constant_catalog` agora lê os membros da enum com o parser de enums já usado pelo conversor. Os testes cobrem o cálculo dos valores implícitos e conferem símbolos reais do Emerald, como `ITEM_ASPEAR_BERRY` e `ITEM_BIG_MUSHROOM`, além de um item introduzido depois da terceira geração que não deve existir no alvo. O CI vai regenerar os relatórios de itens com essa correção; a contagem antiga de itens ausentes não deve ser reutilizada.

## Incompatibilidades de layout confirmadas

- **Habilidades ocultas:** 409 das 512 espécies têm um terceiro slot diferente de `NONE`. A fase 2 ampliou `SpeciesInfo` para três slots e o seletor persistente para dois bits; a escolha de slot 2 pode ser definida por `SetMonAbilityNum` ou `SetBoxMonAbilityNum`.
- **Experiência base:** 105 espécies têm `expYield` acima de 255. A fase 2 ampliou o campo de `u8` para `u16`, evitando truncamento desses valores.
- **Tipo Fairy:** 36 slots de tipo nos registros novos usam `FAIRY`, sem enum-alvo em Emerald. Não basta adicionar um identificador: o cálculo e a tabela de efetividade de tipos também precisam ser adaptados.
- **Enums de habilidades e itens:** os IDs da Expansion não são IDs de Emerald. A fase 2 alocou IDs locais 78–242 para as 165 habilidades adicionais usadas pelas espécies novas e importou seus nomes/descrições; o comportamento de batalha de cada habilidade ainda precisa ser implementado e testado. Itens sem constante ou sem registro de dados permanecem como lacunas explícitas.
- **EVs:** os valores fornecidos estão dentro do limite de 2 bits do struct atual. Quando um EV não é declarado na fonte, o valor de inicialização é registrado como zero, que é o valor padrão de um campo omitido em um inicializador C.

Os números deste documento descrevem o conjunto de dados analisado no CI #1017. Dos 57 itens segurados usados pelas espécies novas, 34 têm constante e registro-alvo no Emerald; 23 ainda não têm constante nem registro de dados. O ledger encontrou 92 referências de item resolvidas entre 138 referências comuns/raras analisadas; uma referência rara permanece sem ID numérico resolvido.

## Saídas e limites

O CI gera:

- `data/pokemon/gen8_species_info_runtime_mapping.json`: mapeamento por espécie, com IDs de origem e destino separados.
- `reports/gen8-conversion/species_info_runtime_mapping_audit.json`: cobertura, lacunas de enum, limites de campos e pendências semânticas.

O ledger permanece marcado como `explicit_symbol_mapping_staging_only`. Não é incluído em `gSpeciesInfo`, não aloca IDs internos, não altera `NUM_SPECIES`, não modifica tabelas de evolução/learnsets e não muda saves. Os IDs de produção das 386 espécies existentes permanecem intocados.

## Próximas etapas de integração

1. Fechar a implementação e os testes das habilidades ausentes, do terceiro slot e do comportamento dos itens.
2. Definir a representação de `expYield` acima de 255 e auditar todos os consumidores antes de alterar o layout.
3. Implementado em `docs/GEN8_FAIRY_TYPE.md`: tipo Fairy com efetividade de batalha, nomes, mensagens, busca da Pokédex e ícones.
4. Integrar os efeitos de batalha das habilidades novas e os dados/efeitos dos itens ausentes.
5. Integrar assets gráficos, ícones e cries e adaptar movimentos, efeitos de batalha e métodos/condições de evolução.
6. Promover os 512 IDs numa ROM de jogo novo, sem exigir migração de saves antigos.

O critério de segurança desta fase é manter o runtime atual compilável e tornar cada incompatibilidade explícita. A conclusão do ledger não significa que as espécies estejam jogáveis.
