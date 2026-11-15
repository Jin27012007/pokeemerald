# Integração Gen 8 — fase 3: tipo Fairy

## Implementação

Fairy agora possui ID Emerald próprio (`TYPE_FAIRY = 18`) e `NUMBER_OF_MON_TYPES` passa a 19. O ID local é diferente do ID da Expansion e é mantido no ledger de conversão.

A tabela de efetividade foi ampliada de 336 para 372 bytes, com 124 triplas de ataque/defesa. Foram adicionadas as 12 interações não neutras de Fairy:

| Ataque | Defesa | Resultado |
|---|---|---|
| Fairy | Fighting | 2× |
| Fairy | Dragon | 2× |
| Fairy | Dark | 2× |
| Fairy | Fire | 0,5× |
| Fairy | Poison | 0,5× |
| Fairy | Steel | 0,5× |
| Fighting | Fairy | 0,5× |
| Poison | Fairy | 2× |
| Bug | Fairy | 0,5× |
| Dragon | Fairy | 0× |
| Dark | Fairy | 0,5× |
| Steel | Fairy | 2× |

A tabela continua usando o sentinel `TYPE_ENDTABLE`. O limite da sondagem aleatória de interações foi corrigido para usar `>=`, impedindo uma leitura exatamente um elemento além do final da tabela.

## Interface e gráfico

- Nome FAIRY registrado em `gTypeNames`.
- Ícone de 32×16 adicionado em `graphics/types/fairy.png`, usando a segunda paleta de tipos (paleta 14).
- A regra de concatenação da folha de ícones agora define a ordem explicitamente: os 18 tipos originais, Fairy, e as cinco categorias de concurso.
- A tela de resumo recebeu a animação e o índice de paleta do tipo Fairy.

## Compatibilidade com Emerald

Hidden Power mantém a tabela de tipos original da terceira geração. Fairy não passa a ser um tipo possível de Hidden Power só porque o número total de tipos aumentou. O cálculo foi ajustado para excluir Normal, Mystery e o tipo posterior Fairy.

## Validação

`tools/test_gen8_fairy_type.py` confere:
- ID 18 e contagem de 19 tipos;
- as 12 interações de Fairy;
- 124 entradas e sentinel da tabela;
- nome, animação, paleta e presença do asset;
- limite seguro de leitura;
- exclusão de Fairy da seleção legada de Hidden Power.

## Limites

Fairy agora está implementado no cálculo de efetividade e na tela de resumo. Ainda faltam os efeitos das 165 habilidades novas, itens ausentes, movimentos e efeitos de batalha, métodos de evolução, sprites de espécies, paletas, ícones e cries. As espécies #387–898 ainda não foram ativadas em `gSpeciesInfo`.
