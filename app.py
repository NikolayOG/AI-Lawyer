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
# DISABILITY = 'DISABILITY'
# ILLNESS = 'ILLNESS'
# DEATH = 'DEATH'
# CHILDREN = 'CHILDREN'

# seed words for the word2vec model
# REASONS = {
#     'disability': DISABILITY,
#     'deaf': DISABILITY,
#     'disabled': DISABILITY,
#     'illness': ILLNESS,
#     'stroke': ILLNESS,
#     'heart': ILLNESS,
#     'disease': ILLNESS,
#     'ill': ILLNESS,
#     'depression': ILLNESS,
#     'depress': ILLNESS,
#     'injury': ILLNESS,
#     'die': DEATH,
#     'death' : DEATH,
#     'deceased' : DEATH,
#     'kid': CHILDREN,
#     'youngster': CHILDREN,
#     'children': CHILDREN,
#     'offspring': CHILDREN,
# }

# print('Loading model...')
# model = KeyedVectors.load_word2vec_format('./wiki.simple.vec')
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


# @app.route('/reasons', methods=['POST'])
# def extract_reasons():
#     global model
#
#     try:
#         content = request.json
#         text_reasons = content['text_reasons']
#
#         word_tokens = word_tokenize(clean_text(text_reasons))
#
#         word_stemmed = [str(wordnet_lemmatizer.lemmatize(w)) for w in word_tokens]
#
#         reason = None
#         reasonslist = set([])
#
#         for w in word_stemmed:
#             for r in REASONS:
#                 try:
#                     if model.similarity(w, r) > 0.35:
#                         reasonslist.add(REASONS[r])
#                         reason = True
#                 except Exception as e:
#                     continue
#
#         if reason:
#             return jsonify({"status": str(1), "reasons": list(reasonslist)})
#         else:
#             return jsonify({"status": str(-1)})
#
#     except Exception as e:
#         return e


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


@app.route('/notice', methods=['POST'])
def extract_details_from_notice():
    try:
        return jsonify({
            "status": str(1),
            "name": "Deborah Smith",
            "address": "11A Upper W. Grove, M13 0BB, Manchester, England",
            "date_issued": '10/03/2019'

        })
    except Exception as e:
        return e


@app.route('/document/<int:document_id>.pdf', methods=['GET'])
def document(document_id):
    document_id = str(document_id)
    return send_from_directory('./documents', document_id + '.pdf', )


if __name__ == '__main__':
    app.run(debug=True)