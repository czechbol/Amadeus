#!/bin/bash
mkdir -p ~/backups
docker exec -i amadeus_db_1 pg_dumpall -c -U postgres > ~/backups/dump_$(date +%Y-%m-%d"_"%H:%M:%S).sql

# compress last month
older=$(date -d "`date +%Y-%m-%d` -1month" +%Y-%m-%d)

cd ~/backups
FILE=./dump_archive.tar.xz
if test -f "$FILE"; then
    unxz "$FILE"
fi

find dump_*.sql -type f -mtime +7 -print0 | tar -rf ./dump_archive.tar --remove-files --null -T -
xz ./dump_archive.tar

cd - > /dev/null

exit 0
