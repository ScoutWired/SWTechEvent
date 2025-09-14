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
           await db.execute("CREATE TABLE IF NOT EXISTS userdata (code TEXT PRIMARY KEY, secret_key TEXT, user_id INTEGER, points INTEGER DEFAULT 0, challenges TEXT, paths TEXT)")
           await db.execute("CREATE TABLE IF NOT EXISTS challenges (id INT PRIMARY KEY, name TEXT, type TEXT, description TEXT, points INTEGER)")
        print("Database is ready")


bot = MyBot(command_prefix='!', intents=nextcord.Intents.all())

async def init_app():
    await asyncio.sleep(0.1)  # Wait for the event loop to start
    app.bot = bot

class submit_system(nextcord.ui.View):
    def __init__(self, code, points, id):
        super().__init__(timeout=None)
        self.code = code
        self.points = points
        self.id = id

    @nextcord.ui.button(label="Approve Submission", custom_id="approve_submission", style=nextcord.ButtonStyle.green)
    async def approve_submission(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Submission Approved!", ephemeral=True)
        async with aiosqlite.connect("codes.db") as db:
            # Get the current challenges string and points for the user
            cursor = await db.execute("SELECT challenges, points FROM userdata WHERE code = ?", (self.code,))
            result = await cursor.fetchone()
            if result is None:
                current_challenges = []
                current_points = 0
            else:
                current_challenges = result[0].split(',') if result[0] else []
                current_points = result[1]
            
            print(current_points)

            # Add the challenge ID to the challenges list
            challenge_id = str(self.id)
            current_challenges.append(challenge_id)

            # Update the challenges string and points in the userdata table
            new_challenges = ",".join(current_challenges)
            new_points = current_points + self.points
            await db.execute("UPDATE userdata SET points = ?, challenges = ? WHERE code = ?", (new_points, new_challenges, self.code))
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
        channel = bot.get_channel(1164465760006045746)  # Replace with desired channel ID
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
app.secret_key = 'SCOUTWIRED2023RealityCheck'

@app.route('/')
async def home():
    return redirect(url_for('login'))

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

@bot.command()
async def load_challenges_path(ctx, path):
    # Open the data.json file and load the challenge data
    with open(f'challenges/path{path}.json') as f:
        challenge_data = json.load(f)

    # Connect to the challenges database
    async with aiosqlite.connect('codes.db') as db:
        # Delete all data from the challenges table
        await db.execute(f'DELETE FROM path{path}')

        # Insert the new challenge data into the challenges table
        for challenge in challenge_data:
            await db.execute(f'INSERT INTO path{path} (id, name, type, description, points, answer) VALUES (?, ?, ?, ?, ?, ?)',
                              (challenge['id'], challenge['name'], challenge['type'], challenge['description'], challenge['points'], challenge['answer']))

        # Commit the changes to the database
        await db.commit()

    # Send a message to confirm that the challenges have been loaded
    await ctx.send('Challenges loaded successfully!')

@bot.command()
async def load_paths(ctx):
    # Open the data.json file and load the challenge data
    with open(f'paths.json') as f:
        challenge_data = json.load(f)

    # Connect to the challenges database
    async with aiosqlite.connect('codes.db') as db:
        # Delete all data from the challenges table
        await db.execute(f'DELETE FROM paths')

        # Insert the new challenge data into the challenges table
        for challenge in challenge_data:
            await db.execute(f'INSERT INTO paths (id, name, type, description) VALUES (?, ?, ?, ?)',
                              (challenge['id'], challenge['name'], challenge['type'], challenge['description']))

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
        # Retrieve the user's completed challenges
        cursor = await db.execute("SELECT challenges FROM userdata WHERE code = ?", (user[0],))
        completed_challenges = await cursor.fetchone()
        if completed_challenges is None or completed_challenges[0] == "":
            completed_challenges = []
        else:
            completed_challenges = completed_challenges[0].split(',') if completed_challenges[0] else []

        # Retrieve the challenges that haven't been completed
        if completed_challenges:
            placeholders = ','.join(['?'] * len(completed_challenges))
            query = "SELECT * FROM challenges WHERE id NOT IN ({})".format(placeholders)
            cursor = await db.execute(query, completed_challenges)
        else:
            cursor = await db.execute("SELECT * FROM challenges")
        
        challenges = await cursor.fetchall()

        data = await db.execute("SELECT points FROM userdata WHERE code = ?", (user[0],))
        points = await data.fetchone()
        
        
    print(user)
    print(challenges)
    print(points)
    return await render_template('dashboard.html', user=user, challenges=challenges, points=points[0])



    
@app.route('/submit/<int:challengenum>', methods=['GET', 'POST'])
async def submit(challengenum):
    user = session.get('user')
    if not user:
        return redirect('/')
    if request.method == 'GET':
        async with aiosqlite.connect('codes.db') as db:
            if challengenum >= 16 and challengenum < 25:
                cursor = await db.execute('SELECT * FROM path1 WHERE id = ?', (challengenum,))
                challenge = await cursor.fetchone()
                if not challenge:
                    return redirect('/dashboard')
                return await render_template('submit.html', challenge=challenge)
            if challengenum >= 24 and challengenum < 37:
                cursor = await db.execute('SELECT * FROM path2 WHERE id = ?', (challengenum,))
                challenge = await cursor.fetchone()
                if not challenge:
                    return redirect('/dashboard')
                return await render_template('submit.html', challenge=challenge)
            if challengenum >= 37 and challengenum < 45:
                cursor = await db.execute('SELECT * FROM path3 WHERE id = ?', (challengenum,))
                challenge = await cursor.fetchone()
                if not challenge:
                    return redirect('/dashboard')
                return await render_template('submit.html', challenge=challenge)
            if challengenum >= 44 and challengenum < 55:
                cursor = await db.execute('SELECT * FROM path4 WHERE id = ?', (challengenum,))
                challenge = await cursor.fetchone()
                if not challenge:
                    return redirect('/dashboard')
                return await render_template('submit.html', challenge=challenge)
            if challengenum >= 0 and challengenum < 16:
                cursor = await db.execute('SELECT * FROM challenges WHERE id = ?', (challengenum,))
                challenge = await cursor.fetchone()
                if not challenge:
                    return redirect('/dashboard')
                return await render_template('submit.html', challenge=challenge)
        
            
            
    
    if request.method == 'POST':
        print("1")
        async with aiosqlite.connect('codes.db') as db:
            print("2")

            cursor = await db.execute('SELECT * FROM challenges WHERE id = ?', (challengenum,))
            print("2.5")
            challenge = await cursor.fetchone()
            print(challenge)

            print("3")
            # Get the current challenges string and points for the user
            cursor = await db.execute("SELECT paths FROM userdata WHERE code = ?", (user[0],))
            result = await cursor.fetchone()
                
            print("HERE2")
            # Add the challenge ID to the challenges list
            challenge_id = str(challengenum)
            
            form = await request.form
            answer = form['answer']
            channel = bot.get_channel(1296379899417858098)
            em = nextcord.Embed(title=f"New Submission from {user[0]}", description=f"**Challenge:** {challenge[1]}\n**Answer:** {answer}")
            print(user[0])
            print(challenge[1])
            await channel.send(embed=em, view=submit_system(user[0], challenge[4], challenge[0]))
            return redirect('/dashboard')
        
@app.route('/challenge/<int:challenge_id>', methods=['GET'])
async def view_challenge(challenge_id):
    async with aiosqlite.connect('codes.db') as db:
        if challenge_id >= 16 and challenge_id < 25:
            print("Test")
            cursor = await db.execute('SELECT * FROM path1 WHERE id = ?', (challenge_id,))
            challenge = await cursor.fetchone()
            print(challenge)
            if not challenge:
                return redirect('/dashboard')
            else:
                return await render_template('challenge.html', challenge=challenge)
        if challenge_id >= 24 and challenge_id < 37:
            cursor = await db.execute('SELECT * FROM path2 WHERE id = ?', (challenge_id,))
            challenge = await cursor.fetchone()
            if not challenge:
                return redirect('/dashboard')
            else:
                return await render_template('challenge.html', challenge=challenge)
        if challenge_id >= 34 and challenge_id < 45:
            cursor = await db.execute('SELECT * FROM path3 WHERE id = ?', (challenge_id,))
            challenge = await cursor.fetchone()
            if not challenge:
                return redirect('/dashboard')
            else:
                return await render_template('challenge.html', challenge=challenge)
        if challenge_id >= 45 and challenge_id < 55:
            cursor = await db.execute('SELECT * FROM path4 WHERE id = ?', (challenge_id,))
            challenge = await cursor.fetchone()
            if not challenge:
                return redirect('/dashboard')
            else:
                return await render_template('challenge.html', challenge=challenge)
                
        cursor = await db.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,))
        challenge = await cursor.fetchone()
        if not challenge:
            return redirect('/dashboard')
        else:
            return await render_template('challenge.html', challenge=challenge)
            
