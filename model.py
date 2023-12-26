import pickle
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from dto import Prediction, PredictionRequest

stopwordFactory = StopWordRemoverFactory()
stopwords = stopwordFactory.get_stop_words()
stemmerFactory = StemmerFactory()
stemmer = stemmerFactory.create_stemmer()
filename = "svm_model.sav"
loaded_model = pickle.load(open(filename, "rb"))


def regexOperation(text):
    # Remove Non-ascii
    res = re.sub(r"[^\x00-\x7F]+", " ", text)

    # Remove url
    res = re.sub(r"http[s]?\:\/\/.[a-zA-Z0-9\.\/\_?=%&#\-\+!]+", " ", res)
    res = re.sub(r"pic.twitter.com?.[a-zA-Z0-9\.\/\_?=%&#\-\+!]+", " ", res)
    # Remove mention
    res = re.sub(r"\@([\w]+)", " ", res)

    # Remove hashtag
    # res = re.sub(r'\#([\w]+)',' ', res)
    # Proccessing hashtag (split camel case)
    res = re.sub(r"((?<=[a-z])[A-Z]|[A-Z](?=[a-z]))", " \\1", res)
    # res = re.sub(r'([A-Z])(?<=[a-z]\1|[A-Za-z]\1(?=[a-z]))',' \\1', res)

    # Remove special character
    res = re.sub(r'[!$%^&*@#()_+|~=`{}\[\]%\-:";\'<>?,.\/]', " ", res)
    # Remove number
    res = re.sub(r"[0-9]+", "", res)
    # Remove consecutive alphabetic characters
    res = re.sub(r"([a-zA-Z])\1\1", "\\1", res)
    # Remove consecutive whitespace
    res = re.sub(" +", " ", res)
    # Remove trailing and leading whitespace
    res = re.sub(r"^[ ]|[ ]$", "", res)

    # Convert to lower case
    res = res.lower()

    return res


def tokenize(text):
    return text.split()


def remove_stopwords(text):
    return [word for word in text if word not in stopwords]


def stemming(text):
    return [stemmer.stem(word) for word in text]


def preprocess(text):
    text = regexOperation(text)
    text = tokenize(text)
    text = remove_stopwords(text)
    text = stemming(text)
    text = " ".join(text)
    return text

def predict_service(request: PredictionRequest) -> Prediction:
    text = request.text
    text = preprocess(text)

    prediction = loaded_model.predict([text])
    score = loaded_model.predict_proba([text])

    prediction_str = "Positif" if prediction[0] == 1 else "Negatif"

    return Prediction(
        prediction=prediction,
        predictionStr=prediction_str,
        score=score[0],
        text=request.text,
        time=request.time,
    )
