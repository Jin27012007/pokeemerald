Route121_SafariZoneEntrance_MapScripts::
	map_script MAP_SCRIPT_ON_FRAME_TABLE, Route121_SafariZoneEntrance_OnFrame
	.byte 0

Route121_SafariZoneEntrance_OnFrame:
	map_script_2 VAR_SAFARI_ZONE_STATE, 1, Route121_SafariZoneEntrance_EventScript_ExitSafariZone
	.2byte 0

Route121_SafariZoneEntrance_EventScript_ExitSafariZone::
	lockall
	applywaitmovement LOCALID_PLAYER, Route121_SafariZoneEntrance_Movement_ExitSafariZone
	setvar VAR_SAFARI_ZONE_STATE, 0
	releaseall
	end

Route121_SafariZoneEntrance_Movement_ExitSafariZone:
	walk_up
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	step_end

Route121_SafariZoneEntrance_EventScript_WelcomeAttendant::
	msgbox Route121_SafariZoneEntrance_Text_WelcomeToSafariZone, MSGBOX_NPC
	end

Route121_SafariZoneEntrance_EventScript_InfoAttendant::
	lock
	faceplayer
	msgbox Route121_SafariZoneEntrance_Text_WelcomeFirstTime, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, Route121_SafariZoneEntrance_EventScript_FirstTimeInfo
	msgbox Route121_SafariZoneEntrance_Text_ComeInAndEnjoy, MSGBOX_DEFAULT
	release
	end

Route121_SafariZoneEntrance_EventScript_FirstTimeInfo::
	msgbox Route121_SafariZoneEntrance_Text_FirstTimeInfo, MSGBOX_DEFAULT
	release
	end

Route121_SafariZoneEntrance_EventScript_EntranceCounterTrigger::
	lockall
	applywaitmovement LOCALID_PLAYER, Common_Movement_WalkInPlaceFasterUp
	showmoneybox 0, 0
	msgbox Route121_SafariZoneEntrance_Text_WouldYouLikeToPlay, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, Route121_SafariZoneEntrance_EventScript_TryEnterSafariZone
	msgbox Route121_SafariZoneEntrance_Text_PlayAnotherTime, MSGBOX_DEFAULT
	goto Route121_SafariZoneEntrance_EventScript_MovePlayerBackFromCounter
	end

Route121_SafariZoneEntrance_EventScript_TryEnterSafariZone::
	checkitem ITEM_POKEBLOCK_CASE
	goto_if_eq VAR_RESULT, 0, Route121_SafariZoneEntrance_EventScript_NoPokeblockCase
	call Route121_SafariZoneEntrance_EventScript_CheckHasRoomForPokemon
	checkmoney 500
	goto_if_eq VAR_RESULT, 0, Route121_SafariZoneEntrance_EventScript_NotEnoughMoney
	playse SE_SHOP
	msgbox Route121_SafariZoneEntrance_Text_ThatWillBe500Please, MSGBOX_DEFAULT
	removemoney 500
	updatemoneybox
	msgbox Route121_SafariZoneEntrance_Text_HereAreYourSafariBalls, MSGBOX_DEFAULT
	playfanfare MUS_OBTAIN_ITEM
	message Route121_SafariZoneEntrance_Text_Received30SafariBalls
	waitfanfare
	msgbox Route121_SafariZoneEntrance_Text_PleaseEnjoyYourself, MSGBOX_DEFAULT
	closemessage
	hidemoneybox
	applywaitmovement LOCALID_PLAYER, Route121_SafariZoneEntrance_Movement_EnterSafariZone
	special EnterSafariMode
	setvar VAR_SAFARI_ZONE_STATE, 2
	clearflag FLAG_GOOD_LUCK_SAFARI_ZONE
	warp MAP_SAFARI_ZONE_SOUTH, 32, 33
	waitstate
	end

Route121_SafariZoneEntrance_EventScript_CheckHasRoomForPokemon::
	getpartysize
	goto_if_ne VAR_RESULT, PARTY_SIZE, Route121_SafariZoneEntrance_EventScript_HasRoomForPokemon
	specialvar VAR_RESULT, ScriptCheckFreePokemonStorageSpace
	goto_if_eq VAR_RESULT, 1, Route121_SafariZoneEntrance_EventScript_HasRoomForPokemon
	msgbox Route121_SafariZoneEntrance_Text_PCIsFull, MSGBOX_DEFAULT
	goto Route121_SafariZoneEntrance_EventScript_MovePlayerBackFromCounter
	end

Route121_SafariZoneEntrance_EventScript_HasRoomForPokemon::
	return

Route121_SafariZoneEntrance_EventScript_NoPokeblockCase::
	msgbox Route121_SafariZoneEntrance_Text_YouNeedPokeblockCase, MSGBOX_DEFAULT
	goto Route121_SafariZoneEntrance_EventScript_MovePlayerBackFromCounter
	end

Route121_SafariZoneEntrance_EventScript_NotEnoughMoney::
	msgbox Route121_SafariZoneEntrance_Text_NotEnoughMoney, MSGBOX_DEFAULT
	goto Route121_SafariZoneEntrance_EventScript_MovePlayerBackFromCounter
	end

Route121_SafariZoneEntrance_EventScript_MovePlayerBackFromCounter::
	closemessage
	hidemoneybox
	applywaitmovement LOCALID_PLAYER, Route121_SafariZoneEntrance_Movement_BackAwayFromCounter
	releaseall
	end

