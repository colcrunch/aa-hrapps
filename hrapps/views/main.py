from django.shortcuts import render

def dashboard(request):
    return render(request, "hrapps/main/dashboard.html")