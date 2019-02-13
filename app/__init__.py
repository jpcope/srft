# Patch our entry point as early as possible for Gevent workers
from gevent.monkey import patch_all
patch_all()

from ddtrace import config
config.flask['distributed_tracing_enabled'] = True
config.flask['service_name'] = 'srft-test'

from flask import Flask

# This goes before any other module imports to prevent circular imports
app = Flask(__name__)

import app.routes as routes
