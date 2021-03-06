# -*- coding: utf-8 -*-
import binascii
from Crypto.Cipher import Blowfish

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.importlib import import_module
from django.utils.translation import gettext as _
from django.db import models

from engines.gdb.utils import get_deploy_status

default_engine = settings.GRAPHDATABASES["default"]["ENGINE"]


def get_upload_to(instance, filename):
    return u"private/%s/%s" % (instance.owner.username, filename)


class Instance(models.Model):
    name = models.CharField(_("name"), max_length=100)
    engine = models.CharField(_("engine"), max_length=50,
                              default=default_engine)
    SCHEME_TYPES = (
        ("http", _("Hypertext Transfer Protocol (http)")),
        ("file", _("File URI scheme (file)")),
        ("https", _("Hypertext Transfer Protocol Secure (https)")),
    )
    scheme = models.CharField(_("scheme"), max_length=8, default="http",
                              choices=SCHEME_TYPES)
    host = models.CharField(_("host"), max_length=250, default="localhost",
                            null=True, blank=True,
                            help_text=_("Host name or unit label"))
    port = models.PositiveIntegerField(_("port"), max_length=10,
                                       default="7474", null=True, blank=True)
    path = models.CharField(_("path"), max_length=250, default="db/data",
                            help_text=_("URL or absolute file system path"))
    username = models.CharField(_("username"), max_length=250,
                                null=True, blank=True)
    encrypted_password = models.CharField(_("encrypted password"),
                                          max_length=32,
                                          null=True, blank=True,
                                          help_text=_("Agregated field"))
    plain_password = models.CharField(_("password"),
                                      max_length=50,
                                      null=True, blank=True,
                                      help_text=_("Type again to change"))
    query = models.TextField(_("query"), null=True, blank=True)
    fragment = models.TextField(_("fragment"), null=True, blank=True)
    key_file = models.FileField(_("Key file"), upload_to=get_upload_to,
                                null=True, blank=True,)
    cert_file = models.FileField(_("Cert file"), upload_to=get_upload_to,
                                 null=True, blank=True,)
    options = models.TextField(_("options"), null=True, blank=True)
    owner = models.ForeignKey(User, verbose_name=_('owner'),
                              related_name="instances")
    TYPE_TYPES = (
        ("private", _("Private")),
        ("public", _("Public")),
        ("shared", _("Shared")),
    )
    type = models.CharField(_("type"), max_length=8, default="private",
                            choices=TYPE_TYPES, null=True, blank=True)
    activation = models.CharField(_("activation code"), max_length=50,
                                  null=True, blank=True,
                                  help_text=_("Blank if already activated"))
    activated = models.NullBooleanField(_("activated"), default=True)

    def __init__(self, *args, **kwargs):
        super(Instance, self).__init__(*args, **kwargs)
        self._gdb = None

    def __unicode__(self):
        return u"%s ~ %s" % (self.name, self._get_connection_string())

    def save(self, *args, **kwargs):
        if self.plain_password:
            self._set_password(self.plain_password)
            self.plain_password = ""
        super(Instance, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('engines.views.edit', [str(self.id)])

    def _get_connection_string(self):
        if self.scheme == u"file":
            if self.host:
                connection_string = "%s://%s/%s" % (self.scheme, self.host,
                                                    self.path)
            else:
                connection_string = "%s://%s" % (self.scheme, self.path)
        else:
            if self.username and self.password and self.port:
                connection_string = "%s://%s:%s@%s:%s/%s/" % (self.scheme,
                                                              self.username,
                                                              self.password,
                                                              self.host,
                                                              self.port,
                                                              self.path)
            elif self.username and self.port:
                connection_string = "%s://%s@%s:%s/%s/" % (self.scheme,
                                                           self.username,
                                                           self.host,
                                                           self.port,
                                                           self.path)
            elif self.port:
                connection_string = "%s://%s:%s/%s/" % (self.scheme, self.host,
                                                        self.port, self.path)
            else:
                connection_string = "%s://%s/%s/" % (self.scheme, self.host,
                                                     self.path)
            if self.query:
                connection_string = "%?%s" % (connection_string, self.query)
            if self.fragment:
                connection_string = "%#%s" % (connection_string, self.fragment)
        return connection_string

    def get_gdb(self, graph=None):
        if not self._gdb:
            connection_dict = {
                "name": self.name,
                "scheme": self.scheme,
                "host": self.host,
                "port": self.port,
                "path": self.path,
                "username": self.username,
                "password": self.password,
                "query": self.query,
                "fragment": self.fragment,
                "key_file": self.key_cert and self.key_cert.file,
                "cert_file": self.cert_file and self.cert_file.file,
                "options": self.options,
            }
            connection_string = self._get_connection_string()
            module = import_module(self.engine)
            self._gdb = module.GraphDatabase(connection_string,
                                             connection_dict, graph)
        return self._gdb

    def _get_password(self):
        if not self.encrypted_password:
            return u""
        enc_obj = Blowfish.new(settings.SECRET_KEY)
        hex_password = binascii.a2b_hex(self.encrypted_password)
        return u"%s" % enc_obj.decrypt(hex_password).rstrip()

    def _set_password(self, value):
        if not value:
            self.encrypted_password = u""
        else:
            enc_obj = Blowfish.new(settings.SECRET_KEY)
            repeat = 8 - (len(value) % 8)
            value = value + " " * repeat
            self.encrypted_password = binascii.b2a_hex(enc_obj.encrypt(value))

    password = property(_get_password, _set_password)

    def get_status(self):
        return get_deploy_status(self.engine, self.name)
