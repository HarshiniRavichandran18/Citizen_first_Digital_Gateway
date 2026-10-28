import pickle, pandas as pd
from pathlib import Path
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
HERE = Path(__file__).parent
# char n-grams cope with Tamil morphology and Tanglish spelling variation
def pipe(): return make_pipeline(TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5)), LogisticRegression(max_iter=1000, C=10))
def train():
    df = pd.read_csv(HERE / 'intent_data.csv'); m = pipe().fit(df.text, df.label)
    pickle.dump(m, open(HERE / 'intent_model.pkl', 'wb')); return m
if __name__ == '__main__':
    df = pd.read_csv(HERE / 'intent_data.csv')
    pred = cross_val_predict(pipe(), df.text, df.label, cv=StratifiedKFold(5, shuffle=True, random_state=1))
    print('5-fold CV accuracy:', round(accuracy_score(df.label, pred), 3))
    print(classification_report(df.label, pred)); print(confusion_matrix(df.label, pred)); train()
