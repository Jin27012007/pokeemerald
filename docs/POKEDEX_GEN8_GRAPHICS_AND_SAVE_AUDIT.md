# Auditoria de gráficos e política de save — Pokédex Gen 8

Branch: `lilycove/development`

## Decisão do projeto sobre saves
O usuário confirmou que não há saves que precisem ser preservados: a ROM é sempre iniciada do zero. Isso elimina a necessidade de manter compatibilidade retroativa com saves antigos durante a expansão. Ainda assim, o layout final do save precisa ser consistente: tamanhos das flags, offsets, checksums e inicialização precisam corresponder à nova definição de espécies. A primeira versão expandida deverá iniciar um save novo e ser testada desde o começo.

## Auditoria de assets gráficos

### Organização confirmada
A pasta `graphics/pokemon/<species>/` usa uma pasta por espécie. Para espécies comuns, a estrutura observada inclui:
- `front.png`: sprite frontal.
- `anim_front.png`: frames/animação frontal.
- `back.png`: sprite traseiro.
- `icon.png`: ícone usado em interfaces.
- `footprint.png`: pegada.
- `normal.pal` e `shiny.pal`: paletas.

A pasta de exemplo `graphics/pokemon/eevee/` contém os sete arquivos acima. Bulbasaur e Chimecho seguem a mesma convenção. A pasta `graphics/pokemon/egg/` possui estrutura própria e não deve ser tratada como espécie normal. Unown também possui estrutura especial, com arquivos de formas individuais e paletas compartilhadas.

### Consequência para a expansão
Cada uma das espécies adicionadas precisa de assets compatíveis com os nomes e formatos esperados pelo pipeline atual. Não basta adicionar apenas `front.png`: loaders, animações, costas, ícones, pegadas e paletas podem ser referenciados por tabelas e scripts de build. Formas alternativas exigem política própria e não devem ser confundidas com novas espécies nacionais.

## Pokédex e recursos gráficos da interface
A pasta `graphics/pokedex/` contém gráficos fixos da interface (interface, menus, mapas, fundos, telas de busca e dados binários). Esses recursos não são automaticamente uma lista de sprites por espécie. A ampliação de 386 para 898 itens exige revisar:
- número de dígitos/contadores exibidos;
- paginação, rolagem e limites de lista;
- tabelas de ordem e busca;
- recursos de mapas/habitats que dependem de espécies;
- memória de trabalho para lista e sprites visíveis.

Não há evidência nesta etapa de que os gráficos fixos da interface precisem todos ser redesenhados; isso depende dos limites de layout e dos contadores efetivamente exibidos.

## Impacto da ausência de saves legados
Pode-se alterar o tamanho de `struct Pokedex` e os offsets subsequentes sem migrar saves antigos, desde que:
1. todos os usos do layout sejam recompilados juntos;
2. a inicialização do save limpe e inicialize os novos campos;
3. os checksums e validações de save continuem corretos;
4. seja usada uma ROM nova com save novo no primeiro teste.
Isso não torna seguro mudar apenas `NUM_SPECIES`: as tabelas e índices ainda precisam estar completos.

## Próximas verificações obrigatórias
- Mapear os arquivos de build que enumeram pastas em `graphics/pokemon`.
- Confirmar contagem e cobertura atual de espécies gráficas por script de assets.
- Verificar `cry_ids.h`, tabela de cries e convenção de arquivos de áudio.
- Revisar arrays de sprites/ícones e tabelas de animação.
- Auditar todos os usos de `NATIONAL_DEX_COUNT`, `NUM_SPECIES` e IDs numéricos fixos.
- Preparar um gerador/validador que falhe se faltar qualquer asset obrigatório para uma espécie.
- Só então iniciar importação de dados e recursos.

## Estado
- [x] Usuário confirmou que não existem saves antigos a preservar.
- [x] Estrutura de assets por espécie inspecionada.
- [x] Exceções de Egg e Unown identificadas.
- [x] Assets da interface da Pokédex localizados.
- [ ] Cobertura total de assets quantificada automaticamente.
- [ ] Tabelas de cries e animações auditadas.
- [ ] Auditoria completa de referências hardcoded.
- [ ] Implementação e compilação.
- [ ] Teste de save novo e runtime no emulador.

## Limitação
Esta etapa foi uma inspeção de diretórios e arquivos via GitHub API. Não houve download integral do repositório, execução do pipeline gráfico, compilação ou teste em emulador.
