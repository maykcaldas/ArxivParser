import dspy
from dspy.datasets.hotpotqa import HotPotQA
from dspy.teleprompt import (
    LabeledFewShot,
    BootstrapFewShotWithRandomSearch,
    BootstrapFinetune,
    Ensemble
)
from dspy.evaluate import Evaluate
from dspy.evaluate import answer_exact_match

import pandas as pd
from notion_utils import get_all_curated_pages


class PaperClassifierSignature(dspy.Signature):
    """Predicts if an arXiv paper is about a language model."""

    title = dspy.InputField(desc="The title of an arXiv paper.")
    abstract = dspy.InputField(desc="The abstract of an arXiv paper.")
    is_lm_paper = dspy.OutputField(desc="Prediction if the paper is about a language model. This answer should be only 'yes' or 'no'.")

class ScientificClassifierSignature(dspy.Signature):
    """Predicts if an arXiv paper is about science."""

    title = dspy.InputField(desc="The title of an arXiv paper.")
    abstract = dspy.InputField(desc="The abstract of an arXiv paper.")
    is_sci_paper = dspy.OutputField(desc="Prediction if the paper is about science. This answer should be only 'yes' or 'no'.")

class ClassifierLM(dspy.Module):
    def __init__(self, signature=PaperClassifierSignature):
        super().__init__()
        self.pred = dspy.Predict(signature)

    def forward(self, title, abstract):
        return self.pred(title=title, abstract=abstract)

class ClassifierCOTLM(dspy.Module):
    def __init__(self, signature=PaperClassifierSignature):
        super().__init__()
        self.cot = dspy.ChainOfThought(signature)

    def forward(self, title, abstract):
        return self.cot(title=title, abstract=abstract)

#TODO: Should I use retrieval here? All examples in the context would be positive examples.

class ArchitectureSignature(dspy.Signature):
    """Predicts the architecture of the language model discussed in an arXiv paper."""

    title = dspy.InputField(desc="The title of an arXiv paper.")
    abstract = dspy.InputField(desc="The abstract of an arXiv paper.")
    architecture = dspy.OutputField(desc="The architecture of the language model discussed in the paper. You answer should only consider the options available in the context. If more than one architecture needs to be listed, separate them with commas.")

class ArchitectureLM(dspy.Module):
    def __init__(self, signature=ArchitectureSignature):
        super().__init__()
        self.cot = dspy.ChainOfThought(ArchitectureSignature)

    def forward(self, title, abstract):
        return self.cot(title=title, abstract=abstract)

def get_LM(model='gpt-4o', pipeline = None, classifier=None, signature=None, data=None, build_db = False):
    if not any([pipeline, classifier, signature]):
        raise ValueError("At least one of pipeline, or classifier and signature should be specified.")
    
    if pipeline:
        if classifier or signature:
            raise ValueError("If pipeline is specified, classifier and signature should not be.")
        
        classifier = pipeline[0]
        signature = pipeline[1]
    
    classifiers = {
        "vanilla-classifier": ClassifierLM,
        "chain-of-thought-classifier": ClassifierCOTLM
    }

    if classifier not in classifiers:
        raise ValueError(f"Classifier {classifier} not found. Available classifiers: {classifiers.keys()}")

    signatures={
        'scientific': ScientificClassifierSignature,
        'lm': PaperClassifierSignature,
        # 'architecture': (ArchitectureLM, None)
    }

    if signature not in signatures:
        raise ValueError(f"Signature {signature} not found. Available signatures: {signatures.keys()}")
    
    lm = dspy.OpenAI(model=model, temperature=2.0)
    #lm = dspy.Together(model=model)
    # dspy.settings.configure(lm=lm)
    classifier, signature = classifiers[classifier], signatures[signature]

    if data:
        dataset = [dspy.Example(x).with_inputs('title', 'abstract') for x in data.to_dict(orient='records')]

        # tp = LabeledFewShot(k=5)
        tp = BootstrapFewShotWithRandomSearch(metric=answer_exact_match)
        bootstrap = tp.compile(classifier(signature), 
                               trainset=dataset[:int(0.8*len(dataset))], 
                               valset=dataset[int(0.8*len(dataset)):]
                               )
        module = bootstrap
    else:
        module =  classifier(signature)

    return lm, module
    

def main():
    ...

if __name__ == "__main__":
    main()