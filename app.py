from flask import Flask, request, render_template
from search import search

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        query = request.form['query']
        results = search(query)
    return render_template('index.html', results=results)

if __name__ == "__main__":
    app.run(debug=True)
