import os
from typing import Tuple, Any, List
from dataclasses import dataclass
import cloudpickle

from dotenv import load_dotenv
load_dotenv()
os.environ["DSP_CACHEBOOL"] = 'False'

import dspy
import pandas as pd
from sklearn.metrics import confusion_matrix

import sys
sys.path.append("../arxivParser")

from notion_utils import get_all_curated_pages, get_all_non_curated_pages, delete_page
from lm_utils import get_LM
from sql_utils import get_session, create_new_paper, get_all_papers

@dataclass
class Experiment:
  model: str
  classifier: Tuple[str, str]
  bootstrap: Any

experiments = [
  Experiment(
    model="gpt-4o", 
    classifier="chain-of-thought-classifier",
    bootstrap=False
  ),
  Experiment(
    model="gpt-4o-mini", 
    classifier="chain-of-thought-classifier",
    bootstrap=False
  ),
  Experiment(
    model="gpt-4-0125-preview", 
    classifier="chain-of-thought-classifier",
    bootstrap=False
  ),
  Experiment(
    model="gpt-3.5-turbo-0125", 
    classifier="chain-of-thought-classifier",
    bootstrap=False
  ),
  Experiment(
    model="gpt-3.5-turbo-instruct", 
    classifier="chain-of-thought-classifier",
    bootstrap=False
  ),
]

def run_experiment(exp: Experiment, data: pd.DataFrame):
    model, classifier = exp.model, exp.classifier
    if exp.bootstrap:
      train_data = data.sample(frac=0.30)
      test_data = data.drop(train_data.index)
    else:
      train_data = None
      test_data = data
    
    results = {}
    lm, is_sci_lm = get_LM(model=model, pipeline=(classifier, "scientific"), data=train_data)
    lm, is_lm_lm  = get_LM(model=model, pipeline=(classifier, "lm"), data=train_data)
    for i, p in test_data.iterrows():
      keywords = ["chemistry", "chemical", "material", "synthesis", "reaction", "biology", "protein", "gene", "genoma"]
      is_sci_kw = any([word in p.abstract.lower() for word in keywords])
      with dspy.context(lm=lm):
        results[i] = {
          "paper": p,
          "is_sci_kw": 'yes' if is_sci_kw else 'no',
          "is_sci_lm": is_sci_lm(title=p.title, abstract=p.abstract).is_sci_paper.lower(),
          "is_lm_lm": is_lm_lm(title=p.title, abstract=p.abstract).is_lm_paper.lower()
        }
    return results


def run_experiments(experiments: List[Experiment], save_path: str):
  with get_session() as db_session:
    data = get_all_papers(db_session)
  
  dois = [x.doi for x in data]
  titles = [x.title for x in data]
  abstracts = [x.abstract for x in data]
  labels = ["yes" if x.is_sci_llm else "no" for x in data]

  data_df = pd.DataFrame({'doi': dois, 'title': titles, 'abstract': abstracts, 'is_sci_llm': labels})
  print(f"Retrieved {len(data_df)} pages from the database for training")

  all_results = {}
  for ndx, exp in enumerate(experiments):
    result = run_experiment(exp, data_df)
    all_results[ndx] = {"exp": exp, "results": result}
  cloudpickle.dump(all_results, open(save_path, "wb"))
  return all_results


def process_results(results_path: str):
  all_results = cloudpickle.load(open(results_path, "rb"))
  
  for i, result in all_results.items():
    exp = result["exp"]
    print(exp.model, exp.classifier)
    results = result["results"]
    y, pred = [], []
    for i, r in results.items():
      pred.append(
        all([True if x=="yes" else False for x in [r['is_sci_kw'], r['is_sci_lm'], r['is_lm_lm']]])
      )
      y.append(True if r['paper'].is_sci_llm=="yes" else False)
    cm = confusion_matrix(y, pred)
    print(cm)
    print("Accuracy:", (cm[0,0]+cm[1,1])/cm.sum())
    print("Precision:", cm[1,1]/(cm[1,1]+cm[0,1]))
    print("Recall:", cm[1,1]/(cm[1,1]+cm[1,0]))
    print("F1:", 2*cm[1,1]/(2*cm[1,1]+cm[1,0]+cm[0,1]))
    print()
    

def main():
  r = run_experiments(experiments, "results_CoT.pkl")
  # print(r)
  process_results("results_CoT.pkl")


if __name__ == "__main__":
  main()

