import nextcord
from nextcord.ext import commands
from quart import url_for, redirect
import quart_discord 
import json
import random
import string
import aiosqlite

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False
    
    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(HelpView())
            self.persistent_views_added = True
        print("Persistent views added")
        print(f"Bot is up and ready | Logged in as {self.user}")
        async with aiosqlite.connect("codes.db") as db:
           await db.execute("CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, user_id INTEGER)")
           await db.commit()
        print("Database is ready")


bot = MyBot(command_prefix='!', intents=nextcord.Intents.all())

class SubmissionModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Submit Challenge",
        )

        self.submissionid = nextcord.ui.TextInput(label="Enter your submission code!", placeholder="Enter your submission here...", custom_id="submission-id", max_length=6, min_length=6)
        self.submissiondata = nextcord.ui.TextInput(label="Enter the string", placeholder="Enter your submission here...", custom_id="submission-data", max_length=3000, min_length=10, style=nextcord.TextInputStyle.paragraph)
        self.add_item(self.submissionid)
        self.add_item(self.submissiondata)

    async def callback(self, interaction): 
        channel = bot.get_channel(845532686776008705)  # Replace with desired channel ID
        await channel.send(f"New submission from {self.submissionid.value}\n`{self.submissiondata.value}`")
        em = nextcord.Embed(title="Submission Sent!", color=nextcord.Color.green())
        return await interaction.send(embed=em)

class SubmitSystem(nextcord.ui.View):
    def __init__(self):
        super().__init__()

    @nextcord.ui.button(label="Submit Challenge", custom_id="designerdashsubmit")
    async def submit_challenge(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(SubmissionModal())

class HelpDropdown(nextcord.ui.Select):
    def __init__(self):
        with open('data.json') as f:
            data = json.load(f)
        options = []
        for challenge in data:
            options.append(nextcord.SelectOption(label=challenge['name']))
        
        super().__init__(placeholder="Select a Challenge!", options=options, min_values=1, max_values=1, custom_id="help-dropdown")
    
    async def callback(self, interaction: nextcord.Interaction):
        with open('data.json') as f:
            data = json.load(f)
        challenge_name = self.values[0]
        for challenge in data:
            if challenge['name'] == challenge_name:
                embed = nextcord.Embed(title=challenge['title'], description=challenge['description'], color=nextcord.Color.blurple())
                embed.add_field(name="`Points Value`", value=f"`+{challenge['points']}`")
                return await interaction.response.send_message(embed=embed, ephemeral=True, view=SubmitSystem())

class HelpView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown())

@bot.command()
async def eventsystem(ctx):
    embed=nextcord.Embed(title="Alpine & Tim's Internet Scavanger Extravaganza", description="Welcome to Alpine and Tim's Internet Scavanger Extravaganza a event run by Alpine and Tim with the assistance of the SW Teach Team.", color=nextcord.Color.orange())
    embed.set_image(url = 'https://i.imgur.com/5xnlICo.png')
    embed.add_field(name="What do i do?", value="To compete in the event you must you must complete challenges to earn points. The team with the most points at the end of the event will win the event. You can find challenges below by scorlling through the dropdown or looking in the #challenges channel wich can provide more detailed information.")
    await ctx.send(embed=embed, view=HelpView())

class CodeAssignView(nextcord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.code = None

    @nextcord.ui.button(label="Generate Code", custom_id="generate_code_bttn", style=nextcord.ButtonStyle.primary)
    async def generate_code_bttn(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        code = await self.generate_code()
        print(code)
        if code is not None:
            em = nextcord.Embed(title="Code Assigned", description=f"Your code is: `{code}`", color=nextcord.Color.green())
            await interaction.send(embed=em, ephemeral=True)
        else:
            em = nextcord.Embed(title="Error", description="Failed to generate code. Please try again later.", color=nextcord.Color.red())
            await interaction.send(embed=em, ephemeral=True)

    async def generate_code(self):
        async with aiosqlite.connect("codes.db") as db:
            cursor = await db.execute("SELECT code FROM codes WHERE user_id = ?", (self.user_id,))
            row = await cursor.fetchone()
            if row is not None:
                self.code = row[0]
                return self.code
            else:
                while True:
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    cursor = await db.execute("SELECT * FROM codes WHERE code = ?", (code,))
                    row = await cursor.fetchone()
                    if row is None:
                        self.code = code
                        await db.execute("INSERT INTO codes (code, user_id) VALUES (?, ?)", (code, self.user_id))
                        await db.commit()
                        return code
                    else:
                        return None

@bot.command()
async def codeassignsys(ctx):
    view = CodeAssignView(ctx.author.id)
    await view.generate_code()
    await ctx.send("Click the button to generate a code.", view=view)

bot.run('')
