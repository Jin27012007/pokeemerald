# Passo 4 — lote 2 de SpeciesInfo (Geração 5)

## Escopo deste lote

Esta etapa acrescenta o lote das 156 espécies que estrearam na Geração 5, correspondentes aos números da Pokédex Nacional 494–649. A fonte continua sendo o snapshot fixado da árvore vendorizada Pokémon Emerald Expansion, e o mesmo parser e os mesmos critérios de completude utilizados no lote da Gen 4 são reaproveitados.

A geração de estreia é determinada pelo intervalo da Pokédex Nacional. Cada espécie mantém separadamente a geração real do arquivo-fonte onde o inicializador foi encontrado. Portanto, não se presume que uma espécie que estreou na Gen 5 esteja necessariamente armazenada em um arquivo chamado `gen_5_families.h`; a proveniência registrada pelo conversor prevalece.

## Dados preservados

Cada linha mantém a identidade Nacional, o símbolo da espécie na fonte, geração e caminho do arquivo-fonte, estatísticas base, captura, experiência, EVs explicitamente declarados, proporção de gênero, amizade, crescimento, tipos, grupos de ovos, habilidades, habilidade oculta, itens segurados, cor do corpo, campos expandidos e inicializador bruto.

Os IDs numéricos continuam pertencendo aos catálogos de enums do snapshot Expansion. Eles não são convertidos nem tratados como IDs de Emerald nesta etapa. Aliases simbólicos não resolvidos, condições de compilação, valores ausentes e gaps de compatibilidade não são preenchidos por suposição.

## Isolamento

O gerador produz `data/pokemon/gen8_species_info_batches/gen5_species_info.json` durante a validação de CI. O arquivo é anexado ao artefato de auditoria junto do lote Gen 4. O lote permanece em staging: não altera `gSpeciesInfo`, `NUM_SPECIES`, IDs internos, estruturas de runtime ou saves. A execução da Gen 5 também regenera e testa o lote da Gen 4 para preservar sua cobertura anterior.

## Critérios de aceitação

- O catálogo canônico de entrada contém exatamente 898 identidades únicas, de 1 a 898.
- O lote Gen 5 contém exatamente 156 registros, cobrindo 494–649 sem lacunas ou duplicatas.
- Cada registro corresponde ao inicializador Expansion cuja identidade `natDexNum` confere com o número Nacional selecionado.
- Os campos obrigatórios da fonte estão presentes e resolvidos; dados incompletos são rejeitados.
- A geração real e o arquivo de origem são mantidos por registro, mesmo quando diferem da geração de estreia.
- Os inicializadores bruto e expandido permanecem disponíveis separadamente para auditoria.
- Os IDs de enums da Expansion e as incompatibilidades com Emerald continuam explicitamente separados.
- Testes cobrem faixa Gen 5, determinismo, identidade, proveniência, integridade e isolamento do runtime.

## Próxima etapa

Depois da revisão deste lote, a próxima faixa é a Geração 6, Pokédex Nacional 650–721. A promoção de qualquer lote ao runtime continua bloqueada até que os mapeamentos entre enums estejam definidos e a migração real dos saves seja validada.
