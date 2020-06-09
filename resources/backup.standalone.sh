#!/bin/bash
mkdir -p ~/backups
pg_dump amadeus > ~/backups/dump_$(date +%Y-%m-%d"_"%H:%M:%S).sql
exit 0
