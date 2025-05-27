from flask import Flask, render_template, request, redirect, session, url_for
import json, requests, os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "revpainelsecreto"

GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_FILE = os.getenv("GITHUB_FILE")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

def get_file_content():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        from base64 import b64decode
        data = b64decode(content['content']).decode()
        sha = content['sha']
        return json.loads(data), sha
    return {}, ""

def update_file_content(data, sha):
    from base64 import b64encode
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    content = json.dumps(data, indent=4)
    payload = {
        "message": "Atualizando keys.json via painel Flask",
        "content": b64encode(content.encode()).decode(),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == ADMIN_USER and pw == ADMIN_PASS:
            session["user"] = user
            return redirect("/painel")
    return render_template("login.html")

@app.route("/painel")
def painel():
    if "user" not in session:
        return redirect("/")
    dados, _ = get_file_content()
    return render_template("painel.html", dados=dados)

@app.route("/gerar", methods=["POST"])
def gerar():
    if "user" not in session:
        return redirect("/")
    from random import choices
    from string import ascii_uppercase, digits
    key = "REV-" + ''.join(choices(ascii_uppercase + digits, k=8))
    dias = int(request.form.get("dias", 1))
    validade = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    dados, sha = get_file_content()
    dados[key] = {"validade": validade, "machine": ""}
    update_file_content(dados, sha)
    return redirect("/painel")

@app.route("/revogar/<key>")
def revogar(key):
    if "user" not in session:
        return redirect("/")
    dados, sha = get_file_content()
    if key in dados:
        dados[key]["machine"] = ""
    update_file_content(dados, sha)
    return redirect("/painel")

@app.route("/excluir/<key>")
def excluir(key):
    if "user" not in session:
        return redirect("/")
    dados, sha = get_file_content()
    if key in dados:
        del dados[key]
    update_file_content(dados, sha)
    return redirect("/painel")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)