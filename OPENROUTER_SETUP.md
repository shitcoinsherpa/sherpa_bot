# OpenRouter Integration Instructions

## What is OpenRouter?

OpenRouter provides unified access to 100+ LLMs through a single API, including models from OpenAI, Anthropic, Meta, Google, and more. This integration allows you to use any model available on OpenRouter instead of being limited to OpenAI models.

## Why Use OpenRouter?

1. **More Model Choices**: Access Claude 3.5 Sonnet, Llama 3.1 405B, Gemini Pro, and dozens more
2. **Cost Optimization**: Many models are cheaper than GPT-4
3. **Fallback Options**: If one provider is down, use another
4. **Single API Key**: Manage all models with one key

## Setup Instructions

### Step 1: Get Your OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai)
2. Sign up for an account
3. Navigate to [API Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Add credits to your account

### Step 2: Apply the Integration

The `openrouter_integration.py` file contains all necessary code changes. You need to manually apply these changes to your `sherpa_bot.py` file:

1. **Add new constants** (Section 1)
   - Add after line ~80 in your sherpa_bot.py

2. **Replace TwitterBot.__init__** (Section 2)
   - Replace the entire `__init__` method

3. **Add new methods** (Section 3)
   - Add these methods to the TwitterBot class:
     - `load_openrouter_models()`
     - `save_openrouter_models()`
     - `get_available_models()`
     - `get_client_for_model()`

4. **Update generate_tweet** (Section 4)
   - Replace the entire `generate_tweet` method

5. **Update UI** (Section 5)
   - Add the new UI components to `create_ui()` function
   - Add after the OpenAI key input section

6. **Update save_credentials** (Section 6)
   - Replace the `save_credentials` method

### Step 3: Configure in the UI

1. Launch the bot (`./run.sh` or `run.bat`)
2. In the credentials section:
   - Select "OpenRouter" or "Both" as your API Provider
   - Enter your OpenRouter API key
   - Save credentials

3. In the OpenRouter Models section:
   - Add custom models by providing:
     - Display Name (e.g., "Claude 3.5 Sonnet")
     - Model ID (e.g., "anthropic/claude-3.5-sonnet")
   - Remove models you don't need

4. When creating characters:
   - You'll now see OpenRouter models in the dropdown
   - Select any OpenRouter model for your character

## Available Default Models

The integration comes with these pre-configured models:

- **Claude 3.5 Sonnet** (`anthropic/claude-3.5-sonnet`) - Best for creative writing
- **Claude 3 Opus** (`anthropic/claude-3-opus`) - Most capable Claude model
- **GPT-4o** (`openai/gpt-4o`) - Latest OpenAI model via OpenRouter
- **Llama 3.1 405B** (`meta-llama/llama-3.1-405b-instruct`) - Open source powerhouse
- **Mixtral 8x22B** (`mistralai/mixtral-8x22b-instruct`) - Fast and capable
- **Gemini Pro 1.5** (`google/gemini-pro-1.5`) - Google's latest

## Finding More Models

1. Visit [OpenRouter Models](https://openrouter.ai/models)
2. Find a model you want to use
3. Copy its ID (shown under the model name)
4. Add it through the UI

## Model ID Format

OpenRouter model IDs follow this pattern: `provider/model-name`

Examples:
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4-turbo`
- `meta-llama/llama-3.1-70b-instruct`
- `google/gemini-pro`

## Using Both Providers

You can configure both OpenAI and OpenRouter:
1. Set API Provider to "Both"
2. Enter both API keys
3. Characters can use models from either provider
4. The bot automatically routes to the correct API

## Cost Considerations

- OpenRouter shows pricing per model on their [models page](https://openrouter.ai/models)
- Many models are significantly cheaper than GPT-4
- Claude 3.5 Sonnet offers excellent quality at lower cost
- Open source models (Llama, Mixtral) are very cost-effective

## Troubleshooting

**"OpenRouter client not initialized"**
- Make sure you've entered and saved your OpenRouter API key
- Restart the bot after adding the key

**Model not showing in dropdown**
- Ensure you've added it in the OpenRouter Models section
- Check that the model ID is correct

**"Failed to generate tweet"**
- Verify your OpenRouter account has credits
- Check that the model ID exists on OpenRouter
- Some models may have specific requirements

## Migration from OpenAI

Your existing characters will continue to work with OpenAI. To migrate a character to OpenRouter:
1. Edit the character
2. Select an OpenRouter model from the dropdown
3. Save the character

## Security

- OpenRouter API keys are encrypted locally (same as OpenAI keys)
- Never share your `encryption.key` file
- API keys are never sent to any third party

## Support

For OpenRouter-specific issues:
- Check [OpenRouter Documentation](https://openrouter.ai/docs)
- Visit [OpenRouter Discord](https://discord.gg/openrouter)

For integration issues:
- Open an issue on the [GitHub repository](https://github.com/shitcoinsherpa/sherpa_bot)
