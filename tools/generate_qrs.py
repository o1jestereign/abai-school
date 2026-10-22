#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code Generator for "Абай атындағы мектеп" (Kyzylorda)
Generates high-resolution branded QR codes for school locations.
"""

import os
import sys
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://abai-school.github.io/"
if not BASE_URL.endswith('/'):
    BASE_URL += '/'

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "qr_codes")
os.makedirs(OUT_DIR, exist_ok=True)

SPOTS = [
    {
        "id": "1_Басты_кіреберіс",
        "spot": "entrance",
        "title": "БАСТЫ КІРЕБЕРІС",
        "sub": "1-қабат · Орталық вестибюль",
        "color": (14, 116, 144)  # cyan-700
    },
    {
        "id": "2_Асхана",
        "spot": "cafe",
        "title": "МЕКТЕП АСХАНАСЫ",
        "sub": "1-қабат · Батыс қанат",
        "color": (217, 119, 6)   # amber-600
    },
    {
        "id": "3_Актовый_зал",
        "spot": "assembly",
        "title": "АКТОВЫЙ ЗАЛ",
        "sub": "1-қабат · Мәжіліс залы",
        "color": (147, 51, 234)  # purple-600
    },
    {
        "id": "4_Спорт_залы",
        "spot": "gym",
        "title": "СПОРТ ЗАЛЫ",
        "sub": "2-қабат · Үлкен спорт кешені",
        "color": (16, 185, 129)  # emerald-500
    },
    {
        "id": "5_Кітапхана",
        "spot": "library",
        "title": "КІТАПХАНА ЖӘНЕ ОҚУ ЗАЛЫ",
        "sub": "3-қабат · Орталық коворкинг",
        "color": (2, 132, 199)   # sky-600
    }
]

print(f"Generating QR codes using Base URL: {BASE_URL}")

for item in SPOTS:
    target_url = f"{BASE_URL}?spot={item['spot']}"
    
    # Create QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
    
    # Create Poster card (800 x 1050 px)
    card_w, card_h = 800, 1050
    card = Image.new('RGBA', (card_w, card_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(card)
    
    # Top header bar
    draw.rectangle([(0, 0), (card_w, 140)], fill=item['color'])
    
    # School header text
    draw.text((card_w // 2, 40), "АБАЙ АТЫНДАҒЫ МЕКТЕП (ҚЫЗЫЛОРДА)", fill=(255, 255, 255), anchor="mm")
    draw.text((card_w // 2, 85), "2D ІШКІ НАВИГАЦИЯ ЖҮЙЕСІ", fill=(224, 242, 254), anchor="mm")
    
    # Location badge / Title
    draw.text((card_w // 2, 210), item['title'], fill=item['color'], anchor="mm")
    draw.text((card_w // 2, 255), item['sub'], fill=(100, 116, 139), anchor="mm")
    
    # Paste QR in center
    qr_w, qr_h = qr_img.size
    qr_x = (card_w - qr_w) // 2
    qr_y = 310
    
    # Border around QR
    draw.rounded_rectangle([(qr_x - 16, qr_y - 16), (qr_x + qr_w + 16, qr_y + qr_h + 16)], radius=16, outline=item['color'], width=4)
    card.paste(qr_img, (qr_x, qr_y), qr_img)
    
    # Instruction text
    draw.text((card_w // 2, qr_y + qr_h + 60), "📷 Телефон камерасымен QR-кодты сканерлеңіз", fill=(15, 23, 42), anchor="mm")
    draw.text((card_w // 2, qr_y + qr_h + 95), "Мектеп картасы осы орыннан бастап бірден ашылады", fill=(100, 116, 139), anchor="mm")
    
    # Footer link
    draw.rectangle([(40, card_h - 75), (card_w - 40, card_h - 35)], fill=(241, 245, 249))
    draw.text((card_w // 2, card_h - 55), target_url, fill=(100, 116, 139), anchor="mm")
    
    out_path = os.path.join(OUT_DIR, f"{item['id']}.png")
    card.save(out_path, format="PNG")
    print(f"  [+] Saved: {out_path} -> {target_url}")

print(f"\nAll QR codes saved successfully in {OUT_DIR}")
