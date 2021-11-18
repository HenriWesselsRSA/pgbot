import discord
from discord.ext.commands.converter import EmojiConverter
import random
from discord.ext import commands
from discord.message import Message
from discord.utils import get
import psycopg2
import math

#client for the bots

conn = psycopg2.connect("""dbname=d7srh03jeemfu host=ec2-52-201-195-11.compute-1.amazonaws.com port=5432 user=etqeaynjqrjbos password=5b97e3e974e70a665d2891a116eae285b1c67d20fcd00b061e657bb81c0170a6 sslmode=require""")
conn.set_session(autocommit=True)

cursor = conn.cursor()

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='$', intents=intents)

# CREATE ALL TABLES IF THEY DO NOT ALREADY EXIST

cursor.execute("create table if not exists experiences (name varchar, experience int);")
cursor.execute("create table if not exists levels (name varchar, level int);")
cursor.execute("create table if not exists warnings (name varchar, warnings text);")
cursor.execute("create table if not exists descriptions (name varchar, description text);")
cursor.execute("create table if not exists roles (name varchar, role text);")

#Do stuff

#Run the client on the server
#token of the bot is in the run so it knows what bot to run
#guild is a class that represents the server and has properties (refer to discord API documentation)
#ctx represents the context
#client.command() makes the function a command the user can use
#client.event() is used for when something is happening

#Will print on our local system ready to show that the bot is running
@bot.event
async def on_ready():
    print("Ready")


#Guild refers to server
#When bot joins the discord server it will create a welcome-channel
@bot.event
async def on_guild_join(guild):
    await guild.create_role(name="Admin")
    welcomechannelFound = False #variable to check if channel exists
    reportchannelFound = False
    counter = 0
    for channel in guild.text_channels:
        if(str(channel) == 'welcome-channel'):
            welcomechannelFound = True
            await channel.send("Hello! I am PGBot, please type in $help if you need assistance.")
        elif(str(channel) == 'reports'):
            reportchannelFound = True
            await channel.send("Hello! I am PGBot, this will be where user reports will be sent")
            counter = counter + 1

        else:
            counter = counter + 1
    if(welcomechannelFound == False): #makes sure channel "welcome-channel" doesn't already exist
        await guild.create_text_channel('welcome-channel') #creates a welcome-channel when bot joins the server so it can welcome future new members
        await guild.text_channels[counter].send("Hello! I am PGBot, please type in $help if you need assistance.") #sends introduction message to welcome-channel just created

    if(reportchannelFound == False):
        adminRole = get(guild.roles, name="Admin")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            adminRole: discord.PermissionOverwrite(read_messages=True)
            

        }
        await guild.create_text_channel('reports', overwrites=overwrites)


@bot.event
async def on_member_join(member):
    embed = discord.Embed(
        title = f"Welcome {member.name}",
        description="Use $help for bot commands or contact an admin if you need help!",
        color = discord.Color.red()
    )
    embed.set_thumbnail(url=member.avatar_url)

     # DATABASE PART

    checkA = False
    cursor.execute("select * from experiences")
    descript = cursor.fetchall()
    for a,b in descript:
         if (a == member.name):
             cursor.execute("delete from experiences where name like '{0}' ".format(member.name))
             cursor.execute("insert into experiences(name, experience) values(%s, %s)", (member.name, 0))
             checkA = True
    
    if (checkA == False):
        cursor.execute("insert into experiences(name, experience) values(%s, %s)", (member.name, 0))
             
    checkB = False
    cursor.execute("select * from levels")
    descript = cursor.fetchall()
    for a,b in descript:
         if (a == member.name):
             cursor.execute("delete from levels where name like '{0}' ".format(member.name))
             cursor.execute("insert into levels(name, level) values(%s, %s)", (member.name, 1))
             checkB = True
    
    if (checkB == False):
        cursor.execute("insert into levels(name, level) values(%s, %s)", (member.name, 1))
    



    for channel in member.guild.text_channels:
        if(str(channel) == 'welcome-channel'):
            await channel.send(embed=embed)
            break
        

