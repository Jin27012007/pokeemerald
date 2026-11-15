# Passo 6 — lote 4 de SpeciesInfo (Geração 7)

## Escopo

Esta etapa acrescenta as 88 espécies que estrearam na Geração 7, correspondentes à Pokédex Nacional #722–809. O lote utiliza o mesmo snapshot fixado de Pokémon Emerald Expansion, o mesmo conversor e os critérios de completude e proveniência aplicados às gerações anteriores.

A geração de estreia é determinada pela faixa da Pokédex Nacional. Cada registro preserva separadamente a geração e o arquivo reais em que o inicializador foi encontrado. A origem não é inferida a partir da geração de estreia.

## Dados preservados

Cada linha mantém identidade Nacional, símbolo na fonte, geração e caminho de origem, estatísticas base, captura, experiência, EVs declarados, proporção de gênero, amizade, crescimento, tipos, grupos de ovos, habilidades, habilidade oculta, itens segurados, cor do corpo, campos expandidos e inicializador bruto.

Os IDs numéricos de tipos, grupos de ovos, crescimento, habilidades e itens continuam no domínio de enums de Pokémon Emerald Expansion. Não são IDs internos de Emerald. Aliases simbólicos não resolvidos, expressões condicionais, campos ausentes e gaps de compatibilidade são explicitados, sem substituição por valores presumidos.

## Isolamento

O gerador produz `data/pokemon/gen8_species_info_batches/gen7_species_info.json` durante o CI. O artefato de auditoria passa a conter os quatro lotes, Gen 4 a Gen 7. Todos permanecem em staging: não alteram `gSpeciesInfo`, `NUM_SPECIES`, IDs internos, estruturas de runtime ou saves.

## Critérios de aceitação

- A entrada canônica contém exatamente 898 identidades únicas (#1–898).
- O lote Gen 7 contém exatamente 88 registros (#722–809), sem lacunas ou duplicatas.
- Cada registro corresponde ao inicializador Expansion cujo `natDexNum` confere com a identidade Nacional selecionada.
- Os campos obrigatórios da fonte estão presentes e resolvidos; dados incompletos são rejeitados.
- A geração e o caminho de origem efetivos são preservados por registro.
- Inicializadores bruto e expandido permanecem disponíveis para auditoria.
- IDs de enum da Expansion e gaps de compatibilidade com Emerald continuam separados.
- Testes cobrem a configuração Gen 7, o intervalo, a proveniência, o determinismo e o isolamento do runtime.
- O CI regenera e testa também os lotes Gen 4, Gen 5 e Gen 6.

## Próxima etapa

A faixa seguinte é a Geração 8, Pokédex Nacional #810–898, com 89 espécies. A ativação de qualquer lote no runtime continua bloqueada até a resolução dos mapeamentos de enums, integração de assets e validação de migração dos saves.
