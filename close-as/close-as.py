import discord
from datetime import datetime
from discord.ext import commands

from core.time import UserFriendlyTime, human_timedelta
from core.models import PermissionLevel
from core import checks


class CloseAs:
    """
    Closes a ticket on behalf of someone else.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ohnojinnieclosedaticket"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    async def closeas, ctx, user: discord.User, *, after: UserFriendlyTime = None):
        """
        Close the thread on the behalf of another user.

        **Usage:**
        [p]asc <user> <regular options that you pass into the close command>

        **Examples:**
        [p]close-as 1234567890123456789 Closed due to no response after 24 hours.
        [p]close-as @xChris_vC#1234 in 24 hours
        """
        thread = ctx.thread

        now = datetime.utcnow()

        close_after = (after.dt - now).total_seconds() if after else 0
        message = after.arg if after else None
        silent = str(message).lower() in {"silent", "silently"}
        cancel = str(message).lower() == "cancel"

        if cancel:

            if thread.close_task is not None or thread.auto_close_task is not None:
                await thread.cancel_closure(all=True)
                embed = discord.Embed(
                    color=self.bot.error_color,
                    description="Scheduled close has been cancelled.",
                )
            else:
                embed = discord.Embed(
                    color=self.bot.error_color,
                    description="This thread has not already been scheduled to close.",
                )

            return await ctx.send(embed=embed)

        if after and after.dt > now:
            await self.send_scheduled_close_message(ctx, after, silent)

        dupe_message = ctx.message
        dupe_message.content = f"The thread close command was invoked by {ctx.author.name}#{ctx.author.discriminator}"

        await thread.note(dupe_message)

        await thread.close(
            closer=user, after=close_after, message=message, silent=silent
        )

    async def send_scheduled_close_message(self, ctx, after, silent=False):
        human_delta = human_timedelta(after.dt)

        silent = "*silently* " if silent else ""

        embed = discord.Embed(
            title="Scheduled close",
            description=f"This thread will close {silent} in {human_delta}.",
            color=self.bot.error_color,
        )

        if after.arg and not silent:
            embed.add_field(name="Message", value=after.arg)

        embed.set_footer(
            text="Closing will be cancelled " "if a thread message is sent."
        )
        embed.timestamp = after.dt

        await ctx.send(embed=embed)

    async def handle_log(self, guild: discord.Guild, ctx, user):
        channel = discord.utils.find(lambda c: "cba-logs" in c.topic, guild.channels)
        if channel is None:
            return
        else:
            embed = discord.Embed(
                color=self.bot.main_color
            )
            embed.description = f"Thread closed by {ctx.author.name}#{ctx.author.discriminator} on the behalf of {user.username}#{user.discriminator} "

            await channel.send(embed)


def setup(bot):
    bot.add_cog(CloseAs(bot))
