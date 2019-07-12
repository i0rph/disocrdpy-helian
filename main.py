import discord
import json
import datetime
import requests
import asyncio
import sys
import gc
import sqlite3
from math import ceil
import random as r
import difflib
from discord.ext import commands

prefix = '/'
bot = commands.Bot(command_prefix=f'{prefix}')
bot.remove_command("help")

con = sqlite3.connect("helian.db")

with open('lang_strings.json', 'r', encoding="utf-8") as data_file:
        lang_strings = json.load(data_file)

with open("exp_data.json", encoding="utf-8") as data_file:
        exp_data = json.load(data_file)

async def lang_check(server_id, channel_id):
        server_id = str(server_id)
        channel_id = str(channel_id)
        with open('lang.json', 'r', encoding="utf-8") as data_file:
                lang = json.load(data_file)

        if server_id in lang:
                try:
                        if channel_id in lang[server_id]['channels']:
                                return lang[server_id]['channels'][channel_id]
                        else:
                                return lang[server_id]['lang']
                except KeyError:
                        return lang[server_id]['lang']
        else:
              return False

async def lang_num(lang):
        if lang == 'ko':
                return 0
        elif lang == 'en':
                return 1
        elif lang == 'jp':
                return 2
        else:
                return False

async def time_convert(time):
        if len(time) == 5:
                pass
        else:
                time = time.replace(":", "")
        if len(time) == 4:
                time = time[0:2] + ":" + time[2:4]
        elif len(time) == 3:
                time = "0" + time[0] + ":" + time[1:3]
        elif len(time) == 2:
                time = "00:" + time
        elif len(time) == 1:
                time = "00:0" + time
                
        return time

def is_owner(ctx):
        return ctx.message.author.id in []

def translator(content, language):
        url = 'https://translation.googleapis.com/language/translate/v2'
        data = {
            "q": content,
            "target": language,
            "key": ""
        }

        try:
            text = requests.get(url, params=data).json()['data']['translations'][0]['translatedText']
        except:
            data = {
                "q": content,
                "target": language,
                "key": ""
            }
            text = requests.get(url, params=data).json()['data']['translations'][0]['translatedText']


        text = text.replace("&quot;", '"').replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#035;", "#").replace("&#039;", "'").replace("&#39;", "'").replace("&#35;", "#")

        result = text[0]

        for char in text[1:]:
            if char == "#":
                if char != result[-1]:
                    result += char
            else:
                result += char

        return result

async def send_msg(channel_id, embed_msg, lang = None, kr = None, en = None, jp = None, post_time = None):
        channel = bot.get_channel(channel_id)

        def trans_msg(lang):
            if lang == 'ko':
                trans_msg = discord.Embed(color=7458112, description=kr)
            elif lang == 'en':
                trans_msg = discord.Embed(color=7458112, description=en)
            elif lang == 'jp':
                trans_msg = discord.Embed(color=7458112, description=jp)
            trans_msg.set_footer(text=post_time)
            return trans_msg

        try:
                if embed_msg.startswith('http'):
                        await channel.send(embed_msg)
                elif lang == None:
                        await channel.send(embed=embed_msg)
                else:
                        await channel.send(embed=trans_msg(await lang_check(channel.guild.id, channel.id)))
        except Exception as e:
                #print(e)
                pass
        asyncio.sleep(25)

async def gf_weibo():
        await bot.wait_until_ready()

        while not bot.is_closed():
                now = datetime.datetime.now()
                cursor = con.cursor()
                cursor.execute("SELECT * FROM weibo WHERE channel_id")
                channels = cursor.fetchall()

                try:
                        get_weibo = requests.get("")
                        weibo = get_weibo.json()

                        print('-----------------------------------------------')
                        print("DateTime: {0}\nWeibo API Checked".format(now.strftime('%Y-%m-%d %H:%M:%S')))
                        print('-----------------------------------------------\n')

                        with open('check.txt', 'r', encoding="utf-8") as make_file:
                                saved_data = make_file.read()

                        def check(user : str):
                                if user == "少女前线":
                                        return True
                                else:
                                        return False

                        if(check(weibo['statuses'][0]['user']['screen_name']) == True):
                                if saved_data != weibo['statuses'][0]['created_at']:
                                        content = weibo['statuses'][0]['text']
                                        post_time = weibo['statuses'][0]['created_at'].replace(" +0800", "")

                                        msg = discord.Embed(color=7458112, description=content)
                                        msg.set_footer(text=post_time)

                                        lists_raw = [send_msg(channel_id[0], msg) for channel_id in channels]
                                        lp_raw = asyncio.get_event_loop()
                                        lp_raw.create_task(asyncio.wait(lists_raw))

                                        try:
                                                trans_content_en = translator(content, 'en')
                                        except:
                                                trans_content_en = "Translation function isn't available due to error occurred while processing. Sorry for inconvenience."
                                        try:
                                                trans_content_kr = translator(content, 'ko')
                                        except:
                                                trans_content_kr = "번역기능 처리 중 문제가 발생하여서 현재 번역기능을 사용할 수 없습니다. 불편을 끼쳐 죄송합니다."
                                        try:
                                                trans_content_jp = translator(content, 'ja')
                                        except:
                                                trans_content_jp = "翻訳機能の処理中にエラーが発生し、現在ご利用できません。ご迷惑をおかけして申し訳ございません。"

                                        lists_trans = [send_msg(channel_id[0], msg, 'multi_lang', trans_content_kr, trans_content_en, trans_content_jp, post_time) for channel_id in channels]
                                        lp_trans = asyncio.get_event_loop()
                                        lp_trans.create_task(asyncio.wait(lists_trans))

                                        if len(weibo['statuses'][0]['pic_urls']) > 0:
                                                for picture in weibo['statuses'][0]['pic_urls']:
                                                        url = picture['thumbnail_pic'].replace('thumbnail', 'large')
                                                        lists_pic = [send_msg(channel_id[0], url) for channel_id in channels]
                                                        lp_url = asyncio.get_event_loop()
                                                        lp_url.create_task(asyncio.wait(lists_pic))
                                                                
                                        with open('check.txt', 'w', encoding="utf-8") as make_file:
                                                make_file.write(weibo['statuses'][0]['created_at'])

                                        print('-----------------------------------------------')
                                        print("DateTime: {0}\nSuccessfully sent Weibo news.".format(now.strftime('%Y-%m-%d %H:%M:%S')))
                                        print('-----------------------------------------------\n')
                                else:
                                        print('-----------------------------------------------')
                                        print("DateTime: {0}\nNo new post since last check.".format(now.strftime('%Y-%m-%d %H:%M:%S')))
                                        print('-----------------------------------------------\n')
                        else:
                                print('-----------------------------------------------')
                                print("User Name is not 少女前线")
                                print('-----------------------------------------------\n')

                        await asyncio.sleep(1800)
                        
                except KeyError as e:
                        print('-----------------------------------------------')
                        print("DateTime: {0}\nError Message: {1}\nWeibo API request limit has reached.".format(now.strftime('%Y-%m-%d %H:%M:%S'), e))
                        print('-----------------------------------------------')
                        await asyncio.sleep(1800)

                except Exception as e:
                        print('-----------------------------------------------')
                        print("DateTime: {0}\nError Message: {1}".format(now.strftime('%Y-%m-%d %H:%M:%S'),e))
                        print('-----------------------------------------------')
                        await asyncio.sleep(1800)

