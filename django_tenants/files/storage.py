import os
import urllib.parse

from django.conf import settings
from django.utils.functional import cached_property

from django.core.files.storage import FileSystemStorage

from django_tenants import utils


class TenantFileSystemStorage(FileSystemStorage):
    """
    Implementation that extends core Django's FileSystemStorage for multi-tenant setups.
    """
    def _clear_cached_properties(self, setting, **kwargs):
        """Reset setting based property values."""
        super()._clear_cached_properties(settings, **kwargs)

        if setting == 'MULTITENANT_RELATIVE_MEDIA_ROOT':
            self.__dict__.pop('relative_media_root', None)

    @cached_property
    def relative_media_root(self):
        try:
            return os.path.join(settings.MEDIA_ROOT, settings.MULTITENANT_RELATIVE_MEDIA_ROOT)
        except AttributeError:
            # MULTITENANT_RELATIVE_MEDIA_ROOT is an optional setting, use the default value if none provided
            return settings.MEDIA_ROOT

    @cached_property
    def relative_media_url(self):
        try:
            multitenant_relative_url = settings.MULTITENANT_RELATIVE_MEDIA_ROOT
        except AttributeError:
            # MULTITENANT_RELATIVE_MEDIA_ROOT is an optional setting. Use the default of just appending
            # the tenant schema_name to STATIC_ROOT if no configuration value is provided
            multitenant_relative_url = "%s"

        multitenant_relative_url = urllib.parse.urljoin(settings.MEDIA_URL, multitenant_relative_url)

        if not multitenant_relative_url.endswith('/'):
            multitenant_relative_url += '/'

        return multitenant_relative_url

    @property  # Not cached like in parent class
    def base_location(self):
        relative_tenant_media_root = utils.parse_tenant_config_path(self.relative_media_root)

        if self._location is None:
            return relative_tenant_media_root

        return os.path.join(self._location, relative_tenant_media_root)

    @property  # Not cached like in parent class
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        relative_tenant_media_url = utils.parse_tenant_config_path(self.relative_media_url)

        if self._base_url is None:
            return relative_tenant_media_url

        relative_tenant_media_url = urllib.parse.urljoin(self._base_url, relative_tenant_media_url)

        return relative_tenant_media_url

    def listdir(self, path):
        """
        More forgiving wrapper for parent class implementation that does not insist on
        each tenant having its own static files dir.
        """
        try:
            return super().listdir(path)
        except FileNotFoundError:
            # Having static files for each tenant is optional - ignore.
            return [], []
