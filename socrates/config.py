import yaml

with open('config.yaml', "r") as f:
    config = yaml.safe_load(f)

try:
    nostr_config = config['nostr']
    chroma_config = config['chroma']
    summarizer_config = config['summarizer']

    CHROMA_MODEL = chroma_config['model']
    SUMMARIZER_MODEL = summarizer_config['model']
    NOSTR_RELAY = nostr_config['relay']
    NOSTR_FILTER = nostr_config['filter']
except KeyError as exc:
    raise KeyError(f"Config error: {exc}")
