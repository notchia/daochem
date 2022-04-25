import os
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

from daochem.database.analysis.base import RESULTS_DIR
from daochem.database.models.blockchain import ContractAbi, DaoFactory
from daochem.database.models.daos import Dao
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

