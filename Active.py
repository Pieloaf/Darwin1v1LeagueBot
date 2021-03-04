import asyncio
import discord

class Active:
    def __init__(self, user, client):
        self.client = client
        self.user = user
        self.task = None

    def __repr__(self):
        return repr(self.user.id)

    def __eq__(self, other):
        return self.user.id == other.user.id
        
    async def start(self):
        await self.user.add_roles(self.client.usefulRoles['Active'])
        self.task = self.client.loop.create_task(self.call_this_in(self.clear, (), 1200))    

    async def clear(self):
        self.client.Active.remove(self)
        await self.user.remove_roles(self.client.usefulRoles['Active'])

    async def update(self):
        self.task.cancel()
        self.task = self.client.loop.create_task(self.call_this_in(self.clear, (), 1200))

    @staticmethod
    async def call_this_in(func, args, time):
        await asyncio.sleep(time)
        if args:
            return await func(args)
        return await func()