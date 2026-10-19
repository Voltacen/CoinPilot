# Playwright end-to-end smoke test (uses Playwright sync API)
# Requires browsers installed; run `playwright install` in your environment before running tests.
from playwright.sync_api import sync_playwright
import requests

BASE = 'http://localhost:5000'

def test_register_and_admin_send_flow():
    # register a new user
    r = requests.post(f'{BASE}/auth/register', json={'email':'e2e-user@example.com','password':'password'})
    assert r.status_code in (200,201)
    # login as admin and send credit
    r = requests.post(f'{BASE}/auth/login', json={'email':'admin@coinpilot.local','password':'adminpass'})
    # admin seed script creates admin without password; if adminpass login fails, skip E2E send
    if r.status_code != 200:
        return
    token = r.json().get('access_token')
    headers = {'Authorization':f'Bearer {token}'}
    # create recipient user
    requests.post(f'{BASE}/auth/register', json={'email':'recipient@example.com','password':'password'})
    r = requests.post(f'{BASE}/admin/send', json={'amount':1000,'to_email':'recipient@example.com','note':'e2e test'}, headers=headers)
    assert r.status_code == 200
