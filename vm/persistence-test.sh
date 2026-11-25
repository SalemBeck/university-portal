#!/usr/bin/env bash
# Part D - admin operation + persistence test (run inside the VM, in ~/university-portal)
cd ~/university-portal
set -a; . ./.env; set +a
PSQL="sudo docker exec uni-db psql -U $POSTGRES_USER -d $POSTGRES_DB -c"
TITLE="Exam timetable published"

echo "\$ curl (admin login + create announcement)"
curl -s -c /tmp/cj -o /dev/null -d "username=$ADMIN_USERNAME&password=$ADMIN_PASSWORD" http://localhost:8080/login
curl -s -b /tmp/cj -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" \
  --data-urlencode "title=$TITLE" --data-urlencode "department_id=1" \
  --data-urlencode "body=The timetable for the January exams is now available at the faculty offices." \
  http://localhost:8080/admin/new

echo "\$ psql: SELECT id, title FROM announcements ORDER BY id;"
$PSQL "SELECT id, title FROM announcements ORDER BY id;"

echo "\$ docker compose rm -sf db        # stop and DELETE the PostgreSQL container"
sudo docker compose rm -sf db 2>&1 | tail -2
echo "\$ docker ps -a --filter name=uni-db"
sudo docker ps -a --filter name=uni-db --format "{{.Names}} {{.Status}}"; echo "(no container)"
echo "\$ docker volume ls"
sudo docker volume ls
echo "\$ docker compose up -d db        # recreate a NEW container with the same volume"
sudo docker compose up -d db 2>&1 | tail -2
until sudo docker exec uni-db pg_isready -q 2>/dev/null; do sleep 1; done
sudo docker ps --filter name=uni-db --format "{{.Names}} {{.ID}} {{.Status}}"
echo "\$ psql: SELECT id, title FROM announcements ORDER BY id;"
$PSQL "SELECT id, title FROM announcements ORDER BY id;"
echo "\$ curl -s http://localhost:8080/announcements | grep '$TITLE'"
curl -s http://localhost:8080/announcements | grep -o "$TITLE" | head -1
