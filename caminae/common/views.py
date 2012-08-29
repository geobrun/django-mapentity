from django.core.serializers import serialize
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils.encoding import force_unicode
from django.utils.functional import Promise, curry
from django.utils import simplejson
from django.views.generic import TemplateView
from django.views.generic.list import ListView


class HttpJSONResponse(HttpResponse):
    def __init__(self, content='', **kwargs):
        kwargs['content_type'] = 'application/json'
        super(HttpJSONResponse, self).__init__(content, **kwargs)


class DjangoJSONEncoder(DateTimeAwareJSONEncoder):
    """
    Taken (slightly modified) from:
    http://stackoverflow.com/questions/2249792/json-serializing-django-models-with-simplejson
    """
    def default(self, obj):
        # https://docs.djangoproject.com/en/dev/topics/serialization/#id2
        if isinstance(obj, Promise):
            return force_unicode(obj)
        if isinstance(obj, QuerySet):
            # `default` must return a python serializable
            # structure, the easiest way is to load the JSON
            # string produced by `serialize` and return it
            return simplejson.loads(serialize('json', obj))
        return super(DjangoJSONEncoder, self).default(obj)

# partial function, we can now use dumps(my_dict) instead
# of dumps(my_dict, cls=DjangoJSONEncoder)
json_django_dumps = curry(simplejson.dumps, cls=DjangoJSONEncoder)

class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    response_class = HttpJSONResponse

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return self.response_class(
            self.convert_context_to_json(context),
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        return json_django_dumps(context)


class JSONListView(JSONResponseMixin, ListView):
    """
    A generic view to serve a model as a layer.
    """
    pass


# Templates for QUnit testing
class QUnitView(TemplateView):
    template_name = "common/qunit/test_base.html"
    jsfiles = []

    def get_context_data(self, **kwargs):
        context = super(QUnitView, self).get_context_data(**kwargs)
        context['jsfiles'] = self.jsfiles
        return context


## Add tests here ##
qunit_views = dict(
    dijkstra=QUnitView.as_view(jsfiles=['js/dijkstra.js', 'core/test_dijkstra.js']),
)


# Reversing directly function using qunit_views.values() does not work, eg:
# [ reverse_lazy(qunit_view) for qunit_view in qunit_views.values() ]
qunit_views_urls = dict((name, reverse_lazy('common:jstest_%s' % name )) for name in qunit_views.keys())

def qunit_tests_list_json(request):
    """List all urls that may be test by an headless browser"""
    return HttpResponse(json_django_dumps(qunit_views_urls), content_type='application/json')


