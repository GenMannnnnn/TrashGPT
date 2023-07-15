import random
import discord
from discord import Message, Intents
from discord.ext import commands
import json


bot = commands.Bot(command_prefix="!", intents=Intents.all())
keyword_messages = {}

# 自定義菜單的內容
help_menu = {
    '垃圾話機器人': {
        '!add <關鍵字> <回覆>': '添加關鍵字與回覆，圖片請使用鏈結',
        '!del <關鍵字>': '刪除關鍵字或指定回覆',
        '!alist':'顯示關鍵字列表'
    },
    '分隊助手': {
        '!member_add <玩家名稱>': '添加玩家',
        '!member_del <玩家名稱>': '移除玩家',
        '!member_list ':'顯示玩家列表',
        '!team_rank':'隨機分隊',
        '!del_all':'清除所有玩家'
    }
}

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='指令幫助菜單(!help)', color=discord.Color.green())

        for category, commands in help_menu.items():
            command_list = '\n'.join([f'{command}: {description}' for command, description in commands.items()])
            embed.add_field(name=category, value=command_list, inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

bot.help_command = MyHelp()


def load_keywords():
    try:
        with open("keywords.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_keywords():
    with open("keywords.json", "w", encoding="utf-8") as file:
        json.dump(keyword_messages, file, ensure_ascii=False)  


@bot.event
async def on_ready():
    
    await bot.change_presence(activity=discord.Game(name="Minecraft"))
    print(f"Bot已登入：{bot.user.name} ({bot.user.id})")
    global keyword_messages
    keyword_messages = load_keywords()


@bot.event
async def on_message(message: Message):
    if message.author == bot.user:
        return

    if (key := message.content) in keyword_messages:
        await message.channel.send(
            random.choice(value)
            if type(value := keyword_messages[key]) is list
            else value
        )

    await bot.process_commands(message)


@bot.command()
async def add(ctx, keyword: str, response: str):
    if keyword in keyword_messages:

        if type(d := keyword_messages[keyword]) is list:
            d.append(response)
        else:
            keyword_messages[keyword] = [d, response]

    else: 
            keyword_messages[keyword] = response

    
    save_keywords()
    


    await ctx.send(f"### 已添加關鍵字")

@bot.command()
async def alist(ctx):
    embed = discord.Embed(title='關鍵字清單(Keyword List)', color=discord.Color.blue())
    
    if keyword_messages:
        for keyword in keyword_messages.keys():
            embed.add_field(name='', value=keyword, inline=True)
    else:
        embed.description = '目前沒有儲存的關鍵字'
    
    await ctx.send(embed=embed)

@bot.command()
async def adel(ctx, keyword: str):
    if keyword in keyword_messages:
        response_list = keyword_responses[keyword]

        if len(response_list) > 1:
            # 如果關鍵字有多個回覆，提供選項給使用者選擇要刪除的回覆
            options = '\n'.join([f'{index + 1}. {response}' for index, response in enumerate(response_list)])
            prompt_message = await ctx.send(f'請選擇要刪除的回覆（輸入數字）：\n{options}')

            def check_response(message):
                return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()

            try:
                user_response = await bot.wait_for('message', check=check_response, timeout=30)
                selected_index = int(user_response.content) - 1

                if 0 <= selected_index < len(response_list):
                    deleted_response = response_list.pop(selected_index)
                    save_keywords()
                    await ctx.send(f'已刪除回覆：{deleted_response}')
                else:
                    await ctx.send('無效的選擇，請重新執行指令')
            except asyncio.TimeoutError:
                await ctx.send('操作逾時，請重新執行指令')
        else:
            # 如果關鍵字只有一個回覆，直接刪除關鍵字
            del keyword_responses[keyword]
            save_keywords()
            await ctx.send(f'已刪除關鍵字：{keyword}')
    else:
        await ctx.send(f'找不到關鍵字：{keyword}')    
    
    
@bot.command()
async def member_add(ctx, player_name):
    server_id = str(ctx.guild.id)
    with open('players.json', 'r') as file:
        players = json.load(file)
    if server_id not in players:
        players[server_id] = []
    players[server_id].append(player_name)
    with open('players.json', 'w') as file:
        json.dump(players, file, indent=4)
    await ctx.send(f'{player_name} 已加入列表。')

@bot.command()
async def member_del(ctx, player_name):
    server_id = str(ctx.guild.id)
    with open('players.json', 'r') as file:
        players = json.load(file)
    if server_id in players and player_name in players[server_id]:
        players[server_id].remove(player_name)
        with open('players.json', 'w') as file:
            json.dump(players, file, indent=4)
        await ctx.send(f'{player_name} 已從列表中移除。')
    else:
        await ctx.send(f'{player_name} 不存在於列表中。')

@bot.command()
async def team_rank(ctx):
    server_id = str(ctx.guild.id)
    with open('players.json', 'r', encoding="utf-8") as file:
        players = json.load(file)

    if server_id not in players or len(players[server_id]) < 2:
        await ctx.send('玩家數量不足，請添加更多玩家。')
        return

    team1, team2 = get_random_teams(players[server_id])

    embed = discord.Embed(title='隊伍分配結果', color=discord.Color.blue())
    embed.add_field(name='隊伍 1', value=', '.join(team1), inline=False)
    embed.add_field(name='隊伍 2', value=', '.join(team2), inline=False)

    await ctx.send(embed=embed)

def get_random_teams(player_list):
    random.shuffle(player_list)
    half_length = len(player_list) // 2
    team1 = player_list[:half_length]
    team2 = player_list[half_length:]
    return team1, team2

@bot.command()
async def member_list(ctx):
    server_id = str(ctx.guild.id)
    with open('players.json', 'r', encoding="utf-8") as file:
        players = json.load(file)
    if server_id in players:
        embed = discord.Embed(title='玩家列表', color=discord.Color.green())
        player_list = ", ".join(players[server_id])
        embed.add_field(name='', value=player_list, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send('列表中無玩家。')
        
@bot.command()
async def del_all(ctx):
    server_id = str(ctx.guild.id)
    with open('players.json', 'r') as file:
        players = json.load(file)
    if server_id in players:
        players.pop(server_id)
        with open('players.json', 'w', encoding="utf-8") as file:
            json.dump(players, file, indent=4)
        await ctx.send('已移所有玩家。')
    else:
        await ctx.send('列表中無玩家。')
        
        
bot.run('ENTER_YOUR_BOT_TOKEN')