from flask import Flask, jsonify, render_template, request
import a10

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    query = data.get('query', '')
    if not isinstance(query, str):
        return jsonify(error='Query must be a string'), 400

    question = query.replace('?', '').lower().split()
    answers, title = a10.query_response(question)
    return jsonify(
        answer='\n'.join(answers),
        answers=answers,
        infoboxTitle=title,
    )

@app.route('/api/infobox', methods=['POST'])
def infobox():
    data = request.get_json(force=True)
    title = data.get('title', '')
    if not isinstance(title, str) or not title.strip():
        return jsonify(error='No title provided'), 400

    try:
        info = a10.get_page_infobox(title.strip())
    except Exception as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(title=title.strip(), infobox=info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
