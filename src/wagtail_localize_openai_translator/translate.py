import json
from wagtail_localize.machine_translators.base import BaseMachineTranslator
from src.wagtail_localize_openai_translator.translate import OpenAI
from typing import Annotated, get_type_hints, get_args
from wagtail_localize.strings import StringValue

TO_API = {
    int: 'integer',
    str: 'string',
    bool: 'boolean',
    float: 'float',
}

REGISTRY = {}

def openai_function(description):
    def decorator(func):
        def _parse_arg(arg, value):
            type_ = get_args(value)[0]

            return {
                'name': arg,
                'description': value.__metadata__[0],
                'type': TO_API[type_],
            }

        func.object = {
            'name': func.__name__,
            'description': description,
            'arguments': [
                _parse_arg(arg, value)
                for arg, value in get_type_hints(func, include_extras=True).items()
            ],
        }
        REGISTRY[func.__name__] = func
        return func
    return decorator


@openai_function(description='Function to call with the result of the translation')
def translation(index: Annotated[int, "Index of the translation"], translated_text: Annotated[int, "The translated text"]):
    return (int(index), translated_text)


class OpenAITranslator(BaseMachineTranslator):
    display_name = "OpenAI"

    def translate(self, source_locale, target_locale, strings):
        client = OpenAI()

        source_locale_display_name = source_locale.get_display_name()
        target_locale_display_name = target_locale.get_display_name()

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a professional translator.
Translate from {source_locale_display_name} to {target_locale_display_name} the messages sent to you. Call the translation function with the translations. Respond only with ok.
Do not assume gender.
                    """,
                },
                {
                    "role": "user",
                    "content": [
                        f"Index {index}: {string.data}"
                        for index, string in enumerate(strings)
                    ],
                }
            ],
            tools=[translation.object],
            tool_choice='auto',
            model="gpt-4-1106-preview",
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        translated_content = []
        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = REGISTRY[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                translated_content[function_response[0]].append(function_response[1])

        return {
            string: StringValue(translation)
            for string, translation in zip(strings, translated_content)
        }

    def can_translate(self, source_locale, target_locale):
        return True
