from flask import jsonify
from flask import Flask, request, send_from_directory, send_file
import spacy
from dateparser import parse
from nltk import word_tokenize, ngrams
import nltk
import string
from nltk.stem import WordNetLemmatizer
from gensim.models import KeyedVectors
import random
import pdfrw
from nameparser import HumanName
wordnet_lemmatizer = WordNetLemmatizer()


app = Flask(__name__, static_url_path='/documents')
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

# print('Loading model...')
# model = KeyedVectors.load_word2vec_format('./crawl-300d-2M.vec')
# print('Model loaded.')


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


@app.route('/date', methods=['POST'])
def parse_date():
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
            return jsonify({"status": str(1), "date": str(parse(str(date))).split(' ')[0]})
        else:
            return jsonify({"status": str(-1)})

    except Exception as e:
        return e


@app.route('/get_document', methods=['POST'])
def get_document():
    try:
        content = request.json
        claimant_name = content['claimant_name']

        name = HumanName(claimant_name)

        claimant_first_name = name.first
        claimant_last_name = name.last

        claimant_dispute_arguments = content['dispute_argument']

        fill_in_values = {
            'claimant2[first]': claimant_first_name,
            'claimant2[last]': claimant_last_name,
            'iDispute8': claimant_dispute_arguments,
            'claimNo5': random.randint(1, 10000000000)
        }


        ANNOT_KEY = '/Annots'
        ANNOT_FIELD_KEY = '/T'
        ANNOT_VAL_KEY = '/V'
        ANNOT_RECT_KEY = '/Rect'
        SUBTYPE_KEY = '/Subtype'
        WIDGET_SUBTYPE_KEY = '/Widget'

        template_pdf = pdfrw.PdfReader('./defence-form.pdf')
        annotations = template_pdf.pages[0][ANNOT_KEY]
        for annotation in annotations:
            if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                if annotation[ANNOT_FIELD_KEY]:
                    key = annotation[ANNOT_FIELD_KEY][1:-1]
                    if key in fill_in_values:
                        annotation.update(
                            pdfrw.PdfDict(V='{}'.format(fill_in_values[key]))
                            )

        filename = './documents/' + str(fill_in_values['claimNo5']) + '.pdf'

        pdfrw.PdfWriter().write(filename,  template_pdf)

        return '/document/' + str(fill_in_values['claimNo5']) + '.pdf'

    except Exception as e:
        return e


@app.route('/document/<int:document_id>.pdf', methods=['GET'])
def document(document_id):
    print('ehrhehrehrhe')
    document_id = str(document_id)
    print()
    return send_from_directory('./documents', document_id + '.pdf', )


if __name__ == '__main__':
    app.run(debug=True)