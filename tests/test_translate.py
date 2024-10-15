import os
from unittest.mock import Mock
from src.wagtail_localize_openai_translator.translate import OpenAITranslator
from wagtail_localize.strings import StringValue


def test_translate():
    en_locale = Mock()
    en_locale.get_display_name = Mock(return_value="English")
    it_locale = Mock()
    it_locale.get_display_name = Mock(return_value="Italian")

    translator = OpenAITranslator({
        "api_key": os.getenv("OPENAI_API_KEY")
    })
    translation_result = translator.translate(it_locale, en_locale, [
        StringValue("Ciao mondo!"),
        StringValue("Partecipa a PyCon Italia!"),
    ])

    assert translation_result == {
        StringValue("Ciao mondo!"): StringValue("Hello world!"),
        StringValue("Partecipa a PyCon Italia!"): StringValue("Join PyCon Italia!"),
    }
