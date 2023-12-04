"""
Module which does some encapsulation of the different models so that they have a:
1. a uniform return value of `SentimentValue`, which is a `tuple[SentimentLabel, float]`;
2. a uniform calling api for the different models, using `Model.process`.
"""

from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from transformers import pipeline
from germansentiment import SentimentModel
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from enum import Enum, auto
from typing import Callable

fr_tokenizer = AutoTokenizer.from_pretrained("tblard/tf-allocine")
fr_model_src = TFAutoModelForSequenceClassification.from_pretrained("tblard/tf-allocine")

fr_model = pipeline('sentiment-analysis', model=fr_model_src, tokenizer=fr_tokenizer)
de_model = SentimentModel()
ru_model = pipeline(model="seara/rubert-tiny2-russian-sentiment")
en_model = SentimentIntensityAnalyzer()

class SentimentLabel(Enum):
    pos = auto()
    neg = auto()
    neu = auto()

    def __str__(self):
        if self == self.pos:
            return 'pos'
        elif self == self.neg:
            return 'neg'
        elif self == self.neu:
            return 'neu'
        else:
            raise TypeError("Requires a sentiment label")

class SentimentValue:
    def __init__(self, label: SentimentLabel, value: float):
        if not isinstance(label, SentimentLabel):
            raise TypeError(f"Sentiment labels require a `Sentiment`")
        else:
            self.label = label
            self.value = value

    def __str__(self):
        return "{ label: " + str(self.label) + ", value: " + str(self.value) + "}"


class Model:
    """
    Polymorphic type which encapsulates modelling: it requires
    a way of transforming the output of the sentiment analysis to `SentimentValue`
    """
    def __init__(self, method):
        self.method = method

    def process(self, text: Callable[str, SentimentValue]) -> SentimentValue:
        return self.method(text)


def fr_process(x: str) -> SentimentValue:
    res = fr_model(x)[0]
    if res['label'] == 'POSITIVE':
        return SentimentValue(SentimentLabel.pos, res['score'])
    elif res['label'] == 'NEGATIVE':
        return SentimentValue(SentimentLabel.pos, res['score'])
    elif res['label'] == 'NEUTRAL':
        return SentimentValue(SentimentLabel.neu, res['score'])

def de_process(x: str) -> SentimentValue:
    classes, probs = de_model.predict_sentiment([x], output_probabilities=True)
    maxs = SentimentLabel.pos if classes[0] == "positive" else SentimentLabel.neg if classes[0] == "negative" else SentimentLabel.neu
    for xs in probs[0]:
        if xs[0] == classes[0]:
            return SentimentValue(maxs, xs[1])

def ru_process(x: str) -> SentimentValue:
    res = ru_model(x)[0]
    label = SentimentLabel.pos if res['label'] == 'positive' else SentimentLabel.neg if res['label'] == 'negative' else SentimentLabel.neu
    score = res['score']
    return SentimentValue(label, score)

def en_process(x: str) -> SentimentValue:
    res = en_model.polarity_scores(x)
    del res['compound']
    res_lbl = list(sorted(res))[-1]
    label = SentimentLabel.pos if res_lbl == 'pos' else SentimentLabel.neg if res_lbl == 'neg' else SentimentLabel.neu
    value = res[res_lbl]
    return SentimentValue(label, value)


fr = Model(fr_process)
"""
The French sentiment object
"""

de = Model(de_process)
"""
The German sentiment object
"""

ru = Model(ru_process)
"""
The Russian sentiment object
"""

en = Model(en_process)
"""
The English sentiment object
"""

# fr_test_sent = "Bonjour mon ami"
# gr_test_sent = "Hallo mein Freund"
# ru_test_sent = "Здравствуй мой друг"
# en_test_sent = "Hello my friend"

# print(fr.process(fr_test_sent))
# print(gr.process(gr_test_sent))
# print(ru.process(ru_test_sent))
# print(en.process(en_test_sent))