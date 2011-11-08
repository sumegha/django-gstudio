"""Test cases for Gstudio's templatetags"""
from datetime import datetime

from django.test import TestCase
from django.template import Context
from django.template import Template
from django.template import TemplateSyntaxError
from django.contrib import comments
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.comments.models import CommentFlag

from tagging.models import Tag

from gstudio.models import Objecttype
from gstudio.models import Author
from gstudio.models import Metatype
from gstudio.managers import DRAFT
from gstudio.managers import PUBLISHED
from gstudio.templatetags.gstudio_tags import get_authors
from gstudio.templatetags.gstudio_tags import get_gravatar
from gstudio.templatetags.gstudio_tags import get_tag_cloud
from gstudio.templatetags.gstudio_tags import get_metatypes
from gstudio.templatetags.gstudio_tags import gstudio_pagination
from gstudio.templatetags.gstudio_tags import get_recent_objecttypes
from gstudio.templatetags.gstudio_tags import get_random_objecttypes
from gstudio.templatetags.gstudio_tags import gstudio_breadcrumbs
from gstudio.templatetags.gstudio_tags import get_popular_objecttypes
from gstudio.templatetags.gstudio_tags import get_similar_objecttypes
from gstudio.templatetags.gstudio_tags import get_recent_comments
from gstudio.templatetags.gstudio_tags import get_recent_linkbacks
from gstudio.templatetags.gstudio_tags import get_calendar_objecttypes
from gstudio.templatetags.gstudio_tags import get_archives_objecttypes
from gstudio.templatetags.gstudio_tags import get_featured_objecttypes
from gstudio.templatetags.gstudio_tags import get_archives_objecttypes_tree