@bot.event
async def on_ready():
        print(f'Logged in as {bot.user.name}')
        print(f'BOT ID : {bot.user.id}')
        print(f'Total Server(s) : {len(bot.guilds)}')
        print(f'Total Channel(s) : {len([c for c in bot.get_all_channels()])}')
        await bot.change_presence(activity=discord.Game(name=f'{prefix}help for commands'))

@bot.event
async def on_command_error(ctx, exception):
        if await lang_check(ctx.message.guild.id, ctx.message.channel.id) == False:
                await ctx.message.channel.send(f'`{prefix}setlang`을 통해서 서버의 언어를 설정해주세요. 이 명령어는 서버 관리자만 사용 할 수 있습니다.\n`{prefix}setlang`を通じてサーバの言語を設定してください。このコマンドはサーバ管理者だけ使用可能です。\nPlease set server language through `{prefix}setlang`. This command is only available for server administrator.')
        else:
                if type(exception) == discord.ext.commands.errors.CommandNotFound:
                        pass
                else:
                        await ctx.send(f'Error: `{exception}`')
                        now = datetime.datetime.now()
                        if exception != None:
                                user_id = ctx.message.author.id
                                user_name = ctx.message.author
                                message = ctx.message.content
                                current_time = now.strftime('%Y-%m-%d %H:%M:%S')

                                if isinstance(ctx.message.channel, discord.abc.PrivateChannel) is False:
                                        server_id = ctx.message.guild.id
                                        server_name = ctx.message.guild.name
                                        channel_id = ctx.message.channel.id
                                        channel_name = ctx.message.channel.name
                                        print('******************** Error ********************')
                                        print("DateTime: {0}\nServer: {1} [{2}]\nUser: {3} [{4}]\nChannel: {5} [{6}]\nMessage: {7}\nError Message: {8}".format(current_time, server_name, server_id, user_name, user_id, channel_name, channel_id, message, exception))
                                        print('******************** Error ********************')
                                else:
                                        print('******************** Error ********************')
                                        print("From DM\nDateTime: {0}\nUser: {1} [{2}]\nMessage: {3}".format(current_time, user_name, user_id, message))
                                        print('******************** Error ********************')

@bot.event
async def on_command_completion(ctx):
        now = datetime.datetime.now()
        if ctx != None:
                user_id = ctx.message.author.id
                user_name = ctx.message.author
                message = ctx.message.content
                current_time = now.strftime('%Y-%m-%d %H:%M:%S')

                if isinstance(ctx.message.channel, discord.abc.PrivateChannel) is False:
                        server_id = ctx.message.guild.id
                        server_name = ctx.message.guild.name
                        channel_id = ctx.message.channel.id
                        channel_name = ctx.message.channel.name
                        print('-----------------------------------------------')
                        print("DateTime: {0}\nServer: {1} [{2}]\nUser: {3} [{4}]\nChannel: {5} [{6}]\nMessage: {7}".format(current_time, server_name, server_id, user_name, user_id, channel_name, channel_id, message))
                        print('-----------------------------------------------\n')
                else:
                        print('-----------------------------------------------')
                        print("From DM\nDateTime: {0}\nUser: {1} [{2}]\nMessage: {3}".format(current_time, user_name, user_id, message))
                        print('-----------------------------------------------\n')

@bot.event
async def on_message(message):
        if isinstance(message.channel, discord.abc.PrivateChannel) is True and message.author != bot.user and not message.content.startswith(f'{prefix}'):
                user = await bot.get_user_info()
                time = message.created_at.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')
                if len(message.attachments) != 0:
                    for attachments in message.attachments:
                        message.content += '\n' + attachments.url
                embed = discord.Embed(color=7458112,title="{0}#{1} [{2}]".format(message.author.name, message.author.discriminator, message.author.id), description=message.content)
                embed.set_footer(text=time)
                await user.send(embed=embed)
                await message.author.send("<@{0}>, Successfully sent message to BOT developer. For help, type `/help`.\n<@{0}>, 성공적으로 봇 개발자에게 메시지를 보냈습니다. 도움말은 `/help`를 통해서 확인해주세요.".format(message.author.id))
        await bot.process_commands(message)

@bot.command()
async def setlang(ctx, lang = None):
        if ctx.message.author.guild_permissions.manage_guild:
                pass
        else:
                await ctx.send('이 명령어는 서버 관리자만 사용 할 수 있습니다.\nこのコマンドはサーバ管理者だけ使用可能です。\nThis command is only available for server administrator.')
                return
        
        if lang not in ['ko', 'en', 'jp'] or lang == None:
                await ctx.send('지원하는 언어는 다음과 같습니다.\n支援している言語には以下の物があります。\nSupported languages are:\n한국어 - `ko`\n日本語 - `jp`\nEnglish - `en`')
                return
        
        with open('lang.json', 'r', encoding="utf-8") as data_file:
                saved_lang = json.load(data_file)

        saved_lang[ctx.message.guild.id] = {'lang': lang}

        with open('lang.json', 'w', encoding="utf-8") as save_file:
                json.dump(saved_lang, save_file, ensure_ascii=False, indent="\t")

        await ctx.send(lang_strings['setlang']['success'][lang])

@bot.command()
@commands.has_permissions(manage_guild=True)
async def setchlang(ctx, chlang):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        
        if chlang not in ['ko', 'en', 'jp']:
                await ctx.send(lang_strings['setchlang']['lang_not_supported'][lang])

        with open('lang.json', 'r', encoding="utf-8") as data_file:
                saved_lang = json.load(data_file)

        try:
                saved_lang[str(ctx.message.guild.id)]['channels'][str(ctx.message.channel.id)] = chlang
        except KeyError:
                saved_lang[str(ctx.message.guild.id)]['channels'] = {str(ctx.message.channel.id): chlang}

        with open('lang.json', 'w', encoding="utf-8") as save_file:
                json.dump(saved_lang, save_file, ensure_ascii=False, indent="\t")

        await ctx.send(lang_strings['setchlang']['success'][chlang])

@bot.command()
@commands.has_permissions(manage_guild=True)
async def delchlang(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)

        with open('lang.json', 'r', encoding="utf-8") as data_file:
                saved_lang = json.load(data_file)

        try:
                del saved_lang[str(ctx.message.guild.id)]['channels'][str(ctx.message.channel.id)]

                with open('lang.json', 'w', encoding="utf-8") as save_file:
                        json.dump(saved_lang, save_file, ensure_ascii=False, indent="\t")
                        
                await ctx.send(lang_strings['delchlang']['success'][lang])
        except KeyError:
                await ctx.send(lang_strings['delchlang']['error'][lang])

