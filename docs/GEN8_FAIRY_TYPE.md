# Tipo Fairy — integração de runtime

## Implementado

- `TYPE_FAIRY` usa o ID local 18; os 18 IDs anteriores não foram renumerados.
- A tabela de dano foi atualizada para o quadro de efetividade da Geração VI: Fairy é forte contra Fighting, Dragon e Dark; resiste a Fire, Poison e Steel; recebe dano super efetivo de Poison e Steel; resiste a Fighting, Bug e Dark; e é imune a Dragon.
- Foram removidas as antigas resistências de Steel contra Ghost e Dark, que não existem a partir da Geração VI.
- Mensagens de batalha, nome do tipo, sprite do resumo, filtro por tipo da Pokédex e arte de 32×16 pixels foram incluídos.
- Clefairy, Clefable, Jigglypuff, Wigglytuff, Mr. Mime, Cleffa, Igglybuff, Togepi, Togetic, Snubbull, Granbull, Marill, Azumarill, Azurill, Mawile, Ralts, Kirlia e Gardevoir receberam os tipos modernos.
- O conversor e o ledger de compatibilidade agora reconhecem o tipo Fairy como mapeável ao ID local 18.

## Limites desta etapa

A implementação adiciona o tipo e seu cálculo de efetividade; ela não completa os movimentos Fairy ausentes, itens específicos do tipo, habilidades novas, nem ativa as 512 espécies #387–898 no runtime. Esses sistemas permanecem separados e não devem ser considerados concluídos por causa desta alteração.

## Validação

O CI executa `tools/test_fairy_type_integration.py` para conferir os 12 confrontos de Fairy, a quantidade de registros da tabela, as tipagens retroativas, o ícone, o filtro da Pokédex e a remoção do bloqueio de enum no pipeline Gen 8.
