import discord
import DiscordUtils
import logging

class interntools:

    async def paginate(ctx, listing, header=None, footer=None, vote=False):
        nb_elm_by_page = 20
        timeout = 300
        pages = []
        embeds = []
        for i in range(len(listing)):
            current_page, rest = divmod(i, nb_elm_by_page)
            if len(pages) <= current_page:
                pages.insert(current_page, list())
            pages[current_page].append(str(listing[i]))
        logging.info(pages)

        i = 0
        for page in pages:
            i += 1
            nl = '\n'
            content = f"{nl}- ".join(['',*page])
            if header is None:
                header = f"Page {i}"
            if footer is not None:
                content += f"{nl}{footer}"
            embeds.append(discord.Embed(color=ctx.author.color).add_field(name=header, value=content))
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, remove_reactions=True, auto_footer=True, timeout=timeout)
        paginator.add_reaction('⏪', 'back')
        paginator.add_reaction('⏩', 'next')
        await paginator.run(embeds)