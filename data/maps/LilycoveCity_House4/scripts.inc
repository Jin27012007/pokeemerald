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
	msgbox LilycoveCity_House4_Text_MomAfterArrival, MSGBOX_DEFAULT
	release
	end

LilycoveCity_House4_EventScript_AdoptionCard::
	lock
	faceplayer
	msgbox LilycoveCity_House4_Text_BirthdayPresent, MSGBOX_DEFAULT
	giveitem ITEM_POKE_BALL, 5
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
	giveitem ITEM_ADOPTION_CARD
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
	setvar VAR_LILYCOVE_OPENING_STATE, 2
	removeobject LOCALID_LILYCOVE_ADOPTION_CARD
	msgbox LilycoveCity_House4_Text_AdoptionCard, MSGBOX_DEFAULT
	release
	end

LilycoveCity_House4_Text_FirstArrival:
	.string "The move to LILYCOVE is finally over.\p"
	.string "MOM sets the last bag down and looks\n"
	.string "around the new house.$"

LilycoveCity_House4_Text_MomWelcome:
	.string "MOM: We made it, {PLAYER}! This is\n"
	.string "our new home in LILYCOVE.\p"
	.string "Let's get settled in. Tomorrow will be\n"
	.string "a big day for you…$"

LilycoveCity_House4_Text_MomAfterArrival:
	.string "MOM: I hope we can make wonderful\n"
	.string "memories here in LILYCOVE.$"

LilycoveCity_House4_Text_BirthdayPresent:
	.string "A birthday present was left for you.\p"
	.string "You open it and find some supplies.$"

LilycoveCity_House4_Text_AdoptionCard:
	.string "There is an ADOPTION CARD inside, too!\p"
	.string "You can take it to the SAFARI and\n"
	.string "adopt your first POKéMON there.$"
