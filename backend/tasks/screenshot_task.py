from .celery_worker import celery
from .models import Transaction
from playwright.sync_api import sync_playwright
from io import BytesIO
from ..extensions import db


def enqueue_receipt_screenshot(tx_ref):
    # in production, call the celery task
    gen_receipt_image.delay(tx_ref)

@celery.task()
def gen_receipt_image(tx_ref):
    tx = Transaction.query.filter_by(tx_ref=tx_ref).first()
    if not tx:
        return {'error':'not found'}
    html = f"<html><body><h1>Receipt {tx.tx_ref}</h1><p>Amount: {tx.amount}</p></body></html>"
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width":900,"height":600})
        page.set_content(html, wait_until='networkidle')
        png = page.screenshot(full_page=True)
        browser.close()
    # In a real app you'd upload to S3 or store in DB; here we simply return size
    return {'tx_ref': tx_ref, 'png_bytes': len(png)}
