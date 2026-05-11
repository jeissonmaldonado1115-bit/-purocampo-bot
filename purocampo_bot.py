import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ── CONFIG ──────────────────────────────────────────────

TOKEN         = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

logging.basicConfig(level=logging.INFO)

# ── MENÚ ────────────────────────────────────────────────

MENU = [
    # Cortes Premium
    {"num": 1,  "nombre": "Solomito de Cerdo",  "precio": 24900, "unidad": "kg",     "seccion": "CORTES PREMIUM"},
    {"num": 2,  "nombre": "Lomo de Cerdo",       "precio": 24900, "unidad": "kg",     "seccion": "CORTES PREMIUM"},
    {"num": 3,  "nombre": "Costilla San Luis",   "precio": 28500, "unidad": "kg",     "seccion": "CORTES PREMIUM"},
    {"num": 4,  "nombre": "Tocineta Barriguero", "precio": 28500, "unidad": "kg",     "seccion": "CORTES PREMIUM"},
    {"num": 5,  "nombre": "Chicharrón Especial", "precio": 25900, "unidad": "kg",     "seccion": "CORTES PREMIUM"},
    # Cortes
    {"num": 6,  "nombre": "Molida de Cerdo",     "precio": 23900, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 7,  "nombre": "Masa de Cerdo",       "precio": 23900, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 8,  "nombre": "Chorizos Premium",    "precio": 23000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 9,  "nombre": "Bondiola",            "precio": 23000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 10, "nombre": "Costilla de Cerdo",   "precio": 23000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 11, "nombre": "Goulash Sin Hueso",   "precio": 21000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 12, "nombre": "Chuleta Sin Piel",    "precio": 21000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 13, "nombre": "Loncha de Pernil",    "precio": 21000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 14, "nombre": "Pernil de Cerdo",     "precio": 22000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 15, "nombre": "Costilla Sin Piel",   "precio": 27500, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 16, "nombre": "Chuleta Con Piel",    "precio": 19800, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 17, "nombre": "Loncha de Brazo",     "precio": 17800, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 18, "nombre": "Papada",              "precio": 16800, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 19, "nombre": "Contracodillo",       "precio": 14000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 20, "nombre": "Oreja de Cerdo",      "precio": 10000, "unidad": "kg",     "seccion": "CORTES"},
    {"num": 21, "nombre": "Tocino Corriente",    "precio": 7500,  "unidad": "kg",     "seccion": "CORTES"},
    {"num": 22, "nombre": "Pezuña",              "precio": 7000,  "unidad": "kg",     "seccion": "CORTES"},
    # Vísceras
    {"num": 23, "nombre": "Espinazo",            "precio": 4900,  "unidad": "kg",     "seccion": "VÍSCERAS"},
    {"num": 24, "nombre": "Asadura",             "precio": 4000,  "unidad": "kg",     "seccion": "VÍSCERAS"},
    {"num": 25, "nombre": "Cabeza de Cerdo",     "precio": 2000,  "unidad": "kg",     "seccion": "VÍSCERAS"},
    # Huevos
    {"num": 26, "nombre": "Huevo Tipo A",        "precio": 14000, "unidad": "cubeta", "seccion": "HUEVOS"},
    {"num": 27, "nombre": "Huevo Doble AA",      "precio": 17000, "unidad": "cubeta", "seccion": "HUEVOS"},
    {"num": 28, "nombre": "Huevo Triple AAA",    "precio": 21000, "unidad": "cubeta", "seccion": "HUEVOS"},
    # Lácteos
    {"num": 29, "nombre": "Queso",               "precio": 25000, "unidad": "kg",     "seccion": "LÁCTEOS"},
]

SECCIONES = ["CORTES PREMIUM", "CORTES", "VÍSCERAS", "HUEVOS", "LÁCTEOS"]

# ── ESTADOS ─────────────────────────────────────────────

CHAT, ESPERANDO_CANTIDAD, DIRECCION, NOMBRE, TELEFONO, CONFIRMACION = range(6)

# ── HELPERS ─────────────────────────────────────────────

