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

client = get_proxy_client()
deployment = retrieve_or_deploy_orchestration(client.ai_core_client)
orchestration_service = OrchestrationService(api_url=deployment.deployment_url, proxy_client=client)

def send_request(prompt, _print=True, _model='gpt-4o', **kwargs):
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
    'categories': ', '.join(f"`{entry}`" for entry in categories)
}

print(option_lists)

mail = dev_set[EXAMPLE_MESSAGE_IDX]

prompt_8 = """Giving the following message:
---
{{?input}}
---
Extract and return a json with the follwoing keys and values:
- "urgency" as one of {{?urgency}}
- "sentiment" as one of {{?sentiment}}
- "categories" list of the best matching support category tags from: {{?categories}}
Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in ```json...```, no newlines, no unnessacary whitespaces.
"""
option_lists = {
    'urgency': ', '.join(f"`{entry}`" for entry in urgency),
    'sentiment': ', '.join(f"`{entry}`" for entry in sentiment),
    'categories': ', '.join(f"`{entry}`" for entry in categories),
}
f_8 = partial(send_request, prompt=prompt_8, **option_lists)

response = f_8(input=mail["message"])
