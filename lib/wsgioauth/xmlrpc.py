# -*- coding: utf-8 -*-
# Lifted from repoze.bfg.xmlrpc!
import xmlrpclib
import webob

__all__ = ['xmlrpc_marshal', 'xmlrpc_response', 'parse_xmlrpc_request',
    'xmlrpc',]

def xmlrpc_marshal(data):
    """ Marshal a Python data structure into an XML document suitable
    for use as an XML-RPC response and return the document.  If
    ``data`` is an ``xmlrpclib.Fault`` instance, it will be marshalled
    into a suitable XML-RPC fault response."""
    if isinstance(data, xmlrpclib.Fault):
        return xmlrpclib.dumps(data)
    else:
        return xmlrpclib.dumps((data,),  methodresponse=True)

def xmlrpc_response(data):
    """ Marshal a Python data structure into a webob ``Response``
    object with a body that is an XML document suitable for use as an
    XML-RPC response with a content-type of ``text/xml`` and return
    the response."""
    xml = xmlrpc_marshal(data)
    response = webob.Response(xml)
    response.content_type = 'text/xml'
    response.content_length = len(xml)
    return response

def parse_xmlrpc_request(request):
    """ Deserialize the body of a request from an XML-RPC request
    document into a set of params and return a two-tuple.  The first
    element in the tuple is the method params as a sequence, the
    second element in the tuple is the method name."""
    if request.content_length > (1 << 23):
        # protect from DOS (> 8MB body)
        raise ValueError('Body too large (%s bytes)' % request.content_length)
    params, method = xmlrpclib.loads(request.body)
    return params, method

def xmlrpc(wrapped):
    """ Function meant to be used as a decorator.  The ``xmlrpc``
    function turns functions which accept params and return Python
    structures into functions.  The decorated function must accept a
    ``context`` argument and zero or more positional arguments
    (conventionally named ``*params``).

    E.g.::

      from wsgioauth.xmlrpc import xmlrpc

      @xmlrpc
      def say(context, what):
          if what == 'hello'
              return {'say':'Hello!'}
          else:
              return {'say':'Goodbye!'}

    Equates to::

      from wsgioauth.xmlrpc import parse_xmlrpc_request
      from wsgioauth.xmlrpc import xmlrpc_response

      def say_view(context, request):
          params, method = parse_xmlrpc_request(request)
          return say(context, *params)

      def say(context, what):
          if what == 'hello'
              return {'say':'Hello!'}
          else:
              return {'say':'Goodbye!'}

    Note that if you use ``repoze.bfg.convention``, you must decorate your
    view function in the following order for it to be recognized by the
    convention machinery as a view::

      @xmlrpc
      def say(context, what):
          if what == 'hello'
              return {'say':'Hello!'}
          else:
              return {'say':'Goodbye!'}

    """
    
    def _curried(context, request):
        params, method = parse_xmlrpc_request(request)
        value = wrapped(context, *params)
        return xmlrpc_response(value)
    _curried.__name__ = wrapped.__name__
    _curried.__grok_module__ = wrapped.__module__ # r.bfg.convention support

    return _curried