# Passo 5 — lote 3 de SpeciesInfo (Geração 6)

## Escopo

Esta etapa acrescenta as 72 espécies que estrearam na Geração 6, correspondentes à Pokédex Nacional #650–721. O lote usa o mesmo snapshot fixado de Pokémon Emerald Expansion, o mesmo conversor e os mesmos critérios de completude e proveniência aplicados às gerações 4 e 5.

A geração de estreia da espécie é identificada pelo intervalo da Pokédex Nacional. O lote mantém separadamente a geração e o caminho efetivos do arquivo-fonte que contém cada inicializador; não presume que o local de declaração seja o mesmo número da geração de estreia.

## Dados preservados

Cada registro mantém identidade Nacional, símbolo da fonte, geração e arquivo de origem, estatísticas base, taxa de captura, experiência, EVs explicitamente declarados, proporção de gênero, amizade, crescimento, tipos, grupos de ovos, habilidades, habilidade oculta, itens segurados, cor do corpo, campos expandidos e inicializador bruto.

Os valores numéricos das enums continuam no domínio de Pokémon Emerald Expansion. Esta etapa não os converte para IDs de Emerald. Aliases simbólicos não resolvidos, ramos condicionais, dados ausentes e incompatibilidades com o runtime são preservados como lacunas explícitas, sem preenchimento presumido.

## Isolamento

O gerador cria `data/pokemon/gen8_species_info_batches/gen6_species_info.json` durante o CI. O artefato de auditoria passa a incluir os três lotes, Gen 4, Gen 5 e Gen 6. Todos permanecem em staging: não alteram `gSpeciesInfo`, `NUM_SPECIES`, IDs internos, estruturas de runtime ou saves.

## Critérios de aceitação

- A entrada canônica contém exatamente 898 identidades únicas (#1–898).
- O lote Gen 6 contém exatamente 72 registros (#650–721), sem lacunas ou duplicatas.
- Cada registro é ligado ao inicializador Expansion cujo `natDexNum` corresponde à identidade Nacional selecionada.
- Todos os campos obrigatórios da fonte estão presentes e resolvidos; registros incompletos são rejeitados.
- A geração e o arquivo de origem efetivos são preservados individualmente.
- Inicializadores bruto e expandido permanecem disponíveis para auditoria.
- IDs de enum da Expansion e gaps de compatibilidade com Emerald permanecem claramente separados.
- Testes cobrem a configuração Gen 6, seleção do intervalo, proveniência, determinismo e isolamento de runtime.
- O CI regenera e valida também os lotes anteriores Gen 4 e Gen 5.

## Próxima etapa

A próxima faixa é a Geração 7, Pokédex Nacional #722–809, com 88 espécies. A ativação no runtime continua bloqueada até a conclusão dos mapeamentos de enums, assets e validação real da migração dos saves.
