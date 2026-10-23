from django.test.runner import DiscoverRunner


class AppTestRunner(DiscoverRunner):
    """apps/ ichidagi ilovalarni standart `manage.py test` ham topsin."""

    def build_suite(self, test_labels=None, **kwargs):
        return super().build_suite(test_labels or ["core", "store", "orders"], **kwargs)
