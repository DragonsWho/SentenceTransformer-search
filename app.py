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
                    error = "Ничего не найдено по вашему запросу."
            except Exception as e:
                error = f"Ошибка при выполнении поиска: {str(e)}"
                results = []
    
    return render_template('index.html', 
                         query=query,
                         results=results,
                         error=error)

if __name__ == "__main__":
    app.run(debug=True)
