from django.conf import settings
from django.http import Http404
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse

from social.utils import setting_name
from social.actions import do_auth, do_complete, do_disconnect
from social.strategies.utils import get_strategy
from social.apps.django_app.utils import psa, BACKENDS, STORAGE
from social.apps.django_app.views import _do_login


STRATEGY = getattr(settings, setting_name('STRATEGY'),
                   'social_auth.strategy.DSAStrategy')


def load_strategy(*args, **kwargs):
    return get_strategy(STRATEGY, STORAGE, *args, **kwargs)


def get_backend(backends, backend, strategy):
    for item in backends:
        path, name = item.rsplit('.', 1)
        module = __import__(path, globals(), locals(), [path])
        klass = getattr(module, name)
        if klass.name == backend:
            uri = reverse('socialauth_complete', kwargs={'backend': backend})
            return klass(strategy, redirect_uri=uri)


@psa('socialauth_complete', load_strategy=load_strategy)
def auth(request, backend):
    backend = get_backend(BACKENDS, backend, request.strategy)
    if backend:
        return do_auth(backend, redirect_name=REDIRECT_FIELD_NAME)
    raise Http404


@csrf_exempt
@psa('socialauth_complete', load_strategy=load_strategy)
def complete(request, backend, *args, **kwargs):
    backend = get_backend(BACKENDS, backend, request.strategy)
    if backend:
        return do_complete(
            backend, _do_login, request.user,
            redirect_name=REDIRECT_FIELD_NAME,
            *args, **kwargs
        )
    raise Http404


@login_required
@psa(load_strategy=load_strategy)
@require_POST
@csrf_protect
def disconnect(request, backend, association_id=None):
    return do_disconnect(request.strategy, request.user, association_id,
                         redirect_name=REDIRECT_FIELD_NAME)
