from django.test import TestCase, RequestFactory
from django.template import Context, Template
from unittest.mock import Mock, patch
from apps.website.templatetags.active_link import active



class ActiveTemplateTagTest(TestCase):
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
        """Test that trailing slashes are properly normalized"""
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
            result = active(request, 'blog_list', )
            
        self.assertEqual(result, 'active')

    def test_match_children_with_deep_nesting(self):
        """Test that deeply nested child pages match when match_children=True"""
        request = self.factory.get('/blog/123/edit/comments/')
        request.path = '/blog/123/edit/comments/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/blog/'
            result = active(request, 'blog_list', )
            
        self.assertEqual(result, 'active')

    def test_match_children_with_custom_css_class(self):
        """Test that custom CSS class works with child page matching"""
        request = self.factory.get('/blog/123/')
        request.path = '/blog/123/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/blog/'
            result = active(request, 'blog_list', css_class='current', )
            
        self.assertEqual(result, 'current')

    def test_url_with_kwargs_exact_match(self):
        """Test that URLs with kwargs work for exact matches"""
        request = self.factory.get('/blog/123/')
        request.path = '/blog/123/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/blog/123/'
            result = active(request, 'blog_detail', pk=123)
            
        self.assertEqual(result, 'active')

    def test_url_with_kwargs_child_match(self):
        """Test that URLs with kwargs work for child page matching"""
        request = self.factory.get('/blog/123/edit/')
        request.path = '/blog/123/edit/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/blog/123/'
            result = active(request, 'blog_detail', match_children=True , pk=123)
            
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
        """Test fallback URL name matching for compatibility"""
        request = self.factory.get('/blog/')
        request.path = '/blog/'
        
        mock_resolved = Mock()
        mock_resolved.url_name = 'blog_list'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse, \
             patch('apps.website.templatetags.active_link.resolve') as mock_resolve:
            mock_reverse.side_effect = Exception('Reverse failed')
            mock_resolve.return_value = mock_resolved
            result = active(request, 'blog_list')
            
        self.assertEqual(result, 'active')

    def test_fallback_url_name_matching_with_kwargs_fails(self):
        """Test that fallback URL name matching doesn't work with kwargs"""
        request = self.factory.get('/blog/123/')
        request.path = '/blog/123/'
        
        mock_resolved = Mock()
        mock_resolved.url_name = 'blog_detail'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse, \
             patch('apps.website.templatetags.active_link.resolve') as mock_resolve:
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
        """Test that root path matching works correctly"""
        request = self.factory.get('/')
        request.path = '/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/'
            result = active(request, 'home')
            
        self.assertEqual(result, 'active')

    def test_empty_path_normalization(self):
        """Test that empty paths are handled correctly"""
        request = self.factory.get('')
        request.path = ''
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = ''
            result = active(request, 'home')
            
        self.assertEqual(result, 'active')


class ActiveTemplateTagIntegrationTest(TestCase):
    """Integration tests using actual Django template rendering"""
    
    def test_template_tag_in_template(self):
        """Test that the template tag works correctly when used in a template"""
        template = Template('{% load active_link %}{% active request "blog_list" %}')
        request = RequestFactory().get('/blog/')
        request.path = '/blog/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/blog/'
            rendered = template.render(Context({'request': request}))
            
        self.assertEqual(rendered, 'active')

    def test_template_tag_with_all_parameters(self):
        """Test template tag with all parameters in template"""
        template = Template(
            '{% load active_link %}'
            '{% active request "blog_detail" "current-page" True pk=123 %}'
        )
        request = RequestFactory().get('/blog/123/edit/')
        request.path = '/blog/123/edit/'
        
        with patch('apps.website.templatetags.active_link.reverse') as mock_reverse:
            mock_reverse.return_value = '/blog/123/'
            rendered = template.render(Context({'request': request}))
            
        self.assertEqual(rendered, 'current-page')