async def add_experience(user, exp):
    #add variable exp to existing exp in database
    myexp = 0
    cursor.execute("select * from experiences")
    exps = cursor.fetchall()
    for a, b in exps:
         if (a == user):
            myexp = int(b)

    cursor.execute("delete from experiences where name like '{0}' ".format(user))
    cursor.execute("insert into experiences(name, experience) values(%s, %s)", (user, myexp + exp))


async def level_up(user):
    myexp = 0
    cursor.execute("select * from experiences")
    exps = cursor.fetchall()
    for a, b in exps:
         if (a == user):
            myexp = int(b)
    
    lvl_start = 0
    cursor.execute("select * from levels") 
    levels = cursor.fetchall() 
    for a, b in levels:
         if (a == user):
            lvl_start = int(b)

    lvl_end = int(myexp ** (1/4)) #formula to calculate leveling up 

    if(lvl_start < lvl_end):
        #await ctx.send(f"{user} has leveled up to level {lvl_end}")
        #update level in database line
        cursor.execute("delete from levels where name like '{0}' ".format(user))
        cursor.execute("insert into levels(name, level) values(%s, %s)", (user, lvl_start + 1))

        
@bot.event
async def on_message(message):
    if message.content == 'Hello PG Bot':
        await message.channel.send('Hello!')
    #Do not mean to offend anyone with any of these words, just making sure the bot censors them!
    badwords = ["shit", "fuck", "bitch", "bastard", "dick", "pussy", "cunt", "twat", "faggot", "nigger", "kike", "nigga", "coon", "vagina", "penis", "fag", "guido",
    "chink", "retard"]
    
    
    for badword in badwords:
        if badword in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention} Watch your language!")
    await bot.process_commands(message)
    await add_experience(message.author.name, 5)
    await level_up(message.author.name)



@bot.command(aliases=['make_color']) #This works now ex.// $make_color colorname hexcode ($make_color Obsidian #5bded1)
@commands.has_permissions(manage_roles=True) # Check if the user executing the command can manage roles
async def create_role(ctx, name, colorstr):
    guild = ctx.guild
    member = ctx.author # sets common variables
    members_roles = member.roles

    for i in range(len(members_roles)-1):
       await member.remove_roles(members_roles[i+1]) #ensures that @everyone isn't removed

    #await member.remove_roles(member.roles) #removes the rest of the user's roles from the server

    await guild.create_role(name=name,color=int(colorstr[1:],16)) #creates users new role

    selectedRole = get(ctx.guild.roles,name=name)

    await member.add_roles(selectedRole)
    
    await ctx.send('Role {} with color {} has been created'.format(name,colorstr))


@bot.command(pass_context=True) #Not 100% functional
@commands.has_role("Admin") # This must be exactly the name of the appropriate role
async def addrole(ctx):
    member = ctx.message.author
    role = get(member.server.roles, name="Test")

     # DATABASE PART
    #cursor.execute("insert into roles(name, role) values(%s, %s)", (member.name, role))
    
    await bot.add_roles(member, role)
    


@bot.command(aliases=['make_role']) #This works now ex.// $make_role TestRole
@commands.has_permissions(manage_roles=True) # Check if the user executing the command can manage roles
async def create_role(ctx, *, name):
	guild = ctx.guild
	await guild.create_role(name=name)
	await ctx.send(f'Role `{name}` has been created')
    


@bot.command(pass_context=True)
async def myinfo(ctx):
    user = ctx.author
    username = ctx.author.name
    count = 0

    mydescription = ""
    cursor.execute("select * from descriptions")
    descriptions = cursor.fetchall()
    for a,b in descriptions:
         if (a == username):
            mydescription = b

    embed = discord.Embed(
        title = f"{username}'s' Info",
        description = mydescription,
        colour = discord.Colour.blue()
    )

    cursor.execute("select * from warnings")
    warnings = cursor.fetchall()
    for a,b in warnings:
         if (a == username):
            count = count + 1

    dateformat = "%b %d, %Y @ %I:%M %p" 

    embed.add_field(name="Warns", value=count)
    embed.add_field(name="Joined Discord", value = ctx.author.created_at.strftime(dateformat))
    embed.add_field(name="Joined Server", value = ctx.author.joined_at.strftime(dateformat))
    embed.set_thumbnail(url=user.avatar_url)

    await ctx.send(embed=embed)


