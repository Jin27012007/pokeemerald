# Etapa 1 — auditoria da expansão do namespace de espécies

## Objetivo

Preparar a expansão dos IDs internos para as 898 espécies canônicas das Gerações 1–8 sem alterar a identidade numérica dos Pokémon que já existem em Emerald e sem colocar dados incompletos no runtime.

## Estado encontrado na branch de trabalho

A branch `gen8/data-conversion` já contém parte da expansão estrutural da Pokédex Nacional:

- `NATIONAL_DEX_COUNT` chega a Calyrex, número 898.
- A interface da Pokédex percorre a faixa Nacional 1–898.
- As entradas e nomes de 387–898 são servidos por dados de Pokédex separados.
- As flags nacionais 413–898 usam uma extensão versionada de SaveBlock1, sem aumentar diretamente o tamanho de `struct Pokedex`.
- A ponte de identidade já preserva os 386 IDs internos nativos reconhecidos pela base.

Isso não significa que os 898 Pokémon já sejam espécies jogáveis. Os 512 novos registros continuam sem ID interno de produção e não podem ser usados por equipe, PC, batalha, evolução ou tabelas indexadas por espécie.

## Limites atuais que precisam ser preservados

Na base de produção:

| Símbolo | Valor/definição atual |
|---|---|
| `SPECIES_CHIMECHO` | 411 |
| `SPECIES_EGG` | 412 |
| `NUM_SPECIES` | `SPECIES_EGG` |
| Unown auxiliar | 27 valores calculados a partir de `NUM_SPECIES + 1` até `NUM_SPECIES + 26` |

Os 386 IDs já associados a espécies nacionais foram comparados com `include/constants/species.h` e precisam permanecer idênticos. Os 512 registros restantes ainda não receberam IDs internos.

## Alterações desta etapa

Foi adicionado um auditor somente de leitura:

- `tools/audit_gen8_species_namespace_readiness.py` gera `reports/gen8-conversion/species_namespace_readiness.json`.
- `tools/test_gen8_species_namespace_readiness.py` verifica a cobertura 898 = 386 + 512, confere os 386 IDs existentes e protege Egg, `NUM_SPECIES` e os valores auxiliares de Unown.

O relatório não sugere números para os 512 novos Pokémon e não altera nenhum arquivo de produção. Isso é intencional: o contrato de promoção existente proíbe alocar IDs antes da revisão dos consumidores e da validação dos sistemas dependentes.

## Bloqueios que impedem a promoção dos novos IDs

A auditoria de runtime já registra:

- 1.115 referências relacionadas a espécies, incluindo 249 de alto risco e 453 ainda não classificadas.
- 322 movimentos de learnsets da Gen 8 sem registros Emerald de batalha/Concurso.
- 172 habilidades sem constantes/implementações no alvo.
- 85 itens segurados sem constantes no alvo; 30 também não têm registros de dados.
- Tipos Fada e Stellar sem suporte no Emerald.
- Dois métodos de evolução que ainda exigem handlers.
- 512 novas espécies sem entrada de cry no alvo e 512 sem payload gráfico completo.
- A extensão de Pokédex do save ainda precisa de testes reais de gravação/leitura nos setores, escrita interrompida, recuperação, compatibilidade com saves antigos e preservação dos setores vizinhos.

## Regra de segurança

Nesta etapa, `NUM_SPECIES`, `SPECIES_EGG`, os IDs de Unown e os IDs internos existentes permanecem inalterados. Não usar o número da Pokédex Nacional como índice de `gSpeciesInfo`, evoluções, learnsets, sprites ou tabelas internas.

A alocação efetiva dos 512 IDs será um commit separado somente depois de resolver os bloqueios, definir a migração dos sentinelas e passar testes de save e runtime. O build da ROM também deve ser executado depois da integração; a auditoria por si só não certifica compilação nem funcionamento no My Boy!.