def fmt_price(n):
    return f"${n:,.0f}".replace(",", ".")

def menu_texto():
    lines = ["📋 *Catálogo Puro Campo*\n"]
    for sec in SECCIONES:
        items = [p for p in MENU if p["seccion"] == sec]
        if not items:
            continue
        label = sec
        if sec == "HUEVOS":
            label = "HUEVOS (por cubeta)"
        lines.append(f"*{label}*")
        for p in items:
            lines.append(f"`{str(p['num']).zfill(2)}` {p['nombre']} — {fmt_price(p['precio'])}/{p['unidad']}")
        lines.append("")
    lines.append("✏️ Escribe el *número* del producto que deseas")
    return "\n".join(lines)

def teclado_principal():
    return ReplyKeyboardMarkup(
        [["📋 Ver menú", "🛒 Mi pedido"],
         ["✅ Finalizar pedido", "🛵 Domicilio"]],
        resize_keyboard=True
    )

def teclado_pago():
    return ReplyKeyboardMarkup(
        [["💜 Nequi", "🔴 Daviplata", "💵 Efectivo"]],
        resize_keyboard=True
    )

def get_carrito(ctx):
    return ctx.user_data.get("carrito", [])

def get_total(ctx):
    return sum(i["subtotal"] for i in get_carrito(ctx))

def resumen_carrito(ctx):
    carrito = get_carrito(ctx)
    if not carrito:
        return "Tu carrito está vacío."
    lines = []
    for item in carrito:
        lines.append(f"• {item['nombre']} × {item['cantidad']} {item['unidad']} = {fmt_price(item['subtotal'])}")
    lines.append(f"\n💰 *Total: {fmt_price(get_total(ctx))}*")
    return "\n".join(lines)

# ── NOTIFICACIÓN AL ADMIN ────────────────────────────────

async def notificar_admin(context, datos):
    if not ADMIN_CHAT_ID:
        return
    carrito = datos["carrito"]
    lines = ["🔔 *NUEVO PEDIDO — Puro Campo*\n"]
    for item in carrito:
        lines.append(f"• {item['nombre']} × {item['cantidad']} {item['unidad']} = {fmt_price(item['subtotal'])}")
    total = sum(i["subtotal"] for i in carrito)
    lines.append(f"\n💰 *Total: {fmt_price(total)}*")
    lines.append(f"💳 *Pago:* {datos['metodo_pago']}")
    lines.append(f"📍 *Dirección:* {datos['direccion']}")
    lines.append(f"👤 *Nombre:* {datos['nombre']}")
    lines.append(f"📱 *WhatsApp:* {datos['telefono']}")
    lines.append(f"🔖 *Pedido #:* {datos['numero_pedido']}")
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text="\n".join(lines),
        parse_mode="Markdown"
    )

# ── HANDLERS ────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["carrito"] = []
    await update.message.reply_text(
        "¡Bienvenido a *Puro Campo*! 🐷\n\n"
        "Cerdo fresco directo de la finca · Cartagena\n\n"
        "Escribe *\"menu\"* o toca 📋 *Ver menú* para ver el catálogo.\n"
        "Luego escribe el número del producto y te pregunto la cantidad.",
        parse_mode="Markdown",
        reply_markup=teclado_principal()
    )
    return CHAT

