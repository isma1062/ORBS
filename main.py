import discord
from discord.ext import commands
import os
from google import genai

# ---------------- CONFIGURACIÓN ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)

# ----------------- TUS DATOS -----------------
OWNER_ID = 1375062145498091560  # Tu owner ID
TOKEN = "MTM0Njk0NzU0ODExNTUwNTI5NQ.Ggkchg.EGftadQ2TtRrtm2uJ8_axMFB2jIsyz0-K-zQsE"  # Pon aquí tu token
GEMINI_API_KEY = "AIzaSyAPPZnBpwtagEQ2bvRx0EStKG_V3SBLqtU"  # Pon aquí tu Gemini API Key

if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None
    print("⚠️ GEMINI_API_KEY no configurada. El chatbot no estará disponible.")

conversation_history = {}

PALABRAS_PROHIBIDAS = [
    "nopor", "porno", "sex", "xxx", "cp", "nsfw",
    "mierda", "puta", "idiota", "imbecil", "maldito"
]
ENLACES_PROHIBIDOS = [
    "porn", "xnxx", "xvideos", "onlyfans", "redtube", "sex", "adult"
]

# ---------------- EVENTOS ----------------

@bot.event
async def on_ready():
    print(f"✅ Orbs conectado como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Moderando I.C.A.P"))

@bot.event
async def on_member_join(member):
    canal = member.guild.system_channel
    if canal:
        await canal.send(f"👋 {member.mention}, bienvenido a **I.C.A.P** 🎉")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    contenido = message.content.lower()

    if any(p in contenido for p in PALABRAS_PROHIBIDAS) or any(l in contenido for l in ENLACES_PROHIBIDOS):
        try:
            await message.delete()
            aviso = await message.channel.send(
                f"🚫 {message.author.mention}, tu mensaje fue eliminado por contenido inapropiado."
            )
            await aviso.delete(delay=5)
        except discord.Forbidden:
            pass
        return

    if "hola orbs" in contenido or message.content.startswith("!orbs"):
        await message.channel.send(f"¡Hola {message.author.name}! 👋 Soy Orbs, el moderador de I.C.A.P. Puedo chatear contigo usando IA. ¡Pregúntame lo que quieras!")
    elif "rango" in contenido and not bot.user.mentioned_in(message):
        roles = [r.name for r in message.author.roles if r.name != "@everyone"]
        if roles:
            await message.channel.send(f"🧠 Tus rangos: {', '.join(roles)}")
        else:
            await message.channel.send("👀 No tienes ningún rango asignado aún.")
    elif bot.user.mentioned_in(message) or message.content.startswith("orbs "):
        if not gemini_client:
            await message.channel.send("❌ El chatbot IA no está disponible. Falta configurar GEMINI_API_KEY.")
            return
        
        user_id = message.author.id
        user_message = message.content.replace(f"<@{bot.user.id}>", "").replace("orbs ", "").strip()
        
        if not user_message:
            await message.channel.send("💬 ¡Hola! Soy Orbs con IA gratis de Google Gemini. ¿En qué puedo ayudarte?")
            return
        
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        conversation_history[user_id].append({"role": "user", "parts": [{"text": user_message}]})
        
        if len(conversation_history[user_id]) > 20:
            conversation_history[user_id] = conversation_history[user_id][-20:]
        
        try:
            async with message.channel.typing():
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        {"role": "user", "parts": [{"text": "Eres Orbs, un bot moderador amigable y útil del servidor de Discord I.C.A.P. Responde de forma concisa, amigable y en español. Tu personalidad es servicial y profesional."}]},
                        *conversation_history[user_id]
                    ]
                )
                
                ai_response = response.text
                conversation_history[user_id].append({"role": "model", "parts": [{"text": ai_response}]})
                
                if len(ai_response) > 2000:
                    chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(ai_response)
        
        except Exception as e:
            await message.channel.send(f"❌ Error al procesar tu mensaje: {str(e)}")
            print(f"Error Gemini: {e}")

# ---------------- SLASH COMMANDS ----------------
# Aquí van todos tus slash commands exactamente como los tienes

# ---------------- COMANDOS EXCLUSIVOS PARA TI ----------------
# Aquí van los comandos de reiniciar, anunciar, limpiar chat, etc.

# ---------------- INICIO DEL BOT ----------------
bot.run(TOKEN)
