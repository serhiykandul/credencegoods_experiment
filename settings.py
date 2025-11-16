from os import environ

SESSION_CONFIGS = [
    dict(
        name='credencegoods_baseline',
        app_sequence=['credencegoodsBJS','demographics'],
        num_demo_participants=16,
    ),
    dict(
        name='credencegoods_exogenous',
        app_sequence=['credencegoodsBJS_Exo','demographics'],
        num_demo_participants=16,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1/7, participation_fee=5.00, doc=""  # 7 points = 1 EUR
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'fr'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '9189722916302'
