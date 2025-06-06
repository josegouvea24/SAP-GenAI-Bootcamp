from typing import Literal, Type, Union, Dict, Any, List, Callable
import re, pathlib, json, time
from functools import partial
EXAMPLE_MESSAGE_IDX = 10

import pathlib
import yaml

from gen_ai_hub.proxy import get_proxy_client
from ai_api_client_sdk.models.status import Status

from gen_ai_hub.orchestration.models.config import OrchestrationConfig
from gen_ai_hub.orchestration.models.llm import LLM
from gen_ai_hub.orchestration.models.message import SystemMessage, UserMessage
from gen_ai_hub.orchestration.models.template import Template, TemplateValue
from gen_ai_hub.orchestration.models.azure_content_filter import AzureContentFilter
from gen_ai_hub.orchestration.service import OrchestrationService

from typing import Callable

from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.models.status import Status
import time
from IPython.display import clear_output


def spinner(check_callback: Callable, timeout: int = 300, check_every_n_seconds: int = 10):
    start = time.time()
    last_check = start
    while time.time() - start < timeout:
        now = time.time()
        if now - start > timeout:
            break
        if now - last_check > check_every_n_seconds:
            return_value = check_callback()
            if return_value:
                return return_value
        for char in '|/-\\':
            clear_output(wait=True)  # Clears the output to show a fresh update
            print(f'Waiting for the deployment to become ready... {char}')
            time.sleep(0.2)  # Adjust the speed as needed


def retrieve_or_deploy_orchestration(ai_core_client: AICoreV2Client,
                                     scenario_id: str = "orchestration",
                                     executable_id: str = "orchestration",
                                     config_suffix: str = "simple",
                                     start_timeout: int = 300):
    if not config_suffix:
        raise ValueError("Empty `config_suffix` not allowed")
    deployments = ai_core_client.deployment.query(
        scenario_id=scenario_id,
        executable_ids=[executable_id],
        status=Status.RUNNING
    )
    if deployments.count > 0:
        return sorted(deployments.resources, key=lambda x: x.start_time)[0]
    config_name = f"{config_suffix}-orchestration"
    configs = ai_core_client.configuration.query(
        scenario_id=scenario_id,
        executable_ids=[executable_id],
        search=config_name
    )
    if configs.count > 0:
        config = sorted(deployments.resources, key=lambda x: x.start_time)[0]
    else:
        config = ai_core_client.configuration.create(
            scenario_id=scenario_id,
            executable_id=executable_id,
            name=config_name,
        )
    deployment = ai_core_client.deployment.create(configuration_id=config.id)

    def check_ready():
        updated_deployment = ai_core_client.deployment.get(deployment.id)
        return None if updated_deployment.status != Status.RUNNING else updated_deployment
    
    return spinner(check_ready)

from tqdm.auto import tqdm
import time

class RateLimitedIterator:
    def __init__(self, iterable, max_iterations_per_minute):
        self._iterable = iter(iterable)
        self._max_iterations_per_minute = max_iterations_per_minute
        self._min_interval = 1.0 / (max_iterations_per_minute / 60.)
        self._last_yield_time = None

    def __iter__(self):
        return self

    def __next__(self):
        current_time = time.time()

        if self._last_yield_time is not None:
            elapsed_time = current_time - self._last_yield_time
            if elapsed_time < self._min_interval:
                time.sleep(self._min_interval - elapsed_time)

        self._last_yield_time = time.time()
        return next(self._iterable)

def evaluation(mail: Dict[str, str], extract_func: Callable, _print=True, **kwargs):
    response = extract_func(input=mail["message"], _print=_print, **kwargs)
    result = {
        "is_valid_json": False,
        "correct_categories": False,
        "correct_sentiment": False,
        "correct_urgency": False,
    }
    try:
        pred = json.loads(response)
    except json.JSONDecodeError:
        result["is_valid_json"] = False
    else:
        result["is_valid_json"] = True
        result["correct_categories"] = 1 - (len(set(mail["ground_truth"]["categories"]) ^ set(pred["categories"])) / len(categories))
        result["correct_sentiment"] = pred["sentiment"] == mail["ground_truth"]["sentiment"]
        result["correct_urgency"] = pred["urgency"] == mail["ground_truth"]["urgency"]
    return result
                                         
from tqdm.auto import tqdm

def transpose_list_of_dicts(list_of_dicts):
    keys = list_of_dicts[0].keys()
    transposed_dict = {key: [] for key in keys}
    for d in list_of_dicts:
        for key, value in d.items():
            transposed_dict[key].append(value)
    return transposed_dict
    
def evalulation_full_dataset(dataset, func, rate_limit=100, _print=False, **kwargs):
    results = [evaluation(mail, func, _print=_print, **kwargs) for mail in tqdm(RateLimitedIterator(dataset, rate_limit), total=len(dataset))]
    results = transpose_list_of_dicts(results)
    n = len(dataset)
    for k, v in results.items():
        results[k] = sum(v) / len(dataset)
    return results

