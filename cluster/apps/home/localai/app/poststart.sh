#!/bin/bash

curl http://localhost:8080/models/apply -H "Content-Type: application/json" -d '{
     "url": "https://raw.githubusercontent.com/go-skynet/model-gallery/main/gpt4all-j.yaml",
     "name": "gpt4all-j"
   }'
