#!/bin/bash
INTERPRETER="python3.5"

TARGET="jidou"
# PARAMETER="-s -j -p --swift --java --php input_FILE output_FILE"
# PARAMETER="--java mobile.aaa"
# PARAMETER="--json tmp.aaa"
# PARAMETER="--swift tmp.aaa"
# PARAMETER="--swift syntaxtest.aaa"
# PARAMETER="--swift mobile.aaa"
# PARAMETER="--php mobile.aaa"
PARAMETER="--server"

#########################################################################################################################
#########################################################################################################################
# Functions

function f09()
{
	run_target
}

function f10()
{
	run_target
}

function f11()
{
	run_target
}

function f12()
{
	run_target
}


#########################################################################################################################
#########################################################################################################################
# Intern


function run_target()
{
	separate "RUN: $TARGET" "yellow"

    $INTERPRETER $TARGET $PARAMETER

	EXITSTATUS=$?

	if [[ $EXITSTATUS -ne 0 ]]; then
		separate "EXIT FAILURE, CODE: $EXITSTATUS" "red"
		exit $EXITSTATUS
	else
		separate "EXIT SUCCESS" "green"
	fi

}


function separate()
{
	NCOLOR="\033[0m"
	case $2 in
		( red )     COLOR="\033[0;31m" ;;
		( green )   COLOR="\033[0;32m" ;;
		( yellow )  COLOR="\033[0;33m" ;;
		( blue )    COLOR="\033[0;34m" ;;
		( magenta ) COLOR="\033[0;35m" ;;
		( cyan )    COLOR="\033[0;36m" ;;
		( white )   COLOR="\033[0;37m" ;;
		( * )       COLOR="\033[0;34m" ;;
	esac

	echo -e "\n$COLOR===================================================================================================="
	echo -e "=======$NCOLOR  $1\n"
}

#########################################################################################################################
#########################################################################################################################
# Handel VIM input

clear 

case $1 in
	( f09 ) f09 ;;
	( f10 ) f10 ;;
	( f11 ) f11 ;;
	( f12 ) f12 ;;
	( * ) f09 ;; 
esac



