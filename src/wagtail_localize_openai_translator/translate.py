from wagtail_localize.machine_translators.base import BaseMachineTranslator
from openai import OpenAI
from wagtail_localize.strings import StringValue
from pydantic import BaseModel

class Translation(BaseModel):
    index: int
    translation: str


class Translations(BaseModel):
    translations: list[Translation]


class OpenAITranslator(BaseMachineTranslator):
    display_name = "OpenAI"

    def translate(self, source_locale, target_locale, strings):
        client = OpenAI(
            api_key=self.options["api_key"],
        )

        source_locale_display_name = source_locale.get_display_name()
        target_locale_display_name = target_locale.get_display_name()

        response = client.beta.chat.completions.parse(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a professional translator.
Translate from {source_locale_display_name} to {target_locale_display_name} the strings sent to you.
Follow the guidelines:
- Do not assume gender
- Never translate the name of the conference "PyCon Italia"
- Never translate to "male" or "female", always use "man" or "woman"
                    """,
                },
                {
                    "role": "user",
                    "content": "\n".join([
                        f"Index {index}: {string.data}"
                        for index, string in enumerate(strings)
                    ]),
                }
            ],
            model="gpt-4o-mini",
            response_format=Translations,
        )
        translations = response.choices[0].message.parsed.translations
        return {
            strings[translation.index]: StringValue(translation.translation)
            for translation in translations
        }

    def can_translate(self, source_locale, target_locale):
        return True
