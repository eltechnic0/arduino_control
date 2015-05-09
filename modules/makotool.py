import os
import cherrypy
import mako.lookup

class TemplateTool(cherrypy.Tool):

  _engine = None
  '''Mako lookup instance'''


  def __init__(self, path):
    viewPath     = os.path.join(path, 'static')
    self._engine = mako.lookup.TemplateLookup(directories = [viewPath])

    cherrypy.Tool.__init__(self, 'before_handler', self.render)

  def __call__(self, *args, **kwargs):
    if args and isinstance(args[0], (types.FunctionType, types.MethodType)):
      # @template
      args[0].exposed = True
      return cherrypy.Tool.__call__(self, **kwargs)(args[0])
    else:
      # @template()
      def wrap(f):
        f.exposed = True
        return cherrypy.Tool.__call__(self, *args, **kwargs)(f)
      return wrap

  def render(self, name = None):
    cherrypy.request.config['template'] = name

    handler = cherrypy.serving.request.handler
    def wrap(*args, **kwargs):
      return self._render(handler, *args, **kwargs)
    cherrypy.serving.request.handler = wrap

  def _render(self, handler, *args, **kwargs):
    template = cherrypy.request.config['template']
    if not template:
      parts = []
      if hasattr(handler.callable, '__self__'):
        parts.append(handler.callable.__self__.__class__.__name__.lower())
      if hasattr(handler.callable, '__name__'):
        parts.append(handler.callable.__name__.lower())
      template = '/'.join(parts)

    data     = handler(*args, **kwargs) or {}
    renderer = self._engine.get_template('{}'.format(template))

    return renderer.render(**data)
