from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPOk, HTTPSeeOther, HTTPNotFound, HTTPBadRequest, HTTPInternalServerError
from pyramid.renderers import render_to_response
from collections import namedtuple
from sqlalchemy.orm import joinedload

from tfhnode.models import *
from tfhpanel.forms import *
from tfhpanel.models import PanelView

import logging
log = logging.getLogger(__name__)

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('pyramid')

def filter_owned(field, query, request):
    return query.filter_by(userid = request.user.id)


class VHostForm(Form):
    name = TextField(_('Name'), min_len=1, max_len=32, regexp='^[a-zA-Z0-9_-]+$')
    catchall = TextField(_('Fallback URI'), required=False, min_len=1, max_len=256)
    autoindex = CheckboxField(_('Autoindex'))
    domains = OneToManyField(_('Domains'), required=False, fm=Domain,
        qf=[filter_owned])

class VHostPanel(PanelView):
    model = VHost
    formclass = VHostForm
    list_fields = [
        (_('Name'), 'name'),
        (_('Domains'), 'domains'),
    ]


class DomainForm(Form):
    domain = TextField(_('Name'), min_len=1, max_len=256)
    vhost = ForeignField(_('VHost'), fm=VHost, qf=[filter_owned])
    hostedns = CheckboxField(_('Hosted NS'))
    public = CheckboxField(_('Public'))
    verified = CheckboxField(_('Verified'), readonly=True)

class DomainPanel(PanelView):
    model = Domain
    formclass = DomainForm
    list_fields = [
        (_('Domain'), 'domain'),
        (_('VHost'), 'vhost'),
        (_('Verified'), 'verified'),
    ]
    
    def read(self):
        d = super().read()
        d['left_template'] = 'domain/view_status.mako'
        return d

def mailbox_destination(mailbox):
    if mailbox.redirect:
        return _('Redirect: ') + mailbox.redirect
    if mailbox.password:
        return _('No password or redirect.')
    return ''


class MailboxForm(Form):
    domain = ForeignField(_('Domain'), fm=Domain, qf=[filter_owned])
    local_part = TextField(_('Local part'), min_len=1, max_len=64)
    redirect = TextField(_('Redirect (if any)'), required=False,
        min_len=1, max_len=512)
    password = PasswordField(_('Password (required to accept mails)'), required=False)

class MailboxPanel(PanelView):
    model = Mailbox
    formclass = MailboxForm
    list_fields = [
        (_('Address'), 'address'),
        (_('Destination'), mailbox_destination),
    ]
    
    def read(self):
        d = super().read()
        d['aliases'] = DBSession.query(Mailbox).filter_by(redirect=d['object'].address).all()
        d['left_template'] = 'mailbox/view_aliases.mako'
        return d


class VHostRewriteForm(Form):
    regexp = TextField(_('RegExp'), min_len=1, max_len=256)
    dest = TextField(_('Rewrite to'), min_len=1, max_len=256)
    redirect_temp = CheckboxField(_('Temporary redirect (302)'))
    redirect_perm = CheckboxField(_('Permanent redirect (301)'))
    last = CheckboxField(_('Last'))

class VHostRewritePanel(PanelView):
    model = VHostRewrite
    formclass = VHostRewriteForm
    parent = VHostPanel
    list_fields = [
        (_('Regular Exception'), 'regexp'),
        (_('Destination'), 'dest'),
    ]


class VHostACLForm(Form):
    title = TextField(_('Title'), min_len=1, max_len=256)
    regexp = TextField(_('RegExp'), min_len=1, max_len=256)
    passwd = TextField(_('passwd file'), min_len=1, max_len=256)

class VHostACLPanel(PanelView):
    model = VHostACL
    formclass = VHostACLForm
    parent = VHostPanel
    list_fields = [
        (_('Title'), 'title'),
        (_('Regular Expression'), 'regexp'),
    ]


class VHostErrorPageForm(Form):
    code = IntegerField(_('Error code'))
    path = TextField(_('Page URI'), min_len=1, max_len=256)

class VHostErrorPagePanel(PanelView):
    model = VHostErrorPage
    formclass = VHostErrorPageForm
    parent = VHostPanel
    list_fields = [
        (_('Code'), 'code'),
        (_('Page'), 'page'),
    ]

