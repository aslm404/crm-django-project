from django.shortcuts import render
from django.views import View

class MaintenanceView(View):
    def get(self, request):
        return render(request, 'maintenance.html', status=503)