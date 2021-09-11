import http

from django.test import TestCase


class AboutURLTests(TestCase):

    def test_urls_correct_template(self):
        url_tempfile = (
            ('/about/author/', 'about/author.html'),
            ('/about/tech/', 'about/tech.html'),
        )
        for (url, tempfile) in url_tempfile:
            with self.subTest(url=url):
                self.assertTemplateUsed(self.client.get(url), tempfile)

    def test_urls_status_code(self):
        url_client_status_code = (
            '/about/author/',
            '/about/tech/',
        )
        for url in url_client_status_code:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, http.HTTPStatus.OK)
