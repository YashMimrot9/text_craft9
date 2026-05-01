from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def correct_text(text, mode="standard"):
    url = "https://api.languagetool.org/v2/check"

    # Pick language style based on mode
    if mode in ["formal", "academic", "business"]:
        style = "FORMAL"
    elif mode == "casual":
        style = "INFORMAL"
    else:
        style = None

    params = {
        "text": text,
        "language": "en-US",
        "enabledOnly": "false",
    }

    response = requests.post(url, data=params)
    result = response.json()
    matches = result.get("matches", [])

    # Apply corrections from end to start so positions don't shift
    corrected = text
    for match in sorted(matches, key=lambda m: m["offset"], reverse=True):
        if match["replacements"]:
            start = match["offset"]
            end   = start + match["length"]
            best  = match["replacements"][0]["value"]
            corrected = corrected[:start] + best + corrected[end:]

    # Basic fixes on top
    import re
    # Fix standalone 'i' -> 'I'
    corrected = re.sub(r'\bi\b', 'I', corrected)
    # Capitalize first letter of sentences
    corrected = re.sub(
        r'(^|(?<=[.!?])\s+)([a-z])',
        lambda m: m.group(1) + m.group(2).upper(),
        corrected
    )

    changes = len(matches)
    return corrected, changes

@app.route('/', methods=['GET', 'POST'])
def index():
    corrected = ""
    original  = ""
    error     = ""
    changes   = 0
    mode      = "standard"

    if request.method == 'POST':
        original = request.form.get('text', '').strip()
        mode     = request.form.get('mode', 'standard')
        if original:
            try:
                corrected, changes = correct_text(original, mode)
            except Exception as e:
                error = "Could not connect to grammar service. Please check your internet connection and try again."

    return render_template('index.html',
                           corrected=corrected,
                           original=original,
                           error=error,
                           changes=changes,
                           mode=mode)

if __name__ == '__main__':
    app.run(debug=True)