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


class ClassifierSignature(dspy.Signature):
    """Predicts if an arXiv paper is about a language model."""

    title = dspy.InputField(desc="The title of an arXiv paper.")
    abstract = dspy.InputField(desc="The abstract of an arXiv paper.")
    is_lm_paper = dspy.OutputField(desc="Prediction if the paper is about a language model. This answer should be only 'yes' or 'no'.")

class ClassifierLM(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(ClassifierSignature)

    def forward(self, title, abstract):
        return self.cot(title=title, abstract=abstract)


class ArchitectureSignature(dspy.Signature):
    """Predicts the architecture of the language model discussed in an arXiv paper."""

    title = dspy.InputField(desc="The title of an arXiv paper.")
    abstract = dspy.InputField(desc="The abstract of an arXiv paper.")
    architecture = dspy.OutputField(desc="The architecture of the language model discussed in the paper. You answer should only consider the options available in the context. If more than one architecture needs to be listed, separate them with commas.")

class ArchitectureLM(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(ArchitectureSignature)

    def forward(self, title, abstract):
        return self.cot(title=title, abstract=abstract)


def get_LM(model='gpt-3.5-turbo-instruct', trainset = None, valset = None, pipeline = None):
    lm = dspy.OpenAI(model=model)
    dspy.settings.configure(lm=lm)
    
    tp = LabeledFewShot(k=5)
    # tp = BootstrapFewShotWithRandomSearch(metric=answer_exact_match)
    dataset = [dspy.Example(x).with_inputs('title', 'abstract') for x in trainset.to_dict(orient='records')]
    bootstrap = tp.compile(pipeline(), trainset=dataset)#, valset=valset)
    return bootstrap

def main():
    ...

if __name__ == "__main__":
    main()