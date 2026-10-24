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
	.string "The move to LILYCOVE is finally over.\p"
	.string "MOM sets the last bag down and looks\n"
	.string "around the new house.$"

LilycoveCity_House4_Text_MomWelcome:
	.string "MOM: We made it, {PLAYER}! This is\n"
	.string "our new home in LILYCOVE.\p"
	.string "And I haven't forgotten what day it\n"
	.string "is. Happy birthday, {PLAYER}!\p"
	.string "Your present is waiting over there.\n"
	.string "Go on, take a look!$"

LilycoveCity_House4_Text_MomBirthdayReminder:
	.string "MOM: Moving day has been hectic, but\n"
	.string "I still wanted you to have a birthday\n"
	.string "to remember. Your present is waiting\n"
	.string "right over there!$"

LilycoveCity_House4_Text_MomAfterArrival:
	.string "MOM: I hope we can make wonderful\n"
	.string "memories here in LILYCOVE. And I hope\n"
	.string "you like your birthday present!$"

LilycoveCity_House4_Text_BirthdayPresent:
	.string "You open your birthday present.\p"
	.string "Inside are five POKé BALLS and a card\n"
	.string "that reads: ADOPTION CARD.$"

LilycoveCity_House4_Text_AdoptionCard:
	.string "MOM chose this card just for you.\p"
	.string "Take it to the SAFARI to adopt your\n"
	.string "first POKéMON. Happy birthday!$"
