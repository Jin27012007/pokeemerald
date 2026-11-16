# Gen 8 — fase 4: golpes e habilidades do tipo Fada

## Implementado nesta fase

A base Emerald agora registra nove golpes do tipo Fada, com IDs locais consecutivos de 355 a 363:

| Golpe | Potência | Precisão | PP | Efeito ligado |
|---|---:|---:|---:|---|
| Fairy Wind | 40 | 100 | 30 | Dano direto |
| Play Rough | 90 | 90 | 10 | 10% de chance de reduzir Ataque |
| Moonblast | 95 | 100 | 15 | 30% de chance de reduzir Ataque Especial |
| Dazzling Gleam | 80 | 100 | 10 | Atinge os dois adversários |
| Fleur Cannon | 130 | 90 | 5 | Reduz Ataque Especial do usuário em dois estágios |
| Nature's Madness | metade do HP atual | 90 | 10 | Efeito Super Fang |
| Spirit Break | 75 | 100 | 15 | Reduz Ataque Especial do alvo |
| Strange Steam | 90 | 95 | 10 | 20% de chance de confundir |
| Springtide Storm | 95 | 80 | 5 | Atinge os dois adversários; 30% de chance de reduzir Ataque |

As rotinas reutilizadas são efeitos de batalha existentes no Emerald. Isso evita inserir ponteiros para scripts ainda inexistentes.

## Categorias físicas e especiais

Emerald originalmente deriva a categoria física/especial do tipo. Como Fairy é um tipo posterior, foi necessário acrescentar uma exceção explícita para Play Rough e Spirit Break, que são golpes físicos. A exceção também cobre o cálculo de dano, o modificador de precisão de Hustle e o registro usado por Counter/Mirror Coat.

## Habilidades implementadas

- **Pixilate:** converte golpes Normal com dano em Fairy e aumenta seu poder em 20%.
- **Fairy Aura:** aumenta em 4/3 o poder dos golpes Fairy enquanto o usuário está ativo.
- **Aura Break:** reverte o aumento de Fairy Aura para 3/4 enquanto um usuário de Aura Break está ativo.

Os nomes e descrições de habilidades adicionais já existiam no catálogo de texto; isso não foi tratado como prova de que seus efeitos de batalha estejam prontos.

## Limites visuais

Os nove golpes já têm entradas na tabela de animações, mas reutilizam animações existentes como substitutas. Ainda não existem sequências gráficas exclusivas para cada golpe Fada.

## Ainda pendente

Dos 23 golpes Fairy catalogados no snapshot do Expansion, 14 ainda não foram ligados ao runtime: Disarming Voice, Draining Kiss, Crafty Shield, Flower Shield, Misty Terrain, Fairy Lock, Aromatic Mist, Geomancy, Baby-Doll Eyes, Light of Ruin, Floral Healing, Sparkly Swirl, Decorate e Misty Explosion.

Também permanecem pendentes as habilidades Aroma Veil, Flower Veil, Sweet Veil, Misty Surge, Pastel Veil, Triage, Dazzling e Queenly Majesty. Essas habilidades dependem de bloqueio de estados, prioridades ou terreno e não devem ser marcadas como funcionais antes de suas rotinas específicas.

## Validação

O teste `tools/test_gen8_fairy_moves_abilities.py` verifica IDs, parâmetros de batalha, textos, entradas de Contest, mapeamentos de animação, categoria física das exceções e os três efeitos de habilidade implementados. O workflow também executa esse teste antes da compilação moderna.
