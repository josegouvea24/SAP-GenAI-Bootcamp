/**
 * Describe this function...
 * @param {IClientAPI} clientAPI
 */
export default async function CallAI(clientAPI) {
    try{
        clientAPI.showActivityIndicator();
        var body = {
            "orchestration_config": {
                "module_configurations": {
                    "templating_module_config": {
                        "template": [
                        {
                            "role": "system",
                            "content": "Content"
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Request: {{ ?input }}"
                                }
                            ]
                        }
                    ]
                    },
                    "llm_module_config": {
                        "model_name": "gpt-4o-mini",
                        "model_params": {
                            "max_tokens": 16384,
                            "temperature": 1,
                            "frequency_penalty": 0.0,
                            "presence_penalty": 0.0
                        },
                        "model_version": "2024-07-18"
                    }
                }
            },
            "input_params": {
                "input": clientAPI.evaluateTargetPath("#Page:Main/#Control:FormCellNote0").getValue()
            }
        };
        clientAPI.getPageProxy().getAppClientData().body = body;
        
        var responseChat = await clientAPI.executeAction({
            "Name": "/AI_01/Actions/Completion.action"
        });
        
        let chatResponseText = responseChat?.data?.orchestration_result?.choices?.[0]?.message?.content || "Error";
        clientAPI.evaluateTargetPath("#Page:Main/#Control:FormCellNote1").setValue(chatResponseText);
        clientAPI.dismissActivityIndicator();

        if (chatResponseText == "Error") {
            clientAPI.executeAction({
                "Name": "/AI_01/Actions/GenericToastMessage.action",
                "Properties": {
                    "Message": "Error "
                }
            });
            clientAPI.dismissActivityIndicator();
            return;
        }
        
    }catch(error){
        clientAPI.executeAction({
            "Name": "/AI_01/Actions/GenericToastMessage.action",
            "Properties": {
                "Message": "Catched Error :"+error
            }
        });
        clientAPI.dismissActivityIndicator();
        return;        
    }
}