#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Resolution Thematic QR Poster Generator
for "Абай атындағы мектеп" (Kyzylorda)
Creates uniquely styled artistic posters:
  1. Басты кіреберіс: Classical architectural portal / pillars & welcome arch
  2. Асхана: Culinary plate with fork, knife & chef accents
  3. Актовый зал: Grand theater stage with velvet curtains & spotlight
  4. Спорт залы: Dynamic athletic sports stadium & court shield
  5. Кітапхана: Open book with bookmark ribbon & pages
"""

import os
import sys
import math
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://abai-school.vercel.app/"
if not BASE_URL.endswith('/'):
    BASE_URL += '/'

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "qr_codes")
os.makedirs(OUT_DIR, exist_ok=True)

# Try loading Windows system font or default
def get_font(size, bold=False):
    font_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

F_HEADER = get_font(26, bold=True)
F_SUBHEAD = get_font(18, bold=False)
F_TITLE = get_font(42, bold=True)
F_BADGE = get_font(20, bold=True)
F_FLOOR = get_font(22, bold=True)
F_INST_MAIN = get_font(24, bold=True)
F_INST_SUB = get_font(18, bold=False)
F_URL = get_font(16, bold=False)

W, H = 1000, 1400

def draw_open_book_poster(qr_img, target_url):
    """5. Кітапхана: Open book framing the QR code"""
    img = Image.new('RGB', (W, H), (248, 250, 252))
    d = ImageDraw.Draw(img)
    
    # Background subtle radial tint
    for r in range(700, 0, -20):
        c = int(248 - (700 - r) * 0.03)
        d.ellipse([(W//2 - r, 700 - r), (W//2 + r, 700 + r)], fill=(c, c + 3, c + 7))
        
    # Top Academic Header Banner
    d.rectangle([(0, 0), (W, 160)], fill=(15, 76, 129)) # Classic academic deep blue
    d.rectangle([(0, 154), (W, 160)], fill=(217, 119, 6)) # Gold stripe
    
    d.text((W // 2, 45), "АБАЙ АТЫНДАҒЫ ДАРЫНДЫ БАЛАЛАРҒА АРНАЛҒАН МЕКТЕП", fill=(255, 255, 255), font=F_HEADER, anchor="mm")
    d.text((W // 2, 90), "2D ІШКІ НАВИГАЦИЯ ЖҮЙЕСІ · DIGITAL TWIN", fill=(186, 230, 253), font=F_SUBHEAD, anchor="mm")
    d.text((W // 2, 125), "3-ҚАБАТ · КІТАПХАНА ЖӘНЕ ОҚУ КОБОРКИНГІ", fill=(254, 240, 138), font=F_BADGE, anchor="mm")
    
    # Title Section
    d.text((W // 2, 220), "📖 КІТАПХАНА ЖӘНЕ ОҚУ ЗАЛЫ", fill=(15, 76, 129), font=F_TITLE, anchor="mm")
    d.text((W // 2, 265), "«Кітап — білім бұлағы» · Ғылым мен өнер орталығы", fill=(100, 116, 139), font=F_SUBHEAD, anchor="mm")

    # ================= DRAW OPEN BOOK =================
    bx, by, bw, bh = 140, 310, 720, 680
    
    # Book Cover Base / Shadow
    d.rounded_rectangle([(bx - 12, by + 12), (bx + bw + 12, by + bh + 24)], radius=24, fill=(203, 213, 225))
    d.rounded_rectangle([(bx - 8, by - 4), (bx + bw + 8, by + bh + 8)], radius=24, fill=(180, 83, 9)) # Leather cover brown-gold
    
    # Book Pages (Left and Right page blocks)
    mid_x = W // 2
    # Left page
    d.rounded_rectangle([(bx + 8, by + 10), (mid_x - 6, by + bh - 8)], radius=18, fill=(255, 253, 245))
    # Right page
    d.rounded_rectangle([(mid_x + 6, by + 10), (bx + bw - 8, by + bh - 8)], radius=18, fill=(255, 253, 245))
    
    # Book spine shadow in middle
    for i in range(12):
        alpha = int(220 + i * 2.5)
        d.line([(mid_x - 6 + i, by + 10), (mid_x - 6 + i, by + bh - 8)], fill=(alpha, alpha - 5, alpha - 12), width=1)
        
    # Page side edges (stack of paper look)
    for p in range(5):
        d.line([(bx + 8 - p * 2, by + bh - 8 + p * 2), (mid_x - 6, by + bh - 8 + p * 2)], fill=(226, 232, 240))
        d.line([(mid_x + 6, by + bh - 8 + p * 2), (bx + bw - 8 + p * 2, by + bh - 8 + p * 2)], fill=(226, 232, 240))
        
    # Red/Gold Ribbon Bookmark hanging down
    d.polygon([(mid_x - 14, by + 4), (mid_x + 14, by + 4), (mid_x + 14, by + bh + 45), (mid_x, by + bh + 25), (mid_x - 14, by + bh + 45)], fill=(220, 38, 38))
    d.polygon([(mid_x - 10, by + 4), (mid_x + 10, by + 4), (mid_x + 10, by + bh + 38), (mid_x, by + bh + 22), (mid_x - 10, by + bh + 38)], fill=(239, 68, 68))

    # Paste QR Code in center of open book
    qw, qh = qr_img.size
    qx = (W - qw) // 2
    qy = by + (bh - qh) // 2 - 10
    
    # White card frame for QR
    d.rounded_rectangle([(qx - 14, qy - 14), (qx + qw + 14, qy + qh + 14)], radius=16, fill=(255, 255, 255), outline=(217, 119, 6), width=3)
    img.paste(qr_img, (qx, qy))
    
    # Instructions Section
    d.text((W // 2, 1050), "📷 Телефон камерасымен осы QR-кодты сканерлеңіз", fill=(15, 23, 42), font=F_INST_MAIN, anchor="mm")
    d.text((W // 2, 1090), "Мектеп картасы бірден 3-қабаттағы Кітапханадан бастап ашылады", fill=(71, 85, 105), font=F_INST_SUB, anchor="mm")
    d.text((W // 2, 1125), "Кез келген сыныпқа немесе залға маршрут сызып береді", fill=(100, 116, 139), font=F_INST_SUB, anchor="mm")
    
    # Footer link bar
    d.rounded_rectangle([(80, 1180), (W - 80, 1250)], radius=12, fill=(241, 245, 249), outline=(203, 213, 225))
    d.text((W // 2, 1215), f"🌐 {target_url}", fill=(71, 85, 105), font=F_URL, anchor="mm")
    
    return img


def draw_cafe_poster(qr_img, target_url):
    """2. Асхана: Culinary plate with fork & knife theme"""
    img = Image.new('RGB', (W, H), (255, 251, 245))
    d = ImageDraw.Draw(img)
    
    # Top Header
    d.rectangle([(0, 0), (W, 160)], fill=(180, 83, 9)) # Warm culinary amber-gold
    d.rectangle([(0, 154), (W, 160)], fill=(245, 158, 11))
    
    d.text((W // 2, 45), "АБАЙ АТЫНДАҒЫ ДАРЫНДЫ БАЛАЛАРҒА АРНАЛҒАН МЕКТЕП", fill=(255, 255, 255), font=F_HEADER, anchor="mm")
    d.text((W // 2, 90), "2D ІШКІ НАВИГАЦИЯ ЖҮЙЕСІ · DIGITAL TWIN", fill=(254, 243, 199), font=F_SUBHEAD, anchor="mm")
    d.text((W // 2, 125), "1-ҚАБАТ · БАТЫС ҚАНАТ · МЕКТЕП АСХАНАСЫ", fill=(254, 252, 232), font=F_BADGE, anchor="mm")
    
    # Title
    d.text((W // 2, 220), "🍽️ МЕКТЕП АСХАНАСЫ", fill=(180, 83, 9), font=F_TITLE, anchor="mm")
    d.text((W // 2, 265), "«Ас — адамның арқауы» · Тәтті әрі құнарлы ас болсын!", fill=(146, 64, 14), font=F_SUBHEAD, anchor="mm")

    # ================= DRAW DINNER PLATE =================
    cx, cy = W // 2, 640
    pr = 310 # Plate outer radius
    
    # Plate drop shadow
    d.ellipse([(cx - pr + 8, cy - pr + 12), (cx + pr + 8, cy + pr + 12)], fill=(229, 231, 235))
    # Plate rim (warm porcelain white with golden edge)
    d.ellipse([(cx - pr, cy - pr), (cx + pr, cy + pr)], fill=(255, 255, 255), outline=(217, 119, 6), width=6)
    # Inner plate circle
    d.ellipse([(cx - pr + 35, cy - pr + 35), (cx + pr - 35, cy + pr - 35)], fill=(254, 252, 247), outline=(245, 158, 11), width=2)
    
    # Draw Fork on left
    fx = 120
    # Fork handle
    d.rounded_rectangle([(fx - 7, cy - 220), (fx + 7, cy + 220)], radius=7, fill=(148, 163, 184))
    d.rounded_rectangle([(fx - 18, cy - 230), (fx + 18, cy - 140)], radius=6, fill=(148, 163, 184))
    # 4 tines
    for t in range(4):
        tx = fx - 14 + t * 9
        d.rounded_rectangle([(tx - 2, cy - 290), (tx + 2, cy - 210)], radius=2, fill=(100, 116, 139))
        
    # Draw Knife on right
    kx = W - 120
    # Knife handle
    d.rounded_rectangle([(kx - 7, cy - 140), (kx + 7, cy + 220)], radius=7, fill=(148, 163, 184))
    # Knife blade
    d.polygon([(kx - 6, cy - 140), (kx + 16, cy - 200), (kx + 16, cy - 280), (kx - 6, cy - 290)], fill=(100, 116, 139))

    # Paste QR in center of plate
    qw, qh = qr_img.size
    qx = cx - qw // 2
    qy = cy - qh // 2
    d.rounded_rectangle([(qx - 12, qy - 12), (qx + qw + 12, qy + qh + 12)], radius=16, fill=(255, 255, 255), outline=(245, 158, 11), width=3)
    img.paste(qr_img, (qx, qy))

    # Instructions
    d.text((W // 2, 1050), "📷 Телефон камерасымен осы QR-кодты сканерлеңіз", fill=(15, 23, 42), font=F_INST_MAIN, anchor="mm")
    d.text((W // 2, 1090), "Мектеп картасы бірден Асханадан бастап ашылады", fill=(71, 85, 105), font=F_INST_SUB, anchor="mm")
    d.text((W // 2, 1125), "Асханадан кез келген кабинетке дейінгі жолды көріңіз", fill=(100, 116, 139), font=F_INST_SUB, anchor="mm")
    
    # Footer link bar
    d.rounded_rectangle([(80, 1180), (W - 80, 1250)], radius=12, fill=(254, 243, 199), outline=(251, 191, 36))
    d.text((W // 2, 1215), f"🌐 {target_url}", fill=(146, 64, 14), font=F_URL, anchor="mm")
    
    return img


def draw_entrance_poster(qr_img, target_url):
    """1. Басты кіреберіс: Classical architectural portal / pillars & welcome arch"""
    img = Image.new('RGB', (W, H), (240, 249, 255))
    d = ImageDraw.Draw(img)
    
    # Header
    d.rectangle([(0, 0), (W, 160)], fill=(14, 116, 144)) # Cyan-teal architecture
    d.rectangle([(0, 154), (W, 160)], fill=(34, 211, 238))
    
    d.text((W // 2, 45), "АБАЙ АТЫНДАҒЫ ДАРЫНДЫ БАЛАЛАРҒА АРНАЛҒАН МЕКТЕП", fill=(255, 255, 255), font=F_HEADER, anchor="mm")
    d.text((W // 2, 90), "2D ІШКІ НАВИГАЦИЯ ЖҮЙЕСІ · DIGITAL TWIN", fill=(207, 250, 254), font=F_SUBHEAD, anchor="mm")
    d.text((W // 2, 125), "1-ҚАБАТ · ОРТАЛЫҚ ВЕСТИБЮЛЬ · БАСТЫ КІРЕБЕРІС", fill=(254, 240, 138), font=F_BADGE, anchor="mm")
    
    # Title
    d.text((W // 2, 220), "🏛️ ҚОШ КЕЛДІҢІЗДЕР! · БАСТЫ КІРЕБЕРІС", fill=(14, 116, 144), font=F_TITLE, anchor="mm")
    d.text((W // 2, 265), "Мектептің бас ғимаратына қош келдіңіз · 1-қабат Вестибюль", fill=(71, 85, 105), font=F_SUBHEAD, anchor="mm")

    # ================= DRAW ARCHITECTURAL PORTAL =================
    ax1, ax2 = 140, W - 140
    top_y = 330
    bot_y = 970
    
    # Pediment Triangle on top
    d.polygon([(W // 2, top_y - 30), (ax1 - 20, top_y + 40), (ax2 + 20, top_y + 40)], fill=(14, 116, 144))
    d.polygon([(W // 2, top_y - 15), (ax1, top_y + 35), (ax2, top_y + 35)], fill=(6, 182, 212))
    
    # Welcome banner on pediment
    d.rounded_rectangle([(W // 2 - 160, top_y + 10), (W // 2 + 160, top_y + 55)], radius=10, fill=(255, 255, 255))
    d.text((W // 2, top_y + 32), "✨ ОРТАЛЫҚ ВЕСТИБЮЛЬ ✨", fill=(14, 116, 144), font=F_BADGE, anchor="mm")
    
    # Left pillar
    d.rectangle([(ax1, top_y + 60), (ax1 + 50, bot_y)], fill=(207, 250, 254), outline=(14, 116, 144), width=3)
    # Pillar grooves
    for g in range(3):
        gx = ax1 + 12 + g * 12
        d.line([(gx, top_y + 75), (gx, bot_y - 15)], fill=(103, 232, 249), width=2)
    # Pillar base & capital
    d.rectangle([(ax1 - 10, top_y + 50), (ax1 + 60, top_y + 70)], fill=(14, 116, 144))
    d.rectangle([(ax1 - 10, bot_y - 10), (ax1 + 60, bot_y + 10)], fill=(14, 116, 144))

    # Right pillar
    d.rectangle([(ax2 - 50, top_y + 60), (ax2, bot_y)], fill=(207, 250, 254), outline=(14, 116, 144), width=3)
    for g in range(3):
        gx = ax2 - 50 + 12 + g * 12
        d.line([(gx, top_y + 75), (gx, bot_y - 15)], fill=(103, 232, 249), width=2)
    d.rectangle([(ax2 - 60, top_y + 50), (ax2 + 10, top_y + 70)], fill=(14, 116, 144))
    d.rectangle([(ax2 - 60, bot_y - 10), (ax2 + 10, bot_y + 10)], fill=(14, 116, 144))
    
    # Inner arch background
    d.rounded_rectangle([(ax1 + 70, top_y + 80), (ax2 - 70, bot_y)], radius=24, fill=(255, 255, 255), outline=(14, 116, 144), width=2)

    # Paste QR in portal center
    qw, qh = qr_img.size
    qx = (W - qw) // 2
    qy = top_y + (bot_y - top_y - qh) // 2 + 15
    d.rounded_rectangle([(qx - 12, qy - 12), (qx + qw + 12, qy + qh + 12)], radius=16, fill=(255, 255, 255), outline=(6, 182, 212), width=4)
    img.paste(qr_img, (qx, qy))

    # Instructions
    d.text((W // 2, 1050), "📷 Телефон камерасымен осы QR-кодты сканерлеңіз", fill=(15, 23, 42), font=F_INST_MAIN, anchor="mm")
    d.text((W // 2, 1090), "Мектеп картасы бірден осы Басты кіреберістен ашылады", fill=(71, 85, 105), font=F_INST_SUB, anchor="mm")
    d.text((W // 2, 1125), "Кез келген кабинетті таңдап, маршрутты көріңіз", fill=(100, 116, 139), font=F_INST_SUB, anchor="mm")
    
    # Footer link bar
    d.rounded_rectangle([(80, 1180), (W - 80, 1250)], radius=12, fill=(207, 250, 254), outline=(103, 232, 249))
    d.text((W // 2, 1215), f"🌐 {target_url}", fill=(14, 116, 144), font=F_URL, anchor="mm")
    
    return img


def draw_assembly_poster(qr_img, target_url):
    """3. Актовый зал: Grand theater stage with velvet curtains & spotlight"""
    img = Image.new('RGB', (W, H), (250, 245, 255))
    d = ImageDraw.Draw(img)
    
    # Header
    d.rectangle([(0, 0), (W, 160)], fill=(88, 28, 135)) # Royal deep purple
    d.rectangle([(0, 154), (W, 160)], fill=(168, 85, 247))
    
    d.text((W // 2, 45), "АБАЙ АТЫНДАҒЫ ДАРЫНДЫ БАЛАЛАРҒА АРНАЛҒАН МЕКТЕП", fill=(255, 255, 255), font=F_HEADER, anchor="mm")
    d.text((W // 2, 90), "2D ІШКІ НАВИГАЦИЯ ЖҮЙЕСІ · DIGITAL TWIN", fill=(243, 232, 255), font=F_SUBHEAD, anchor="mm")
    d.text((W // 2, 125), "1-ҚАБАТ · СОЛТҮСТІК БЛОК · АКТОВЫЙ ЗАЛ", fill=(254, 240, 138), font=F_BADGE, anchor="mm")
    
    # Title
    d.text((W // 2, 220), "🎭 АКТОВЫЙ ЗАЛ (МӘЖІЛІС ЗАЛЫ)", fill=(88, 28, 135), font=F_TITLE, anchor="mm")
    d.text((W // 2, 265), "Мәдениет, өнер және салтанатты іс-шаралар орталығы", fill=(107, 33, 168), font=F_SUBHEAD, anchor="mm")

    # ================= DRAW THEATER CURTAINS & STAGE =================
    sx, sy, sw, sh = 120, 310, 760, 680
    
    # Stage floor (wood plank look)
    d.rounded_rectangle([(sx, sy + sh - 80), (sx + sw, sy + sh)], radius=12, fill=(180, 83, 9))
    d.rectangle([(sx, sy + sh - 10), (sx + sw, sy + sh)], fill=(120, 53, 15))
    
    # Spotlight Cone in background
    d.polygon([(W // 2, sy), (sx + 80, sy + sh - 80), (sx + sw - 80, sy + sh - 80)], fill=(255, 255, 255))
    
    # Left Curtain (Velvet Drape with folds)
    d.polygon([(sx, sy), (sx + 130, sy), (sx + 80, sy + sh - 80), (sx, sy + sh - 80)], fill=(126, 34, 206))
    d.polygon([(sx, sy), (sx + 90, sy), (sx + 40, sy + sh - 80), (sx, sy + sh - 80)], fill=(147, 51, 234))
    # Curtain tieback gold rope
    d.arc([(sx + 20, sy + 320), (sx + 80, sy + 380)], 0, 180, fill=(234, 179, 8), width=6)
    
    # Right Curtain
    d.polygon([(sx + sw, sy), (sx + sw - 130, sy), (sx + sw - 80, sy + sh - 80), (sx + sw, sy + sh - 80)], fill=(126, 34, 206))
    d.polygon([(sx + sw, sy), (sx + sw - 90, sy), (sx + sw - 40, sy + sh - 80), (sx + sw, sy + sh - 80)], fill=(147, 51, 234))
    d.arc([(sx + sw - 80, sy + 320), (sx + sw - 20, sy + 380)], 0, 180, fill=(234, 179, 8), width=6)

    # Top Scalloped Valance Curtain
    d.rectangle([(sx, sy), (sx + sw, sy + 50)], fill=(126, 34, 206))
    for sc in range(8):
        sc_x = sx + sc * (sw // 8)
        d.chord([(sc_x, sy + 25), (sc_x + (sw // 8), sy + 75)], 0, 180, fill=(147, 51, 234), outline=(234, 179, 8), width=3)

    # Paste QR in center stage
    qw, qh = qr_img.size
    qx = (W - qw) // 2
    qy = sy + (sh - qh) // 2 + 10
    d.rounded_rectangle([(qx - 14, qy - 14), (qx + qw + 14, qy + qh + 14)], radius=18, fill=(255, 255, 255), outline=(147, 51, 234), width=4)
    img.paste(qr_img, (qx, qy))

    # Instructions
    d.text((W // 2, 1050), "📷 Телефон камерасымен осы QR-кодты сканерлеңіз", fill=(15, 23, 42), font=F_INST_MAIN, anchor="mm")
    d.text((W // 2, 1090), "Мектеп картасы бірден Актовый залдан бастап ашылады", fill=(71, 85, 105), font=F_INST_SUB, anchor="mm")
    d.text((W // 2, 1125), "Залдан шығып, мектептің кез келген жеріне бағыт алыңыз", fill=(100, 116, 139), font=F_INST_SUB, anchor="mm")
    
    # Footer link bar
    d.rounded_rectangle([(80, 1180), (W - 80, 1250)], radius=12, fill=(243, 232, 255), outline=(216, 180, 254))
    d.text((W // 2, 1215), f"🌐 {target_url}", fill=(107, 33, 168), font=F_URL, anchor="mm")
    
    return img


def draw_gym_poster(qr_img, target_url):
    """4. Спорт залы: Dynamic athletic sports stadium & court shield"""
    img = Image.new('RGB', (W, H), (240, 253, 244))
    d = ImageDraw.Draw(img)
    
    # Header
    d.rectangle([(0, 0), (W, 160)], fill=(4, 120, 87)) # Emerald sports green
    d.rectangle([(0, 154), (W, 160)], fill=(52, 211, 153))
    
    d.text((W // 2, 45), "АБАЙ АТЫНДАҒЫ ДАРЫНДЫ БАЛАЛАРҒА АРНАЛҒАН МЕКТЕП", fill=(255, 255, 255), font=F_HEADER, anchor="mm")
    d.text((W // 2, 90), "2D ІШКІ НАВИГАЦИЯ ЖҮЙЕСІ · DIGITAL TWIN", fill=(209, 250, 229), font=F_SUBHEAD, anchor="mm")
    d.text((W // 2, 125), "2-ҚАБАТ · ҮЛКЕН СПОРТ КЕШЕНІ · СПОРТ ЗАЛЫ", fill=(254, 240, 138), font=F_BADGE, anchor="mm")
    
    # Title
    d.text((W // 2, 220), "🏀 СПОРТ ЗАЛЫ (ҮЛКЕН КЕШЕН)", fill=(4, 120, 87), font=F_TITLE, anchor="mm")
    d.text((W // 2, 265), "«Дені саудың — жаны сау» · Салауатты өмір салты", fill=(6, 95, 70), font=F_SUBHEAD, anchor="mm")

    # ================= DRAW SPORTS SHIELD / COURT =================
    cx, cy = W // 2, 640
    sw, sh = 680, 680
    
    # Court Shield Base
    d.rounded_rectangle([(cx - sw // 2, cy - sh // 2), (cx + sw // 2, cy + sh // 2)], radius=32, fill=(255, 255, 255), outline=(5, 150, 105), width=6)
    
    # Basketball court lines background inside shield
    # Court center circle
    d.ellipse([(cx - 160, cy - 160), (cx + 160, cy + 160)], outline=(167, 243, 208), width=3)
    d.line([(cx - sw // 2 + 10, cy), (cx + sw // 2 - 10, cy)], fill=(167, 243, 208), width=3)
    
    # Top and bottom 3-point arcs
    d.arc([(cx - 240, cy - sh // 2 - 80), (cx + 240, cy - sh // 2 + 240)], 0, 180, fill=(167, 243, 208), width=3)
    d.arc([(cx - 240, cy + sh // 2 - 240), (cx + 240, cy + sh // 2 + 80)], 180, 360, fill=(167, 243, 208), width=3)

    # Paste QR in center
    qw, qh = qr_img.size
    qx = cx - qw // 2
    qy = cy - qh // 2
    d.rounded_rectangle([(qx - 14, qy - 14), (qx + qw + 14, qy + qh + 14)], radius=18, fill=(255, 255, 255), outline=(16, 185, 129), width=4)
    img.paste(qr_img, (qx, qy))

    # Instructions
    d.text((W // 2, 1050), "📷 Телефон камерасымен осы QR-кодты сканерлеңіз", fill=(15, 23, 42), font=F_INST_MAIN, anchor="mm")
    d.text((W // 2, 1090), "Мектеп картасы автоматты түрде 2-ҚАБАТТАҒЫ Спорт залдан ашылады", fill=(71, 85, 105), font=F_INST_SUB, anchor="mm")
    d.text((W // 2, 1125), "Спорт залдан кез келген кабинетке дейінгі маршрутты көріңіз", fill=(100, 116, 139), font=F_INST_SUB, anchor="mm")
    
    # Footer link bar
    d.rounded_rectangle([(80, 1180), (W - 80, 1250)], radius=12, fill=(209, 250, 229), outline=(110, 231, 183))
    d.text((W // 2, 1215), f"🌐 {target_url}", fill=(4, 120, 87), font=F_URL, anchor="mm")
    
    return img


def make_qr(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert('RGB')


print(f"Generating Artistically Themed QR Posters for: {BASE_URL}")

POSTERS = [
    ("1_Басты_кіреберіс", "entrance", draw_entrance_portal := draw_entrance_poster),
    ("2_Асхана", "cafe", draw_cafe_poster),
    ("3_Актовый_зал", "assembly", draw_assembly_poster),
    ("4_Спорт_залы", "gym", draw_gym_poster),
    ("5_Кітапхана", "library", draw_open_book_poster),
]

for filename, spot, func in POSTERS:
    target_url = f"{BASE_URL}?spot={spot}"
    qr_img = make_qr(target_url)
    poster = func(qr_img, target_url)
    out_path = os.path.join(OUT_DIR, f"{filename}.png")
    poster.save(out_path, format="PNG", quality=95)
    print(f"  [+] Saved {out_path} -> {target_url}")

print(f"\nAll 5 Thematic Posters generated successfully in {OUT_DIR}!")
