from discord.ext import commands
from mysql_params import *
from const import INIT_ELO
from Ranks import set_rank
import pymysql.cursors


class DBCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    def connect_to_db():
        return pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS,
            db=DB_NAME, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
        )

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.client.db = self.connect_to_db()
            await self.client.log("Database connected")
            await self.add_all_user_to_db()
        except Exception as e:
            await self.client.log(e)

    @commands.Cog.listener()
    async def on_connect(self):
        if self.client.db or not self.client.is_ready():
            return
        try:
            self.client.db = self.connect_to_db()
            await self.client.log("Database connected")
            await self.add_all_user_to_db()
        except Exception as e:
            await self.client.log(e)

    async def reconnect(self):
        try:
            self.client.db = self.connect_to_db()
            await self.client.log("Database connected")
            await self.add_all_user_to_db()
        except Exception as e:
            await self.client.log(e)

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            if self.client.db:
                self.client.db.close()
                self.client.db = None
            await self.reconnect()
        except Exception as e:
            await self.client.log(e)

    async def remove_region_platform(self, region_or_platform, user_id, value):
        try:
            with self.client.db.cursor() as cursor:
                sql = "SELECT %s FROM `players` WHERE `user_id`=%s"
                cursor.execute(sql, (region_or_platform, user_id))
                result = cursor.fetchone()
                if result[region_or_platform] != value:
                    return
                sql = "UPDATE `players` SET %s='' WHERE `user_id`=%s"
                cursor.execute(sql, (region_or_platform, user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log("Error removing user {}:".format(region_or_platform), e)
        return

    async def set_region_platform(self, region_or_platform, user_id, value):
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `{}`='{}' WHERE `user_id`=%s".format(region_or_platform, value)
                cursor.execute(sql, (user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log("Error setting user {}:".format(region_or_platform), e)
        return

    async def wins(self, user_id, new_elo, fix=False):
        toUpdate = "`victory` = `victory` + 1,"
        if fix=True:
            toUpdate += "`defeat` = `defeat` - 1,"
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `streak` = `streak` + 1, %s `elo` = %s WHERE `user_id`=%s"
                cursor.execute(sql, (toUpdate, new_elo, user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log("Error Updating user wins:", e)
            return False
        return True

    async def lose(self, user_id, new_elo, fix=False):
        toUpdate = "`defeat` = `defeat` + 1,"
        if fix=True:
            toUpdate += " `victory` = `victory` - 1,"
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `streak` = 0, %s `elo` = %s WHERE `user_id`=%s"
                cursor.execute(sql, (toUpdate, new_elo, user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log("Error Updating user lose:", e)
            return False
        return True

    async def update_player(self, user_id, avatar_url, user_name):
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `avatar_url` = %s, `user_name` = %s WHERE `user_id`=%s"
                cursor.execute(sql, (avatar_url, user_name, user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log("Error Updating user:", e)
        return None

    async def get_user(self, user_id):
        try:
            with self.client.db.cursor() as cursor:
                sql = "SELECT * FROM `players` WHERE `user_id`=%s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result
        except Exception as e:
            await self.client.log("Error looking up user_id {}.\n{}".format(user_id, e))
        return None

    async def add_user_to_db(self, member):
        try:
            with self.client.db.cursor() as cursor:
                sql = "INSERT INTO `players` (`user_id`, `user_name`, `first_seen`, `avatar_url`, `elo`)" +\
                    " VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (member.id, member.display_name, member.joined_at, str(member.avatar_url), INIT_ELO))
            self.client.db.commit()
            await self.client.log("Added user: " + member.display_name)
            return await self.get_user(member.id)
        except Exception as e:
            await self.client.log("Error adding user:", e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user = await self.get_user(member.id)
        if not user:
            await self.add_user_to_db(member)
            await member.add_roles(self.client.RankRoles['Inmate'])
        else:
            await set_rank(self.client, member, user['elo'])

    async def add_all_user_to_db(self):
        for member in self.client.get_all_members():
            if not member.bot:
                user = await self.get_user(member.id)
                if not user:
                    await self.add_user_to_db(member)
                else:
                    await self.update_player(member.id, user['avatar_url'], user['user_name'])

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if (before.avatar_url != after.avatar_url) or (before.display_name != after.display_name):
            await self.update_player(after.id, str(after.avatar_url), after.display_name)

    async def get_user_rank(self, platform, user_id):
        try:
            with self.client.db.cursor() as cursor:
                var = 'user_name,avatar_url,platform,region,elo,victory,defeat,streak'
                sql = "select rank from (select @r:=@r+1 as rank, user_name, user_id from players,(select @r:=0) as r where platform = %s order by (victory+defeat >=10) desc, elo desc) as card where user_id = %s"
                cursor.execute(sql, (platform, int(user_id)))
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result
        except Exception as e:
            await self.client.log("Error looking up user_id {}.\n{}".format(user_id, e))
        return None

def setup(client):
    client.add_cog(DBCog(client))
