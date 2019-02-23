from flask import jsonify
from flask import Flask, request
import spacy
from dateparser import parse
from nltk import word_tokenize, ngrams
import nltk
import string
from nltk.stem import WordNetLemmatizer
from gensim.models import KeyedVectors
wordnet_lemmatizer = WordNetLemmatizer()


app = Flask(__name__)
spacy_nlp = spacy.load('en')

# topics
DISABILITY = 'DISABILITY'
ILLNESS = 'ILLNESS'
DEATH = 'DEATH'
CHILDREN = 'CHILDREN'

# seed words
REASONS = {
    'disability': DISABILITY,
    'disabled': DISABILITY,
    'illness': ILLNESS,
    'stroke': ILLNESS,
    'heart': ILLNESS,
    'disease': ILLNESS,
    'ill': ILLNESS,
    'injury': ILLNESS,
    'die': DEATH,
    'death' : DEATH,
    'deceased' : DEATH,
    'kid': CHILDREN,
    'youngster': CHILDREN,
    'children': CHILDREN
}

print('Loading model...')
model = KeyedVectors.load_word2vec_format('./crawl-300d-2M.vec')
print('Model loaded.')


def clean_text(text):
    fix_text = ''
    for c in text.strip().lower():
        if c in ['?', '.', ","]:
            fix_text += ' ' + c + ' '
        elif c in string.ascii_letters or c in list(map(str, list(range(10)))):
            fix_text += c
        else:
            fix_text += ' '

    return fix_text


@app.route('/reasons', methods=['POST'])
def extract_reasons():
    global model

    try:
        content = request.json
        text_reasons = content['text_reasons']

        word_tokens = word_tokenize(clean_text(text_reasons))

        word_stemmed = [str(wordnet_lemmatizer.lemmatize(w)) for w in word_tokens]

        reason = None
        reasonslist = []

        for w in word_stemmed:
            for r in REASONS:
                if model.similarity(w, r) > 0.35:
                    reasonslist.append(REASONS[r])
                    reason = True

                    # print('Reason', reasonslist[r])
        if reason:
            return jsonify({"status": str(1), "reasons": reasonslist})
        else:
            return jsonify({"status": str(-1)})



    except Exception as e:
        return e


@app.route('/address', methods=['POST'])
def parse_address():
    try:
        content = request.json
        text_date = content['text_date']

        if 'text_date' not in content:
            return jsonify({"status": str(-1)})

        document = spacy_nlp(text_date)

        date = None

        for element in document.ents:
            if str(element.label_) == 'DATE':
                date = str(element)

        # sometimes it fixes the date extraction
        if not date:
            text_date = 'a ' + text_date

            document = spacy_nlp(text_date)

            for element in document.ents:
                if str(element.label_) == 'DATE':
                    date = str(element)

        if date:
            return jsonify({"status": str(1), "date": str(parse(str(date)))})
        else:
            return jsonify({"status": str(-1)})

    except Exception as e:
        return e


if __name__ == '__main__':
    app.run(debug=True)