@bot.command(pass_context=True)
async def warn(ctx, member: discord.Member, *, reason):

    # DATABASE PART
    cursor.execute("insert into warnings(name, reason) values(%s, %s)", (member.name, reason))

    if member.id in {ctx.author.id}:
        return await ctx.send("You can't warn yourself")

    embed = discord.Embed(
        title = f"{member} has been warned by {ctx.author.name}",
        colour = discord.Colour.red()
    )
    embed.add_field(name="Reason: ", value = reason)
    await ctx.send(embed=embed)

@bot.command(pass_context=True)
@commands.has_role("Admin")
async def showWarns(ctx, member: discord.Member, *, pageNumber):

    warn1= NULL #Set it equal to (pageNumber * 3) - 3
    warn2 = NULL #Set it equal to (pageNumber * 3) - 2
    warn3 = NULL #Set it equal to (pageNumber * 3) - 1

    warn1Index = (int(pageNumber)* 3) - 3
    warn2Index = (int(pageNumber)* 3) - 2
    warn3Index = (int(pageNumber)* 3) - 1

    
    count = 0
    cursor.execute("select * from warnings")
    warnings = cursor.fetchall()
    for a, b in warnings:
         if (a == member.name):
            count = count + 1
            if(count == warn1Index):
                warn1 = b
            elif(count == warn2Index):
                warn2 = b

            elif(count == warn3Index):
                warn3 = b
         
    numOfWarns = count
    numOfPages = math.ceil(count/3) #Take number of warns user has and divide by 3 (make sure to always round up if decimal value)


    embed = discord.Embed(
        title = f"{member.name}'s Warnings Pg: {pageNumber}/{numOfPages}"
    )
    
    embed.add_field(name=f"Warn #{warn1Index + 1} Reason:", value= warn1)
    embed.add_field(name=f"Warn #{warn2Index + 1} Reason:", value= warn2)
    embed.add_field(name=f"Warn #{warn3Index + 1} Reason:", value= warn3)
    embed.set_thumbnail(url=member.avatar_url)

    await ctx.send(embed=embed)



#@bot.command(pass_context=True)
#@commands.has_role("Admin")
#async def deleteWarn(ctx, member: discord.Member, *, warningNumber):
    #deletes the warn number indicated by previous command

@bot.command(pass_context=True)
async def rockpaperscissors(ctx):
    
    options = ["🪨", "🧾", "✂️"]

    def check(reaction, user):

        return user == ctx.author and  (str(reaction) == options[0] or str(reaction) == options[1] or str(reaction) == options[2])
    embed = discord.Embed(
        title = f"{ctx.author.name}'s' Rock Paper Scissors Game",
        description = 'React to only one emoji in order to chose!',
        colour = discord.Colour.blue()
    )
    embed.set_thumbnail(url="https://www.peppermintbar.co.uk/wp-content/uploads/2017/04/RPS_Event-01.jpg")
    message = await ctx.send(embed=embed)
    for emojis in options:
        await message.add_reaction(emojis)

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout = 10.0, check = check)
        botChoice = random.choice(options)
        
        if(str(reaction) == botChoice):
            await ctx.send(f"You chose {reaction} and PG Bot chose {botChoice} You tied!")
        elif((botChoice == "🪨" and str(reaction) == "✂️") or (botChoice == "🧾" and str(reaction) == "🪨" ) or (botChoice == "✂️" and str(reaction) == "🧾")):
            await ctx.send(f"You chose {reaction} and PG Bot chose {botChoice} You lost!")
        else:
            await ctx.send(f"You chose {reaction} and PG Bot chose {botChoice} You won!")
        
        

    except:
        await message.delete()
    


@bot.command(pass_context = True)
async def report(ctx, member: discord.Member, *, reason):
    for channel in ctx.guild.text_channels:
        if(str(channel) == 'reports'):
            embed = discord.Embed(
                title = f"{ctx.author.name}'s' Report",
                description = f'{ctx.author} has reported {member} for "{reason}"',
                colour = discord.Colour.red()
            )
            embed.set_thumbnail(url=member.avatar_url)
            await channel.send(embed=embed)


