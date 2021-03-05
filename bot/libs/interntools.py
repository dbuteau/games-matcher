import os
import sys
import discord
import DiscordUtils
import logging


class interntools:

    async def paginate(
            ctx, listing, header=None,
            footer=None, remove_reaction=True, vote=False, limit=10):

        try:
            logger = logging.getLogger('discord')
            nb_elm_by_page = limit
            timeout = 300
            pages = []
            embeds = []
            for i in range(len(listing)):
                current_page, rest = divmod(i, nb_elm_by_page)
                if len(pages) <= current_page:
                    pages.insert(current_page, list())
                pages[current_page].append(str(listing[i]))
            logger.debug(f"pages: {pages}")

            i = 0
            for page in pages:
                i += 1
                nl = '\n'
                content = f"{nl}- ".join(['', *page])
                if header is None:
                    header = f"Page {i}"
                if footer is not None:
                    content += f"{nl}{footer}"
                embeds.append(
                    discord.Embed(color=ctx.author.color)
                    .add_field(name=header, value=content))
            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
                        ctx, remove_reactions=remove_reaction,
                        auto_footer=True, timeout=timeout)
            if len(pages) > 1:
                paginator.add_reaction('⏪', 'back')
                paginator.add_reaction('⏩', 'next')
            await paginator.run(embeds)
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise Exception(f'{fname}({exc_tb.tb_lineno}): {err}') from err

    async def progressbar(max_value, current_value):
        max_part = 20
        msg = ''
        for x in range(max_part):
            rest = (current_value * max_part / max_value)
            if x <= rest:
                msg += ':white_small_square:'
            else:
                msg += ':black_small_square:'
            if rest == max_part:
                msg += "\n_Completed_"
        logger = logging.getLogger('discord')
        logger.info(msg)
        return msg
