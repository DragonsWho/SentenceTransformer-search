import json
import numpy as np
from deepseek_search_api import DeepseekSearchAPI

class DeepseekSearch:
    def __init__(self):
        # Load search database
        with open('search_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Load embeddings and metadata
        self.embeddings = np.array(data['embeddings']['data']).reshape(data['embeddings']['shape'])
        self.metadata = data['metadata']
        
        # Initialize Deepseek API
        self.deepseek = DeepseekSearchAPI()

    def cosine_similarity(self, vec_a, vec_b):
        """Compute cosine similarity between two vectors"""
        return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

    def search(self, query, top_k=3):
        """Search for relevant summaries and generate Deepseek response"""
        # First, use Deepseek to analyze the query
        analysis_prompt = f"""Analyze this search query and extract key information:
        
        {query}
        
        Return a JSON object with these fields:
        - main_topics: List of main topics
        - key_concepts: List of key concepts
        - search_intent: What the user is looking for
        """
        
        try:
            analysis = self.deepseek.generate(analysis_prompt, 
                system_message="You are a search query analysis assistant.")
            import json
            query_analysis = json.loads(analysis)
        except:
            query_analysis = {
                'main_topics': [],
                'key_concepts': [],
                'search_intent': ''
            }
        
        # Search through summaries using the analysis
        results = []
        for i, metadata in enumerate(self.metadata):
            summary = self.get_summary_content(metadata['file'])
            
            # Count matches with query analysis
            match_score = 0
            for topic in query_analysis.get('main_topics', []):
                if topic.lower() in summary.lower():
                    match_score += 1
                    
            for concept in query_analysis.get('key_concepts', []):
                if concept.lower() in summary.lower():
                    match_score += 1
                    
            if query_analysis.get('search_intent', '').lower() in summary.lower():
                match_score += 2
                
            if match_score > 0:
                results.append({
                    'metadata': metadata,
                    'score': match_score,
                    'summary': summary
                })
        
        # Sort by match score
        results.sort(key=lambda x: x['score'], reverse=True)
        top_results = results[:top_k]
        
        # Generate Deepseek response
        context = "\n\n".join([
            f"Summary {i+1} ({res['metadata']['project']}):\n{res['summary']}"
            for i, res in enumerate(top_results)
        ])
        
        prompt = f"""Based on these summaries:
        {context}
        
        Answer this question: {query}
        
        Be specific and reference the summaries when possible.
        """
        response = self.deepseek.generate(prompt)
        
        return {
            'response': response,
            'sources': [res['metadata'] for res in top_results]
        }

    def get_summary_content(self, filename):
        """Get content of a summary file"""
        with open(f'summaries/{filename}', 'r', encoding='utf-8') as f:
            return f.read()

if __name__ == "__main__":
    searcher = DeepseekSearch()
    while True:
        query = input("Enter your query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
            
        result = searcher.search(query)
        print("\nResponse:")
        print(result['response'])
        print("\nSources:")
        for source in result['sources']:
            print(f"- {source['project']}")
        print()
