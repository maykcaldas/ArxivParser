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

def get_LM(model='gpt-4o', data=None, pipeline = None, build_db = False):
    pipelines={
        'scientific-classifier': (ClassifierLM, ScientificClassifierSignature),
        'lm-classifier': (ClassifierLM, PaperClassifierSignature),
        'architecture': (ArchitectureLM, None)
    }

    if pipeline not in pipelines:
        raise ValueError(f"Pipeline {pipeline} not found. Available pipelines: {pipelines.keys()}")
    
    dataset = [dspy.Example(x).with_inputs('title', 'abstract') for x in data.to_dict(orient='records')]

    lm = dspy.OpenAI(model=model)
    module, signature = pipelines[pipeline]
    dspy.settings.configure(lm=lm)
    
    tp = LabeledFewShot(k=5)
    # tp = BootstrapFewShotWithRandomSearch(metric=answer_exact_match)
    bootstrap = tp.compile(module(signature), trainset=dataset)#, valset=valset)
    return bootstrap

def main():
    ...

if __name__ == "__main__":
    main()