@bot.command()
@commands.has_permissions(manage_guild=True)
async def weibo(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        
        cursor = con.cursor()
        cursor.execute("SELECT * FROM weibo WHERE channel_id=?", (ctx.channel.id,))
        result = cursor.fetchall()

        if len(result) == 1:
                cursor.execute("DELETE FROM weibo WHERE channel_id=?", (ctx.channel.id,))
                con.commit()
                        
                await ctx.send(lang_strings['weibo']['disable'][lang].format(ctx.message.channel.mention))
        else:
                cursor.execute("INSERT INTO weibo VALUES(?)", (ctx.channel.id,))
                con.commit()
                        
                await ctx.send(lang_strings['weibo']['enable'][lang].format(ctx.message.channel.mention))

@bot.command()
async def help(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        
        embed = discord.Embed(color = 7458112, title="Helian v2.0\n", description="")
        embed.add_field(name=f"{prefix}setlang", value=lang_strings['help']['setlang'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}setchlang", value=lang_strings['help']['setchlang'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}delchlang", value=lang_strings['help']['delchlang'][lang], inline=False)
        embed.add_field(name=f"{prefix}doll or {prefix}d", value=lang_strings['help']['doll'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}random or {prefix}rnd", value=lang_strings['help']['random'][lang], inline=False)
        embed.add_field(name=f"{prefix}info", value=lang_strings['help']['info'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}equip or {prefix}e", value=lang_strings['help']['equip'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}exp", value=lang_strings['help']['exp'][lang].format(prefix), inline=False)
        '''
        embed.add_field(name=f"{prefix}winfo", value=lang_strings['help']['winfo'][lang], inline=False)
        embed.add_field(name=f"{prefix}ulist or {prefix}ul", value=lang_strings['help']['ulist'][lang], inline=False)
        '''
        embed.add_field(name=f"{prefix}currency", value=lang_strings['help']['currency'][lang], inline=False)
        '''
        embed.add_field(name=f"{prefix}voicequiz or {prefix}vq", value=lang_strings['help']['voicequiz'][lang], inline=False)
        embed.add_field(name=f"{prefix}leaderboard or {prefix}lb", value=lang_strings['help']['leaderboard'][lang], inline=False)
        '''
        embed.add_field(name=f"{prefix}choose or {prefix}ch", value=lang_strings['help']['choose'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}avatar or {prefix}av", value=lang_strings['help']['avatar'][lang].format(prefix), inline=False)
        embed.add_field(name=f"{prefix}weibo", value=lang_strings['help']['weibo'][lang], inline=False)
        embed.add_field(name=f"{prefix}stats", value=lang_strings['help']['stats'][lang], inline=False)

        if lang == 'ko':
                embed.add_field(name="Special Thanks To", value="인형정보를 제공해준 댕댕베이스에 감사드립니다.\nhttp://ddb.kirsi.moe/", inline=False)

        embed.add_field(name=lang_strings['stats']['invite'][lang], value="https://discordapp.com/oauth2/authorize?client_id={0}&scope=bot&permissions=66186303".format(bot.user.id), inline=True)

        await ctx.send(embed=embed)

@bot.command(aliases=['av'])
async def avatar(ctx, user = None):
        if user == None:
                msg = discord.Embed(color=7458112, title=str(ctx.message.author))
                msg.set_image(url=ctx.message.author.avatar_url)
        elif user.startswith("<@"):
                user = user.replace("<@", "").replace(">", "").replace("!", "")
                member = discord.utils.find(lambda m: str(m.id) == user, ctx.message.guild.members)
                msg = discord.Embed(color=7458112, title=str(member))
                msg.set_image(url=member.avatar_url)
        else:
                member_storage = []
                for member in ctx.message.guild.members:
                        member_storage.append(member.display_name.lower())
                user_get = difflib.get_close_matches(user.lower(), member_storage, cutoff=0.1)
                member = discord.utils.find(lambda m: m.display_name.lower() == user_get[0], ctx.message.guild.members)
                msg = discord.Embed(color=7458112, title=str(member))
                msg.set_image(url=member.avatar_url)
        await ctx.send(embed=msg)

@bot.command()
async def say(ctx, *, content):
        await ctx.message.delete()
        await ctx.send(content)

@bot.command(aliases=['ch'])
async def choose(ctx, *, message):
        choices = message.split(',')
        select = r.randrange(0,len(choices))
        await ctx.send(choices[select])

@bot.command(aliases=['d'])
async def doll(ctx, time):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        
        time = await time_convert(time)

        page = 1
        data = []
        end_check = False

        if len(time) != 5:
                await ctx.send(embed = discord.Embed(color=16711680,description=lang_strings['doll']['time_error'][lang].format(ctx.message.author.id)))
        else:
                try:
                        cursor = con.cursor()
                        cursor.execute("SELECT * FROM doll_info WHERE time=?", (time,))
                        data = cursor.fetchall()
                        
                        def paginate(page = 1):
                                if lang == 'ko':
                                        doll_name = eval(data[page - 1][1])[1]
                                else:
                                        doll_name = eval(data[page - 1][1])[0]
                                msg = discord.Embed(color=7458112)
                                msg.add_field(name=lang_strings['paginate']['type'][lang], value=data[page - 1][3], inline=True)
                                msg.add_field(name=lang_strings['paginate']['rarity'][lang], value=str(data[page - 1][4])+lang_strings['paginate']['stars'][lang], inline=True)
                                msg.add_field(name=lang_strings['paginate']['time'][lang], value=data[page - 1][2], inline=True)
                                msg.add_field(name=lang_strings['paginate']['name_doll'][lang], value=doll_name, inline=True)
                                msg.set_image(url=data[page - 1][5])
                                if len(data) != 1:
                                        msg.set_footer(text="{0}/{1}".format(page, len(data)))
                                return msg

                        msg = await ctx.send(embed=paginate(page))

                        if len(data) != 1:
                                await msg.add_reaction('\u2B05')
                                await msg.add_reaction('\u27A1')
                                while end_check == False:
                                        try:
                                                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: u.id == ctx.message.author.id)
                                                if reaction != None and page < len(data) and reaction.emoji == '\u27A1':
                                                        page += 1
                                                        await msg.remove_reaction('\u27A1', user)
                                                        await msg.edit(embed=paginate(page))
                                                elif reaction != None and (page - 1) != 0 and reaction.emoji == '\u2B05':
                                                        page -= 1
                                                        await msg.remove_reaction('\u2B05', user)
                                                        await msg.edit(embed=paginate(page))
                                                elif (page - 1) == 0:
                                                        await msg.remove_reaction('\u2B05', user)
                                                elif page == len(data):
                                                        await msg.remove_reaction('\u27A1', user)
                                        except asyncio.TimeoutError:
                                                await msg.clear_reactions()
                                                end_check = True
                                                break
                except IndexError:
                        await ctx.send(embed=discord.Embed(color=16711680,description=lang_strings['doll']['not_found'][lang].format(ctx.message.author.id)))

async def buff_to_convert(lang, gtype):
	if lang == 'ko':
		if gtype == 'ALL':
			return '모든총기'
		elif gtype == 'HG':
			return '권총'
		elif gtype == 'AR':
			return '돌격소총'
		elif gtype == 'SMG':
			return '기관단총'
		elif gtype == 'MG':
			return '기관총'
		elif gtype == 'SG':
			return '산탄총'
	elif lang == 'en':
		if gtype == 'ALL':
			return 'all gun'
		else:
			return gtype

async def info_form(lang, langnum, data, answer_num=0, remodel=False):
	if lang == 'ko':
		name = eval(data[answer_num][1])[1]
	else:
		name = eval(data[answer_num][1])[0]
	time = data[answer_num][2]
	gunid = data[answer_num][0]
	gun_type = data[answer_num][3]
	star = str(data[answer_num][4])
	if star != 'Extra':
		star += lang_strings['paginate']['stars'][lang]
	buff_graphic = data[answer_num][6]
	buff_description = eval(data[answer_num][7])[langnum]
	buff_to = data[answer_num][13]
	if lang == 'ko':
		temp_type = await buff_to_convert(lang, buff_to)
		buff_description = f'버프칸의 {temp_type}에게 {buff_description}'
	elif lang == 'en':
		temp_type = await buff_to_convert(lang, buff_to)
		buff_description = f'{buff_description} to {temp_type}'
	skill_name = eval(data[answer_num][8])[langnum]
	skill_description = eval(data[answer_num][9])[langnum]
	img_url = data[answer_num][5]
	illustrator = data[answer_num][10]
	CV = data[answer_num][11]
	if CV == 'None' and lang == 'ko':
		CV = '미정'
	if remodel == True:
		remodel_skill_1_name = eval(data[answer_num][14])[langnum]
		remodel_skill_1_description = eval(data[answer_num][15])[langnum]
		remodel_skill_2_name = eval(data[answer_num][16])[langnum]
		remodel_skill_2_description = eval(data[answer_num][17])[langnum]
		remodel_buff = eval(data[answer_num][18])[langnum]
		if lang == 'ko':
			temp_type = await buff_to_convert(lang, buff_to)
			remodel_buff = f'버프칸의 {temp_type}에게 {remodel_buff}'
		elif lang == 'en':
			temp_type = await buff_to_convert(lang, buff_to)
			remodel_buff = f'{remodel_buff} to {temp_type}'
		remodel_image = data[answer_num][19]
		remodel_rarity = str(data[answer_num][20]) + lang_strings['paginate']['stars'][lang]
		if data[answer_num][21] != None:
			remodel_tile = data[answer_num][21]
		else:
			remodel_tile = buff_graphic
	msg = discord.Embed(color=7458112)
	msg.add_field(name=lang_strings['paginate']['name_doll'][lang], value=name, inline=True)
	msg.add_field(name=lang_strings['paginate']['type'][lang], value=gun_type, inline=True)
	if remodel == True:
		msg.add_field(name=lang_strings['paginate']['rarity'][lang], value=remodel_rarity, inline=True)
	else:
		msg.add_field(name=lang_strings['paginate']['rarity'][lang], value=star, inline=True)
	msg.add_field(name=lang_strings['paginate']['time'][lang], value=time, inline=True)
	msg.add_field(name=lang_strings['paginate']['num'][lang], value=gunid, inline=False)
	if remodel == True:
		msg.add_field(name=lang_strings['paginate']['buff'][lang], value='{}\n\n{}'.format(remodel_tile, remodel_buff), inline=True)
		msg.add_field(name=lang_strings['paginate']['skill'][lang], value='**{}**\n{}\n\n**{}**\n{}'.format(remodel_skill_1_name, remodel_skill_1_description, remodel_skill_2_name, remodel_skill_2_description), inline=True)
		msg.set_image(url=remodel_image)
	else:
		msg.add_field(name=lang_strings['paginate']['buff'][lang], value='{}\n\n{}'.format(buff_graphic, buff_description), inline=True)
		msg.add_field(name=lang_strings['paginate']['skill'][lang], value='**{}**\n{}'.format(skill_name, skill_description), inline=True)
		msg.set_image(url=img_url)
	msg.add_field(name=lang_strings['paginate']['illustrator'][lang], value=illustrator, inline=True)
	msg.add_field(name=lang_strings['paginate']['cv'][lang], value=CV, inline=True)
	return msg

@bot.command()
async def info(ctx, *, term : str):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        langnum = await lang_num(lang)

        term = f'%{term}%'

        try:
                cursor = con.cursor()
                cursor.execute("SELECT * FROM doll_info WHERE alias LIKE ?", (term,))
                data = cursor.fetchall()

                if len(data) == 1:
                        embed = await info_form(lang, langnum, data)
                        msg = await ctx.send(embed=embed)

                        if data[0][20] != None:
                        	end_check = False
                        	remodel_toggle = False
                        	await msg.add_reaction('\u23EB')
                        	await msg.add_reaction('\u23EC')

                        	while end_check == False:
                        		try:
                        			reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: u.id == ctx.message.author.id)
                        			if reaction != None and remodel_toggle == False and reaction.emoji == '\u23EB':
                        				remodel_toggle = True
                        				await msg.remove_reaction('\u23EB', user)
                        				embed = await info_form(lang, langnum, data, 0, remodel_toggle)
                        				await msg.edit(embed=embed)
                        			elif reaction != None and remodel_toggle == True and reaction.emoji == '\u23EC':
                        				remodel_toggle = False
                        				await msg.remove_reaction('\u23EC', user)
                        				embed = await info_form(lang, langnum, data, 0, remodel_toggle)
                        				await msg.edit(embed=embed)
                        			elif remodel_toggle == False:
                        				await msg.remove_reaction('\u23EC', user)
                        			elif remodel_toggle == True:
                        				await msg.remove_reaction('\u23EB', user)
                        		except asyncio.TimeoutError:
                        			await msg.clear_reactions()
                        			end_check = True
                        			break
                        
                elif len(data) == 0:
                        return
                
                else:
                        temp = '```'
                        temp_cnt = 0
                        temp_keys = []

                        for doll in data:
                                if lang == 'ko':
                                        temp += f'\n{temp_cnt} : {eval(doll[1])[1]}'
                                else:
                                        temp += f'\n{temp_cnt} : {eval(doll[1])[0]}'
                                temp_cnt += 1

                        temp += '```'

                        ask_msg = await ctx.send(temp)

                        temp_range = []

                        for num in range(0, len(data)):
                                temp_range.append(str(num))

                        try:
                                answer = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id and m.content in temp_range)

                                await ctx.message.channel.delete_messages([ask_msg, answer])

                                answer_num = int(answer.content)

                                embed = await info_form(lang, langnum, data, answer_num)
                                msg = await ctx.send(embed=embed)

                                if data[answer_num][20] != None:
                                	end_check = False
                                	remodel_toggle = False
                                	await msg.add_reaction('\u23EB')
                                	await msg.add_reaction('\u23EC')

                                	while end_check == False:
                                		try:
                                			reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: u.id == ctx.message.author.id)
                                			if reaction != None and remodel_toggle == False and reaction.emoji == '\u23EB':
                                				remodel_toggle = True
                                				await msg.remove_reaction('\u23EB', user)
                                				embed = await info_form(lang, langnum, data, answer_num, remodel_toggle)
                                				await msg.edit(embed=embed)
                                			elif reaction != None and remodel_toggle == True and reaction.emoji == '\u23EC':
                                				remodel_toggle = False
                                				await msg.remove_reaction('\u23EC', user)
                                				embed = await info_form(lang, langnum, data, answer_num, remodel_toggle)
                                				await msg.edit(embed=embed)
                                			elif remodel_toggle == False:
                                				await msg.remove_reaction('\u23EC', user)
                                			elif remodel_toggle == True:
                                				await msg.remove_reaction('\u23EB', user)
                                		except asyncio.TimeoutError:
                                			await msg.clear_reactions()
                                			end_check = True
                                			break

                        except asyncio.TimeoutError:
                                ask_msg.delete()

        except Exception as e:
            #print(e)
            await ctx.send(f'Error: `{e}`')
                #await ctx.send(lang_strings['info']['not_found'][lang])

        
