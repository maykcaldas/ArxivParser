import os
from typing import Tuple, Any, List
from dataclasses import dataclass
import cloudpickle
import glob

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

import matplotlib.pyplot as plt
import urllib.request
import matplotlib as mpl
import matplotlib.font_manager as font_manager
import seaborn as sns

urllib.request.urlretrieve('https://github.com/google/fonts/raw/main/ofl/ibmplexmono/IBMPlexMono-Regular.ttf', 'IBMPlexMono-Regular.ttf')
fe = font_manager.FontEntry(
    fname='IBMPlexMono-Regular.ttf',
    name='plexmono')
font_manager.fontManager.ttflist.append(fe)
plt.rcParams.update({'axes.facecolor':'#f5f4e9',
            'grid.color' : '#AAAAAA',
            'axes.edgecolor':'#333333',
            'figure.facecolor':'#FFFFFF',
            'axes.grid': False,
            'axes.prop_cycle':   plt.cycler('color', plt.cm.Dark2.colors),
            'font.family': fe.name,
            'figure.figsize': (3.5,3.5 / 1.2),
            'ytick.left': True,
            'xtick.bottom': True
           })


@dataclass
class Experiment:
  model: str
  classifier: Tuple[str, str]
  bootstrap: Any

class Result:
  def __init__(self, exp: Experiment, results: Any, cm:List[List[int]], accuracy: float, precision: float, recall: float, f1: float):
    self.exp = exp
    self.results = results
    self.cm = cm
    self.accuracy = accuracy
    self.precision = precision
    self.recall = recall
    self.f1 = f1

  def __str__(self):
    return f"Result:\n\tModel: {self.exp.model} - {self.exp.classifier}\n\t{self.cm}\n\tAccuracy: {self.accuracy}\n\tPrecision: {self.precision}\n\tRecall: {self.recall}\n\tF1: {self.f1}"


experiments = [
  # Experiment(
  #   model="gpt-4o", 
  #   classifier="chain-of-thought-classifier",
  #   bootstrap=True
  # ),
  # Experiment(
  #   model="gpt-4o-mini", 
  #   classifier="chain-of-thought-classifier",
  #   bootstrap=True
  # ),
  # Experiment(
  #   model="gpt-4-0125-preview", 
  #   classifier="chain-of-thought-classifier",
  #   bootstrap=True
  # ),
  # Experiment(
  #   model="gpt-3.5-turbo-0125", 
  #   classifier="vanilla-classifier",
  #   bootstrap=True
  # ),
  # Experiment(
  #   model="gpt-3.5-turbo-instruct", 
  #   classifier="vanilla-classifier",
  #   bootstrap=True
  # ),
  Experiment(
    model="meta-llama/Meta-Llama-3-8B-Instruct-Lite", 
    classifier="vanilla-classifier",
    bootstrap=True
  ),
  Experiment(
    model="meta-llama/Llama-2-7b-hf", 
    classifier="vanilla-classifier",
    bootstrap=True
  ),
  Experiment(
    model="mistralai/Mistral-7B-v0.1", 
    classifier="vanilla-classifier",
    bootstrap=True
  ),
  Experiment(
    model="mistralai/Mistral-7B-Instruct-v0.2", 
    classifier="vanilla-classifier",
    bootstrap=True
  ),
]

def run_experiment(exp: Experiment, data: pd.DataFrame, n_replicates: int = 1):
    model, classifier = exp.model, exp.classifier
    if exp.bootstrap:
      train_data = data.sample(frac=0.30)
      test_data = data.drop(train_data.index)
    else:
      train_data = None
      test_data = data
    
    replicates = []
    for n in range(n_replicates):
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
            "is_sci_lm": is_sci_lm(title=p.title, abstract=p.abstract).answer.lower(),
            "is_lm_lm": is_lm_lm(title=p.title, abstract=p.abstract).answer.lower()
          }
      replicates.append(results)
        # if i>2: break
    return replicates


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


def plot_results(results: List[Result]):
  models_list = []
  prompt_list = []
  accuracy_list = []
  for i, result in enumerate(results):
    models_list.append(result.exp.model)
    prompt_list.append(result.exp.classifier)
    accuracy_list.append(result.accuracy)

  data = {
      'Model': models_list,
      'Prompt scheme': prompt_list,
      'Accuracy': accuracy_list,
  }

  df = pd.DataFrame(data)
  print(df)

  plt.figure(figsize=(12, 8))
  sns.barplot(x='Prompt scheme', y='Accuracy', hue='Model', data=df)
  # plt.title('Model Accuracy by Prompt Scheme')
  plt.xlabel('Prompt Scheme')
  plt.ylabel('Accuracy')
  plt.legend(title='Model', bbox_to_anchor=(0.5, 1.1), loc='upper center', ncol=5)
  plt.xticks(rotation=0)
  plt.tight_layout()
  plt.show()


def process_results(results_path: str = "."):
  all_results = []
  for result in glob.glob(f"{results_path}/results*.pkl"):
    res = cloudpickle.load(open(result, "rb"))
    for i, r in res.items():
      all_results.append(r)

  results_list = []
  for result in all_results:
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
    result = Result(
      exp=exp,
      results=results,
      cm=cm,
      accuracy=(cm[0,0]+cm[1,1])/cm.sum(),
      precision=cm[1,1]/(cm[1,1]+cm[0,1]),
      recall=cm[1,1]/(cm[1,1]+cm[1,0]),
      f1=2*cm[1,1]/(2*cm[1,1]+cm[1,0]+cm[0,1]),
      )
    
    print(result)
    results_list.append(result)

  return results_list


def main():
  # all_results = run_experiments(experiments, "results_vanilla_bootstrap_together.pkl")
  results_list = process_results()
  plot_results(results_list)


if __name__ == "__main__":
  main()

