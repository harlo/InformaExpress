#! /bin/bash

source ~/.bash_profile

function do_update {
	cd $1
	if ([ $# -eq 1 ]); then
		G_BRANCH=master
	else
		G_BRANCH=$2

	git fetch --all
	git reset --hard origin/$G_BRANCH
	git pull origin $G_BRANCH
}

C_A=~/InformaAnnex
C_F=~/InformaFrontend

declare -a U_MODS=("$C_A" "$C_A/lib/Annex" "$C_A/lib/Annex/lib/Core" "$C_F" "$C_F/lib/Frontend" "$C_F/lib/Frontend/lib/Core")
for U_MOD in "${U_MODS[@]}"; do
	do_update $U_MOD $1
done