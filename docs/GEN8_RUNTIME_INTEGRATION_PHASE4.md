# Integração Gen 8 — fase 4: catálogo de itens

## Dados adicionados

Foram adicionados 23 IDs locais de itens, com registros em `gItems`, preços, nomes, descrições e entradas na tabela de ícones:

Absorb Bulb, Black Sludge, Cell Battery, Electirizer, Electric Seed, Grassy Seed, Honey, Lagging Tail, Leader's Crest, Leek, Light Clay, Magmarizer, Metronome, Misty Seed, Oval Stone, Psychic Seed, Razor Claw, Razor Fang, Red Nectar, Shed Shell, Snowball, Sticky Barb e Wide Lens.

Os IDs são locais de Emerald e não copiam os valores da Expansion. Os itens foram colocados no bolso de itens. Os registros de Honey e Red Nectar ainda usam o comportamento de campo indisponível, pois Honey Encounter e mudança de forma não foram implementados nesta fase.

## Hold effects

Foram reservados IDs locais 67–77 para:
- Absorb Bulb
- Black Sludge
- Cell Battery
- Lagging Tail
- Light Clay
- Metronome
- Shed Shell
- Snowball
- Sticky Barb
- Terrain Seed
- Wide Lens

Leek reutiliza o efeito de Stick já existente para Farfetch'd. Razor Claw reutiliza Scope Lens e Razor Fang reutiliza Flinch.

Os parâmetros dos quatro Terrain Seeds foram registrados, mas o sistema de terrenos ainda não existe em Emerald.

## Estado funcional

Esta fase integra os dados e evita que espécies novas apontem para itens sem constante, registro ou entrada de ícone. **Ela não declara os efeitos de batalha dos novos itens como funcionais.** Os IDs de hold effect foram reservados, mas os comportamentos ainda precisam ser implementados e testados: ativação ao receber golpes, dano/cura no fim do turno, transferência de Sticky Barb, precisão de Wide Lens, prioridade de Lagging Tail, duração de telas, Metronome, Shed Shell e terrenos.

Os ícones atuais usam temporariamente o ícone de interrogação para evitar referências nulas. Os ícones próprios serão importados/adaptados na fase de assets.

## Validação

`tools/test_gen8_item_registry.py` verifica:
- 23 constantes e registros de item;
- descrições e entradas de ícone;
- IDs de hold effect únicos dentro de 8 bits;
- reutilização explícita dos efeitos existentes para Leek, Razor Claw e Razor Fang.

A tabela de compatibilidade continua marcando o comportamento dos itens novos como pendente. As espécies #387–898 ainda não foram ativadas em `gSpeciesInfo`.