@bot.command()
async def add_challenge(ctx, code: str, challenge_id: int):
    async with aiosqlite.connect("codes.db") as db:
        # Check if the code exists in the database
        cursor = await db.execute("SELECT * FROM userdata WHERE code = ?", (code,))
        row = await cursor.fetchone()
        if row is None:
            await ctx.send("Invalid code.")
        else:
            # Get the current challenges string for the user
            current_challenges = row[4]
            if current_challenges is None:
                current_challenges = ""
            else:
                current_challenges = str(current_challenges)

            # Add the challenge ID to the challenges string
            if current_challenges == "":
                new_challenges = str(challenge_id)
            else:
                new_challenges = current_challenges + "," + str(challenge_id)

            # Update the challenges string in the userdata table
            await db.execute("UPDATE userdata SET challenges = ? WHERE code = ?", (new_challenges, code))
            await db.commit()
            await ctx.send(f"Challenge {challenge_id} added to code {code}.")

@app.route('/generate', methods=['GET', 'POST'])
async def generate():
    if request.method == 'GET':
        return await render_template('generate.html')
    
    if request.method == 'POST':
        async with aiosqlite.connect('codes.db') as db:
            form = await request.form
            username = form['username']
            password = form['password']
            print(username, password)

            # Check if the username already exists in the database
            cursor = await db.execute("SELECT * FROM userdata WHERE code = ?", (username,))
            row = await cursor.fetchone()
            if row is not None:
                return "Username already exists. Please try again. To try agian click here: <a href='/generate'>Generate</a>"

            # If the username doesn't exist, add it to the database
            await db.execute("INSERT INTO userdata (code, secret_key) VALUES (?, ?)", (username, password))
            await db.commit()


            return "User created successfully. Please login here: <a href='/login'>Login</a>"



    

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
    bot_task = bot.start('HAHAHA NO TOKEN HERE :)')
    app_task = app.run_task(host='localhost', port=0000)
    await asyncio.gather(bot_task, app_task)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())