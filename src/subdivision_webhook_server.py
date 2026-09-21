from aiohttp import web
import discord
import json

from config import SUBDIVISION_FORM_WEBHOOK_SECRET

CHANNEL_IDS = {
    "swat": 1047611796246245487,
    "sciu": 1047611527571705917,
    "k9": 1234,
}

ROLE_IDS = {
    "swat": 1047611350785982466,
    "sciu": 1047611194837577869,  # replace with actual role ID
    "k9": 1234,    # replace with actual role ID
}

SECRET = SUBDIVISION_FORM_WEBHOOK_SECRET

async def handle_form(request: web.Request) -> web.Response:
    try:
        if request.headers.get("X-Secret") != SECRET:
            return web.Response(status=401, text="Unauthorized")

        data = await request.json()
        form_type = data.get("form_type")
        fields = data.get("fields", [])
        title = data.get("title", "Form Submission")

        channel_id = CHANNEL_IDS.get(form_type)
        role_id = ROLE_IDS.get(form_type)

        if not channel_id:
            return web.Response(status=400, text="Unknown form type")
        if not role_id:
            return web.Response(status=400, text="No role configured for this form type")

        bot = request.app["bot"]
        channel = bot.get_channel(channel_id)
        if not channel:
            return web.Response(status=500, text="Channel not found")

        embed = discord.Embed(
            title=title,
            color=16777164,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Made by Dillon :)")

        for field in fields:
            embed.add_field(
                name=field["name"][:256],
                value=field["value"][:1024],
                inline=False
            )

        await channel.send(
            content=f"<@&{role_id}>",
            allowed_mentions=discord.AllowedMentions(roles=True),
            embed=embed
        )
        return web.Response(status=200, text="OK")
    except Exception as e:
        return web.Response(status=500, text=str(e))

async def start_server_sub(bot: discord.Client, port: int = 8134):
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/form", handle_form)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Webhook server running on port {port}")
