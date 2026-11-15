# Integração Gen 8 — fase 5: primeiros efeitos de itens

## Efeitos implementados

- **Absorb Bulb:** ao receber dano de um golpe Water, consome o item e aumenta Sp. Atk em um estágio.
- **Cell Battery:** ao receber dano de um golpe Electric, consome o item e aumenta Attack em um estágio.
- **Snowball:** ao receber dano de um golpe Ice, consome o item e aumenta Attack em um estágio.
- **Wide Lens:** aumenta a precisão do portador pelo parâmetro de 10%.
- **Light Clay:** Reflect e Light Screen duram oito turnos em vez de cinco.
- **Lagging Tail:** define velocidade efetiva zero na comparação de ordem de ação, depois da prioridade do movimento e antes da verificação de Quick Claw.
- **Leek:** reutiliza o efeito de Stick já existente para Farfetch'd.
- **Razor Claw:** reutiliza o efeito Scope Lens de aumento de crítico.
- **Razor Fang:** reutiliza o efeito Flinch já existente.

Os três itens que aumentam stats usam o fluxo de script de item/berry existente, que consome o item e aplica a animação/mensagem de aumento. O tipo do golpe é resolvido pelo helper `GET_MOVE_TYPE`, incluindo golpes de tipo dinâmico.

## Itens ainda pendentes

- Black Sludge e Sticky Barb: dano/cura de fim de turno e transferência por contato.
- Metronome: contador de golpes consecutivos e multiplicador de dano.
- Shed Shell: escapar de efeitos de aprisionamento.
- Electric, Grassy, Misty e Psychic Seeds: exigem o sistema de terrenos e a aplicação do stat correspondente.
- Electirizer, Magmarizer, Oval Stone, Razor Claw, Razor Fang e Leader's Crest: integração com métodos de evolução.
- Honey: uso de campo/atração de encontros.
- Red Nectar: mudança persistente de forma.

A auditoria de dependências marca como comportamento verificado apenas os nove itens implementados/reutilizados acima. Os demais continuam com comportamento pendente, mesmo que já tenham IDs e registros de item.

## Testes

`tools/test_gen8_item_behaviors.py` verifica os gatilhos por tipo, o uso do script de aumento de stats, os multiplicadores/durações e a ordem de Lagging Tail. O CI também executa o teste de catálogo da fase 4.

A integração continua em staging; as espécies #387–898 não foram ativadas em `gSpeciesInfo`.