async def chat_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t  = update.message.text.strip()
    tl = t.lower()

    # Ver menú
    if any(x in tl for x in ["menu", "carta", "catalogo", "ver menú", "📋"]):
        await update.message.reply_text(menu_texto(), parse_mode="Markdown")
        return CHAT

    # Mi pedido
    if any(x in tl for x in ["mi pedido", "carrito", "🛒"]):
        carrito = get_carrito(ctx)
        if not carrito:
            await update.message.reply_text("No tiene productos aún 😅\n\nEscriba *menu* para ver el catálogo.", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"*Su pedido actual* 🛒\n\n{resumen_carrito(ctx)}\n\nEscriba otro número para seguir o toque *✅ Finalizar pedido*",
                parse_mode="Markdown"
            )
        return CHAT

    # Finalizar
    if any(x in tl for x in ["finalizar", "listo", "pagar", "✅"]):
        carrito = get_carrito(ctx)
        if not carrito:
            await update.message.reply_text("No tiene productos en el pedido aún 😅", parse_mode="Markdown")
            return CHAT
        await update.message.reply_text(
            f"*Su pedido:*\n\n{resumen_carrito(ctx)}\n\n¿Cómo prefiere pagar?",
            parse_mode="Markdown",
            reply_markup=teclado_pago()
        )
        return CHAT

    # Domicilio
    if any(x in tl for x in ["domicilio", "entrega", "envio", "🛵"]):
        await update.message.reply_text(
            "Hacemos domicilio en Cartagena 🛵\n"
            "Coordinamos fecha y dirección al confirmar el pedido.",
            reply_markup=teclado_principal()
        )
        return CHAT

    # Método de pago
    if any(x in tl for x in ["nequi", "💜"]):
        ctx.user_data["metodo_pago"] = "💜 Nequi (301 468 2572)"
        await update.message.reply_text(
            "💜 *Nequi* ✅\n\n¿A qué dirección le llevamos en Cartagena? 📍",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
        )
        return DIRECCION

    if any(x in tl for x in ["daviplata", "🔴"]):
        ctx.user_data["metodo_pago"] = "🔴 Daviplata"
        await update.message.reply_text(
            "🔴 *Daviplata* ✅\n\n¿A qué dirección le llevamos en Cartagena? 📍",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
        )
        return DIRECCION

    if any(x in tl for x in ["efectivo", "💵"]):
        ctx.user_data["metodo_pago"] = "💵 Efectivo"
        await update.message.reply_text(
            "💵 *Efectivo* ✅\n\n¿A qué dirección le llevamos en Cartagena? 📍",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
        )
        return DIRECCION

    # ── FIX: si hay producto activo, redirigir a esperando_cantidad ──
    if ctx.user_data.get("producto_activo"):
        return await esperando_cantidad(update, ctx)

    # Número de producto — solo acepta número solo sin texto adicional
    import re
    match = re.match(r'^(\d{1,2})$', t.strip())
    if match:
        num  = int(match.group(1))
        prod = next((p for p in MENU if p["num"] == num), None)
        if prod:
            ctx.user_data["producto_activo"] = prod
            u = "cubetas" if prod["unidad"] == "cubeta" else "kilos"
            await update.message.reply_text(
                f"*{prod['nombre']}*\n{fmt_price(prod['precio'])} por {prod['unidad']}\n\n¿Cuántos {u} desea?",
                parse_mode="Markdown"
            )
            return ESPERANDO_CANTIDAD
        else:
            await update.message.reply_text(
                f"No existe el producto *{num}*.\nEscriba *menu* para ver los números disponibles.",
                parse_mode="Markdown"
            )
        return CHAT

    await update.message.reply_text(
        "Escribe *menu* para ver el catálogo 📋\no el número del producto directamente.\n\nEj: *2* para Lomo · *26* para Huevo Tipo A",
        parse_mode="Markdown",
        reply_markup=teclado_principal()
    )
    return CHAT

