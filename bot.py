import nextcord
from nextcord.ext import commands
import quart_discord 
import json
import random
import string
import aiosqlite
from quart import Quart, redirect, url_for, render_template, request, session
import sqlite3
import asyncio
import aiosqlite

logs_channel = 1122115961135308811

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False
    
    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(HelpView())
            self.add_view(CodeAssignView())
            self.persistent_views_added = True
        print("Persistent views added")
        print(f"Bot is up and ready | Logged in as {self.user}")
        async with aiosqlite.connect("codes.db") as db:
           await db.execute("CREATE TABLE IF NOT EXISTS userdata (code TEXT PRIMARY KEY, secret_key TEXT, user_id INTEGER, points INTEGER DEFAULT 0, challenges TEXT)")
           await db.execute("CREATE TABLE IF NOT EXISTS challenges (id INT PRIMARY KEY, name TEXT, type TEXT, description TEXT, points INTEGER)")
           await db.commit()
        print("Database is ready")


bot = MyBot(command_prefix='!', intents=nextcord.Intents.all())

async def init_app():
    await asyncio.sleep(0.1)  # Wait for the event loop to start
    app.bot = bot

class submit_system(nextcord.ui.View):
    def __init__(self, code, points):
        super().__init__(timeout=None)
        self.code = code
        self.points = points

    @nextcord.ui.button(label="Approve Submission", custom_id="approve_submission", style=nextcord.ButtonStyle.green)
    async def approve_submission(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Submission Approved!", ephemeral=True)
        async with aiosqlite.connect("codes.db") as db:
            cursor = await db.execute("SELECT * FROM userdata WHERE code = ?", (self.code,))
            row = await cursor.fetchone()
            new_points = row[3] + self.points
            await db.execute("UPDATE userdata SET points = ? WHERE code = ?", (new_points, self.code))
            await db.commit()

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
        channel = bot.get_channel(1120676913514553414)  # Replace with desired channel ID
        await channel.send(f"New submission from {self.submissionid.value}\n`{self.submissiondata.value}`", view=submit_system(self.submissionid.value))
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
    def __init__(self, user_id = None):
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
            cursor = await db.execute("SELECT code FROM userdata WHERE user_id = ?", (self.user_id,))
            row = await cursor.fetchone()
            if row is not None:
                self.code = row[0]
                return self.code
            else:
                while True:
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    cursor = await db.execute("SELECT * FROM userdata WHERE code = ?", (code,))
                    row = await cursor.fetchone()
                    if row is None:
                        self.code = code
                        await db.execute("INSERT INTO userdata (code, user_id) VALUES (?, ?)", (code, self.user_id))
                        await db.commit()
                        return code
                    else:
                        return None

@bot.command()
async def codeassignsys(ctx):
    view = CodeAssignView(ctx.author.id)
    await view.generate_code()
    await ctx.send("Click the button to generate a code.", view=view)
    
@bot.command()
async def add_user(ctx):
    code = "admin"
    secret_key = "test"
    user_id = ctx.author.id
    points = 0
    challenges = ""
    async with aiosqlite.connect("codes.db") as db:
        await db.execute("INSERT INTO userdata (code, secret_key, user_id, points, challenges) VALUES (?, ?, ?, ?, ?)", (code, secret_key, user_id, points, challenges))
        await db.commit()
    await ctx.send("User added successfully!")
    
@bot.command()
async def get_users(ctx):
    async with aiosqlite.connect("codes.db") as db:
        cursor = await db.execute("SELECT * FROM userdata")
        rows = await cursor.fetchall()
        if rows is None:
            await ctx.send("No users found.")
        else:
            message = "Users:\n"
            for row in rows:
                message += f"Code: {row[0]}, Secret Key: {row[1]}, User ID: {row[2]}, Points: {row[3]}, Challenges: {row[4]}\n"
            await ctx.send(message)

@bot.command()
@commands.has_role("Team Member")
async def add_points(ctx, code: str, points: int):
    async with aiosqlite.connect("codes.db") as db:
        cursor = await db.execute("SELECT * FROM userdata WHERE code = ?", (code,))
        row = await cursor.fetchone()
        if row is None:
            await ctx.send("Invalid code.")
        else:
            new_points = row[3] + points
            await db.execute("UPDATE userdata SET points = ? WHERE code = ?", (new_points, code))
            await db.commit()
            await ctx.send(f"{points} points added to code {code}.")
            
@bot.command()
@commands.has_role("Team Member")
async def remove_points(ctx, code: str, points: int):
    async with aiosqlite.connect("codes.db") as db:
        cursor = await db.execute("SELECT * FROM userdata WHERE code = ?", (code,))
        row = await cursor.fetchone()
        if row is None:
            await ctx.send("Invalid code.")
        else:
            new_points = row[3] - points
            if new_points < 0:
                new_points = 0
            await db.execute("UPDATE userdata SET points = ? WHERE code = ?", (new_points, code))
            await db.commit()
            await ctx.send(f"{points} points removed from code {code}.")

app = Quart(__name__)
app.secret_key = 'SCOUTWIRED2023ScavengerHunt'

@app.route('/')
async def home():
    return await render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        form = await request.form
        code = form['code']
        secret_key = form['secret_key']

        async with aiosqlite.connect('codes.db') as db:
            cursor = await db.execute(
                'SELECT * FROM userdata WHERE code = ? AND secret_key = ?',
                (code, secret_key)
            )
            user = await cursor.fetchone()
            if user:
                session['user'] = user
                return redirect(url_for('dashboard'))  # Redirect to the dashboard route
            else:
                return redirect(url_for('home')) # Redirect to home route

    return await render_template('login.html')

@bot.command()
async def load_challenges(ctx):
    # Open the data.json file and load the challenge data
    with open('data.json') as f:
        challenge_data = json.load(f)

    # Connect to the challenges database
    async with aiosqlite.connect('codes.db') as db:
        # Delete all data from the challenges table
        await db.execute('DELETE FROM challenges')

        # Insert the new challenge data into the challenges table
        for challenge in challenge_data:
            await db.execute('INSERT INTO challenges (id, name, type, description, points) VALUES (?, ?, ?, ?, ?)',
                              (challenge['id'], challenge['name'], challenge['type'], challenge['description'], challenge['points']))

        # Commit the changes to the database
        await db.commit()

    # Send a message to confirm that the challenges have been loaded
    await ctx.send('Challenges loaded successfully!')

@app.route('/dashboard')
async def dashboard():
    user = session.get('user')
    if not user:
        return redirect('/')  # Redirect to the login route if user is not logged in
    
    async with aiosqlite.connect('codes.db') as db:
        cursor = await db.execute('SELECT * FROM challenges')
        challenges = await cursor.fetchall()

    return await render_template('dashboard.html', user=user, challenges=challenges)
    
@app.route('/submit/<int:challengenum>', methods=['GET', 'POST'])
async def submit(challengenum):
    user = session.get('user')
    if not user:
        return redirect('/')
    if request.method == 'GET':
        async with aiosqlite.connect('codes.db') as db:
            cursor = await db.execute('SELECT * FROM challenges WHERE id = ?', (challengenum,))
            challenge = await cursor.fetchone()
            if not challenge:
                return redirect('/dashboard')
            return await render_template('submit.html', challenge=challenge)
    
    if request.method == 'POST':
        async with aiosqlite.connect('codes.db') as db:
            cursor = await db.execute('SELECT * FROM challenges WHERE id = ?', (challengenum,))
            challenge = await cursor.fetchone()
            if not challenge:
                return redirect('/dashboard')
            form = await request.form
            answer = form['answer']
            channel = bot.get_channel(1122115961135308811)
            em = nextcord.Embed(title=f"New Submission from {user[0]}", description=f"**Challenge:** {challenge[1]}\n**Answer:** {answer}", color=nextcord.Color.green())
            await channel.send(embed=em, view=submit_system(user[0], challenge[4]))
            return redirect('/dashboard')

async def generate_code():
    async with aiosqlite.connect("codes.db") as db:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        await db.execute("INSERT INTO userdata (code) VALUES (?)", (code,))
        await db.commit()
        return code
    
async def generate_secret_key(code):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    async with aiosqlite.connect("codes.db") as db:
        await db.execute("UPDATE userdata SET secret_key = ? WHERE code = ?", (key, code))
        await db.commit()
        return key 

@app.route('/generate', methods=['GET'])
async def generate():
    if request.method == 'GET':
        code = await generate_code()     
        secret_key = await generate_secret_key(code)
        return await render_template('generate.html', code=code, secret_key=secret_key)

async def fetch_leaderboard():
    conn = await aiosqlite.connect('codes.db')  # Replace with your database file path
    cursor = await conn.execute('SELECT code, points FROM userdata ORDER BY points DESC')
    leaderboard = await cursor.fetchall()
    await cursor.close()
    await conn.close()
    return leaderboard

@app.route('/leaderboard')
async def leaderboard():
    leaderboard_data = await fetch_leaderboard()
    return await render_template('leaderboard.html', leaderboard=list(leaderboard_data))
    
app.before_serving(init_app)

async def main():
    bot_task = bot.start('')
    app_task = app.run_task(host='0.0.0.0', port=8081)
    await asyncio.gather(bot_task, app_task)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