@bot.command(aliases=['e'])
async def equip(ctx, time):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        langnum = await lang_num(lang)

        time = await time_convert(time)

        page = 1
        data = []
        end_check = False

        if len(time) != 5:
                await ctx.send(embed = discord.Embed(color=16711680,description=lang_strings['equip']['time_error'][lang].format(ctx.message.author.id)))
        elif time[1] in ['3', '4', '5']:
                try:
                        cursor = con.cursor()
                        cursor.execute("SELECT * FROM equip_info WHERE time=?", (time,))
                        data = cursor.fetchall()
                        
                        msg = discord.Embed(color=7458112)
                        msg.add_field(name=lang_strings['paginate']['name_fairy'][lang], value=eval(data[0][1])[langnum], inline=True)
                        msg.add_field(name=lang_strings['paginate']['type'][lang], value=eval(data[0][3])[langnum], inline=True)
                        msg.add_field(name=lang_strings['paginate']['time'][lang], value=data[0][0], inline=True)
                        msg.add_field(name=lang_strings['paginate']['stats'][lang], value=eval(data[0][4])[langnum], inline=True)
                        msg.add_field(name=lang_strings['paginate']['skill'][lang], value='**{}**\n{}'.format(eval(data[0][6])[langnum], eval(data[0][7])[langnum]), inline=True)
                        msg.set_image(url=data[0][5])

                        await ctx.send(embed=msg)
                except IndexError:
                        await ctx.send(embed=discord.Embed(color=16711680,description=lang_strings['equip']['not_found'][lang].format(ctx.message.author.id)))
        else:
                try:
                        cursor = con.cursor()
                        cursor.execute("SELECT * FROM equip_info WHERE time=?", (time,))
                        data = cursor.fetchall()
                        
                        def paginate(page = 1):
                                msg = discord.Embed(color=7458112)
                                msg.add_field(name=lang_strings['paginate']['name_equip'][lang], value=eval(data[page - 1][1])[langnum], inline=True)
                                msg.add_field(name=lang_strings['paginate']['type'][lang], value=eval(data[page - 1][3])[langnum], inline=True)
                                msg.add_field(name=lang_strings['paginate']['rarity'][lang], value=str(data[page - 1][2])+lang_strings['paginate']['stars'][lang], inline=True)
                                msg.add_field(name=lang_strings['paginate']['time'][lang], value=data[page - 1][0], inline=True)
                                msg.add_field(name=lang_strings['paginate']['stats'][lang], value=eval(data[page - 1][4])[langnum], inline=True)
                                msg.set_thumbnail(url=data[page - 1][5])
                                if len(data) != 1:
                                        msg.set_footer(text="{0}/{1}".format(page, len(data)))
                                return msg
                        def check(reaction, user):
                                if user == bot.user:
                                        return False
                                else:
                                        e = str(reaction.emoji)
                                        return e.startswith(('\u2B05', '\u27A1'))
                                
                        msg = await ctx.send(embed=paginate(page))

                        if len(data) != 1:
                                await msg.add_reaction('\u2B05')
                                await msg.add_reaction('\u27A1')

                                while end_check == False:
                                        try:
                                                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: u.id == ctx.message.author.id)

                                                if reaction != None and page < len(data) and reaction.emoji == '\u27A1':
                                                        page += 1
                                                        await msg.remove_reaction('\u27A1', user)
                                                        await msg.edit(embed=paginate(page))
                                                elif reaction != None and (page - 1) != 0 and reaction.emoji == '\u2B05':
                                                        page -= 1
                                                        await msg.remove_reaction('\u2B05', user)
                                                        await msg.edit(embed=paginate(page))
                                                elif (page - 1) == 0:
                                                        await msg.remove_reaction('\u2B05', user)
                                                elif page == len(data):
                                                        await msg.remove_reaction('\u27A1', user)
                                        except asyncio.TimeoutError:
                                                await msg.clear_reactions()
                                                end_check = True
                                                break
                except IndexError:
                        await ctx.send(embed=discord.Embed(color=16711680,description=lang_strings['equip']['not_found'][lang].format(ctx.message.author.id)))