Route121_SafariZoneEntrance_Movement_BackAwayFromCounter:
	walk_right
	step_end

Route121_SafariZoneEntrance_Movement_EnterSafariZone:
	walk_left
	walk_left
	walk_left
	walk_left
	walk_left
	walk_left
	walk_down
	delay_16
	step_end

Route121_SafariZoneEntrance_EventScript_TrainerTipSign::
	msgbox Route121_SafariZoneEntrance_Text_TrainerTip, MSGBOX_SIGN
	end


Route121_SafariZoneEntrance_EventScript_AdoptionAttendant::
	lock
	faceplayer
	checkitem ITEM_ADOPTION_CARD
	goto_if_eq VAR_RESULT, FALSE, Route121_SafariZoneEntrance_EventScript_AdoptionNoCard
	goto_if_ge VAR_LILYCOVE_OPENING_STATE, 3, Route121_SafariZoneEntrance_EventScript_AdoptionAlreadyDone
	msgbox Route121_SafariZoneEntrance_Text_AdoptionWelcome, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, Route121_SafariZoneEntrance_EventScript_AdoptionLeave
	getpartysize
	goto_if_ne VAR_RESULT, PARTY_SIZE, Route121_SafariZoneEntrance_EventScript_AdoptionChoose
	specialvar VAR_RESULT, ScriptCheckFreePokemonStorageSpace
	goto_if_eq VAR_RESULT, 1, Route121_SafariZoneEntrance_EventScript_AdoptionChoose
	msgbox Route121_SafariZoneEntrance_Text_AdoptionStorageFull, MSGBOX_DEFAULT
	goto Route121_SafariZoneEntrance_EventScript_AdoptionLeave
	end

Route121_SafariZoneEntrance_EventScript_AdoptionChoose::
	msgbox Route121_SafariZoneEntrance_Text_AdoptionSkitty, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, Route121_SafariZoneEntrance_EventScript_AdoptSkitty
	msgbox Route121_SafariZoneEntrance_Text_AdoptionEevee, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, Route121_SafariZoneEntrance_EventScript_AdoptEevee
	msgbox Route121_SafariZoneEntrance_Text_AdoptionVulpix, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, Route121_SafariZoneEntrance_EventScript_AdoptVulpix
	goto Route121_SafariZoneEntrance_EventScript_AdoptionLeave
	end

Route121_SafariZoneEntrance_EventScript_AdoptSkitty::
	givepokemon SPECIES_SKITTY, 5, ITEM_NONE
	goto Route121_SafariZoneEntrance_EventScript_AdoptionComplete
	end

Route121_SafariZoneEntrance_EventScript_AdoptEevee::
	givepokemon SPECIES_EEVEE, 5, ITEM_NONE
	goto Route121_SafariZoneEntrance_EventScript_AdoptionComplete
	end

Route121_SafariZoneEntrance_EventScript_AdoptVulpix::
	givepokemon SPECIES_VULPIX, 5, ITEM_NONE
	goto Route121_SafariZoneEntrance_EventScript_AdoptionComplete
	end

Route121_SafariZoneEntrance_EventScript_AdoptionComplete::
	removeitem ITEM_ADOPTION_CARD
	setvar VAR_LILYCOVE_OPENING_STATE, 3
	playfanfare MUS_OBTAIN_ITEM
	msgbox Route121_SafariZoneEntrance_Text_AdoptionComplete, MSGBOX_DEFAULT
	release
	end

Route121_SafariZoneEntrance_EventScript_AdoptionNoCard::
	msgbox Route121_SafariZoneEntrance_Text_AdoptionNeedCard, MSGBOX_DEFAULT
	release
	end

Route121_SafariZoneEntrance_EventScript_AdoptionAlreadyDone::
	msgbox Route121_SafariZoneEntrance_Text_AdoptionAlreadyDone, MSGBOX_DEFAULT
	release
	end

Route121_SafariZoneEntrance_EventScript_AdoptionLeave::
	release
	end

Route121_SafariZoneEntrance_Text_AdoptionWelcome:
	.string "Welcome to the SAFARI adoption desk!\p"
	.string "Show me your ADOPTION CARD and you\n"
	.string "can choose a partner to take home.$"

Route121_SafariZoneEntrance_Text_AdoptionSkitty:
	.string "Would you like to adopt SKITTY?$"

Route121_SafariZoneEntrance_Text_AdoptionEevee:
	.string "Would you like to adopt EEVEE?$"

Route121_SafariZoneEntrance_Text_AdoptionVulpix:
	.string "Would you like to adopt VULPIX?$"

Route121_SafariZoneEntrance_Text_AdoptionStorageFull:
	.string "Your party and PC are full. Make room\n"
	.string "before choosing your new partner.$"

Route121_SafariZoneEntrance_Text_AdoptionComplete:
	.string "Congratulations! Your new partner is\n"
	.string "ready to begin this journey with you.$"

Route121_SafariZoneEntrance_Text_AdoptionNeedCard:
	.string "You'll need an ADOPTION CARD from\n"
	.string "your family before adopting a POKéMON.$"

Route121_SafariZoneEntrance_Text_AdoptionAlreadyDone:
	.string "You've already adopted your first\n"
	.string "partner. Take good care of them!$"

