import re
import emoji

stop_words = {
    "the", "is", "a", "an", "and", "or",
    "to", "of", "in", "on", "for",
    "this", "that", "it", "be", "are",
    "was", "were", "am"
}


def remove_urls(text):
    return re.sub(r'http\S+|www\S+|https\S+', '', text)


def remove_emojis(text):
    return emoji.replace_emoji(text, replace='')


def remove_special_chars(text):
    return re.sub(r'[^a-zA-Z\s]', '', text)


def remove_stopwords(words):
    return [word for word in words if word not in stop_words]


def clean_comment(text):

    text = text.lower()

    text = remove_urls(text)

    text = remove_emojis(text)

    text = remove_special_chars(text)

    words = text.split()

    words = remove_stopwords(words)

    text = " ".join(words)

    return text