from django.urls import reverse

from fctools_salary.services.binom.update import update_basic_info


class UpdateDatabaseMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        if (request.method == 'GET' and request.path == '/admin/fctools_salary/') or \
                (request.method == 'POST' and request.path == reverse('count')):
            update_basic_info()
        return self._get_response(request)