async def esperando_cantidad(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import re
    t     = update.message.text.strip()
    match = re.search(r'(\d+(?:[.,]\d+)?)', t)
    if not match:
        await update.message.reply_text("Por favor escribe solo la cantidad. Ej: *2* o *1.5*", parse_mode="Markdown")
        return ESPERANDO_CANTIDAD

    cantidad = float(match.group(1).replace(",", "."))
    prod     = ctx.user_data.get("producto_activo")
    subtotal = prod["precio"] * cantidad
    carrito  = get_carrito(ctx)
    idx = next((i for i, x in enumerate(carrito) if x["num"] == prod["num"]), -1)
    if idx >= 0:
        carrito[idx]["cantidad"] += cantidad
        carrito[idx]["subtotal"] += subtotal
    else:
        carrito.append({**prod, "cantidad": cantidad, "subtotal": subtotal})
    ctx.user_data["carrito"] = carrito
    ctx.user_data["producto_activo"] = None

    u = "cubeta(s)" if prod["unidad"] == "cubeta" else "kg"
    await update.message.reply_text(
        f"✅ *{cantidad} {u} de {prod['nombre']}* — {fmt_price(subtotal)}\n\n"
        f"👉 Escribe otro número para seguir\n"
        f"✅ O toca *Finalizar pedido* para pagar",
        parse_mode="Markdown",
        reply_markup=teclado_principal()
    )
    return CHAT

async def pedir_direccion(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["direccion"] = update.message.text.strip()
    await update.message.reply_text("¿Cuál es su nombre completo?")
    return NOMBRE

async def pedir_nombre(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text("¿Su número de WhatsApp?")
    return TELEFONO

async def pedir_telefono(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import random
    ctx.user_data["telefono"]      = update.message.text.strip()
    numero_pedido                  = f"PC-{random.randint(10000,99999)}"
    ctx.user_data["numero_pedido"] = numero_pedido

    carrito   = get_carrito(ctx)
    total     = get_total(ctx)
    metodo    = ctx.user_data.get("metodo_pago", "")
    direccion = ctx.user_data.get("direccion", "")
    nombre    = ctx.user_data.get("nombre", "")
    telefono  = ctx.user_data.get("telefono", "")

    lines = [f"📋 *Resumen del pedido #{numero_pedido}*\n"]
    for item in carrito:
        lines.append(f"• {item['nombre']} × {item['cantidad']} {item['unidad']} = {fmt_price(item['subtotal'])}")
    lines.append(f"\n💰 *Total: {fmt_price(total)}*\n")
    lines.append("─────────────────")
    lines.append(f"💳 *Pago:* {metodo}")
    if "Nequi" in metodo:
        lines.append(f"📲 *Número Nequi:* 301 468 2572")
    lines.append(f"📍 *Dirección:* {direccion}")
    lines.append(f"👤 *Nombre:* {nombre}")
    lines.append(f"📱 *WhatsApp:* {telefono}")
    lines.append("\n¿Confirma su pedido?")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["✅ Confirmar", "❌ Cancelar"]], resize_keyboard=True)
    )
    return CONFIRMACION

async def confirmar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.strip().lower()
    if "confirm" in t or "✅" in t:
        datos = {
            "carrito":       get_carrito(ctx),
            "metodo_pago":   ctx.user_data.get("metodo_pago", ""),
            "direccion":     ctx.user_data.get("direccion", ""),
            "nombre":        ctx.user_data.get("nombre", ""),
            "telefono":      ctx.user_data.get("telefono", ""),
            "numero_pedido": ctx.user_data.get("numero_pedido", ""),
        }
        await notificar_admin(ctx, datos)
        nombre = datos["nombre"]
        await update.message.reply_text(
            f"🎉 *¡Pedido confirmado!*\n\n"
            f"En breve le contactamos al *{datos['telefono']}* para coordinar la entrega.\n\n"
            f"¡Gracias, {nombre}! 🐷\n\n"
            f"*Puro Campo · Del campo a tu mesa*",
            parse_mode="Markdown",
            reply_markup=teclado_principal()
        )
        ctx.user_data["carrito"] = []
        return CHAT
    else:
        await update.message.reply_text(
            "Pedido cancelado ❌\n\nPuede seguir agregando productos o escribir *menu* para ver el catálogo.",
            parse_mode="Markdown",
            reply_markup=teclado_principal()
        )
        return CHAT

async def cancelar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["carrito"] = []
    await update.message.reply_text("Conversación reiniciada. Escriba /start para comenzar.", reply_markup=teclado_principal())
    return CHAT

# ── MAIN ────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler)],
        states={
            CHAT:               [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler)],
            ESPERANDO_CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, esperando_cantidad)],
            DIRECCION:          [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_direccion)],
            NOMBRE:             [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_nombre)],
            TELEFONO:           [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_telefono)],
            CONFIRMACION:       [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=false,
    )

    app.add_handler(conv)
    print("🐷 Bot Puro Campo iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
