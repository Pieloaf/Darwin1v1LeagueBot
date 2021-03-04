from discord.ext import commands
from mysql_params import *
from const import INIT_ELO
from Ranks import set_rank
import pymysql.cursors
from datetime import datetime


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

    async def wins(self, user_id, new_elo, revert=False):
        toUpdate = "`streak` + 1, `victory` = `victory` + 1, `elo` = "
        if revert==True:
            streak = await self.streak_count(user_id)
            toUpdate = f"{streak}, `defeat` = `defeat` - 1, `elo` = `elo` + "
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `streak` = {} %s WHERE `user_id`=%s".format(toUpdate)
                cursor.execute(sql, (new_elo, user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log("Error Updating user wins:", e)
            return False
        return True

    async def lose(self, user_id, new_elo, revert=False):
        toUpdate = "0, `defeat` = `defeat` + 1, `elo` = "
        if revert==True:
            streak = await self.streak_count(user_id)
            if streak != 0:
                streak -= 1
            toUpdate = f" {streak} , `victory` = `victory` - 1, `elo` = `elo` - "
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `streak` = {} %s WHERE `user_id`=%s".format(toUpdate)
                cursor.execute(sql, (new_elo, user_id))
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
                await self.client.log("Updated User: ", user_name)
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

    async def get_game(self, game_id):
        try:
            with self.client.db.cursor() as cursor:
                sql = "SELECT * FROM `games` WHERE `game_id`=%s"
                cursor.execute(sql, (game_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result
        except Exception as e:
            await self.client.log("Error looking up game_id {}.\n{}".format(user_id, e))
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
            await member.add_roles(self.client.usefulRoles['Unranked'])
        elif (str(member.avatar_url) != user['avatar_url']) or (member.name != user['user_name']):
            await self.update_player(member.id, str(member.avatar_url), member.name)
            
    async def add_all_user_to_db(self):
        for member in self.client.get_all_members():
            if not member.bot:
                user = await self.get_user(member.id)
                if not user:
                    await self.add_user_to_db(member)
                elif (str(member.avatar_url) != user['avatar_url']) or (member.name != user['user_name']):
                    await self.update_player(member.id, str(member.avatar_url), member.name)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if (before.avatar_url != after.avatar_url) or (before.name != after.name):
            await self.update_player(after.id, str(after.avatar_url), after.name)

    async def get_user_rank(self, user_id, platform=None, region=None):
        regionSelect = ''
        if platform != None and region != None:
            regionSelect =  f"where platform = '{platform}' and region = '{region}'"
        try:
            with self.client.db.cursor() as cursor:
                sql = f"select rank from (select @r:=@r+1 as rank, user_name, user_id from players,(select @r:=0) as r {regionSelect} order by (victory+defeat >=10) desc, elo desc) as card where user_id = {user_id}"
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    return None
                else:
                    return result
        except Exception as e:
            await self.client.log("Error looking up user_id {}.\n{}".format(user_id, e))
        return None

    async def add_game_to_db(self, game, winner, loser, gained, lost):
        try:
            with self.client.db.cursor() as cursor:
                sql = "insert into games(game_id,timestamp,winner,loser,elo_gain,elo_loss)" +\
                    " values(%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (game, datetime.now(), winner.id, loser.id, gained, lost))
            self.client.db.commit()
            await self.client.log("Recorded game: " + str(game)+f"\n{winner.name} beats {loser.name}")
        except Exception as e:
            await self.client.log("Error adding game:", e)
        
    async def game_count(self, winner, loser):
        try:
            with self.client.db.cursor() as cursor:
                sql = "select count(*) from games where ((winner = %s and loser = %s) or (winner = %s and loser = %s)) and  ( timestamp > DATE_ADD(%s, INTERVAL -1 DAY));"
                cursor.execute(sql, (winner, loser, loser, winner, datetime.now()))
                result = cursor.fetchone()['count(*)']
                return int(result)
        except Exception as e:
            await self.client.log(e)

    async def sus_games(self, user):
        try:
            with self.client.db.cursor() as cursor:
                sql = "select count(*) from games where (winner = %s or loser = %s) and  ( timestamp > DATE_ADD(%s, INTERVAL -4 MINUTE));"
                cursor.execute(sql, (user, user, datetime.now()))
                result = cursor.fetchone()['count(*)']
                return result
        except Exception as e:
            await self.client.log(e)
        
    async def streak_count(self, user):
        try:
            streak = 0
            with self.client.db.cursor() as cursor:
                sql = f"select * from games where (winner = {user} or loser = {user}) order by id desc"
                cursor.execute(sql)
                result = cursor.fetchall()
                for game in result:
                    if game['winner'] == user:
                        streak +=1
                    else:
                        break
                return streak
        except Exception as e:
            await self.client.log(e)

    async def delete_game(self, game):
        try:
            with self.client.db.cursor() as cursor:
                sql = "delete from games where game_id = %s"
                cursor.execute(sql, (game))
                self.client.db.commit()
        except Exception as e:
            await self.client.log(e)
    
    async def get_qual(self, platform, region):
        try:
            with self.client.db.cursor() as cursor:
                sql = "select user_name from (SELECT user_name, elo FROM `players` WHERE platform=%s and region=%s and (victory+defeat >=10) order by elo desc limit 8) as boop"
                cursor.execute(sql, (platform, region))
                result = cursor.fetchall()
                if not result:
                    return None
                else:
                    return result
        except Exception as e:
            await self.client.log("Error:\n{}".format(e))
        return None

    async def update_max_streak(self, user_id):
        try:
            with self.client.db.cursor() as cursor:
                sql = "UPDATE `players` SET `max_streak` = `streak` WHERE user_id = %s"
                cursor.execute(sql, (user_id))
                self.client.db.commit()
        except Exception as e:
            await self.client.log(e)
        return

    async def games_to_revert(self, user_id, limit=0):
        toLim = f'limit {limit}'
        if limit == 0:
            toLim = ''
        try:
            with self.client.db.cursor() as cursor:
                sql = "Select game_id, id from `games` where winner = %s or loser = %s order by id desc {}".format(toLim)
                cursor.execute(sql, (user_id, user_id))
                result = cursor.fetchall()
                if not result:
                    return None
                else:
                    return result
        except Exception as e:
            await self.client.log("Error:\n{}".format(e))
        return None

def setup(client):
    client.add_cog(DBCog(client))
