"""Generic LLM wrapper.

One thin function — `ask` — talks to Claude, OpenAI, and Gemini through a single client.

The trick that keeps this small: all three providers expose an OpenAI-compatible chat API, so the
already-installed `openai` SDK can reach every one of them just by swapping the `base_url`, the API
key, and the model name. No extra dependencies, one code path.

The cost of that simplicity is that we only get the common feature subset (plain chat + JSON output);
provider-native extras such as Anthropic prompt-caching or Gemini grounding are not reachable here. If
you ever need those, reach for the provider's native SDK instead.

Usage:
	from core.integrations.llm import ask, CLAUDE_SONNET, GPT_5, GEMINI_FLASH

	ask('Summarise this invoice in one line.', model=CLAUDE_SONNET)

	class Invoice(BaseModel):
		vendor: str
		total: float

	ask('Extract the invoice fields.', model=GPT_5, schema=Invoice)  # -> Invoice instance
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel


class Provider(Enum):
	"""An LLM vendor reachable through the OpenAI-compatible chat API.

	Value is `(api_key_env, base_url, supports_json_mode)`. A `base_url` of `None` means the SDK's
	default (the real OpenAI). `supports_json_mode` flags whether the endpoint honours
	`response_format={'type': 'json_object'}`; Anthropic's compatibility shim does not, so we lean on
	the schema instruction + validation alone there (see `ask`).
	"""

	OPENAI = ('OPENAI_API_KEY', None, True)
	ANTHROPIC = ('ANTHROPIC_API_KEY', 'https://api.anthropic.com/v1/', False)
	GEMINI = ('GEMINI_API_KEY', 'https://generativelanguage.googleapis.com/v1beta/openai/', True)

	@property
	def api_key_env(self):
		return self.value[0]

	@property
	def base_url(self):
		return self.value[1]

	@property
	def supports_json_mode(self):
		return self.value[2]


@dataclass(frozen=True)
class Model:
	"""A concrete model on a given provider. Build your own freely: `Model(Provider.OPENAI, 'gpt-5')`."""

	provider: Provider
	name: str


# A handful of ready-made models. These names track each vendor's current catalogue — adjust as the
# providers ship new ones; nothing else needs to change.
GPT_5 = Model(Provider.OPENAI, 'gpt-5')
GPT_5_MINI = Model(Provider.OPENAI, 'gpt-5-mini')
CLAUDE_OPUS = Model(Provider.ANTHROPIC, 'claude-opus-4-7')
CLAUDE_SONNET = Model(Provider.ANTHROPIC, 'claude-sonnet-4-6')
CLAUDE_HAIKU = Model(Provider.ANTHROPIC, 'claude-haiku-4-5')
GEMINI_PRO = Model(Provider.GEMINI, 'gemini-2.5-pro')
GEMINI_FLASH = Model(Provider.GEMINI, 'gemini-2.5-flash')


_clients: dict[Provider, OpenAI] = {}


def _client(provider: Provider) -> OpenAI:
	"""Return a memoised OpenAI client pointed at `provider`."""
	if provider not in _clients:
		api_key = os.getenv(provider.api_key_env)
		if not api_key:
			raise RuntimeError(f'Missing API key: set the {provider.api_key_env} environment variable.')
		_clients[provider] = OpenAI(api_key=api_key, base_url=provider.base_url)
	return _clients[provider]


def _strip_fences(text: str) -> str:
	"""Drop a leading/trailing markdown code fence some models wrap JSON in."""
	stripped = text.strip()
	if stripped.startswith('```'):
		stripped = stripped.split('\n', 1)[-1]  # drop the opening ``` / ```json line
		stripped = stripped.rsplit('```', 1)[0]  # drop the closing fence
	return stripped.strip()


T = TypeVar('T', bound=BaseModel)


def ask(prompt: str, model: Model, *, system: str | None = None, schema: Type[T] | None = None, **kwargs) -> str | T:
	"""Send a single-turn query to `model` and return its reply.

	Args:
		prompt: The user message.
		model: Which model to call (e.g. `CLAUDE_SONNET`, or any `Model(...)`).
		system: Optional system / instruction prompt.
		schema: Optional Pydantic model. When given, the reply is parsed and validated against it and
			the matching instance is returned instead of raw text.
		**kwargs: Forwarded verbatim to the chat-completions call (`temperature`, `max_tokens`, ...).

	Returns:
		The reply text, or — when `schema` is set — a validated instance of it.
	"""
	messages: list[dict] = []
	if system:
		messages.append({'role': 'system', 'content': system})

	if schema is not None:
		# Works on every provider regardless of native JSON support: we describe the shape and validate.
		json_schema = json.dumps(schema.model_json_schema())
		messages.append(
			{
				'role': 'system',
				'content': f'Respond with a single JSON object that conforms to this JSON schema. '
				f'Output only the JSON, with no markdown fences or commentary.\n\n{json_schema}',
			}
		)
		if model.provider.supports_json_mode:
			kwargs.setdefault('response_format', {'type': 'json_object'})

	messages.append({'role': 'user', 'content': prompt})

	completion = _client(model.provider).chat.completions.create(model=model.name, messages=messages, **kwargs)
	content = completion.choices[0].message.content or ''

	if schema is None:
		return content
	return schema.model_validate_json(_strip_fences(content))
