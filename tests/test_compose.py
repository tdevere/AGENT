import yaml


def test_compose_services():
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)

    services = compose.get('services', {})
    assert {'db', 'redis', 'api', 'client'}.issubset(services.keys())

    api_env = services['api']['environment']
    assert api_env['DATABASE_URL'] == 'mysql2://bibleuser:biblepass@db/bible_api'
    assert api_env['REDIS_URL'] == 'redis://redis:6379'
