from flask import Flask, request, jsonify, render_template_string
import requests
import re

app = Flask(__name__)

# Replace with your actual key
TOGETHER_API_KEY = '23d1b1be9ea1568a275b086e854ef7583449c0a61016dabf9da0dbbb7f885081'
TOGETHER_URL = 'https://api.together.xyz/v1/chat/completions'
MODEL_NAME = 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free'

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# Planner Agent
def classify_task(prompt):
    # Very basic classification
    if "script" in prompt.lower() or "code" in prompt.lower():
        return "script"
    else:
        return "steps"

# Executor Agent
def get_response(prompt, task_type):
    if task_type == "steps":
        system_prompt = "You are a ServiceNow expert helping citizen developers. Explain everything in clear steps."
    else:
        system_prompt = "You are a ServiceNow developer. Write simple and production-ready scripts for the given task."

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 512
    }

    response = requests.post(TOGETHER_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    reply = response.json()['choices'][0]['message']['content']
    return re.sub(r'\*\*(.*?)\*\*', r'\1', reply)

# HTML UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ServiceNow AI Agent</title>
    <style>
        body { font-family: Arial; margin: 40px auto; padding: 20px; max-width: 1000px; }
        #container { display: flex; gap: 20px; }
        #left, #right { flex: 1; }
        input, button { padding: 10px; width: 100%; margin-top: 10px; font-size: 16px; }
        .response { margin-top: 10px; background: #f2f2f2; padding: 10px; border-radius: 5px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h2>ServiceNow AI Agent (Agentic AI Style)</h2>
    <div id="container">
        <div id="left">
            <h4>Ask your question</h4>
            <input type="text" id="prompt" placeholder="e.g., How do I create a catalog item?">
            <button onclick="sendPrompt()">Submit</button>
        </div>
        <div id="right">
            <h4>Agent Response</h4>
            <div class="response" id="response">Waiting for your question...</div>
        </div>
    </div>

    <script>
        async function sendPrompt() {
            const prompt = document.getElementById('prompt').value;
            document.getElementById('response').innerText = 'Thinking...';

            const res = await fetch('/servicenow-agent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            const data = await res.json();
            document.getElementById('response').innerText = data.reply || data.error;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/servicenow-agent', methods=['POST'])
def servicenow_agent():
    user_input = request.json.get('prompt', '')
    task_type = classify_task(user_input)
    
    try:
        reply = get_response(user_input, task_type)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