@bot.command()
async def currency(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)

        with open("currency_data.json", encoding="utf-8") as data_file:
                currency_data = json.load(data_file)
        
        def get_currency(currency : str, lang):
                if lang == 'en':
                        money = 'USD'
                elif lang == 'jp':
                        money = 'JPY'
                elif lang == 'ko':
                        money = 'KRW'
                data = json.loads(requests.get(f"https://api.manana.kr/exchange/rate/{money}/{currency}.json").text)
                raw_date = data[0]['date']
                rate = data[0]['rate']

                return {'date': raw_date, 'rate': rate}

        if lang == 'en':
                USD = get_currency('CNY', lang)
        else:
                USD = get_currency('USD', lang)
                
        TWD = get_currency('TWD', lang)
        HKD = get_currency('HKD', lang)

        msg = discord.Embed(color=7458112,title=lang_strings['currency']['title'][lang])

        for data in currency_data:
                CNY = data
                if lang == 'en':
                        USD_value = float(USD['rate']) * int(CNY)
                else:
                        USD_value = float(USD['rate']) * float(currency_data[CNY]['USD'])
                TWD_value = float(TWD['rate']) * float(currency_data[CNY]['TWD'])
                HKD_value = float(HKD['rate']) * float(currency_data[CNY]['HKD'])
                msg.add_field(name=f"{CNY}元", value=lang_strings['currency']['value'][lang].format(str(round(USD_value)), str(round(TWD_value)), str(round(HKD_value))), inline=False)
                
        msg.set_footer(text=lang_strings['currency']['date'][lang] + USD['date'])
        await ctx.send(embed=msg)


