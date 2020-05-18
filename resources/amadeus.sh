#!/bin/bash
if [[ $1 == "stop" ]]; then
	stop
else
	stop
	start
fi

stop () {
	# kill the bot process
	if test -f "~/amadeus.pid"; then
		kill `cat ~/amadeus.pid`
		rm -f ~/amadeus.pid
	fi

	# stop log synchronisation
	if test -f "~/journalctl.pid"; then
		kill `cat ~/journalctl.pid`
		rm -f ~/journalctl.pid
	fi
}

start () {
	# run the bot process and save its log
	rm -f ~/amadeus.log
	nohup python3 -u amadeus/amadeus.py > ~/amadeus.log &
	echo $! > ~/amadeus.pid

	# start log synchronisation
	rm -f ~/journalctl.log
	nohup python3 -u amadeus/resources/mirror.py > ~/journalctl.log &
	echo $! > ~/journalctl.pid
}

exit 0
