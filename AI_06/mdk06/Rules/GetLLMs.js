/**
 * Returns a hardcoded array of available LLM model identifiers.
 * 
 * Models included span across multiple providers (OpenAI, Anthropic, Google, IBM, AWS, Mistral),
 * covering a variety of use cases: from lightweight edge AI to enterprise-grade reasoning and multimodal interaction.
 * 
 * Reference:
 * - https://openai.com/index/introducing-o3-and-o4-mini/
 * - https://openai.com/index/learning-to-reason-with-llms/
 * 
 * @param {IClientAPI} clientAPI - MDK Client API context (not used in this implementation, but preserved for interface compatibility).
 * @returns {Array<Object>} An array of objects each containing a `model` key that identifies an LLM.
 */
export default function GetLLMs(clientAPI) {

    // Define the list of supported LLMs by their model identifiers.
    const llms = [

        // === Anthropic Claude 3 Series ===
        { "model": "anthropic--claude-3-haiku" },         // Fastest Claude 3 model, ideal for real-time responses.
        { "model": "anthropic--claude-3-opus" },          // Most capable Claude model; excels in deep reasoning.
        { "model": "anthropic--claude-3-sonnet" },        // Balanced performance and speed for general use.
        { "model": "anthropic--claude-3.5-sonnet" },      // Enhanced version with improved latency.
        { "model": "anthropic--claude-3.7-sonnet" },      // Latest Claude iteration, optimized for low-lag logic tasks.

        // === OpenAI GPT-4 and o-series ===
        { "model": "gpt-4" },                             // Standard high-accuracy GPT-4 model for broad tasks.
        { "model": "gpt-4.1" },                           // Improved version with greater stability and accuracy.
        { "model": "gpt-4.1-mini" },                      // Smaller variant, optimized for fast inference.
        { "model": "gpt-4.1-nano" },                      // Even smaller footprint for embedded environments.
        { "model": "gpt-4o" },                            // Multimodal model (text/image/audio) with OpenAI’s fastest latency.
        { "model": "gpt-4o-mini" },                       // Compact version of GPT-4o for edge scenarios.

        // === Google DeepMind Gemini Series ===
        { "model": "gemini-1.5-flash" },                  // Optimized for high-speed conversational AI.
        { "model": "gemini-1.5-pro" },                    // Full-featured model with multimodal and reasoning support.
        { "model": "gemini-2.0-flash" },                  // Updated low-latency model for instruction tasks.
        { "model": "gemini-2.0-flash-lite" },             // Ultra-light variant for constrained environments.

        // === IBM Granite ===
        { "model": "ibm--granite-13b-chat" },             // Privacy-aware model designed for regulated industries.

        // === Mistral AI (Hosted by SAP) ===
        { "model": "mistralai--mistral-large-instruct" }, // Open-weight, instruction-tuned LLM for enterprise.
        { "model": "mistralai--mistral-small-instruct" }, // Lightweight, instruction-optimized for fast execution.

        // === Amazon Bedrock: Nova & Titan ===
        { "model": "amazon--nova-lite" },                 // General comprehension model.
        { "model": "amazon--nova-micro" },                // Minimal model for serverless/IoT.
        { "model": "amazon--nova-pro" },                  // Advanced model for reasoning-heavy workloads.
        { "model": "amazon--titan-text-express" },        // Expressive generation model for UI flows.
        { "model": "amazon--titan-text-lite" },           // Lightweight model for high-volume generation.

        // === OpenAI Reasoning-Optimized Models ===
        { "model": "o1" },                                // o1 is a mid-sized Large Language Model developed by OpenAI that focuses on improving reasoning accuracy rather than just generating fluent text. It was trained using a technique called process supervision, which teaches the model to prioritize correct reasoning steps over merely correct final answers.
        { "model": "o3" },                                // Mid-size OpenAI model trained with process supervision for reasoning accuracy.
        { "model": "o3-mini" },                           // Compact version of o3 for fast, cost-effective inference.
        { "model": "o4-mini" }                            // Successor to o3-mini; better multilingual reasoning and robustness.
    ];

    // Return the hardcoded list of models
    return llms;
}