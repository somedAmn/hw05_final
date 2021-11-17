from django.test import TestCase


class CorePagesTests(TestCase):
    def test_404_page_use_correct_template(self):
        response = self.client.get('unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
