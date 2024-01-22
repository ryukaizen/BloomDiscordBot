import asyncio
import subprocess
import textwrap
import config.config as cfg
from typing import Dict, Any, List, Tuple
from discord.ext.commands import Bot
import discord
from shared.constants import GOVERNANCE_BUDGET_CHANNEL, GOVERNANCE_CHANNEL

proposals: List[Dict[str, Any]] = []

ongoing_votes: Dict[int, Dict[str, Any]] = {}


# prepare the draft by setting the type, channel ID, and title based on the draft type
async def prepare_draft(draft: Dict[str, Any]) -> Tuple[str, str, str]:
    draft_type = draft["type"].lower()
    if draft_type not in ["budget", "governance"]:
        raise ValueError(f"Invalid draft type: {draft_type}")

    if draft_type == "budget":
        id_type = "budget"
        channel_name = GOVERNANCE_BUDGET_CHANNEL
        cfg.current_budget_id += 1
        cfg.update_id_values(
            cfg.current_budget_id, id_type
        )  # Update the governance ID in the config file
        title = f"Bloom Budget Proposal (BBP) #{cfg.current_budget_id}: {draft['name']}"
    else:
        id_type = "governance"
        channel_name = GOVERNANCE_CHANNEL
        cfg.current_governance_id += 1
        cfg.update_id_values(
            cfg.current_governance_id, id_type
        )  # Update the governance ID in the config file
        title = f"Bloom Governance Proposal (BGP) #{cfg.current_governance_id}: {draft['name']}"

    return id_type, channel_name, title


# publish the draft by creating a thread with the prepared content and starting a vote timer
async def publish_draft(draft: Dict[str, Any], bot: Bot, guild_id: int) -> None:
    id_type, channel_name, title = await prepare_draft(draft)

    forum_channel = discord.utils.get(
        bot.get_guild(guild_id).channels, name=channel_name
    )
    if not forum_channel:
        print("Error: Channel not found.")
        return

    # Store the content in a variable
    content = textwrap.dedent(
        f"""
    **{title}**

    __**Abstract**__
    {draft["abstract"]}

    **__Background__**
    {draft["background"]}

    **👍 Yes**

    **👎 Reassess**

    **❌ Abstain**

    Vote will conclude in 48h from now.
    """
    )

    thread_with_message = await forum_channel.create_thread(name=title, content=content)

    ongoing_votes[thread_with_message.thread.id] = {
        "draft": draft,  # Store the draft info
        "yes_count": 0,  # Initialize counts
        "reassess_count": 0,
        "abstain_count": 0,
    }

    await vote_timer(
        thread_with_message.thread.id, bot, guild_id, channel_name, title, draft
    )


async def vote_timer(
    thread_id: int,
    bot: Bot,
    guild_id: int,
    channel_name: str,
    title: str,
    draft: Dict[str, Any],
) -> None:
    # Sleep until the vote ends
    await asyncio.sleep(48 * 3600)

    # Fetch the guild using the guild_id
    guild = bot.get_guild(guild_id)
    if not guild:
        print(f"Error: Guild with id {guild_id} not found.")
        return

    # Fetch the channel by name
    channel = discord.utils.get(guild.channels, name=channel_name)
    thread = channel.get_thread(thread_id)

    # Fetch the initial message in the thread using the thread ID
    message = await thread.fetch_message(thread_id)

    for reaction in message.reactions:
        if str(reaction.emoji) == "👍":
            ongoing_votes[message.id]["yes_count"] = reaction.count
        elif str(reaction.emoji) == "👎":
            ongoing_votes[message.id]["reassess_count"] = reaction.count
        elif str(reaction.emoji) == "❌":
            ongoing_votes[message.id]["abstain_count"] = reaction.count

    # Check the result and post it
    result_message = f"Vote for '{title}' has concluded:\n\n"

    if ongoing_votes[message.id]["yes_count"] >= 5:  # Set to quorum needed
        result_message += (
            "The vote passes! :tada:, snapshot proposal will now be created"
        )
        # Call the snapshot creation function
        subprocess.run(
            [
                "node",
                "./snapshot/wrapper.js",
                title,
                draft["abstract"],
                draft["background"],
                "Yes",
                "No",
                "Abstain",
            ],
            check=True,
        )
    else:
        result_message += "The vote fails. :disappointed:"

    result_message += f"\n\nYes: {ongoing_votes[message.id]['yes_count']}\nReassess: {ongoing_votes[message.id]['reassess_count']}\nAbstain: {ongoing_votes[message.id]['abstain_count']}"

    await bot.get_channel(thread_id).send(result_message)

    # Remove the vote from ongoing_votes
    del ongoing_votes[message.id]
