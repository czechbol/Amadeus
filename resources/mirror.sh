#!/bin/bash
# Give the bot time to start
sleep 60

while :
do
	d=$(date +"MIRROR TIMESTAMP: %Y-%m-%d %H:%M:%S")

	if test -f "~/amadeus.log"; then
		echo -e "$d\n$(cat ~/amadeus.log)" > ~/.amadeus
	else
		echo -e "$d\n" > ~/.amadeus
	fi
	echo $d > ~/.journalctl
	sudo journalctl -u amadeus >> ~/.journalctl

	docker cp ~/.amadeus amadeus_bot_1:/amadeus/amadeus.log
	docker cp ~/.journalctl    amadeus_bot_1:/amadeus/journalctl.log

	rm -f ~/.amadeus
	rm -f ~/.journalctl

	sleep 300
done
