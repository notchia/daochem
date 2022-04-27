import os
from django.shortcuts import render

from daochem.database.analysis.base import RESULTS_DIR
from utils.files import load_json


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    stats = load_json(os.path.join(RESULTS_DIR, "index.json"))
    context = {
        'stats': stats,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


def factories(request):
    """Get some stats on the factories"""

    factories = load_json(os.path.join(RESULTS_DIR, "factories.json"))
    context = {
        'factories': factories,
    }

    return render(request, 'factories.html', context)


def twitter(request):
    """Get some stats on the tweets"""

    stats = load_json(os.path.join(RESULTS_DIR, "twitter.json"))
    context = {
        'meta': stats['meta'],
        'accounts': stats['accounts'],
        'gov_tweet': stats['governance_tweet_stats'],
        'gov_topics': stats["governance_topic_stats"],
    }

    return render(request, 'twitter.html', context)