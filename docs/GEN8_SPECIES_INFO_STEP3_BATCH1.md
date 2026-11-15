# Passo 3 — lote 1 de SpeciesInfo (Geração 4)

## Escopo deste lote

Esta primeira entrega organiza os dados básicos das 107 espécies que estrearam na Geração 4, correspondentes aos números da Pokédex Nacional 387–493. O lote é derivado dos inicializadores da árvore vendorizada de Pokémon Emerald Expansion, usando o snapshot identificado em `tools/vendor/pokeemerald-expansion/README.md`.

A geração de estreia da espécie não deve ser confundida com a geração do arquivo onde a fonte mantém o inicializador. Por isso, cada registro preserva seu `source_generation` real e o caminho `gen_N_families.h` correspondente. Uma espécie da Gen4 pode estar declarada em um arquivo de família mais antigo — por exemplo, o registro #406 foi localizado no arquivo de Gen3. O lote continua sendo Gen4 pelo intervalo Nacional; a proveniência do arquivo nunca é reescrita para fazer parecer que veio de Gen4.

## Conteúdo importado para staging

Cada registro conserva a identidade Nacional, símbolo de origem, geração da fonte, estatísticas base, taxa de captura, experiência, valores de EV, proporção de gênero, amizade, crescimento, tipos, grupos de ovos, habilidades, habilidade oculta, itens segurados e cor do corpo. Também conserva os campos expandidos e o inicializador bruto original para auditoria.

Os IDs numéricos de tipos, grupos, crescimento, habilidades e itens pertencem ao domínio da fonte Expansion. O arquivo inclui os catálogos dessas enums; esses números não são IDs de Emerald. Quando a fonte usa um alias simbólico que o parser ainda não consegue reduzir a inteiro (por exemplo, uma habilidade definida por outro contador de enum), o lote preserva o símbolo original e marca o ID numérico como não resolvido (`null`). Não substitui aliases por zero nem por IDs presumidos.

## Isolamento

O resultado é gerado em `data/pokemon/gen8_species_info_batches/gen4_species_info.json` durante a validação e anexado ao artefato de conversão. Não é incluído em `gSpeciesInfo`, não altera `NUM_SPECIES`, não atribui IDs internos e não muda saves. A compatibilidade com os campos e enums de Emerald permanece explicitamente separada.

## Critérios de aceitação

- O catálogo nacional de entrada contém exatamente 898 identidades únicas (1–898).
- O lote contém exatamente 107 registros, sem lacunas ou duplicatas, no intervalo 387–493, correspondente à geração de estreia 4.
- Cada registro preserva a geração e o arquivo de origem efetivamente encontrados no parser (1–8), sem pressupor que a pasta de origem coincide com a geração de estreia.
- Cada registro aponta para um inicializador Expansion cujo `natDexNum` confere com a identidade nacional selecionada.
- Os campos básicos exigidos são resolvidos; nenhum valor ausente é preenchido silenciosamente por este gerador.
- O inicializador bruto e a expansão de macros são preservados separadamente.
- Os gaps de compatibilidade com Emerald são mantidos no relatório.
- Testes unitários cobrem determinismo, identidade, proveniência, cobertura e rejeição de dados incompletos.

## Próximo lote

Após a validação deste lote, o próximo grupo natural é a Geração 5 (Pokédex Nacional 494–649). Os dados continuam em staging até que o esquema de IDs, os mapeamentos de enums, os assets e a migração dos saves autorizem sua promoção ao runtime.
