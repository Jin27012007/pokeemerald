LilycoveCity_House4_MapScripts::
	map_script MAP_SCRIPT_ON_FRAME_TABLE, LilycoveCity_House4_OnFrame
	map_script MAP_SCRIPT_ON_TRANSITION, LilycoveCity_House4_OnTransition
	.byte 0

LilycoveCity_House4_OnTransition:
	goto_if_ge VAR_LILYCOVE_OPENING_STATE, 2, LilycoveCity_House4_EventScript_HideAdoptionCard
	end

LilycoveCity_House4_EventScript_HideAdoptionCard:
	removeobject LOCALID_LILYCOVE_ADOPTION_CARD
	end

LilycoveCity_House4_OnFrame:
	map_script_2 VAR_LILYCOVE_OPENING_STATE, 0, LilycoveCity_House4_EventScript_FirstArrival
	.2byte 0

LilycoveCity_House4_EventScript_FirstArrival::
	lockall
	setvar VAR_LILYCOVE_OPENING_STATE, 1
	msgbox LilycoveCity_House4_Text_FirstArrival, MSGBOX_DEFAULT
	closemessage
	msgbox LilycoveCity_House4_Text_MomWelcome, MSGBOX_DEFAULT
	closemessage
	releaseall
	end

LilycoveCity_House4_EventScript_Mom::
	lock
	faceplayer
	goto_if_ge VAR_LILYCOVE_OPENING_STATE, 2, LilycoveCity_House4_EventScript_MomAfterBirthday
	msgbox LilycoveCity_House4_Text_MomBirthdayReminder, MSGBOX_DEFAULT
	release
	end

LilycoveCity_House4_EventScript_MomAfterBirthday::
	msgbox LilycoveCity_House4_Text_MomAfterArrival, MSGBOX_DEFAULT
	release
	end

LilycoveCity_House4_EventScript_AdoptionCard::
	lock
	faceplayer
	@ Check both rewards before giving either one, so a full bag cannot
	@ let the player repeatedly collect only the POKé BALLS.
	checkitemspace ITEM_POKE_BALL, 5
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
	checkitemspace ITEM_ADOPTION_CARD, 1
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
	msgbox LilycoveCity_House4_Text_BirthdayPresent, MSGBOX_DEFAULT
	giveitem ITEM_POKE_BALL, 5
	giveitem ITEM_ADOPTION_CARD
	setvar VAR_LILYCOVE_OPENING_STATE, 2
	removeobject LOCALID_LILYCOVE_ADOPTION_CARD
	msgbox LilycoveCity_House4_Text_AdoptionCard, MSGBOX_DEFAULT
	release
	end

LilycoveCity_House4_Text_FirstArrival:
	.string "A mudança para Lilycove finalmente\n"
	.string "terminou.\p"
	.string "Mamãe guarda a última mala e olha\n"
	.string "ao redor da casa nova.$"

LilycoveCity_House4_Text_MomWelcome:
	.string "Mãe: Chegamos, {PLAYER}! Esta é\n"
	.string "nossa nova casa em Lilycove.\p"
	.string "Eu não esqueci que dia é hoje.\n"
	.string "Feliz aniversário, {PLAYER}!\p"
	.string "Seu presente está ali. Pode abrir!$"

LilycoveCity_House4_Text_MomBirthdayReminder:
	.string "Mãe: A mudança foi corrida, mas\n"
	.string "não esqueci seu aniversário.\n"
	.string "Seu presente está ali!$"

LilycoveCity_House4_Text_MomAfterArrival:
	.string "Mãe: Espero que a gente crie\n"
	.string "muitas lembranças em Lilycove.\p"
	.string "Espero que goste do presente!$"

LilycoveCity_House4_Text_BirthdayPresent:
	.string "Você abre o presente de aniversário.\p"
	.string "Dentro há cinco Poké Bolas e uma\n"
	.string "carta: Cartão de Adoção.$"

LilycoveCity_House4_Text_AdoptionCard:
	.string "Mamãe escolheu esta carta para você.\p"
	.string "Leve-a à Zona Safari para adotar\n"
	.string "seu primeiro Pokémon. Parabéns!$"
