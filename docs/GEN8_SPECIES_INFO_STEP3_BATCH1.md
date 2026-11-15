# Passo 3 — lote 1 de SpeciesInfo (Geração 4)

## Escopo deste lote

Esta primeira entrega organiza os dados básicos das 107 espécies introduzidas na Geração 4, correspondentes aos números da Pokédex Nacional 387–493. O lote é derivado dos inicializadores da árvore vendorizada de Pokémon Emerald Expansion, usando o snapshot identificado em `tools/vendor/pokeemerald-expansion/README.md`.

## Conteúdo importado para staging

Cada registro conserva a identidade Nacional, símbolo de origem, geração da fonte, estatísticas base, taxa de captura, experiência, valores de EV, proporção de gênero, amizade, crescimento, tipos, grupos de ovos, habilidades, habilidade oculta, itens segurados e cor do corpo. Também conserva os campos expandidos e o inicializador bruto original para auditoria.

Os IDs numéricos de tipos, grupos, crescimento, habilidades e itens pertencem ao domínio da fonte Expansion. O arquivo inclui os catálogos dessas enums; esses números não são IDs de Emerald.

## Isolamento

O resultado é gerado em `data/pokemon/gen8_species_info_batches/gen4_species_info.json` durante a validação e anexado ao artefato de conversão. Não é incluído em `gSpeciesInfo`, não altera `NUM_SPECIES`, não atribui IDs internos e não muda saves. A compatibilidade com os campos e enums de Emerald permanece explicitamente separada.

## Critérios de aceitação

- O catálogo nacional de entrada contém exatamente 898 identidades únicas (1–898).
- O lote contém exatamente 107 registros, sem lacunas ou duplicatas, todos na geração 4 e no intervalo 387–493.
- Cada registro aponta para um inicializador Expansion cujo `natDexNum` confere com a identidade nacional selecionada.
- Os campos básicos exigidos são resolvidos; nenhum valor ausente é preenchido silenciosamente por este gerador.
- O inicializador bruto e a expansão de macros são preservados separadamente.
- Os gaps de compatibilidade com Emerald são mantidos no relatório.
- Testes unitários cobrem determinismo, identidade, proveniência, cobertura e rejeição de dados incompletos.

## Próximo lote

Após a validação deste lote, o próximo grupo natural é a Geração 5 (Pokédex Nacional 494–649). Os dados continuam em staging até que o esquema de IDs, os mapeamentos de enums, os assets e a migração dos saves autorizem sua promoção ao runtime.
