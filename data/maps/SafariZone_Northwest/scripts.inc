SafariZone_Northwest_MapScripts::
	.byte 0

SafariZone_Northwest_EventScript_AdoptionAttendant::
	lock
	faceplayer
	goto_if_eq VAR_LILYCOVE_ADOPTION_STATE, 1, SafariZone_Northwest_EventScript_AlreadyAdopted
	checkitem ITEM_ADOPTION_CARD
	goto_if_eq VAR_RESULT, FALSE, SafariZone_Northwest_EventScript_NoAdoptionCard
	msgbox SafariZone_Northwest_Text_AdoptionIntro, MSGBOX_DEFAULT
	msgbox SafariZone_Northwest_Text_ChooseSkitty, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, SafariZone_Northwest_EventScript_AdoptSkitty
	msgbox SafariZone_Northwest_Text_ChooseEevee, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, SafariZone_Northwest_EventScript_AdoptEevee
	msgbox SafariZone_Northwest_Text_ChooseVulpix, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, SafariZone_Northwest_EventScript_AdoptVulpix
	msgbox SafariZone_Northwest_Text_ChangedMind, MSGBOX_DEFAULT
	release
	end

SafariZone_Northwest_EventScript_NoAdoptionCard::
	msgbox SafariZone_Northwest_Text_NeedCard, MSGBOX_DEFAULT
	release
	end

SafariZone_Northwest_EventScript_AlreadyAdopted::
	msgbox SafariZone_Northwest_Text_AlreadyAdopted, MSGBOX_DEFAULT
	release
	end

SafariZone_Northwest_EventScript_AdoptSkitty::
	bufferspeciesname STR_VAR_1, SPECIES_SKITTY
	givemon SPECIES_SKITTY, 5
	goto SafariZone_Northwest_EventScript_CheckAdoptionResult
	end

SafariZone_Northwest_EventScript_AdoptEevee::
	bufferspeciesname STR_VAR_1, SPECIES_EEVEE
	givemon SPECIES_EEVEE, 5
	goto SafariZone_Northwest_EventScript_CheckAdoptionResult
	end

SafariZone_Northwest_EventScript_AdoptVulpix::
	bufferspeciesname STR_VAR_1, SPECIES_VULPIX
	givemon SPECIES_VULPIX, 5
	goto SafariZone_Northwest_EventScript_CheckAdoptionResult
	end

SafariZone_Northwest_EventScript_CheckAdoptionResult::
	goto_if_eq VAR_RESULT, MON_GIVEN_TO_PARTY, SafariZone_Northwest_EventScript_AdoptionSucceeded
	goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC, SafariZone_Northwest_EventScript_AdoptionSucceeded
	msgbox SafariZone_Northwest_Text_NoRoom, MSGBOX_DEFAULT
	release
	end

SafariZone_Northwest_EventScript_AdoptionSucceeded::
	removeitem ITEM_ADOPTION_CARD, 1
	setvar VAR_LILYCOVE_ADOPTION_STATE, 1
	msgbox SafariZone_Northwest_Text_AdoptionSucceeded, MSGBOX_DEFAULT
	release
	end

SafariZone_Northwest_Text_AdoptionIntro:
	.string "TEM UM CARTAO DE ADOTACAO?\p"
	.string "VOU AJUDAR VOCE A ESCOLHER\n"
	.string "SEU PRIMEIRO POKéMON.$"

SafariZone_Northwest_Text_ChooseSkitty:
	.string "GOSTARIA DE ADOTAR SKITTY?$"

SafariZone_Northwest_Text_ChooseEevee:
	.string "GOSTARIA DE ADOTAR EEVEE?$"

SafariZone_Northwest_Text_ChooseVulpix:
	.string "GOSTARIA DE ADOTAR VULPIX?$"

SafariZone_Northwest_Text_ChangedMind:
	.string "SEM PROBLEMA. VOLTE QUANDO\n"
	.string "QUISER ESCOLHER UM COMPANHEIRO.$"

SafariZone_Northwest_Text_NeedCard:
	.string "PARA ADOTAR UM POKéMON, VOCE\n"
	.string "PRECISA DO CARTAO DE ADOTACAO\n"
	.string "QUE VEIO COM SEU PRESENTE.$"

SafariZone_Northwest_Text_AlreadyAdopted:
	.string "VOCE JA ADOTOU SEU PRIMEIRO\n"
	.string "POKéMON. CUIDE BEM DELE!$"

SafariZone_Northwest_Text_NoRoom:
	.string "SUA EQUIPE E O PC ESTAO CHEIOS.\p"
	.string "LIBERE ESPACO E VOLTE. O CARTAO\n"
	.string "AINDA ESTA COM VOCE.$"

SafariZone_Northwest_Text_AdoptionSucceeded:
	.string "PARABENS! VOCE ADOTOU {STR_VAR_1}!\p"
	.string "CUIDE BEM DO SEU NOVO COMPANHEIRO\n"
	.string "E PREPARE-SE PARA OS CONCURSOS!$"
