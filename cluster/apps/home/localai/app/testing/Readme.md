## Carly

curl https://ai.midori-ai.xyz/v1/chat/completions   -H "Content-Type: application/json"   -H "Authorization: Bearer sk-localai-984277269935714314-ad9c572624434c808bf852fc04dbe9f9"   -d @temp3 | jq


## Hermes

curl $LOCALAI/v1/chat/completions   -H "Content-Type: application/json"  -d @temp3 | jq
