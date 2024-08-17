from django.shortcuts import render


def example(request, state=None):
    return render(request, "elections.html", { "title": "Título vindo do Django" })

def politic(request, state=None):
    return render(request, "politic.html", {})
