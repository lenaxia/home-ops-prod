import json

# Read the content of the grammar file
with open('grammar.txt', 'r') as file:
    grammar_content = file.read()

# Ensure proper escaping of the grammar content
escaped_grammar_content = grammar_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

# Create the JSON payload
payload = {
    "model": "neuralhermes-2.5-7b",
    "messages": [
        {
            "role": "user",
            "content": "Do you like apples?"
        }
    ],
    "grammar": escaped_grammar_content
}

# Convert the payload to a JSON string with proper formatting
json_payload = json.dumps(payload, indent=2)

# Save the JSON payload to a file
with open('request.json', 'w') as json_file:
    json_file.write(json_payload)

print("JSON payload saved to request.json")

