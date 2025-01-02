from flask import Flask, request, render_template
from search import search, format_results

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    results = []
    error = None
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            try:
                results = search(query)
                if not results:
                    error = "No results found for your query."
            except Exception as e:
                error = f"Search error: {str(e)}"
                results = []
    
    return render_template('index.html', 
                         query=query,
                         results=results,
                         error=error)

if __name__ == "__main__":
    app.run(debug=True)