client = get_proxy_client()
deployment = retrieve_or_deploy_orchestration(client.ai_core_client)
orchestration_service = OrchestrationService(api_url=deployment.deployment_url, proxy_client=client)

def pretty_print_table(data):
    # Get all row names (outer dict keys)
    row_names = list(data.keys())

    # Get all column names (inner dict keys)
    if row_names:
        column_names = list(data[row_names[0]].keys())
    else:
        column_names = []

    # Calculate column widths
    column_widths = [max(len(str(column_name)), max(len(f"{data[row][column_name]:.2f}") for row in row_names)) for column_name in column_names]
    row_name_width = max(len(str(row_name)) for row_name in row_names)

    # Print header
    header = f"{'':>{row_name_width}} " + " ".join([f"{column_name:>{width}}" for column_name, width in zip(column_names, column_widths)])
    print(header)
    print("=" * len(header))

    # Print rows
    for row_name in row_names:
        row = f"{row_name:>{row_name_width}} " + " ".join([f"{data[row_name][column_name]:>{width}.1%}" for column_name, width in zip(column_names, column_widths)])
        print(row)

overall_result = {}

def send_request(prompt, _print=True, _model='gemini-1.5-flash', **kwargs):
    config = OrchestrationConfig(
        llm=LLM(name=_model),
        template=Template(messages=[UserMessage(prompt)])
    )
    template_values = [TemplateValue(name=key, value=value) for key, value in kwargs.items()]
    answer = orchestration_service.run(config=config, template_values=template_values)
    result = answer.module_results.llm.choices[0].message.content
    if _print:
        formatted_prompt = answer.module_results.templating[0].content
        print(f"<-- PROMPT --->\n{formatted_prompt if _print else prompt}\n<--- RESPONSE --->\n{result}")   
    return result

HERE = pathlib.Path.cwd()

with (HERE / 'filtered_mails-hardest.jsonl').open() as stream:
    mails = [json.loads(line) for line in stream if line.strip()]

dev_set, test_set = mails[:int(len(mails)/2)], mails[int(len(mails)/2):]
test_set_small = test_set[:20]

categories = set()
urgency = set()
sentiment = set()
for mail in mails:
    categories = categories.union(set(mail['ground_truth']['categories']))
    urgency.add(mail['ground_truth']['urgency'])
    sentiment.add(mail['ground_truth']['sentiment'])

option_lists = {
    'urgency': ', '.join(f"`{entry}`" for entry in urgency),
    'sentiment': ', '.join(f"`{entry}`" for entry in sentiment),
    'categories': ', '.join(f"`{entry}`" for entry in categories),
}

print(option_lists)

mail = dev_set[EXAMPLE_MESSAGE_IDX]

import random
random.seed(42)

k = 3
examples = random.sample(dev_set, k)

example_template = """<example>
{example_input}

## Output

{example_output}
</example>"""

examples = '\n---\n'.join([example_template.format(example_input=example["message"], example_output=json.dumps(example["ground_truth"])) for example in examples])

example_template_metaprompt = """<example>
{example_input}

## Output
{key}={example_output}
</example>"""

prompt_get_guide = """Here are some example:
---
{{?examples}}
---
Use the examples above to come up with a guide on how to distinguish between {{?options}} {{?key}}.
Use the following format:
```
### **<category 1>**
- <instruction 1>
- <instruction 2>
- <instruction 3>
### **<category 2>**
- <instruction 1>
- <instruction 2>
- <instruction 3>
...
```
When creating the guide:
- make it step-by-step instructions
- Consider than some labels in the examples might be in correct
- Avoid including explicit information from the examples in the guide
The guide has to cover: {{?options}}
"""

guides = {}

for i, key in enumerate(["categories", "urgency", "sentiment"]):
    options = option_lists[key]
    selected_examples_txt_metaprompt = '\n---\n'.join([example_template_metaprompt.format(example_input=example["message"], key=key, example_output=example["ground_truth"][key]) for example in dev_set])
    guides[f"guide_{key}"] = send_request(prompt=prompt_get_guide, examples=selected_examples_txt_metaprompt, key=key, options=options, _print=False, _model='gpt-4o')

print(guides['guide_urgency'])

prompt_13 = """Your task is to classify messages.
Here are some examples:
---
{{?few_shot_examples}}
---
This is an explanation of `urgency` labels:
---
{{?guide_urgency}}
---
This is an explanation of `sentiment` labels:
---
{{?guide_sentiment}}
---
This is an explanation of `support` categories:
---
{{?guide_categories}}
---
Giving the following message:
---
{{?input}}
---
extract and return a json with the follwoing keys and values:
- "urgency" as one of {{?urgency}}
- "sentiment" as one of {{?sentiment}}
- "categories" list of the best matching support category tags from: {{?categories}}
Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.
"""

f_13 = partial(send_request, prompt=prompt_13, **option_lists, few_shot_examples=examples, **guides)

response = f_13(input=mail["message"])

overall_result["metaprompting_and_few_shot--gemini-1.5-flash"] = evalulation_full_dataset(test_set_small, f_13, _model='gemini-1.5-flash')
pretty_print_table(overall_result) 
