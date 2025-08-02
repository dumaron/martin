import os

from openai import OpenAI

singleton_client = None


def init_openai():
	global singleton_client

	if singleton_client is None:
		singleton_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

	return singleton_client


def speech_to_text(file):
	client = init_openai()
	return client.audio.transcriptions.create(model='whisper-1', file=file, language='en')
