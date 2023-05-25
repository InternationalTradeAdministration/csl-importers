#!/bin/sh
curl --request POST -H "Content-Type:application/json" \
  --data '{"input":"sample queue data"}' \
  http://localhost:7071/admin/functions/$1
