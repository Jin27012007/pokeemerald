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
	.string "A MUDANCA PARA LILYCOVE FINALMENTE\n"
	.string "TERMINOU.\p"
	.string "MAE GUARDA A ULTIMA MALA E OLHA\n"
	.string "AO REDOR DA CASA NOVA.$"

LilycoveCity_House4_Text_MomWelcome:
	.string "MAE: CHEGAMOS, {PLAYER}! ESTA E\n"
	.string "NOSSA NOVA CASA EM LILYCOVE.\p"
	.string "EU NAO ESQUECI QUE DIA E HOJE.\n"
	.string "FELIZ ANIVERSARIO, {PLAYER}!\p"
	.string "SEU PRESENTE ESTA ALI. PODE ABRIR!$"

LilycoveCity_House4_Text_MomBirthdayReminder:
	.string "MAE: A MUDANCA FOI CORRIDA, MAS\n"
	.string "NAO ESQUECI SEU ANIVERSARIO.\n"
	.string "SEU PRESENTE ESTA ALI!$"

LilycoveCity_House4_Text_MomAfterArrival:
	.string "MAE: ESPERO QUE A GENTE CRIE\n"
	.string "MUITAS LEMBRANCAS EM LILYCOVE.\p"
	.string "ESPERO QUE GOSTE DO PRESENTE!$"

LilycoveCity_House4_Text_BirthdayPresent:
	.string "VOCE ABRE O PRESENTE DE ANIVERSARIO.\p"
	.string "DENTRO HA CINCO POKé BOLAS E UMA\n"
	.string "CARTA: CARTAO DE ADOTACAO.$"

LilycoveCity_House4_Text_AdoptionCard:
	.string "MAE ESCOLHEU ESTA CARTA PARA VOCE.\p"
	.string "LEVE-A A ZONA SAFARI PARA ADOTAR\n"
	.string "SEU PRIMEIRO POKéMON. PARABENS!$"
