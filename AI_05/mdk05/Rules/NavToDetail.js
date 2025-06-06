export default async function NavToDetail(clientAPI) {
    try {
        // Show a loading indicator while the operation is in progress
        clientAPI.showActivityIndicator();

        // Retrieve the current action binding (should include the user's message)
        let actionBinding = clientAPI.getPageProxy().getActionBinding();

        // Extract the user's input message from the binding
        const userInput = actionBinding.message;

        // Define the orchestration request body with a structured prompt for the AI model
        var body = {
            "orchestration_config": {
                "module_configurations": {
                    "templating_module_config": {
                        "template": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        // Prompt template using placeholders for dynamic input and options
                                        "text": `Giving the following message:
                                        ---
                                        {{ ?input }}
                                        ---
                                        Extract and return a json with the following keys and values:
                                        - "urgency" as one of {{ ?urgency }}
                                        - "sentiment" as one of {{ ?sentiment }}
                                        - "categories" list of the best matching support category tags from: {{ ?categories }}
                                        Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. 
                                        Never enclose it in \`\`\`json...\`\`\`, no newlines, no unnecessary whitespaces.`
                                    }
                                ]
                            }
                        ]
                    },
                    // Configuration for the language model (LLM) to use
                    "llm_module_config": {
                        "model_name": "gpt-4o-mini",
                        "model_params": {
                            "max_tokens": 2048,
                            "temperature": 0.7
                        },
                        "model_version": "2024-07-18"
                    }
                }
            },
            // Input parameters to be injected into the prompt template
            "input_params": {
                "input": userInput,
                "urgency": "`high`, `medium`, `low`",
                "sentiment": "`positive`, `neutral`, `negative`",
                "categories": "`facility_management_issues`, `quality_and_safety_concerns`, `maintenance_requests`, `tenant_relations`"
            }
        };

        // Store the body in AppClientData so it can be accessed by the Completion.action
        clientAPI.getPageProxy().getAppClientData().body = body;

        // Call the orchestration execution action to get the AI-generated result
        const response = await clientAPI.executeAction("/mdk05/Actions/Completion.action");

        // Extract the AI response content, or fallback to "Error"
        const content = response?.data?.orchestration_result?.choices?.[0]?.message?.content || "Error";

        // Try to parse the AI response as JSON
        let extractedInfo = {};
        try {
            extractedInfo = JSON.parse(content);
        } catch (e) {
            extractedInfo = { error: "Invalid JSON response" };
        }

        // Merge the extracted AI info with the original action binding
        let mergedBinding = {
            ...actionBinding,
            ...extractedInfo
        };

        // Set the merged object as the new action binding to be used in the next page
        clientAPI.getPageProxy().setActionBinding(mergedBinding);

        // Hide the loading indicator
        clientAPI.dismissActivityIndicator();

        // Navigate to the detail page using the updated binding
        return clientAPI.executeAction("/mdk05/Actions/NavToDetail.action");

    } catch (error) {
        // If an error occurs, show a message box and hide the activity indicator
        clientAPI.executeAction({
            Name: "/mdk05/Actions/GenericMessageBox.action",
            Properties: { Message: "Error: " + error }
        });
        clientAPI.dismissActivityIndicator();
    }
}