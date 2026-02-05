
import json
import os
from collections import Counter
from db import load_done

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TimeWiz Word Cloud</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js"></script>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f4f4f9; }
        #canvas { width: 80%; height: 80%; border: 1px solid #ccc; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>
    <script>
        const list = __DATA__;
        
        WordCloud(document.getElementById('canvas'), { 
            list: list,
            gridSize: 16,
            weightFactor: function (size) {
                return Math.pow(size, 2.3) * document.getElementById('canvas').width / 1024;
            },
            fontFamily: 'Times, serif',
            color: 'random-dark',
            rotateRatio: 0.5,
            rotationSteps: 2,
            backgroundColor: '#fff'
        });
    </script>
</body>
</html>
"""

def generate_wordcloud():
    done_items = load_done()
    if not done_items:
        return "No data for word cloud."

    # Count frequencies of descriptions
    # Or split into words? "Study Math" -> Study: 1, Math: 1
    # Let's simple split by space for now to get "keywords"
    words = []
    for item in done_items:
        desc = item.get('description', '')
        words.extend(desc.split())
    
    # Clean words (remove short/common?)
    # For MVP, keep all non-empty
    words = [w for w in words if w.strip()]
    
    counts = Counter(words)
    # Format for wordcloud2.js: [['word', count], ...]
    data_list = [[word, count * 10] for word, count in counts.items()] 
    # Scaled count * 10 for visibility if count is low

    html_content = TEMPLATE.replace('__DATA__', json.dumps(data_list))
    
    # Save to artifacts directory in brain? 
    # Or just return path if saved locally?
    # The prompt implies skill generates it.
    # I'll save it to the skill folder's examples or output dir.
    # But usually artifacts are user-facing.
    
    # Let's save to a localized `output` folder in the skill for now.
    # Determine base directory relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'output')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'wordcloud.html')
    with open(output_path, 'w') as f:
        f.write(html_content)
        
    return output_path
