# Either import these settings in your base.py or write your own.

MCHANGA_PAYMENT_METHODS = (
    {
        'provider': 'mchanga',
        'id': 'mchanga-mpesa',
        'profile': 'mpesa',
        'name': 'M-PESA',
        'restricted_countries': ('KE',),
        'supports_recurring': False,
    },
    {
        'provider': 'mchanga',
        'id': 'mchanga-airtel',
        'profile': 'airtel',
        'name': 'Airtel',
        'restricted_countries': ('KE',),
        'supports_recurring': False,
    },
)
