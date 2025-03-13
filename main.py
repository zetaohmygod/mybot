import os
import nextcord, json, requests, re, certifi
from myserver import server_on

os.system("title Flexzy Bot - Auto Topup")

bot, config = commands.Bot(command_prefix='flexzy!', help_command=None, intents=nextcord.Intents.all()), json.load(open('./config.json', 'r', encoding='utf-8'))

class BuyModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__('กรอกลิ้งค์อั่งเปาของท่าน')
        self.a = nextcord.ui.TextInput(
            label='Truemoney Wallet Angpao',
            placeholder='https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.add_item(self.a)

    async def callback(self, interaction: nextcord.Interaction):
        link = str(self.a.value).replace(' ', '')
        if re.match(r'https:\/\/gift\.truemoney\.com\/campaign\/\?v=[a-zA-Z0-9]{18}', link):
            print(f'URL {link} DISCORD-ID {interaction.user.id}')
            url = f"https://ro-exec.live/flexzy_tw.php?phone={config['phone']}&link={link}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                print(f"Request failed: {e}")
                embed = nextcord.Embed(description='เกิดข้อผิดพลาดในการเชื่อมต่อ', color=nextcord.Color.from_rgb(255, 0, 0))
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            except ValueError:
                print("Failed to decode JSON response")
                embed = nextcord.Embed(description='เกิดข้อผิดพลาดในการประมวลผลข้อมูล', color=nextcord.Color.from_rgb(255, 0, 0))
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if data.get('status') == 'SUCCESS':
                amount = int(float(data.get('amount', 0)))
                embed = None
                for roleData in config['roleSettings']:
                    if amount == roleData['price']:
                        role = nextcord.utils.get(interaction.user.guild.roles, id=int(roleData['roleId']))
                        if role in interaction.user.roles:
                            embed = nextcord.Embed(description='ไม่สามารถซื้อได้คุณมียศอยู่แล้ว', color=nextcord.Color.from_rgb(255, 0, 0))
                        else:
                            await interaction.user.add_roles(role)
                            embed = nextcord.Embed(description='เติมเงินสำเร็จ', color=nextcord.Color.from_rgb(0, 255, 0))

                        user_avatar_url = interaction.user.avatar.url if interaction.user.avatar else None
                        log_embed = nextcord.Embed(
                            title=f'🧧 **ประวัติการซื้อยศ [ซองอั่งเปา]** 🧧',
                            description=f'👤`ผู้ใช้` : <@{interaction.user.id}>\n💰`ราคา` : `{amount}` บาท\n🎁`ได้รับยศ` : <@&{roleData["roleId"]}>',
                            color=nextcord.Color.from_rgb(0, 255, 0)
                        )
                        if user_avatar_url:
                            log_embed.set_thumbnail(url=user_avatar_url)

                        guild_icon_url = interaction.guild.icon.url if interaction.guild.icon else None
                        log_embed.set_footer(text=interaction.guild.name, icon_url=guild_icon_url)
                        await bot.get_channel(int(config['channelLog'])).send(embed=log_embed)
                        break
                
                if embed is None:
                    embed = nextcord.Embed(description='จำนวนเงินผิดพลาด', color=nextcord.Color.from_rgb(255, 0, 0))
            elif data.get('status') == 'FAIL':
                x_reason = data.get('reason')
                if x_reason is None:
                    print("Error: 'reason' not found in data")
                    embed = nextcord.Embed(description='ไม่สามารถดึงค่า reason ได้ !', color=nextcord.Color.from_rgb(255, 0, 0))
                else:
                    if (x_reason == "VOUCHER_OUT_OF_STOCK"):
                        embed = nextcord.Embed(description=f'เติมเงินไม่สำเร็จ: ซองถูกใช้ไปแล้วค้าบ !', color=nextcord.Color.from_rgb(255, 0, 0))
                    else:
                        reason = data.get('reason', 'Unknown error')
                        print(f"Redemption failed. Reason: {reason}\n")
                        embed = nextcord.Embed(description=f'เติมเงินไม่สำเร็จ: {reason}', color=nextcord.Color.from_rgb(255, 0, 0))


            else:
                print("Unexpected response status")
                embed = nextcord.Embed(description='ต้องมีอะไรผิดพลาดตรงไหนนนนนนนนนนนนน', color=nextcord.Color.from_rgb(255, 0, 0))
        else:
            embed = nextcord.Embed(description='เติมเงินไม่สำเร็จ : ลิ้งค์รับเงินแล้ว/ลิ้งค์ผิด', color=nextcord.Color.from_rgb(255, 0, 0))
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except nextcord.errors.NotFound:
            print("Interaction expired or unknown.")

class BuyView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.link_button = nextcord.ui.Button(style=nextcord.ButtonStyle.link, label="จ้างทำบอท", url='https://discord.gg/gY2EU3BSCF') 
        self.add_item(self.link_button)

    @nextcord.ui.button(label='[🧧] เติมเงิน', custom_id='buyRole', style=nextcord.ButtonStyle.blurple)
    async def buyRole(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(BuyModal())

    @nextcord.ui.button(label='[🛒] ราคายศทั้งหมด', custom_id='priceRole', style=nextcord.ButtonStyle.blurple)
    async def priceRole(self, button: nextcord.Button, interaction: nextcord.Interaction):
        description = ''
        for roleData in config['roleSettings']:
            description += f'เติมเงิน {roleData["price"]} บาท จะได้รับยศ\n𓆩⟡𓆪  <@&{roleData["roleId"]}>\n₊✧──────✧₊∘\n'
        embed = nextcord.Embed(
            title='ราคายศทั้งหมด',
            color=nextcord.Color.from_rgb(93, 176, 242),
            description=description
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    os.system("cls")
    print(f"LOGIN AS: {bot.user}")
    print("Command : /setup\n")
    bot.add_view(BuyView())

@bot.slash_command(name='setup', description='setup')
async def setup(interaction: nextcord.Interaction):
    if (int(interaction.user.id) == int(config['ownerId'])):
        await interaction.channel.send(embed=nextcord.Embed(
            title='**【⭐】TOPUP TRUEWALLET**',
            description='ซื้อยศอัตโนมัติ 24ชั่วโมง\n・กดปุ่ม "เติมเงิน" เพื่อซื้อยศ\n・กดปุ่ม "ราคายศ" เพื่อดูราคายศ',
            color=nextcord.Color.from_rgb(100, 220, 255),
        ).set_thumbnail(url='https://cdn.discordapp.com/attachments/1315974327186751519/1349786575856336950/standard_10.gif?ex=67d45e35&is=67d30cb5&hm=c60dffcb43d1645c6cdc1ebf7661994bb2975c145f88d30572b4696544dabe2a&')
        .set_image(url='https://cdn.discordapp.com/attachments/1349781395366477989/1349800096744865803/standard_8.gif?ex=67d46acd&is=67d3194d&hm=0a9c5f15ca832df60c9deae4f7eed4fb31ebc8d218c601623e3d070eb2ef4b7a&'), view=BuyView())
        await interaction.response.send_message(
            'Successfully reloaded application [/] commands.', ephemeral=True)
    else:
        await interaction.response.send_message(
           'มึงไม่ได้เป็น Owner ไอควาย ใช้ไม่ได้', ephemeral=True)
        
server_on()

bot.run(os.getenv['token'])