@bot.command(aliases=['rnd'])
async def random(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        if lang == 'ko':
                langnum = 1
        else:
                langnum = 0
        
        cursor = con.cursor()
        cursor.execute("SELECT * FROM doll_info")
        data = cursor.fetchall()

        select = r.choice(data)
        name = eval(select[1])[langnum]
        gun_type = select[3]
        star = str(select[4])
        if star != 'Extra':
                star += lang_strings['paginate']['stars'][lang]
        img = select[5]
        time = select[0]

        msg = discord.Embed(color=7458112)
        msg.add_field(name=lang_strings['paginate']['type'][lang], value=gun_type, inline=True)
        msg.add_field(name=lang_strings['paginate']['rarity'][lang], value=star, inline=True)
        msg.add_field(name=lang_strings['paginate']['time'][lang], value=time, inline=True)
        msg.add_field(name=lang_strings['paginate']['name_doll'][lang], value=name, inline=True)
        msg.set_image(url=img)

        await ctx.send(embed=msg)

@bot.command()
async def exp(ctx, current_lv : str, current_exp : int, target_lv : str, oath = None):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        global exp_data

        target_temp = target_lv
        acc_lv = 0

        result = 0
        total_exp = 0

        if oath == None:
                oath = 1
        else:
                oath = 2
        if exp_data[current_lv]['current_end'] > current_exp and current_exp >= 0 and int(target_lv) > int(current_lv):
                if int(target_lv) > 115:
                        if int(current_lv) > 115:
                                temp_lv = current_lv
                        else:
                                temp_lv = '115'
                        acc_lv += exp_data[target_lv]["target"] - exp_data[temp_lv]["target"]
                        target_lv = '115'
                if int(target_lv) > 110 and int(current_lv) < 115:
                        if int(current_lv) > 110:
                                temp_lv = current_lv
                        else:
                                temp_lv = '110'
                        acc_lv += exp_data[target_lv]["target"] - exp_data[temp_lv]["target"]
                        target_lv = '110'
                if int(target_lv) > 100 and int(current_lv) < 110:
                        if int(current_lv) > 100:
                                temp_lv = current_lv
                        else:
                                temp_lv = '100'
                        acc_lv += exp_data[target_lv]["target"] - exp_data[temp_lv]["target"]
                        target_lv = '100'
                if int(target_temp) > 100:
                        if int(current_lv) > 100:
                                result += ceil((acc_lv - current_exp) / (3000 * oath))
                                total_exp = acc_lv
                        else:
                                result += ceil(acc_lv / (3000 * oath))
                                total_exp += acc_lv
                if int(target_lv) <= 100 and int(current_lv) < 100:
                        result += ceil(((exp_data[target_lv]["target"] - exp_data[current_lv]["target"]) - current_exp) / 3000)
                        total_exp += (exp_data[target_lv]["target"] - exp_data[current_lv]["target"]) - current_exp
                        
                await ctx.send(embed=discord.Embed(color=7458112, description=lang_strings['exp']['result'][lang].format(current_lv, current_exp, target_temp, result, total_exp)))
        else:
                await ctx.send(embed = discord.Embed(color=16711680,description=lang_strings['exp']['error'][lang].format(ctx.message.author.id)))
'''
@bot.command()
async def winfo(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        user = ctx.message.author
        await ctx.message.delete()
        ask_platform = await ctx.send(lang_strings['winfo']['ask_platform'][lang].format(ctx.message.author.mention))
        try:
                answer_platform = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)
                if answer_platform.content == '6':
                        await ctx.message.channel.delete_messages([ask_platform, answer_platform])
                        return
                elif answer_platform.content not in ["1", "2", "3", "4", "5"]:
                        await ctx.message.channel.delete_messages([ask_platform, answer_platform])
                        await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['num_error'][lang].format(ctx.message.author.id)))
                        return
                else:
                        pass
        except asyncio.TimeoutError:
                await ask_platform.delete()
                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['timeout'][lang].format(ctx.message.author.id)))
                return
        
        if lang == 'en':
                platform_data = {"1": "bilibili", "2": "DigitalSky", "3": "Korea", "4": "Taiwan", "5": "Japan"}
        elif lang == 'ko':
                platform_data = {"1": "비리비리", "2": "운영사", "3": "한국", "4": "대만", "5": "일본"}
        elif lang == 'jp':
                platform_data = {"1": "ビリビリ", "2": "運営社", "3": "韓国", "4": "台湾", "5": "日本"}
        platform = platform_data.get(answer_platform.content)
        await ctx.message.channel.delete_messages([ask_platform, answer_platform])

        if answer_platform.content == "1":
                ask_server = await ctx.send(lang_strings['winfo']['ask_server'][lang].format(ctx.message.author.mention))
                try:
                        answer_server = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)
                        if int(answer_server.content) not in range(0,11):
                                await ctx.message.channel.delete_messages([ask_server, answer_server])
                                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['num_error'][lang].format(ctx.message.author.id)))
                                return
                        else:
                                server = answer_server.content
                                await ctx.message.channel.delete_messages([ask_server, answer_server])
                except asyncio.TimeoutError:
                        await ask_server.delete()
                        await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['timeout'][lang].format(ctx.message.author.id)))
                        return

        elif answer_platform.content == "2":
                ask_server = await ctx.send(lang_strings['winfo']['ask_server'][lang].format(ctx.message.author.mention))
                try:
                        answer_server = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)
                        if int(answer_server.content) not in range(0,14):
                                await ctx.message.channel.delete_messages([ask_server, answer_server])
                                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['num_error'][lang].format(ctx.message.author.id)))
                                return
                        else:
                                server = answer_server.content
                                await ctx.message.channel.delete_messages([ask_server, answer_server])
                except asyncio.TimeoutError:
                        await ask_server.delete()
                        await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['timeout'][lang].format(ctx.message.author.id)))
                        return
        else:
                server = ''

        ask_nick = await ctx.send(lang_strings['winfo']['ask_nick'][lang].format(ctx.message.author.mention))

        try:
                answer_nick = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)

        except asyncio.TimeoutError:
                await ask_nick.delete()
                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['timeout'][lang].format(ctx.message.author.id)))
                return

        await ctx.message.channel.delete_messages([ask_nick, answer_nick])
        nick = answer_nick.content

        ask_uid = await ctx.send(lang_strings['winfo']['ask_uid'][lang].format(ctx.message.author.mention))

        try:
                answer_uid = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)

        except asyncio.TimeoutError:
                await ask_uid.delete()
                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['timeout'][lang].format(ctx.message.author.id)))
                return

        await ctx.message.channel.delete_messages([ask_uid, answer_uid])
        uid = answer_uid.content

        with open('friend.json', 'r', encoding="utf-8") as data_file:
                friend_info = json.load(data_file)

        try:
                for i in friend_info[str(user)]:
                        if i['platform'] == platform+server and i['nick'] == nick and i['uid'] == uid:
                                await bot.reply(lang_strings['winfo']['duplicated'][lang])
                                return
                        else:
                                pass
        except:
                pass

        ask_check = await ctx.send(lang_strings['winfo']['ask_check'][lang].format(ctx.message.author.mention, platform+server,nick,uid))

        try:
                answer_check = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)
                await ctx.message.channel.delete_messages([ask_check, answer_check])

                if answer_check.content in ["y","Y"]:
                        try:
                                friend_info[str(user)].append({"platform": answer_platform.content, "platform_str": platform+server, "nick": nick, "uid": uid, "lang": lang})
                        except KeyError:
                                friend_info[str(user)] = []
                                friend_info[str(user)].append({"platform": answer_platform.content, "platform_str": platform+server, "nick": nick, "uid": uid, "lang": lang})

                        with open('friend.json', 'w', encoding="utf-8") as make_file:
                                json.dump(friend_info, make_file, ensure_ascii=False, indent="\t")
        except asyncio.TimeoutError:
                await ask_check.delete()
                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['winfo']['timeout'][lang].format(ctx.message.author.id)))
                return

@bot.command(aliases=['ul'])
async def ulist(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        await ctx.message.delete()
        ask_platform = await ctx.send(lang_strings['ulist']['ask_platform'][lang].format(ctx.message.author.id))
        try:
                answer_platform = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id)

                if answer_platform.content == '6':
                        await ctx.message.channel.delete_messages([ask_platform, answer_platform])
                        return
                else:
                        pass

        except asyncio.TimeoutError:
                await bot.delete_message(ask_platform)
                await ctx.send(embed=discord.Embed(color=16711680, description=lang_strings['ulist']['timeout'][lang].format(ctx.message.author.id)))
                return

        await ctx.message.channel.delete_messages([ask_platform, answer_platform])

        with open('friend.json', 'r', encoding="utf-8") as data_file:
                friend = json.load(data_file)

        data = []
        page = 1
        end_check = False

        for i in friend:
                for x in friend[i]:
                        if x['platform'] == answer_platform.content and lang == x['lang']:
                                data.append({"nick": x['nick'], "uid": x['uid'], "platform": x['platform_str'], "id": i})
                                
        def check(reaction, user):
                if user == bot.user:
                        return False
                else:
                        e = str(reaction.emoji)
                        return e.startswith(('\u2B05', '\u27A1'))

        def total_page(data):
                if len(data) % 10 == 0:
                        return round(len(data)/30)
                else:
                        return round(len(data)/30 + 0.5)

        def paginate(page = 1):
                msg = '```\n'
                try:
                        for i in range((page * 30 - 30), (page * 30), 1):
                                if data[i]['platform'] in ['3','4','5']:
                                        msg += "{0} ({1}) - {2}\n".format(data[i]['id'], data[i]['nick'], data[i]['uid'])
                                else:
                                        msg += "{0} ({1}) - {2} ({3})\n".format(data[i]['id'], data[i]['nick'], data[i]['uid'], data[i]['platform'])
                except:
                        pass

                if total_page(data) != 1:
                        msg += '{0}/{1}\n'.format(page, total_page(data))
                msg += '```'
                return msg

        msg = await ctx.send(paginate(page))

        if len(data) > 30:
                await msg.add_reaction('\u2B05')
                await msg.add_reaction('\u27A1')

                while end_check == False:
                        try:
                                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: u.id == ctx.message.author.id)

                                if reaction != None and page < len(data) and reaction.emoji == '\u27A1':
                                        page += 1
                                        await msg.remove_reaction('\u27A1', user)
                                        await msg.edit(embed=paginate(page))
                                elif reaction != None and (page - 1) != 0 and reaction.emoji == '\u2B05':
                                        page -= 1
                                        await msg.remove_reaction('\u2B05', user)
                                        await msg.edit(embed=paginate(page))
                                elif (page - 1) == 0:
                                        await msg.remove_reaction('\u2B05', user)
                                elif page == len(data):
                                        await msg.remove_reaction('\u27A1', user)
                        except asyncio.TimeoutError:
                                await msg.clear_reactions()
                                end_check = True
                                break

@bot.command(aliases=['vq'])
async def voicequiz(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        
        try:
                vc = await ctx.message.author.voice.channel.connect()

                with open('voice.json', 'r', encoding='utf-8') as read_file:
                        voice_dict = json.load(read_file)

                pt = 0
                while True:
                        voices = voice_dict
                        selected_dolls = []
                        for i in range(0,5):
                                selected = r.choice(voices)
                                voices.remove(selected)
                                selected_dolls.append(selected)

                        question = "```\n"
                        temp = []
                        cnt = 1
                        for doll in selected_dolls:
                                if lang == 'ko':
                                        doll_name = doll[list(doll.keys())[0]]['gun_name_KR']
                                else:
                                        doll_name = list(doll.keys())[0]
                                question += f"{cnt}. {doll_name}\n"
                                doll_dict = doll[list(doll.keys())[0]]
                                temp.append({'name': doll_name, 'gun_name_KR': doll_dict['gun_name_KR'], 'number': doll_dict['number']})
                                cnt += 1
                                
                        question += '```'
                        selected = r.choice(temp)
                        if lang == 'ko':
                                answer = {'name': selected['gun_name_KR'], 'id': selected['number']}
                        else:
                                answer = {'name': selected['name'], 'id': selected['number']}

                        await ctx.send(lang_strings['voicequiz']['question'][lang])

                        filename = './voice/' + answer['id'] + '_TITLECALL_JP.wav'
                        vc.play(discord.FFmpegPCMAudio(f'{filename}'))
                        while True:
                                if vc.is_playing() == False:
                                        break
                        vc.stop()

                        await ctx.send(question)

                        try:
                                user_answer = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id and m.content in ['1','2','3','4','5'])

                                if user_answer.content == str(temp.index(selected) + 1):
                                        pt += 1
                                        await ctx.send(lang_strings['voicequiz']['answer'][lang].format(pt))
                                else:
                                        await ctx.send(lang_strings['voicequiz']['wrong'][lang].format(answer['name'], pt))
                                        if pt != 0:
                                                await ctx.send(lang_strings['voicequiz']['ask_save'][lang])
                                        else:
                                                break

                                        try:
                                                end_answer = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id and m.content in ['1','2'])

                                                if end_answer.content == '1' and pt != 0:
                                                        with open('voice_leaderboard.json', 'r', encoding='utf-8') as data_file:
                                                                leaderboard_data = json.load(data_file)

                                                        if str(pt) not in leaderboard_data.keys():
                                                                leaderboard_data[str(pt)] = []
                                                                leaderboard_data[str(pt)].append(str(int(datetime.datetime.timestamp(datetime.datetime.now()))) + '|' + str(ctx.message.author))
                                                                leaderboard_data[str(pt)].sort()
                                                                leaderboard_data[str(pt)].reverse()
                                                        else:
                                                                leaderboard_data[str(pt)].append(str(int(datetime.datetime.timestamp(datetime.datetime.now()))) + '|' + str(ctx.message.author))
                                                                leaderboard_data[str(pt)].sort()
                                                                leaderboard_data[str(pt)].reverse()

                                                        with open('voice_leaderboard.json', 'w', encoding='utf-8') as make_file:
                                                                json.dump(leaderboard_data, make_file, ensure_ascii=False, indent="\t")

                                                        await ctx.send(lang_strings['voicequiz']['saved'][lang].format(ctx.message.author.id))
                                                        break
                                                else:
                                                        ctx.send(lang_strings['voicequiz']['end'][lang].format(ctx.message.author.id))
                                                        break

                                        except asyncio.TimeoutError:
                                                break

                        except asyncio.TimeoutError:
                                await ctx.send(lang_strings['voicequiz']['timeout'][lang].format(answer['name'], pt))
                                if pt != 0:
                                        await ctx.send(lang_strings['voicequiz']['ask_save'][lang])

                                        try:
                                                end_answer = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author.id == ctx.message.author.id and m.content in ['1','2'])

                                                if end_answer.content == '1' and pt != 0:
                                                        with open('voice_leaderboard.json', 'r', encoding='utf-8') as data_file:
                                                                leaderboard_data = json.load(data_file)

                                                        if str(pt) not in leaderboard_data.keys():
                                                                leaderboard_data[str(pt)] = []
                                                                leaderboard_data[str(pt)].append(str(int(datetime.datetime.timestamp(datetime.datetime.now()))) + '|' + str(ctx.message.author))
                                                                leaderboard_data[str(pt)].sort()
                                                                leaderboard_data[str(pt)].reverse()
                                                        else:
                                                                leaderboard_data[str(pt)].append(str(int(datetime.datetime.timestamp(datetime.datetime.now()))) + '|' + str(ctx.message.author))
                                                                leaderboard_data[str(pt)].sort()
                                                                leaderboard_data[str(pt)].reverse()

                                                        with open('voice_leaderboard.json', 'w', encoding='utf-8') as make_file:
                                                                json.dump(leaderboard_data, make_file, ensure_ascii=False, indent="\t")

                                                        await ctx.send(lang_strings['voicequiz']['saved'][lang].format(ctx.message.author.id))
                                                        break
                                                else:
                                                        ctx.send(lang_strings['voicequiz']['end'][lang].format(ctx.message.author.id))
                                                        break
                                        

                                        except asyncio.TimeoutError:
                                                break
                await vc.disconnect()
        except AttributeError:
                await ctx.send(lang_strings['voicequiz']['not_in_voice'][lang].format(ctx.message.author.id))
                await vc.disconnect()
        except Exception as e:
                await ctx.send(lang_strings['voicequiz']['error'][lang].format(ctx.message.author.id, e))
                await vc.disconnect()

@bot.command(aliases=['lb'])
async def leaderboard(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        
        with open('voice_leaderboard.json', 'r', encoding='utf-8') as data_file:
                leaderboard_data = json.load(data_file)

        keys = list(leaderboard_data.keys())
        keys.sort(key=int)
        keys.reverse()

        msg = lang_strings['leaderboard']['title'][lang]

        cnt = 0
        for x in keys:
                if cnt == 10:
                        break
                for i in leaderboard_data[x]:
                        if cnt == 10:
                                break
                        data = i.split('|')
                        msg += lang_strings['leaderboard']['count'][lang].format(data[1], x)
                        cnt += 1
        msg += '```'
        await ctx.send(msg)
'''
@bot.command()
async def stats(ctx):
        lang = await lang_check(ctx.message.guild.id, ctx.message.channel.id)
        memory_usage = round(sum(sys.getsizeof(i) for i in gc.get_objects())/1000000, 2)
        total_server_cnt = len(bot.guilds)
        total_text_channel_cnt = 0
        total_voice_channel_cnt = 0

        for channel in bot.get_all_channels():
                if 'Text' in str(type(channel)):
                        total_text_channel_cnt += 1
                elif 'Voice' in str(type(channel)):
                        total_voice_channel_cnt += 1

        msg = discord.Embed(color=7458112, title="Helian v2.1")
        msg.add_field(name=lang_strings['stats']['developer'][lang], value="iorph#0001", inline=True)
        msg.add_field(name=lang_strings['stats']['developer_id'][lang], value="104922432955035648", inline=True)
        msg.add_field(name=lang_strings['stats']['bot_id'][lang], value=bot.user.id, inline=True)
        msg.add_field(name=lang_strings['stats']['memory'][lang], value="{} MB".format(memory_usage), inline=True)
        msg.add_field(name=lang_strings['stats']['presence'][lang], value=lang_strings['stats']['presence_value'][lang].format(total_server_cnt, total_text_channel_cnt, total_voice_channel_cnt), inline=True)
        msg.add_field(name=lang_strings['stats']['invite'][lang], value="https://discordapp.com/oauth2/authorize?client_id={0}&scope=bot&permissions=66186303".format(bot.user.id), inline=True)

        await ctx.send(embed=msg)

@bot.command(aliases=['sc'])
@commands.check(is_owner)
async def sendchannel(ctx, channelid, *, msg):
        destination = discord.utils.get(bot.get_all_channels(), id=int(channelid))
        embed = discord.Embed(color=7458112, description=msg)
        embed.set_footer(text=ctx.message.author)
        await destination.send(embed=embed)
        await ctx.message.author.send("<@{0}>, **{1} 서버의 {2} 채널**에 메시지를 성공적으로 전송했습니다.".format(ctx.message.author.id, destination.guild.name, destination.name))

@bot.command(aliases=['su'])
@commands.check(is_owner)
async def senduser(ctx, userid, *, msg):
        destination = discord.utils.get(bot.get_all_members(), id=int(userid))
        embed = discord.Embed(color=7458112, description=msg)
        embed.set_footer(text=ctx.message.author)
        await destination.send(embed=embed)
        await ctx.message.author.send("<@{0}>, **{1} ({2})**님에게 메시지를 성공적으로 전송했습니다.".format(ctx.message.author.id, destination, destination.id))

@bot.command()
@commands.check(is_owner)
async def reload_str(ctx):
        with open('lang_strings.json', 'r', encoding="utf-8") as data_file:
                lang = json.load(data_file)

        global lang_strings

        lang_strings = lang

        await ctx.send('String Reload complete!')

@bot.command()
@commands.check(is_owner)
async def reload_db(ctx):
        global con

        con = sqlite3.connect("helian.db")

        await ctx.send('DB Reload complete!')

bot.loop.create_task(gf_weibo())
bot.run('')
