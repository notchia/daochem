from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from daochem.database.models.blockchain import DaoFactory


def index(request):
    return HttpResponse("Hello, world. You're at the DAOs index.")


def factory_contract_summary(request, contract_address):
    fac = DaoFactory.objects.get(Q(contract_address=contract_address))
    r_lines = []
    r_lines.append(f"These are the results for the factory contract {fac.contract_address.contract_name} for {fac.dao_framework.name} version {fac.version} at {contract_address}")
    totalTransactions = fac.related_transactions.count()
    r_lines.append(f"Number of contract-creating transactions: {totalTransactions}")
    
    return HttpResponse("\n\n".join(r_lines))