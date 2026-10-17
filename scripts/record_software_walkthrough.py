import os
import sys
import time
import subprocess
import threading
from playwright.sync_api import sync_playwright
import imageio_ffmpeg

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from config import Config

class DemoConfig(Config):
    WTF_CSRF_ENABLED = False  # Allows smooth simulated walkthrough
    TESTING = False

def run_server(port=5055):
    app = create_app(DemoConfig)
    # Run quietly
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

def record_walkthrough():
    port = 5055
    base_url = f"http://127.0.0.1:{port}"

    print("1. Starting local demo server on port", port)
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to bind

    temp_video_dir = os.path.abspath("temp_video_recordings")
    os.makedirs(temp_video_dir, exist_ok=True)
    final_mp4 = os.path.abspath("arch_realty_software_walkthrough.mp4")

    print("2. Launching browser recorder via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=[
                "--start-maximized",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=temp_video_dir,
            record_video_size={"width": 1440, "height": 900}
        )

        page = context.new_page()

        # Helper for smooth visual scrolling
        def smooth_scroll(y_amount, steps=10, delay=0.08):
            for i in range(steps):
                page.evaluate(f"window.scrollBy(0, {y_amount / steps})")
                time.sleep(delay)

        def add_banner(text, subtext=""):
            page.evaluate(f"""
                (function() {{
                    var old = document.getElementById('demo-scene-banner');
                    if (old) old.remove();
                    var b = document.createElement('div');
                    b.id = 'demo-scene-banner';
                    b.style.position = 'fixed';
                    b.style.bottom = '24px';
                    b.style.right = '24px';
                    b.style.background = 'rgba(15, 23, 42, 0.92)';
                    b.style.color = '#ffffff';
                    b.style.padding = '12px 20px';
                    b.style.borderRadius = '10px';
                    b.style.boxShadow = '0 10px 25px rgba(0,0,0,0.3)';
                    b.style.zIndex = '99999';
                    b.style.fontFamily = 'Inter, -apple-system, sans-serif';
                    b.style.borderLeft = '4px solid #3b82f6';
                    b.style.backdropFilter = 'blur(6px)';
                    b.style.transition = 'all 0.3s ease';
                    b.innerHTML = '<strong style="display:block; font-size:14px; color:#60a5fa;">{text}</strong>' +
                                  '<span style="font-size:12px; color:#cbd5e1;">{subtext}</span>';
                    document.body.appendChild(b);
                }})()
            """)

        print("3. Recording Scene 1: Login Portal & 1-Click Role Switcher...")
        page.goto(f"{base_url}/auth/login", wait_until="networkidle")
        add_banner("ARCH Realty ERP+CRM", "Enterprise Real Estate Management Platform")
        time.sleep(2)

        add_banner("1-Click Unified Role Access", "Instant switching between Admin, Sales, Field, Finance, HR, Marketing & IT")
        time.sleep(1.5)
        # Use 1-click credential filler
        page.evaluate("fillCreds('admin', 'admin123')")
        time.sleep(1.2)
        page.locator("button[type='submit']").first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        print("4. Recording Scene 2: Top Header Universal Check-In & GPS Tracing...")
        add_banner("Universal Department GPS Check-In", "Real-time coordinate tracing & micro-market location logging")
        time.sleep(1.5)
        # Click Check In button in header
        checkin_btn = page.locator("button:has-text('Check In')").first
        if checkin_btn.is_visible():
            checkin_btn.click()
            time.sleep(2)
            # Confirm check-in in modal
            confirm_btn = page.locator("#punch-submit-btn")
            if confirm_btn.is_visible():
                confirm_btn.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)

        print("5. Recording Scene 3: Central Command Center & Executive KPIs...")
        add_banner("Executive Command Center", "Active inquiries, Receivables pipeline & Real-time Staff Status")
        time.sleep(1.5)
        smooth_scroll(450, steps=12, delay=0.07)
        time.sleep(1.5)
        smooth_scroll(500, steps=12, delay=0.07)
        time.sleep(1.5)
        smooth_scroll(-950, steps=15, delay=0.05)
        time.sleep(1.5)

        print("6. Recording Scene 4: Sales CRM & Client Shortlisting...")
        add_banner("Sales CRM & Lead Inquiries", "Full qualification pipeline, client requirements & deal stages")
        page.goto(f"{base_url}/crm/leads", wait_until="networkidle")
        time.sleep(2)
        smooth_scroll(350, steps=8, delay=0.06)
        time.sleep(1.5)
        page.goto(f"{base_url}/shortlisting/", wait_until="networkidle")
        add_banner("Client Shortlisting", "AI-powered property matching & client preference tracking")
        time.sleep(2)

        print("7. Recording Scene 5: Property Inventory & Smart Matching...")
        add_banner("Commercial & Residential Inventory", "Active listings, Pre-Leased assets & Mandates")
        page.goto(f"{base_url}/properties/", wait_until="networkidle")
        time.sleep(2)
        smooth_scroll(400, steps=10, delay=0.06)
        time.sleep(1.5)

        print("8. Recording Scene 6: Finance & Brokerage Receivables...")
        add_banner("Finance & Brokerage Management", "Realized commissions, invoicing, TDS & operating expenses")
        page.goto(f"{base_url}/finance/", wait_until="networkidle")
        time.sleep(2)
        smooth_scroll(450, steps=10, delay=0.06)
        time.sleep(1.5)

        print("9. Recording Scene 7: HR Operations & Department Attendance Radar...")
        add_banner("Department Attendance Radar", "Live Leaflet mapping of check-ins with department filters")
        page.goto(f"{base_url}/hr/attendance", wait_until="networkidle")
        time.sleep(2)
        smooth_scroll(400, steps=10, delay=0.06)
        time.sleep(2)
        # Filter by department
        sales_pill = page.locator("a:has-text('Sales')").first
        if sales_pill.is_visible():
            sales_pill.click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
        field_pill = page.locator("a:has-text('Field Ops')").first
        if field_pill.is_visible():
            field_pill.click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)

        print("10. Recording Scene 8: Unified Digital Marketing & IT...")
        add_banner("Unified Digital Marketing & IT", "Ad campaigns (CPL/CTR), IT asset inventory & ticketing")
        page.goto(f"{base_url}/marketing/", wait_until="networkidle")
        time.sleep(2)
        page.goto(f"{base_url}/it/", wait_until="networkidle")
        time.sleep(2)

        print("11. Recording Scene 9: Live GPS Tracking & Field Travel Radar...")
        add_banner("Live GPS Tracking Radar", "On-field executive movement, site visit audit trail & travel logs")
        page.goto(f"{base_url}/gps/", wait_until="networkidle")
        time.sleep(2)
        smooth_scroll(400, steps=10, delay=0.06)
        time.sleep(2)

        print("12. Recording Scene 10: Conclusion & Shift Check-Out...")
        page.goto(f"{base_url}/dashboard/", wait_until="networkidle")
        add_banner("End of Shift Check-Out", "Accurate hour calculation & location stamp")
        time.sleep(1.5)
        checkout_btn = page.locator("button:has-text('Check Out')").first
        if checkout_btn.is_visible():
            checkout_btn.click()
            time.sleep(1.5)
            confirm_out = page.locator("#punch-submit-btn")
            if confirm_out.is_visible():
                confirm_out.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)

        add_banner("ARCH Realty ERP+CRM", "Complete Real Estate Operating System • Ready for Production")
        time.sleep(3)

        print("13. Finalizing Playwright video recording...")
        page_video = page.video
        page.close()
        context.close()
        raw_video = page_video.path()
        browser.close()

    print(f"Recorded raw video: {raw_video} ({os.path.getsize(raw_video)} bytes)")

    # Convert to high-quality MP4 using imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"4. Transcoding to standard MP4 using ffmpeg: {final_mp4}")
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", raw_video,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-preset", "medium",
        "-crf", "22",
        final_mp4
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0 and os.path.exists(final_mp4):
        size_mb = os.path.getsize(final_mp4) / (1024 * 1024)
        print(f"SUCCESS! Video created at: {final_mp4} ({size_mb:.2f} MB)")
        # Clean up temp recordings
        try:
            for f in os.listdir(temp_video_dir):
                os.remove(os.path.join(temp_video_dir, f))
            os.rmdir(temp_video_dir)
        except Exception:
            pass
        return True
    else:
        print("FFmpeg conversion error:", res.stderr.decode('utf-8', errors='ignore'))
        return False

if __name__ == '__main__':
    record_walkthrough()