class TemplateTagsTestCase(TestCase):
    """Test cases for Template tags"""

    def setUp(self):
        params = {'title': 'My objecttype',
                  'content': 'My content',
                  'tags': 'gstudio, test',
                  'creation_date': datetime(2010, 1, 1),
                  'slug': 'my-objecttype'}
        self.objecttype = Objecttype.objects.create(**params)

    def publish_objecttype(self):
        self.objecttype.status = PUBLISHED
        self.objecttype.featured = True
        self.objecttype.sites.add(Site.objects.get_current())
        self.objecttype.save()

    def test_get_metatypes(self):
        context = get_metatypes()
        self.assertEquals(len(context['metatypes']), 0)
        self.assertEquals(context['template'], 'gstudio/tags/metatypes.html')

        Metatype.objects.create(title='Metatype 1', slug='metatype-1')
        context = get_metatypes('custom_template.html')
        self.assertEquals(len(context['metatypes']), 1)
        self.assertEquals(context['template'], 'custom_template.html')

    def test_get_authors(self):
        context = get_authors()
        self.assertEquals(len(context['authors']), 0)
        self.assertEquals(context['template'], 'gstudio/tags/authors.html')

        user = User.objects.create_user(username='webmaster',
                                        email='webmaster@example.com')
        self.objecttype.authors.add(user)
        self.publish_objecttype()
        context = get_authors('custom_template.html')
        self.assertEquals(len(context['authors']), 1)
        self.assertEquals(context['template'], 'custom_template.html')

    def test_get_recent_objecttypes(self):
        context = get_recent_objecttypes()
        self.assertEquals(len(context['objecttypes']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/recent_objecttypes.html')

        self.publish_objecttype()
        context = get_recent_objecttypes(3, 'custom_template.html')
        self.assertEquals(len(context['objecttypes']), 1)
        self.assertEquals(context['template'], 'custom_template.html')
        context = get_recent_objecttypes(0)
        self.assertEquals(len(context['objecttypes']), 0)

    def test_get_featured_objecttypes(self):
        context = get_featured_objecttypes()
        self.assertEquals(len(context['objecttypes']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/featured_objecttypes.html')

        self.publish_objecttype()
        context = get_featured_objecttypes(3, 'custom_template.html')
        self.assertEquals(len(context['objecttypes']), 1)
        self.assertEquals(context['template'], 'custom_template.html')
        context = get_featured_objecttypes(0)
        self.assertEquals(len(context['objecttypes']), 0)

    def test_get_random_objecttypes(self):
        context = get_random_objecttypes()
        self.assertEquals(len(context['objecttypes']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/random_objecttypes.html')

        self.publish_objecttype()
        context = get_random_objecttypes(3, 'custom_template.html')
        self.assertEquals(len(context['objecttypes']), 1)
        self.assertEquals(context['template'], 'custom_template.html')
        context = get_random_objecttypes(0)
        self.assertEquals(len(context['objecttypes']), 0)

    def test_get_popular_objecttypes(self):
        context = get_popular_objecttypes()
        self.assertEquals(len(context['objecttypes']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/popular_objecttypes.html')

        self.publish_objecttype()
        context = get_popular_objecttypes(3, 'custom_template.html')
        self.assertEquals(len(context['objecttypes']), 0)
        self.assertEquals(context['template'], 'custom_template.html')

        params = {'title': 'My second objecttype',
                  'content': 'My second content',
                  'tags': 'gstudio, test',
                  'status': PUBLISHED,
                  'slug': 'my-second-objecttype'}
        site = Site.objects.get_current()
        second_objecttype = Objecttype.objects.create(**params)
        second_objecttype.sites.add(site)

        comments.get_model().objects.create(comment='My Comment 1', site=site,
                                            content_object=self.objecttype)
        comments.get_model().objects.create(comment='My Comment 2', site=site,
                                            content_object=self.objecttype)
        comments.get_model().objects.create(comment='My Comment 3', site=site,
                                            content_object=second_objecttype)
        context = get_popular_objecttypes(3)
        self.assertEquals(context['objecttypes'], [self.objecttype, second_objecttype])
        self.objecttype.status = DRAFT
        self.objecttype.save()
        context = get_popular_objecttypes(3)
        self.assertEquals(context['objecttypes'], [second_objecttype])

    def test_get_similar_objecttypes(self):
        self.publish_objecttype()
        source_context = Context({'object': self.objecttype})
        context = get_similar_objecttypes(source_context)
        self.assertEquals(len(context['objecttypes']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/similar_objecttypes.html')

        params = {'title': 'My second objecttype',
                  'content': 'This is the second objecttype of my tests.',
                  'tags': 'gstudio, test',
                  'status': PUBLISHED,
                  'slug': 'my-second-objecttype'}
        site = Site.objects.get_current()
        second_objecttype = Objecttype.objects.create(**params)
        second_objecttype.sites.add(site)

        source_context = Context({'object': second_objecttype})
        context = get_similar_objecttypes(source_context, 3,
                                      'custom_template.html',
                                      flush=True)
        self.assertEquals(len(context['objecttypes']), 1)
        self.assertEquals(context['template'], 'custom_template.html')

    def test_get_archives_objecttypes(self):
        context = get_archives_objecttypes()
        self.assertEquals(len(context['archives']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/archives_objecttypes.html')

        self.publish_objecttype()
        params = {'title': 'My second objecttype',
                  'content': 'My second content',
                  'tags': 'gstudio, test',
                  'status': PUBLISHED,
                  'creation_date': datetime(2009, 1, 1),
                  'slug': 'my-second-objecttype'}
        site = Site.objects.get_current()
        second_objecttype = Objecttype.objects.create(**params)
        second_objecttype.sites.add(site)

        context = get_archives_objecttypes('custom_template.html')
        self.assertEquals(len(context['archives']), 2)
        self.assertEquals(context['archives'][0], datetime(2010, 1, 1))
        self.assertEquals(context['archives'][1], datetime(2009, 1, 1))
        self.assertEquals(context['template'], 'custom_template.html')

    def test_get_archives_tree(self):
        context = get_archives_objecttypes_tree()
        self.assertEquals(len(context['archives']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/archives_objecttypes_tree.html')

        self.publish_objecttype()
        params = {'title': 'My second objecttype',
                  'content': 'My second content',
                  'tags': 'gstudio, test',
                  'status': PUBLISHED,
                  'creation_date': datetime(2009, 1, 10),
                  'slug': 'my-second-objecttype'}
        site = Site.objects.get_current()
        second_objecttype = Objecttype.objects.create(**params)
        second_objecttype.sites.add(site)

        context = get_archives_objecttypes_tree('custom_template.html')
        self.assertEquals(len(context['archives']), 2)
        self.assertEquals(context['archives'][0], datetime(2009, 1, 10))
        self.assertEquals(context['archives'][1], datetime(2010, 1, 1))
        self.assertEquals(context['template'], 'custom_template.html')

    def test_get_calendar_objecttypes(self):
        source_context = Context()
        context = get_calendar_objecttypes(source_context)
        self.assertEquals(context['previous_month'], None)
        self.assertEquals(context['next_month'], None)
        self.assertEquals(context['template'], 'gstudio/tags/calendar.html')

        self.publish_objecttype()
        context = get_calendar_objecttypes(source_context,
                                       template='custom_template.html')
        self.assertEquals(context['previous_month'], datetime(2010, 1, 1))
        self.assertEquals(context['next_month'], None)
        self.assertEquals(context['template'], 'custom_template.html')

        context = get_calendar_objecttypes(source_context, 2009, 1)
        self.assertEquals(context['previous_month'], None)
        self.assertEquals(context['next_month'], datetime(2010, 1, 1))

        source_context = Context({'month': datetime(2009, 1, 1)})
        context = get_calendar_objecttypes(source_context)
        self.assertEquals(context['previous_month'], None)
        self.assertEquals(context['next_month'], datetime(2010, 1, 1))

        source_context = Context({'month': datetime(2010, 1, 1)})
        context = get_calendar_objecttypes(source_context)
        self.assertEquals(context['previous_month'], None)
        self.assertEquals(context['next_month'], None)

        params = {'title': 'My second objecttype',
                  'content': 'My second content',
                  'tags': 'gstudio, test',
                  'status': PUBLISHED,
                  'creation_date': datetime(2008, 1, 1),
                  'slug': 'my-second-objecttype'}
        site = Site.objects.get_current()
        second_objecttype = Objecttype.objects.create(**params)
        second_objecttype.sites.add(site)

        source_context = Context()
        context = get_calendar_objecttypes(source_context, 2009, 1)
        self.assertEquals(context['previous_month'], datetime(2008, 1, 1))
        self.assertEquals(context['next_month'], datetime(2010, 1, 1))
        context = get_calendar_objecttypes(source_context)
        self.assertEquals(context['previous_month'], datetime(2010, 1, 1))
        self.assertEquals(context['next_month'], None)

    def test_get_recent_comments(self):
        site = Site.objects.get_current()
        context = get_recent_comments()
        self.assertEquals(len(context['comments']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/recent_comments.html')

        comment_1 = comments.get_model().objects.create(
            comment='My Comment 1', site=site,
            content_object=self.objecttype)
        context = get_recent_comments(3, 'custom_template.html')
        self.assertEquals(len(context['comments']), 0)
        self.assertEquals(context['template'], 'custom_template.html')

        self.publish_objecttype()
        context = get_recent_comments()
        self.assertEquals(len(context['comments']), 1)

        author = User.objects.create_user(username='webmaster',
                                          email='webmaster@example.com')
        comment_2 = comments.get_model().objects.create(
            comment='My Comment 2', site=site,
            content_object=self.objecttype)
        comment_2.flags.create(user=author,
                               flag=CommentFlag.MODERATOR_APPROVAL)
        context = get_recent_comments()
        self.assertEquals(list(context['comments']), [comment_2, comment_1])

    def test_get_recent_linkbacks(self):
        user = User.objects.create_user(username='webmaster',
                                        email='webmaster@example.com')
        site = Site.objects.get_current()
        context = get_recent_linkbacks()
        self.assertEquals(len(context['linkbacks']), 0)
        self.assertEquals(context['template'],
                          'gstudio/tags/recent_linkbacks.html')

        linkback_1 = comments.get_model().objects.create(
            comment='My Linkback 1', site=site,
            content_object=self.objecttype)
        linkback_1.flags.create(user=user, flag='pingback')
        context = get_recent_linkbacks(3, 'custom_template.html')
        self.assertEquals(len(context['linkbacks']), 0)
        self.assertEquals(context['template'], 'custom_template.html')

        self.publish_objecttype()
        context = get_recent_linkbacks()
        self.assertEquals(len(context['linkbacks']), 1)

        linkback_2 = comments.get_model().objects.create(
            comment='My Linkback 2', site=site,
            content_object=self.objecttype)
        linkback_2.flags.create(user=user, flag='trackback')
        context = get_recent_linkbacks()
        self.assertEquals(list(context['linkbacks']), [linkback_2, linkback_1])

    def test_gstudio_pagination(self):
        class FakeRequest(object):
            def __init__(self, get_dict):
                self.GET = get_dict

        source_context = Context({'request': FakeRequest(
            {'page': '1', 'key': 'val'})})
        paginator = Paginator(range(200), 10)

        context = gstudio_pagination(source_context, paginator.page(1))
        self.assertEquals(context['page'].number, 1)
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [18, 19, 20])
        self.assertEquals(context['GET_string'], '&key=val')
        self.assertEquals(context['template'], 'gstudio/tags/pagination.html')

        source_context = Context({'request': FakeRequest({})})
        context = gstudio_pagination(source_context, paginator.page(2))
        self.assertEquals(context['page'].number, 2)
        self.assertEquals(context['begin'], [1, 2, 3, 4])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [18, 19, 20])
        self.assertEquals(context['GET_string'], '')

        context = gstudio_pagination(source_context, paginator.page(3))
        self.assertEquals(context['begin'], [1, 2, 3, 4, 5])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(6))
        self.assertEquals(context['begin'], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(11))
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [9, 10, 11, 12, 13])
        self.assertEquals(context['end'], [18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(15))
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [13, 14, 15, 16, 17, 18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(18))
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [16, 17, 18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(19))
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [17, 18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(20))
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [18, 19, 20])

        context = gstudio_pagination(source_context, paginator.page(10),
                                    begin_pages=1, end_pages=3,
                                    before_pages=4, after_pages=3,
                                    template='custom_template.html')
        self.assertEquals(context['begin'], [1])
        self.assertEquals(context['middle'], [6, 7, 8, 9, 10, 11, 12, 13])
        self.assertEquals(context['end'], [18, 19, 20])
        self.assertEquals(context['template'], 'custom_template.html')

        paginator = Paginator(range(50), 10)
        context = gstudio_pagination(source_context, paginator.page(1))
        self.assertEquals(context['begin'], [1, 2, 3, 4, 5])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [])

        paginator = Paginator(range(60), 10)
        context = gstudio_pagination(source_context, paginator.page(1))
        self.assertEquals(context['begin'], [1, 2, 3, 4, 5, 6])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [])

        paginator = Paginator(range(70), 10)
        context = gstudio_pagination(source_context, paginator.page(1))
        self.assertEquals(context['begin'], [1, 2, 3])
        self.assertEquals(context['middle'], [])
        self.assertEquals(context['end'], [5, 6, 7])

    def test_gstudio_breadcrumbs(self):
        class FakeRequest(object):
            def __init__(self, path):
                self.path = path

        source_context = Context({'request': FakeRequest('/')})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 1)
        self.assertEquals(context['breadcrumbs'][0].name, 'Blog')
        self.assertEquals(context['breadcrumbs'][0].url,
                          reverse('gstudio_objecttype_archive_index'))
        self.assertEquals(context['separator'], '/')
        self.assertEquals(context['template'], 'gstudio/tags/breadcrumbs.html')

        context = gstudio_breadcrumbs(source_context,
                                     '>', 'Weblog', 'custom_template.html')
        self.assertEquals(len(context['breadcrumbs']), 1)
        self.assertEquals(context['breadcrumbs'][0].name, 'Weblog')
        self.assertEquals(context['separator'], '>')
        self.assertEquals(context['template'], 'custom_template.html')

        source_context = Context(
            {'request': FakeRequest(self.objecttype.get_absolute_url()),
             'object': self.objecttype})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 5)

        cat_1 = Metatype.objects.create(title='Metatype 1', slug='metatype-1')
        source_context = Context(
            {'request': FakeRequest(cat_1.get_absolute_url()),
             'object': cat_1})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 3)
        cat_2 = Metatype.objects.create(title='Metatype 2', slug='metatype-2',
                                        parent=cat_1)
        source_context = Context(
            {'request': FakeRequest(cat_2.get_absolute_url()),
             'object': cat_2})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 4)

        tag = Tag.objects.get(name='test')
        source_context = Context(
            {'request': FakeRequest(reverse('gstudio_tag_detail',
                                            args=['test'])),
             'object': tag})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 3)

        User.objects.create_user(username='webmaster',
                                 email='webmaster@example.com')
        author = Author.objects.get(username='webmaster')
        source_context = Context(
            {'request': FakeRequest(author.get_absolute_url()),
             'object': author})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 3)

        source_context = Context(
            {'request': FakeRequest(reverse(
                'gstudio_objecttype_archive_year', args=[2011]))})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 2)

        source_context = Context({'request': FakeRequest(reverse(
            'gstudio_objecttype_archive_month', args=[2011, '03']))})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 3)

        source_context = Context({'request': FakeRequest(reverse(
            'gstudio_objecttype_archive_day', args=[2011, '03', 15]))})
        context = gstudio_breadcrumbs(source_context)
        self.assertEquals(len(context['breadcrumbs']), 4)
        # More tests can be done here, for testing path and objects in context

    def test_get_gravatar(self):
        self.assertEquals(
            get_gravatar('webmaster@example.com'),
            'http://www.gravatar.com/avatar/86d4fd4a22de452'
            'a9228298731a0b592.jpg?s=80&amp;r=g')
        self.assertEquals(
            get_gravatar('  WEBMASTER@example.com  ', 15, 'x', '404'),
            'http://www.gravatar.com/avatar/86d4fd4a22de452'
            'a9228298731a0b592.jpg?s=15&amp;r=x&amp;d=404')

    def test_get_tags(self):
        Tag.objects.create(name='tag')
        t = Template("""
        {% load gstudio_tags %}
        {% get_tags as objecttype_tags %}
        {{ objecttype_tags|join:", " }}
        """)
        html = t.render(Context())
        self.assertEquals(html.strip(), '')
        self.publish_objecttype()
        html = t.render(Context())
        self.assertEquals(html.strip(), 'test, gstudio')

        template_error_as = """
        {% load gstudio_tags %}
        {% get_tags a_s objecttype_tags %}"""
        self.assertRaises(TemplateSyntaxError, Template, template_error_as)

        template_error_args = """
        {% load gstudio_tags %}
        {% get_tags as objecttype tags %}"""
        self.assertRaises(TemplateSyntaxError, Template, template_error_args)

    def test_get_tag_cloud(self):
        context = get_tag_cloud()
        self.assertEquals(len(context['tags']), 0)
        self.assertEquals(context['template'], 'gstudio/tags/tag_cloud.html')
        self.publish_objecttype()
        context = get_tag_cloud(6, 'custom_template.html')
        self.assertEquals(len(context['tags']), 2)
        self.assertEquals(context['template'], 'custom_template.html')