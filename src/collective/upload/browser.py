# -*- coding: utf-8 -*-

import json

from Acquisition import aq_inner

from five import grok
from zope.container.interfaces import INameChooser
from zope.component import queryMultiAdapter
from zope.interface import Interface

from plone.directives import dexterity

from collective.upload.interfaces import IUploadBrowserLayer

IMAGE_MIMETYPES = ['image/jpeg', 'image/gif', 'image/png']

grok.templatedir('templates')


# TODO: implement drag&drop here
class Folder_Contents(grok.View):
    grok.context(Interface)
    grok.layer(IUploadBrowserLayer)
    grok.require('cmf.ModifyPortalContent')


# XXX: do we really need dexterity.DisplayForm?
# TODO: rename view
class Organize(dexterity.DisplayForm):
    grok.context(IUploadBrowserLayer)
    grok.require('cmf.ModifyPortalContent')


# XXX: do we really need dexterity.DisplayForm?
# TODO: convert into a folder action: Upload files and images
class Media_Uploader(dexterity.DisplayForm):
    grok.context(IUploadBrowserLayer)
    grok.require('cmf.ModifyPortalContent')

    files = []

    def __call__(self, *args, **kwargs):
        if hasattr(self.request, "REQUEST_METHOD"):
            json_view = queryMultiAdapter((self.context, self.request),
                                          name=u"api")
            if self.request["REQUEST_METHOD"] == "POST":
                if getattr(self.request, "files[]", None) is not None:
                    files = self.request['files[]']
                    uploaded = self.upload([files])
                    if uploaded and json_view:
                        upped = []
                        for item in uploaded:
                            upped.append(json_view.getContextInfo(item))
                        return json_view.dumps(upped)
                return json_view()
        return super(Media_Uploader, self).__call__(*args, **kwargs)

    def upload(self, files):
        loaded = []
        namechooser = INameChooser(self.context)
        if not isinstance(files, list):
            files = [files]
        for item in files:
            if item.filename:
                content_type = item.headers.get('Content-Type')
                id_name = namechooser.chooseName(item.filename, self.context)
                portal_type = 'File'
                if content_type in IMAGE_MIMETYPES:
                    portal_type = 'Image'
                try:
                    self.context.invokeFactory(portal_type, id=id_name, file=item)
                    self.context[id_name].reindexObject()
                    newfile = self.context[id_name]
                    loaded.append(newfile)
                except:
                    pass
            if loaded:
                return loaded
            return False


class JSON_View(grok.View):
    grok.context(IUploadBrowserLayer)
    grok.name('api')
    grok.require('cmf.ModifyPortalContent')

    json_var = {'name': 'File-Name.jpg',
                'size': 999999,
                'url': '\/\/nohost.org',
                'thumbnail_url': '//nohost.org',
                'delete_url': '//nohost.org',
                'delete_type': 'DELETE',
                }

    def __call__(self):
        self.response.setHeader('Content-Type', 'text/plain')
        return super(JSON_View, self).__call__()

    def dumps(self, json_var=None):
        """ """
        if json_var is None:
            json_var = {}
        return json.dumps(json_var)

    def getContextInfo(self, context=None):
        if context is None:
            context = self.context
        context = aq_inner(context)

        context_state = queryMultiAdapter((context, self.request),
                                        name=u'plone_context_state')
        context_name = context_state.object_title()
        context_url = context_state.object_url()
        del_url = context_url
        info = {'name': context_name,
                'url':  context_url,
                'size': context.size(),
                'delete_url':  del_url,
                'delete_type': 'DELETE',
                }
        if context.Type() == 'Image':
            info['thumbnail_url'] = context_url + '/image_thumb'
        return info

    def getContainerInfo(self):
        contents = []
        for item in self.context.objectIds():
            item_info = self.getContextInfo(self.context[item])
            contents.append(item_info)
        return contents

    def render(self):
        return self.dumps(self.getContainerInfo())
