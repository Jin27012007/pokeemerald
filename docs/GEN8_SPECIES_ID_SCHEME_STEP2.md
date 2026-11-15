# Passo 2 — esquema de IDs internos e política de formas

## Estado

**Proposta de arquitetura; não ativa no runtime.** Nenhum ID de produção, sentinela, estrutura persistida ou tabela C foi alterado nesta etapa.

O contrato canônico continua sendo a Pokédex Nacional 1–898. O número nacional identifica a espécie de forma externa e estável; o ID interno de Emerald continua sendo outro domínio e nunca deve ser usado como se fosse igual ao número nacional.

## 1. Esquema de IDs internos

### Regras obrigatórias

1. Preservar exatamente os 386 IDs internos que já correspondem às espécies nacionais presentes em Emerald.
2. Preservar os 25 IDs históricos SPECIES_OLD_UNOWN_B a SPECIES_OLD_UNOWN_Z, atualmente 252–276. Eles não são 25 espécies nacionais adicionais.
3. Atribuir os 512 novos IDs canônicos de maneira determinística, ordenando os registros ainda sem ID pelo número da Pokédex Nacional e usando uma faixa contínua depois do último ID normal existente.
4. Manter SPECIES_NONE como zero.
5. Manter SPECIES_EGG como sentinela imediatamente após a última espécie normal.
6. Manter os 27 valores auxiliares SPECIES_UNOWN_B a SPECIES_UNOWN_QMARK fora da faixa de espécies normais, derivados da posição de NUM_SPECIES.
7. Não usar números da Pokédex Nacional como índices diretos de gSpeciesInfo, evoluções, learnsets, gráficos, ícones, paletas ou outras tabelas internas.

### Faixa candidata — somente para planejamento

Com os limites atuais verificados na branch:

| Intervalo/símbolo | Atual | Proposta |
|---|---:|---:|
| Espécies internas existentes | IDs originais, até 411 | Preservar todos os IDs |
| Novas espécies canônicas | Sem ID de produção | 412–923 |
| SPECIES_EGG | 412 | 924 |
| NUM_SPECIES | SPECIES_EGG = 412 | SPECIES_EGG = 924 |
| Unown auxiliar B–Z, ! e ? | 413–439 | 925–951 |
| SPECIES_OLD_UNOWN_B–Z | 252–276 | Preservar 252–276 |

A faixa 412–923 é calculada a partir de 512 novos registros. Os IDs candidatos são distribuídos em ordem crescente de National Dex, sem alterar os 386 IDs existentes. O relatório gerado registra cada par National Dex/ID interno candidato e marca todos os novos IDs como não utilizáveis no runtime.

A expansão também deslocaria os sentinelas. Portanto, a mudança futura não poderá consistir em apenas alterar NUM_SPECIES: SPECIES_EGG e os 27 valores auxiliares de Unown precisam acompanhar a nova faixa.

## 2. Migração de saves exigida pelo esquema

A proposta exige uma migração explícita antes de ativar a nova faixa:

| Valor salvo antigo | Destino candidato |
|---|---|
| Espécies existentes e SPECIES_NONE | Manter o valor |
| SPECIES_OLD_UNOWN_B–Z (252–276) | Manter o valor |
| SPECIES_EGG (412) | 924 |
| Unown auxiliar B–Z, ! e ? (413–439) | 925–951, preservando a letra |

A existência e o uso persistente dos valores auxiliares de Unown devem ser verificados em todos os caminhos antes da promoção. A migração precisa inventariar, no mínimo, party, PC, daycare, correspondência/mail, vencedores de Concursos, surtos/outbreaks, registros de batalha e outros campos salvos que guardem espécies.

O BoxPokemon armazena os substructs seguros criptografados e possui checksum. A migração não deve fazer substituição cega de bytes: os dados devem ser lidos e regravados pelos caminhos que preservam checksum, personalidade e criptografia. O bloco de PC e os saves rotativos precisam ser testados separadamente. O esquema não autoriza ainda a migração nem a mudança de sentinelas.

## 3. Política de formas

A decisão de escopo é: **as 898 entradas nacionais representam espécies-base canônicas; formas regionais e alternativas não criam novas entradas nacionais nem novos IDs internos de espécie.**

Cada forma terá uma chave simbólica própria (form_key) associada ao número nacional da espécie-base. Ela pertence a um domínio separado do ID interno da espécie. O arquivo data/pokemon/gen8_form_policy.json define o contrato de dados.

| Política | Uso | Cria entrada nacional? | Cria ID interno de espécie? |
|---|---|---:|---:|
| canonical | Forma-base/default única de cada espécie | Sim | Sim |
| cosmetic | Variação visual recuperável pelos dados já existentes | Não | Não |
| persistent_separate | Forma que altera identidade de jogo persistente | Não | Não |
| temporary_battle | Transformação temporária de batalha | Não | Não |

Regras de implementação:

- canonical: exatamente uma forma-base por número Nacional; é a linha principal da Pokédex.
- cosmetic: só pode dispensar estado persistente quando a aparência puder ser reconstruída deterministicamente, por exemplo por personalidade ou dados já salvos. Se não puder, não é cosmética para fins de armazenamento.
- persistent_separate: usa um form_key estável, separado do ID da espécie. A forma precisa acompanhar party/PC, daycare, troca e save/load. Seu campo de armazenamento exige desenho versionado próprio; não se deve aumentar BoxPokemon ou consumir bits livres sem auditoria.
- temporary_battle: fica apenas no estado de batalha e não substitui a espécie armazenada em party/PC.
- Forma sem classificação explícita permanece bloqueada para importação no runtime. Não existe classificação implícita como cosmetic.

Cada registro de forma precisa guardar National Dex da espécie-base, símbolo da espécie-base, chave da forma, símbolo original da fonte, política, diferenças de gameplay e dependências gráficas/evolutivas. A classificação individual das referências encontradas na fonte continua sendo uma tarefa posterior; este passo define o contrato, não declara todas as formas já classificadas.

## 4. Implementação nesta etapa

- data/pokemon/gen8_form_policy.json: contrato estruturado de formas e campos obrigatórios.
- tools/gen8_species_id_scheme.py: gera uma proposta de IDs para 898 registros, preservando os IDs atuais e explicitando o deslocamento futuro dos sentinelas.
- tools/test_gen8_species_id_scheme.py: verifica a faixa candidata, os 25 IDs OLD_UNOWN, o Egg, os 27 valores auxiliares de Unown, a política de formas e a condição não-runtime.
- reports/gen8-conversion/species_id_scheme_proposal.json: relatório gerado durante CI, não consumido pelo runtime.

## 5. O que continua bloqueado

Esta proposta não autoriza alterar include/constants/species.h, NUM_SPECIES, gSpeciesInfo, estruturas de Pokémon, tabelas de evolução/learnset, saves ou assets. A ativação requer resolver os consumidores de IDs, completar dados/recursos Gen 8, implementar a compatibilidade de movimentos/Concursos, terminar o teste real de gravação e recuperação de save e revisar a migração de todos os campos persistidos.

A compilação da ROM moderna confirma apenas que a base continua compilável. Ela não demonstra que as 512 novas espécies já possam ser capturadas, armazenadas ou usadas em batalha.
