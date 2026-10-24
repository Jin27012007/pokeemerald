LilycoveCity_House4_MapScripts::
	map_script MAP_SCRIPT_ON_FRAME_TABLE, LilycoveCity_House4_OnFrame
	map_script MAP_SCRIPT_ON_LOAD, LilycoveCity_House4_OnLoad
	map_script MAP_SCRIPT_ON_TRANSITION, LilycoveCity_House4_OnTransition
	.byte 0

LilycoveCity_House4_OnLoad:
	goto_if_ge VAR_LILYCOVE_OPENING_STATE, 1, LilycoveCity_House4_OnLoadDone
	@ Set the initial tile before the player is created on the map.
	setobjectxyperm LOCALID_PLAYER, 5, 4
LilycoveCity_House4_OnLoadDone:
	end

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
	@ Walk from the front of the room toward Mom, then turn to face her.
	applymovement LOCALID_PLAYER, LilycoveCity_House4_Movement_WalkToMom
	waitmovement 0
	msgbox LilycoveCity_House4_Text_MomWelcome, MSGBOX_DEFAULT
	closemessage
	releaseall
	end

LilycoveCity_House4_Movement_WalkToMom:
	walk_up
	walk_up
	walk_up
	walk_right
	walk_in_place_faster_up
	step_end

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
	.string "A mudanca para Lilycove finalmente\n"
	.string "terminou.\p"
	.string "Mamae guarda a ultima mala e olha\n"
	.string "ao redor da casa nova.$"

LilycoveCity_House4_Text_MomWelcome:
	.string "Mae: Chegamos, {PLAYER}! Esta e\n"
	.string "nossa nova casa em Lilycove.\p"
	.string "Eu nao esqueci que dia e hoje.\n"
	.string "Feliz aniversario, {PLAYER}!\p"
	.string "Seu presente esta ali. Pode abrir!$"

LilycoveCity_House4_Text_MomBirthdayReminder:
	.string "Mae: A mudanca foi corrida, mas\n"
	.string "nao esqueci seu aniversario.\n"
	.string "Seu presente esta ali!$"

LilycoveCity_House4_Text_MomAfterArrival:
	.string "Mae: Espero que a gente crie\n"
	.string "muitas lembrancas em Lilycove.\p"
	.string "Espero que goste do presente!$"

LilycoveCity_House4_Text_BirthdayPresent:
	.string "Voce abre o presente de aniversario.\p"
	.string "Dentro ha cinco Poke Bolas e uma\n"
	.string "carta: Cartao de Adocao.$"

LilycoveCity_House4_Text_AdoptionCard:
	.string "Mamae escolheu esta carta para voce.\p"
	.string "Leve-a a Zona Safari para adotar\n"
	.string "seu primeiro Pokemon. Parabens!$"
