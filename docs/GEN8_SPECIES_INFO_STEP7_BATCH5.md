# Passo 7 — lote 5 de SpeciesInfo (Geração 8)

## Escopo

Esta etapa acrescenta as 89 espécies que estrearam na Geração 8, correspondentes à Pokédex Nacional #810–898. O lote utiliza o mesmo snapshot fixado de Pokémon Emerald Expansion, o mesmo conversor e os critérios de completude e proveniência aplicados às gerações 4 a 7.

A geração de estreia é identificada pelo intervalo da Pokédex Nacional. Cada espécie preserva separadamente a geração e o arquivo-fonte efetivos onde seu inicializador foi encontrado. Não se presume que o arquivo onde a espécie foi declarada corresponda à geração de estreia.

## Dados preservados

Cada registro mantém identidade Nacional, símbolo de origem, geração e caminho do arquivo de origem, estatísticas base, taxa de captura, experiência, EVs explicitamente declarados, proporção de gênero, amizade, crescimento, tipos, grupos de ovos, habilidades, habilidade oculta, itens segurados, cor do corpo, campos expandidos e inicializador bruto.

Os IDs numéricos de tipos, grupos de ovos, crescimento, habilidades e itens permanecem no domínio de enums do snapshot Pokémon Emerald Expansion. Eles não são IDs de Emerald. Aliases simbólicos não resolvidos, expressões condicionais, campos ausentes e gaps de compatibilidade são preservados explicitamente, sem substituição por valores presumidos.

## Isolamento

O gerador produz `data/pokemon/gen8_species_info_batches/gen8_species_info.json` durante o CI. O artefato de auditoria passa a conter os cinco lotes, Gen 4 a Gen 8. Todos continuam em staging: não alteram `gSpeciesInfo`, `NUM_SPECIES`, IDs internos, estruturas de runtime ou saves.

## Critérios de aceitação

- A entrada canônica contém exatamente 898 identidades únicas (#1–898).
- O lote Gen 8 contém exatamente 89 registros (#810–898), sem lacunas ou duplicatas.
- Cada registro corresponde ao inicializador Expansion cujo `natDexNum` confere com a identidade Nacional selecionada.
- Os campos obrigatórios da fonte estão presentes e resolvidos; registros incompletos são rejeitados.
- A geração e o caminho do arquivo de origem efetivos são preservados individualmente.
- Inicializadores bruto e expandido permanecem disponíveis para auditoria.
- IDs numéricos das enums Expansion e gaps de compatibilidade com Emerald continuam separados.
- Testes cobrem configuração, faixa, quantidade, identidade, proveniência, determinismo e isolamento do runtime.
- O CI regenera e valida também os lotes Gen 4, Gen 5, Gen 6 e Gen 7.

## Fechamento da importação de SpeciesInfo

Com este lote, os intervalos de estreia Gen 4–Gen 8 cobrem as 512 espécies novas da Pokédex Nacional (#387–898): 107 da Gen 4, 156 da Gen 5, 72 da Gen 6, 88 da Gen 7 e 89 da Gen 8. Isso fecha a organização dos dados básicos em lotes de staging, mas não significa que as espécies estejam jogáveis no runtime de Emerald.

A próxima fase é consolidar os dados e resolver a conversão dos enums da Expansion para os domínios de Emerald, além de integrar assets, tabelas de batalha/evolução e validar migração real dos saves antes de qualquer ativação em runtime.
