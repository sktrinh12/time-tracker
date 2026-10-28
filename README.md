# time-tracker

- useful terminal commands
```bash
sqlite3 ~/Documents/work/time-tracker/data/time.db "SELECT (julianday('1970-01-01 ' || '13:00') - julianday('1970-01-01 ' || start_time)) * 24 FROM time_entries WHERE id = 545;"

sqlite3 ~/Documents/work/time-tracker/data/time.db "SELECT (julianday('1970-01-01 ' || end_time) - julianday('1970-01-01 ' || start_time)) * 24 FROM time_entries WHERE id = 545;"

echo $(( $(date -d "15:16" +%s) - $(date -d "13:45" +%s) )) | awk '{print $1 / 3600 " hours"}'
```
