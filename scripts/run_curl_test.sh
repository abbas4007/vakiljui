#!/bin/bash
curl -s https://ai.liara.ir/api/6a6988970c9069a744511750/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $1" \
  -d @/tmp/curl_payload.json | python3 -m json.tool