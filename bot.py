import discord
from discord.ext import commands
from sqlalchemy import create_engine, text
import threading
import time
from sqlalchemy.exc import SQLAlchemyError, OperationalError



backup = create_engine('sqlite:///urls_old.db')
engine = create_engine('sqlite:///urls.db')

def getRandomFile():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM urls ORDER BY RANDOM() LIMIT 1")).fetchall()
        return result[0]

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("failed to connect to the main urls.db using urls_old.db")
        return getBackupRandomFile();

def getBackupRandomFile():
    with backup.connect() as connection:
        result = connection.execute(text("SELECT * FROM urls ORDER BY RANDOM() LIMIT 1")).fetchall()
    return result[0]



random_file = None

def update_random_file():
    global random_file
    while True:
        random_file = getRandomFile()  # Generate a random float
        time.sleep(2.5)  # Wait for 5 seconds




threading.Thread(target=update_random_file).start()





bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.slash_command(description = "get random chan video or image hehe")
@commands.is_nsfw()
async def randomfile(ctx):
    rand_file = random_file
    response_str = f''
    response_str = f'{rand_file[3]}'
    response_str += f'\n site: {rand_file[1]}'
    response_str += f'\n board: {rand_file[2]}'
    response_str += f'\n comment: {rand_file[4]}'
    await ctx.respond(response_str) # Send the embed with some text

@randomfile.error
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    await ctx.respond("Need to be in nsfw channel!!!")



bot.run('discord key')
