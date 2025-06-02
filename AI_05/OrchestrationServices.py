YOUR_API_URL = "https://api.ai.prod.us-east-1.aws.ml.hana.ondemand.com/v2/inference/deployments/d4f47cb57c6f627a"

from gen_ai_hub.orchestration.models.message import SystemMessage, UserMessage
from gen_ai_hub.orchestration.models.template import Template, TemplateValue

template = Template(
    messages=[
        SystemMessage("You are a helpful translation assistant."),
        UserMessage(
            "Translate the following text to {{?to_lang}}: {{?text}}"
        ),
    ],
    defaults=[
        TemplateValue(name="to_lang", value="German"),
    ],
)

from gen_ai_hub.orchestration.models.llm import LLM

llm = LLM(name="gpt-4o", version="latest", parameters={"max_tokens": 256, "temperature": 0.2})

from gen_ai_hub.orchestration.models.config import OrchestrationConfig

config = OrchestrationConfig(
    template=template,
    llm=llm,
)

from gen_ai_hub.orchestration.service import OrchestrationService

orchestration_service = OrchestrationService(api_url=YOUR_API_URL, config=config)
result = orchestration_service.run(template_values=[
    TemplateValue(name="text", value="The Orchestration Service is working!")
])
print(result.orchestration_result.choices[0].message.content)
