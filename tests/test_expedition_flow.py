import pytest
from main import detect_travel_intent, _slugify, construct_post_url


def test_detect_expedition_question():
    msg = "Do you plan jungle safari expedition?"
    info = detect_travel_intent(msg)
    assert info['expedition_intent'] is True
    assert info['travel_intent'] is True


def test_detect_location():
    msg = "I want to go to Tadoba National Park"
    info = detect_travel_intent(msg)
    assert 'tadoba' in info['locations']


def test_slugify_and_url():
    title = "Tadoba National Park"
    slug = _slugify(title)
    assert slug == 'tadoba-national-park'

    package = {'region': 'Tadoba National Park', 'title': 'Tadoba Expedition'}
    url = construct_post_url(package)
    assert 'expeditions/tadoba-national-park' in url
