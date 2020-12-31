from const import rolesValues


async def clear_rank(client, player):
    for role in client.RankRoles:
        await player.remove_roles(client.RankRoles[role])


def get_rank(client, player):
    for role in client.RankRoles:
        if client.RankRoles[role] in player.roles:
            return client.RankRoles[role].name


def get_new_rank(player_elo):
    for rank, elo in rolesValues:
        if player_elo >= elo:
            return rank


async def set_rank(client, player, player_elo_str):
    player_elo = int(player_elo_str)
    new_rank = get_new_rank(player_elo)
    current_rank = get_rank(client, player)
    if current_rank == new_rank:
        return
    await clear_rank(client, player)
    await player.add_roles(client.RankRoles[new_rank])
