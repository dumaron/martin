from unittest.mock import Mock, patch

from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase

from apps.website.templatetags.active_link import active


class ActiveTemplateTagTest(SimpleTestCase):
	def setUp(self):
		self.factory = RequestFactory()

	def test_exact_match_returns_active_class(self):
		"""Test that exact URL match returns the active CSS class"""
		request = self.factory.get('/blog/')
		request.path = '/blog/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list')

		self.assertEqual(result, 'active')

	def test_exact_match_with_trailing_slash_normalization(self):
		"""A request path without the trailing slash matches a URL that ends with one."""
		request = self.factory.get('/blog')
		request.path = '/blog'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list')

		self.assertEqual(result, 'active')

	def test_no_match_returns_empty_string(self):
		"""Test that non-matching URLs return empty string"""
		request = self.factory.get('/home/')
		request.path = '/home/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list')

		self.assertEqual(result, '')

	def test_custom_css_class(self):
		"""Test that custom CSS class is returned when specified"""
		request = self.factory.get('/blog/')
		request.path = '/blog/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list', css_class='highlighted')

		self.assertEqual(result, 'highlighted')

	def test_match_children_false_does_not_match_child_pages(self):
		"""Test that child pages don't match when match_children=False"""
		request = self.factory.get('/blog/123/edit/')
		request.path = '/blog/123/edit/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list', match_children=False)

		self.assertEqual(result, '')

	def test_match_children_true_matches_child_pages(self):
		"""Test that child pages match when match_children=True"""
		request = self.factory.get('/blog/123/')
		request.path = '/blog/123/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list')

		self.assertEqual(result, 'active')

	def test_match_children_with_deep_nesting(self):
		"""Test that deeply nested child pages match when match_children=True"""
		request = self.factory.get('/blog/123/edit/comments/')
		request.path = '/blog/123/edit/comments/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list')

		self.assertEqual(result, 'active')

	def test_match_children_with_custom_css_class(self):
		"""A child page of the URL returns the custom CSS class when one is given."""
		request = self.factory.get('/blog/123/')
		request.path = '/blog/123/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list', css_class='current')

		self.assertEqual(result, 'current')

	def test_url_with_kwargs_exact_match(self):
		"""A URL reversed with kwargs is active when the request path equals it."""
		request = self.factory.get('/blog/123/')
		request.path = '/blog/123/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/123/'
			result = active(request, 'blog_detail', pk=123)

		self.assertEqual(result, 'active')

	def test_url_with_kwargs_child_match(self):
		"""A URL reversed with kwargs is active on its child pages when match_children=True."""
		request = self.factory.get('/blog/123/edit/')
		request.path = '/blog/123/edit/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/123/'
			result = active(request, 'blog_detail', match_children=True, pk=123)

		self.assertEqual(result, 'active')

	def test_url_with_wrong_kwargs_no_match(self):
		"""Test that URLs with wrong kwargs don't match"""
		request = self.factory.get('/blog/456/')
		request.path = '/blog/456/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/123/'
			result = active(request, 'blog_detail', pk=123)

		self.assertEqual(result, '')

	def test_reverse_fails_returns_empty_string(self):
		"""Test that when reverse() fails, empty string is returned"""
		request = self.factory.get('/blog/')
		request.path = '/blog/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.side_effect = Exception('Reverse failed')
			result = active(request, 'blog_list')

		self.assertEqual(result, '')

	def test_fallback_url_name_matching(self):
		"""When reverse() fails, the link is still active if the request path resolves to the same URL name."""
		request = self.factory.get('/blog/')
		request.path = '/blog/'

		mock_resolved = Mock()
		mock_resolved.url_name = 'blog_list'

		with (
			patch('apps.website.templatetags.active_link.reverse') as mock_reverse,
			patch('apps.website.templatetags.active_link.resolve') as mock_resolve,
		):
			mock_reverse.side_effect = Exception('Reverse failed')
			mock_resolve.return_value = mock_resolved
			result = active(request, 'blog_list')

		self.assertEqual(result, 'active')

	def test_fallback_url_name_matching_with_kwargs_fails(self):
		"""When reverse() fails and kwargs are given, the URL name fallback is skipped and an empty string is returned."""
		request = self.factory.get('/blog/123/')
		request.path = '/blog/123/'

		mock_resolved = Mock()
		mock_resolved.url_name = 'blog_detail'

		with (
			patch('apps.website.templatetags.active_link.reverse') as mock_reverse,
			patch('apps.website.templatetags.active_link.resolve') as mock_resolve,
		):
			mock_reverse.side_effect = Exception('Reverse failed')
			mock_resolve.return_value = mock_resolved
			result = active(request, 'blog_detail', pk=123)

		self.assertEqual(result, '')

	def test_similar_urls_dont_false_match(self):
		"""Test that similar URLs don't incorrectly match with match_children"""
		request = self.factory.get('/blog-archive/')
		request.path = '/blog-archive/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			result = active(request, 'blog_list')

		self.assertEqual(result, '')

	def test_root_path_matching(self):
		"""The root path is active when the URL reverses to the root path."""
		request = self.factory.get('/')
		request.path = '/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/'
			result = active(request, 'home')

		self.assertEqual(result, 'active')

	def test_empty_path_normalization(self):
		"""An empty request path is active when the URL reverses to an empty path."""
		request = self.factory.get('')
		request.path = ''

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = ''
			result = active(request, 'home')

		self.assertEqual(result, 'active')

	def test_template_tag_in_template(self):
		"""Rendered in a template, the tag outputs the active class on the page the URL points to."""
		template = Template('{% load active_link %}{% active request "blog_list" %}')
		request = RequestFactory().get('/blog/')
		request.path = '/blog/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/'
			rendered = template.render(Context({'request': request}))

		self.assertEqual(rendered, 'active')

	def test_template_tag_with_all_parameters(self):
		"""Rendered in a template with a custom class and kwargs, the tag outputs that class on a child page."""
		template = Template('{% load active_link %}{% active request "blog_detail" "current-page" True pk=123 %}')
		request = RequestFactory().get('/blog/123/edit/')
		request.path = '/blog/123/edit/'

		with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
			mock_reverse.return_value = '/blog/123/'
			rendered = template.render(Context({'request': request}))

		self.assertEqual(rendered, 'current-page')
