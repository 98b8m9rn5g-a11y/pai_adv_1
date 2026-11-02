"""Small supervised text classifier. Training and inference stay on the CPU."""
import json
from importlib.resources import files

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline


def load_examples(name):
    return json.loads(files("pai_delivery").joinpath("data", name).read_text())


class IntentClassifier:
    def __init__(self, min_score=0.55, min_margin=0.15):
        train = load_examples("train.json")
        self.model = make_pipeline(
            TfidfVectorizer(analyzer="char", ngram_range=(1, 3), sublinear_tf=True),
            LogisticRegression(C=8.0, max_iter=1000, random_state=42),
        )
        self.model.fit([row[0] for row in train], [row[1] for row in train])
        self.min_score = min_score
        self.min_margin = min_margin

    def predict(self, text):
        probabilities = self.model.predict_proba([text])[0]
        indices = probabilities.argsort()[::-1]
        score = float(probabilities[indices[0]])
        margin = score - float(probabilities[indices[1]])
        label = str(self.model.classes_[indices[0]])
        # A closed-set classifier can be confident on unrelated text. Reject
        # inputs mostly outside the character vocabulary learned from training.
        chars = [char.lower() for char in text if char.isalnum()]
        vocabulary = self.model.steps[0][1].vocabulary_
        coverage = sum(char in vocabulary for char in chars) / len(chars) if chars else 0.0
        accepted = coverage >= 0.5 and score >= self.min_score and margin >= self.min_margin
        return {"label": label, "score": round(score, 4), "margin": round(margin, 4),
                "coverage": round(coverage, 4), "accepted": bool(accepted)}


def main():
    classifier = IntentClassifier()
    examples = load_examples("evaluation.json")
    rows = [{"text": text, "expected": label, **classifier.predict(text)} for text, label in examples]
    result = {
        "training_examples": len(load_examples("train.json")),
        "evaluation_examples": len(rows),
        "classification_correct": sum(row["label"] == row["expected"] for row in rows),
        "accepted_and_correct": sum(row["accepted"] and row["label"] == row["expected"] for row in rows),
        "results": rows,
        "out_of_scope_checks": [
            {"text": text, **classifier.predict(text)}
            for text in ["明日の天気を教えて", "空を飛んでください", "受付か倉庫のどちらか"]
        ],
        "limitations": "Small manually authored dataset; scores are uncalibrated; no general language understanding.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
