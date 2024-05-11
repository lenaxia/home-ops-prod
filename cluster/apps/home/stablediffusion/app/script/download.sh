#!/bin/bash

# Function to download a file if it does not exist
download_if_not_exists() {
  local directory=$1
  local url=$2
  local filename=$3

  # Create directory if it doesn't exist
  mkdir -p "$directory"

  # Change to directory
  cd "$directory"

  # Check if file exists
  if [ ! -f "$filename" ]; then
    echo "Downloading $filename..."
    wget -c -O "$filename" "$url"
  else
    echo "File $filename already exists, skipping download."
  fi
}

# Stable-diffusion models
download_if_not_exists "/data/models/Stable-diffusion" "https://s3.thekao.cloud/public/sd/forgottenmixAnimation_v10.safetensors" "forgottenmixAnimation_v10.safetensors"
download_if_not_exists "/data/models/Stable-diffusion" "https://civitai.com/api/download/models/75" "anythingV3_fp16.safetensors"
download_if_not_exists "/data/models/Stable-diffusion" "https://civitai.com/api/download/models/290640?type=Model&format=SafeTensor&size=pruned&fp=fp16" "ponyDiffusionV6XL.safetensors"
download_if_not_exists "/data/models/Stable-diffusion" "https://civitai.com/api/download/models/490254" "zavyChromaXL_v70.safetensors"
download_if_not_exists "/data/models/Stable-diffusion" "https://s3.thekao.cloud/public/sd/f222.ckpt" "f222.ckpt"
download_if_not_exists "/data/models/Stable-diffusion" "https://civitai.com/api/download/models/471120" "juggernautXL_RunDiffusion_Hyper.safetensors"
download_if_not_exists "/data/models/Stable-diffusion" "https://civitai.com/api/download/models/425083?type=Model&format=SafeTensor&size=full&fp=fp32" "revAnimated_V2Rebirth.safetensors"

# Lora models
download_if_not_exists "/data/models/Lora" "https://huggingface.co/toto10/Loras/resolve/main/kidnap_v0.2.safetensors" "kidnap_v0.2.safetensors"
download_if_not_exists "/data/models/Lora" "https://civitai.com/api/download/models/87153" "more_details.safetensors"
download_if_not_exists "/data/models/Lora" "https://civitai.com/api/download/models/62833" "add_details.safetensors"
download_if_not_exists "/data/models/Lora" "https://civitai.com/api/download/models/29860?type=Model&format=SafeTensor&size=full&fp=fp16" "selfBreastGrab.safetensors"
download_if_not_exists "/data/models/Lora" "https://civitai.com/api/download/models/50309" "BondageAndDildos.safetensors"
download_if_not_exists "/data/models/Lora" "https://civitai.com/api/download/models/118166?type=Model&format=SafeTensor" "woodenHorse.safetensors"
download_if_not_exists "/data/models/Lora" "https://civitai.com/api/download/models/142718" "faces_v3.safetensors"

# Embedding models
download_if_not_exists "/data/models/embeddings" "https://civitai.com/api/download/models/60095" "bad_prompt_version2-neg.pt"
download_if_not_exists "/data/models/embeddings" "https://civitai.com/api/download/models/9208" "easynegative.safetensors"
download_if_not_exists "/data/models/embeddings" "https://civitai.com/api/download/models/20068" "badhandv4.pt"
download_if_not_exists "/data/models/embeddings" "https://civitai.com/api/download/models/125849" "bad_hands_5.pt"
download_if_not_exists "/data/models/embeddings" "https://civitai.com/api/download/models/5637" "ng_deepnegative_v1_75t.pt"
download_if_not_exists "/data/models/embeddings" "https://civitai.com/api/download/models/25820" "verybadimagenegative_v1.3.pt"

