# Lilycove Adoption — Plano de expansão da Pokédex até a Geração 8

## Escopo aprovado
- Incluir todas as 898 espécies nacionais das Gerações 1 a 8, sem filtro temático.
- Não importar o motor de batalha do CFRU.
- Preservar o sistema de Concursos Pokémon de Emerald como sistema principal.
- Formas regionais e formas alternativas não contam como espécies nacionais adicionais; serão avaliadas em etapa separada.
- O escopo de 898 refere-se às espécies nacionais até Calyrex. Não inclui variantes de forma como espécies distintas.

## Auditoria inicial da branch `lilycove/development`
Arquivos identificados como centrais:
- `include/constants/species.h`: enumeração/IDs das espécies.
- `include/constants/pokemon.h`: constantes comuns, limites e estrutura conceitual usada pelo jogo.
- `src/data/pokemon/species_info.h`: atributos obrigatórios de cada espécie.
- `src/data/pokemon/level_up_learnsets.h`: movimentos aprendidos por nível.
- `src/pokemon.c`: conversões, validações e tabelas auxiliares de espécie.
- `src/pokemon_summary_screen.c`: interface de resumo, incluindo páginas separadas para movimentos de batalha e de concurso.
- `src/contest.c` e `include/constants/contest.h`: sistema de concursos e seus efeitos.
- `Makefile`: compilação da ROM.

## Riscos e dependências que precisam ser auditados antes de mudar os IDs
1. Limites de espécie e sentinelas: `NUM_SPECIES`, `SPECIES_NONE`, espécies inválidas, limites de arrays, bitmasks e verificações de faixa.
2. Enumeração: IDs internos atuais não podem ser simplesmente sobrescritos sem mapear save data, scripts, mapas, encontros, treinadores, Pokédex e referências numéricas.
3. Dados de espécie: cada nova espécie precisa de entrada válida em `gSpeciesInfo`, incluindo atributos usados pelo engine mesmo que batalhas não sejam o foco.
4. Gráficos: sprites frontais/traseiros, paletas, ícones, animações, cries e outros recursos esperados pelos loaders devem ter convenções completas.
5. Pokédex: entradas, nomes, categorias, alturas/pesos, habitats e numeração regional/nacional.
6. Evoluções e obtenção: métodos de evolução, itens, presentes, encontros, criação/ovos e compatibilidade com os sistemas existentes.
7. Movimentos e concursos: golpes não existentes na Gen 3 não podem ser atribuídos sem dados de movimento e metadados de concurso compatíveis. A migração não deve alterar inadvertidamente os efeitos/atratividade dos golpes existentes.
8. Save: confirmar que IDs expandidos cabem nas estruturas persistidas e que a migração não invalida saves existentes; se necessário, definir versão/migração explícita.
9. Ferramentas de build: atualizar geradores de gráficos/dados e scripts, além de verificar limites de ROM e RAM.

## Estratégia de implementação
1. Concluir auditoria de todas as ocorrências de limites e tabelas relacionadas a espécies.
2. Definir um esquema explícito de IDs nacionais e política para formas.
3. Adicionar dados de espécie em lotes verificáveis, acompanhados de validação de cobertura.
4. Integrar assets gráficos usando as ferramentas e formatos já adotados pelo projeto.
5. Definir política de movimentos para Pokémon de gerações posteriores, preservando o formato de contest do Emerald.
6. Atualizar Pokédex, party, PC, evolução, obtenção e scripts.
7. Compilar builds modern e normal quando possível; executar testes de regressão para captura, armazenamento, troca entre caixas, salvar/carregar, evolução, resumo e concursos.

## Restrições
- Esta alteração documental não adiciona Pokémon jogáveis nem assets.
- Nenhum código do CFRU foi copiado.
- CFRU pode servir como referência de estrutura/dados somente após verificação de licença, créditos e permissões aplicáveis.
- Não declarar a Pokédex expandida até a cobertura de dados e testes de runtime estarem concluídos.

## Estado
- [x] Escopo de 898 espécies aprovado pelo usuário.
- [x] Arquivos centrais identificados na branch.
- [ ] Auditoria integral de limites e referências.
- [ ] Decisão final de política de formas.
- [ ] Pipeline de dados e assets.
- [ ] Implementação e testes.
