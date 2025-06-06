// Import a custom function to retrieve emails
import getEmails from './GetEmails';

// Define an asynchronous function named NavToDetail, which is exported as the default export
export default async function NavToDetail(clientAPI) {
    try {
        // Show a loading indicator while the operation is in progress
        clientAPI.showActivityIndicator();

        // Retrieve the current action binding (should contain input parameters such as the selected AI model)
        let actionBinding = clientAPI.getPageProxy().getActionBinding();
       
        // Get the list of emails using a helper function
        const emails = getEmails(clientAPI);

        // Calculate the halfway point of the emails list
        const half = Math.floor(emails.length / 2);

        // Use only the second half of the list as the test set
        const test_set = emails.slice(half);

        // Take the first 2 items from the test set to limit the evaluation
        const test_set_small = test_set.slice(0, 2);

        // Initialize score counters for evaluation metrics
        let totalUrgencyScore = 0;
        let totalSentimentScore = 0;
        let totalCategoryScore = 0;

        // Count of processed emails
        let count = test_set_small.length;

        // Variable to hold the last parsed result (optional use)
        let str;

        // Loop through each email in the small test set
        for (const email of test_set_small) {

            // Construct the AI orchestration request body
            const body = {
                orchestration_config: {
                    module_configurations: {
                        templating_module_config: {
                            template: [{
                                role: "user",
                                content: [{
                                    type: "text",
                                    text: `Giving the following message:
                                            ---
                                            {{ ?input }}
                                            ---
                                            Extract and return a json with the following keys and values:
                                            - "urgency" as one of {{ ?urgency }}
                                            - "sentiment" as one of {{ ?sentiment }}
                                            - "categories" list of the best matching support category tags from: {{ ?categories }}
                                            Your complete message should be a valid json string that can be read directly and only contain the keys mentioned in the list above. Never enclose it in \`\`\`json\`\`\`, no newlines, no unnecessary whitespaces.`
                                }]
                            }]
                        },
                        // Specify the AI model to use, as selected by the user
                        llm_module_config: {
                            model_name: actionBinding.model
                        }
                    }
                },
                // Provide the dynamic input parameters for the template
                input_params: {
                    input: email.message,
                    urgency: "`high`, `medium`, `low`",
                    sentiment: "`positive`, `neutral`, `negative`",
                    categories: "`facility_management_issues`, `general_inquiries`, `sustainability_and_environmental_practices`, `quality_and_safety_concerns`, `routine_maintenance_requests`, `cleaning_services_scheduling`, `training_and_support_requests`, `specialized_cleaning_services`, `customer_feedback_and_complaints`, `emergency_repair_services`"
                }
            };

            // Store the request body in client data (can be accessed by Completion.action)
            clientAPI.getPageProxy().getAppClientData().body = body;

            // Call the Completion.action to execute the orchestration and get the prediction
            const response = await clientAPI.executeAction("/mdk06/Actions/Completion.action");

            // Extract the predicted content from the orchestration response
            const content = response?.data?.orchestration_result?.choices?.[0]?.message?.content || "{}";

            let parsed = {};
            try {
                // Try to parse the content as JSON
                parsed = JSON.parse(content);
            } catch (_) {
                // If parsing fails, skip this entry
                continue;
            }

            // Access the ground truth labels associated with the current email
            const gt = email.ground_truth;

            // Evaluate the urgency match (binary score)
            const urgencyScore = parsed.urgency === gt.urgency ? 1 : 0;

            // Evaluate the sentiment match (binary score)
            const sentimentScore = parsed.sentiment === gt.sentiment ? 1 : 0;

            // Initialize the category match score
            let categoryScore = 0;

            // If both predicted and ground truth categories are arrays, calculate the Jaccard similarity
            if (Array.isArray(gt.categories) && Array.isArray(parsed.categories)) {
                const gtSet = new Set(gt.categories);
                const predSet = new Set(parsed.categories);
                const intersection = [...gtSet].filter(x => predSet.has(x));
                const union = new Set([...gtSet, ...predSet]);
                categoryScore = union.size > 0 ? intersection.length / union.size : 0;
            }

            // Accumulate the evaluation scores
            totalUrgencyScore += urgencyScore;
            totalSentimentScore += sentimentScore;
            totalCategoryScore += categoryScore;

            // Optionally store the last parsed result
            str = parsed;
        }

        // Calculate the average score for each metric
        const averageUrgency = totalUrgencyScore / count;
        const averageSentiment = totalSentimentScore / count;
        const averageCategory = totalCategoryScore / count;

        // Create a new binding object that includes the original values and the calculated scores
        let mergedBinding = {
            ...actionBinding,
            averageUrgency,
            averageSentiment,
            averageCategory
        };

        // Set the merged object as the new action binding to be used in the next page
        clientAPI.getPageProxy().setActionBinding(mergedBinding);

        // Hide the loading indicator now that the operation is done
        clientAPI.dismissActivityIndicator();

        // Navigate to the detail page with the updated action binding
        return clientAPI.executeAction("/mdk06/Actions/NavToDetail.action");

    } catch (error) {
        // If any error occurs, display a message and hide the activity indicator
        clientAPI.executeAction({
            Name: "/mdk06/Actions/GenericMessageBox.action",
            Properties: { Message: "Error: " + error }
        });
        clientAPI.dismissActivityIndicator();
    }
}