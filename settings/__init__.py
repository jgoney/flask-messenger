from settings_common import *

# Conditionally import additional settings depending on whether we're developing or in production

# Can be set, for example by checking for a given environmental variable, or by detecting the hostname
production = False

if production:
    from settings_prod import *
else:
    from settings_dev import *