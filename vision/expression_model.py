"""map the face read to one of her expressions.

two ways, same as the rest of EchoSelf: a plain rule baseline that always works,
and an optional learned mapper (pytorch) you can calibrate on your OWN face so she
imitates the way YOU actually express things - that's the cloning. the baseline is
the floor; the learned one takes over once you've shown it a few of your faces."""

import importlib.util

from vision.features import FEATURES, to_vector

# her expressions, the only things we ever map to
LABELS = ["neutral", "happy", "patient", "thinking", "celebrating", "drift"]


def torch_available():
    return importlib.util.find_spec("torch") is not None


class BaselineMapper:
    # plain thresholds. rough on purpose - it's the floor, the learned mapper is
    # where it gets personal. tuned against the normalized features (eye-distance
    # units), to be refined live.

    def predict(self, feat):
        if feat["mouth_curve"] > 0.10 and feat["mouth_open"] > 0.25:
            return "celebrating"
        if feat["mouth_curve"] > 0.05:
            return "happy"
        if feat["eye_open"] < 0.15:
            return "drift"
        if feat["brow"] < -0.02:
            return "thinking"
        if feat["mouth_curve"] < -0.03:
            return "patient"
        return "neutral"


class LearnedMapper:
    # a tiny MLP from the face features to one of her expressions, trained by
    # behavioural cloning on your demonstrations. needs pytorch; if it's not here
    # or not trained yet, the Mirror just uses the baseline.

    def __init__(self):
        self.net     = None
        self.trained = False

    def fit(self, samples, epochs=300, seed=0):
        # samples: list of (feature_vector, label_name)
        import torch
        import torch.nn as nn
        torch.manual_seed(seed)
        xs = torch.tensor([v for v, _ in samples], dtype=torch.float32)
        ys = torch.tensor([LABELS.index(l) for _, l in samples], dtype=torch.long)
        self.net = nn.Sequential(nn.Linear(len(FEATURES), 16), nn.ReLU(),
                                 nn.Linear(16, len(LABELS)))
        opt  = torch.optim.Adam(self.net.parameters(), lr=0.05)
        loss = nn.CrossEntropyLoss()
        for _ in range(epochs):
            opt.zero_grad()
            out = self.net(xs)
            l   = loss(out, ys)
            l.backward()
            opt.step()
        self.trained = True
        return self

    def predict(self, vector):
        import torch
        with torch.no_grad():
            out = self.net(torch.tensor([vector], dtype=torch.float32))
            return LABELS[int(out.argmax(dim=1)[0])]


class Mirror:
    # the thing capture.py talks to: feed it a face read, get back an expression.
    # uses your trained model when there is one, else the baseline.

    def __init__(self):
        self.baseline = BaselineMapper()
        self.learned  = None

    def calibrate(self, demos):
        # demos: list of (feature_dict, label_name) - your own faces, labelled.
        # returns True if a model got trained, False if pytorch isn't here.
        if not torch_available():
            return False
        samples = [(to_vector(f), label) for f, label in demos]
        self.learned = LearnedMapper().fit(samples)
        return True

    def to_expression(self, feat):
        if self.learned is not None and self.learned.trained:
            return self.learned.predict(to_vector(feat))
        return self.baseline.predict(feat)
