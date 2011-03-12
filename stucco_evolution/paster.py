from paste.script.templates import Template, var
from paste.util.template import paste_script_template_renderer

class EvolveModule(Template):
    """Create a stucco_evolution evolution module."""
    _template_dir = '+template+'
    summary = 'Create a stucco_evolution evolution module.'
    template_renderer = staticmethod(paste_script_template_renderer)
