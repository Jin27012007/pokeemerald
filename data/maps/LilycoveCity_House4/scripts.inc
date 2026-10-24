LilycoveCity_House4_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, LilycoveCity_House4_OnTransition
	.byte 0

LilycoveCity_House4_OnTransition:
	call_if_eq VAR_LILYCOVE_OPENING_STATE, 0, LilycoveCity_House4_EventScript_FirstArrival
	end

LilycoveCity_House4_EventScript_FirstArrival::
	lockall
	setvar VAR_LILYCOVE_OPENING_STATE, 1
	msgbox LilycoveCity_House4_Text_FirstArrival, MSGBOX_DEFAULT
	closemessage
	releaseall
	end

LilycoveCity_House4_Text_FirstArrival:
	.string "The move to LILYCOVE is finally over.\p"
	.string "MOM smiles and sets the last bag down.\p"
	.string "MOM: We made it. This is our new home.\p"
	.string "Let's get settled in. Tomorrow will be\n"
	.string "a big day for you…$"