@bot.command(pass_context = True)
async def meme(ctx):
    memeUrls = ["https://thumbor.granitemedia.com/money-minion-meme/beegdqBq51kH8lxuOCtFDxtDEq8=/750x0/filters:quality(80)/granite-web-prod/9a/5f/9a5fbb688fe04c80b8cabb9885d4e6cd.jpeg",
                "https://cache.lovethispic.com/uploaded_images/thumbs/389722-Me-Starting-School-Vs-Me-At-Graduation.jpg", 
                "https://media1.popsugar-assets.com/files/thumbor/l3tGpIatkHybxJGKNsK1BDe_WJs/fit-in/1024x1024/filters:format_auto-!!-:strip_icc-!!-/2014/08/08/878/n/1922507/9ed5cdef48c5ef69_thumb_temp_image32304521407524949/i/Funny-Cat-GIFs.jpg",
                "https://media.istockphoto.com/photos/cat-surfing-on-internet-picture-id1172290687?k=20&m=1172290687&s=612x612&w=0&h=xINesZHX6C7C6PH5PfRx2cDn8d69o01osus3YjXq1QU=",
                "https://i.barkpost.com/wp-content/uploads/2015/02/featmeme.jpg?q=70&fit=crop&crop=entropy&w=808&h=500",
    ]
    await ctx.send(random.choice(memeUrls))


@bot.command(pass_context = True)
async def crystalBall(ctx,*,question):
   response =[
       'Without a doubt.',
       'Seems likely.',
       'Maybe I shouldnt tell you now',
       'Cant predict that right now',
       'Im gonna have to say no',
       'Its not looking too great',
       'Absolutely'
   ]
   embed = discord.Embed(
       title = f"{ctx.author.name}'s Crystal Ball",
       colour = discord.Colour.blue()
   )
   embed.add_field(name= "The Crystal ball says: ",value=random.choice(response))
   embed.set_thumbnail(url="https://images-na.ssl-images-amazon.com/images/I/81P-syPiMXL.png")
   await ctx.send(embed=embed)

@bot.command()
async def poll(ctx,*,message):
   emb=discord.Embed(title=" POLL", description=f"{message}")
   msg= await ctx.send(embed=emb)
   await msg.add_reaction('👍')
   await msg.add_reaction('👎')

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, *, number):
    intNum = int(number)
    if(intNum <= 50):
        await ctx.channel.purge(limit=intNum)
    else:
        await ctx.send("Sorry you can not clear more than 50 messages")




@bot.command(pass_context = True)
async def setDescription(ctx, *, description):
    check = False
    cursor.execute("select * from descriptions")
    descript = cursor.fetchall()
    for a,b in descript:
         if (a == ctx.author.name and b != ""):
             cursor.execute("delete from descriptions where name like '{0}' ".format(ctx.author.name))
             cursor.execute("insert into descriptions(name, description) values(%s, %s)", (ctx.author.name, description))
             check = True
    
    if (check == False):
        cursor.execute("insert into descriptions(name, description) values(%s, %s)", (ctx.author.name, description))
             

# DATABASE TEST
# namae = "Name"
# role = "Role"
# reason = "Reason"
# count = 0
# cursor.execute("insert into names (name, level) values (%s, %s)", (namae, 0.0))
# cursor.execute("select * from names")
# print(cursor.fetchall())
# cursor.execute("insert into roles (name, role) values (%s, %s)", (namae, role))
# cursor.execute("select * from roles")
# print(cursor.fetchall())
# cursor.execute("insert into warnings(name, reason) values(%s, %s)", (namae, reason))
# cursor.execute("select * from warnings")
# print(cursor.fetchall())
# cursor.execute("select * from warnings")
# warnings = cursor.fetchall()
# for a,b in warnings:
#     if (a == namae):
#         count = count + 1
# print(count)


'''
@bot.command()
async def ping(ctx):
    await ctx.send('arg')
'''

bot.run('ODk0NzM5MDIyMTMwMzMxNzEx.YVuYpg.Aay8sT8RhyEyMIrAH0_zXGgHd24')

cursor.close()
conn.close()