import discord
from discord.ext import commands
import os
from google import genai

# ---------------- CONFIGURACIÓN ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)
OWNER_ID = 1375062145498091560

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None
    print("⚠️ GEMINI_API_KEY no configurada. El chatbot no estará disponible.")

conversation_history = {}

# Palabras y enlaces prohibidos
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

    # Detectar palabras o links inapropiados
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

    # Chat básico predefinido
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

@bot.slash_command(description="Muestra tu rango actual")
async def rango(ctx):
    roles = [r.name for r in ctx.author.roles if r.name != "@everyone"]
    if roles:
        await ctx.respond(f"🧠 Tus rangos: {', '.join(roles)}")
    else:
        await ctx.respond("👀 No tienes ningún rango asignado.")

@bot.slash_command(description="Banea a un usuario (solo moderadores)")
@commands.has_permissions(ban_members=True)
async def ban(ctx, usuario: discord.Member, razon: str = "No especificada"):
    if usuario.id == ctx.author.id:
        await ctx.respond("❌ No puedes banearte a ti mismo.")
        return
    await usuario.ban(reason=razon)
    await ctx.respond(f"✅ {usuario} fue baneado. Razón: {razon}")

@bot.slash_command(description="Desbanea un usuario por ID (solo moderadores)")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: str, razon: str = "No especificada"):
    try:
        user = await bot.fetch_user(int(user_id))
        await ctx.guild.unban(user, reason=razon)
        await ctx.respond(f"✅ {user} ha sido desbaneado. Razón: {razon}")
    except:
        await ctx.respond("❌ No se pudo desbanear al usuario.")

@bot.slash_command(description="Expulsa a un usuario (solo moderadores)")
@commands.has_permissions(kick_members=True)
async def kick(ctx, usuario: discord.Member, razon: str = "No especificada"):
    if usuario.id == ctx.author.id:
        await ctx.respond("❌ No puedes expulsarte a ti mismo.")
        return
    await usuario.kick(reason=razon)
    await ctx.respond(f"✅ {usuario} fue expulsado. Razón: {razon}")

@bot.slash_command(description="Limpia mensajes del canal (solo moderadores)")
@commands.has_permissions(manage_messages=True)
async def limpiar(ctx, cantidad: int):
    if cantidad < 1 or cantidad > 100:
        await ctx.respond("❌ Debes indicar un número entre 1 y 100.")
        return
    await ctx.channel.purge(limit=cantidad)
    await ctx.respond(f"🧹 Se han eliminado {cantidad} mensajes.", ephemeral=True)

# ---------------- COMANDOS EXCLUSIVOS PARA TI ----------------

@bot.slash_command(description="Reinicia Orbs (solo creador)")
async def reiniciar(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.respond("🚫 Solo el creador de Orbs puede usar este comando.")
        return
    await ctx.respond("🔁 Reiniciando Orbs... (simulado en Replit)")
    print("♻️ Reinicio solicitado por el creador.")

@bot.slash_command(description="Envía un anuncio (solo creador)")
async def anunciar(ctx, mensaje: str):
    if ctx.author.id != OWNER_ID:
        await ctx.respond("🚫 Solo el creador puede usar este comando.")
        return
    for canal in ctx.guild.text_channels:
        try:
            await canal.send(f"📢 **Anuncio de Orbs:** {mensaje}")
        except:
            pass
    await ctx.respond("✅ Anuncio enviado.")

@bot.slash_command(description="Limpia tu historial de conversación con el chatbot IA")
async def limpiar_chat(ctx):
    user_id = ctx.author.id
    if user_id in conversation_history:
        conversation_history[user_id] = []
        await ctx.respond("🧹 Tu historial de conversación ha sido limpiado.", ephemeral=True)
    else:
        await ctx.respond("📝 No tienes historial de conversación.", ephemeral=True)

@bot.slash_command(description="Chatea con Orbs usando IA gratis de Google Gemini")
async def chat(ctx, pregunta: str):
    if not gemini_client:
        await ctx.respond("❌ El chatbot IA no está disponible. Falta configurar GEMINI_API_KEY.", ephemeral=True)
        return
    
    await ctx.defer()
    
    user_id = ctx.author.id
    
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": "user", "parts": [{"text": pregunta}]})
    
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    
    try:
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
            await ctx.respond(ai_response[:2000])
            remaining = ai_response[2000:]
            while remaining:
                await ctx.followup.send(remaining[:2000])
                remaining = remaining[2000:]
        else:
            await ctx.respond(ai_response)
    
    except Exception as e:
        await ctx.respond(f"❌ Error al procesar tu pregunta: {str(e)}", ephemeral=True)
        print(f"Error Gemini: {e}")

@bot.slash_command(description="Muestra todos los comandos disponibles de Orbs")
async def ayuda(ctx):
    embed = discord.Embed(
        title="🤖 Comandos de Orbs",
        description="Soy Orbs, tu bot moderador con IA integrada. Aquí están mis funciones:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="💬 Chatbot IA (Google Gemini - 100% GRATIS)",
        value=(
            "• **Mencióname** o escribe `orbs [mensaje]` en el chat\n"
            "• `/chat [pregunta]` - Chatea conmigo usando comandos slash\n"
            "• `/limpiar_chat` - Limpia tu historial de conversación"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👮 Moderación",
        value=(
            "• `/ban [usuario] [razón]` - Banea a un usuario\n"
            "• `/kick [usuario] [razón]` - Expulsa a un usuario\n"
            "• `/unban [user_id] [razón]` - Desbanea a un usuario\n"
            "• `/limpiar [cantidad]` - Elimina mensajes del canal"
        ),
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Información",
        value="• `/rango` - Muestra tus rangos actuales",
        inline=False
    )
    
    if ctx.author.id == OWNER_ID:
        embed.add_field(
            name="⚙️ Comandos de Administrador",
            value=(
                "• `/reiniciar` - Reinicia el bot\n"
                "• `/anunciar [mensaje]` - Envía un anuncio a todos los canales"
            ),
            inline=False
        )
    
    embed.set_footer(text="🛡️ Moderando I.C.A.P con IA")
    
    await ctx.respond(embed=embed, ephemeral=True)

# ---------------- INICIO DEL BOT ----------------
token = os.getenv("TOKEN")
if not token:
    raise ValueError("❌ ERROR: No se encontró el token de Discord. Por favor, configura la variable de entorno TOKEN en los secretos de Replit.")
bot.run(token)
