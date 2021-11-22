from discord.ext.commands import Converter, Context
from datetime import date, datetime


class DateConverter(Converter):

    async def convert(self, ctx: Context, argument: str) -> date:
        # Parse the date from the argument string.
        # Date is expected to be in a human readble format.
        # Example: "2020-01-01", "2020.01.01", "01.01.2020", "01-01-2020"
        try:
            return datetime.strptime(argument, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(argument, "%Y.%m.%d").date()
            except ValueError:
                try:
                    return datetime.strptime(argument, "%d.%m.%Y").date()
                except ValueError:
                    try:
                        return datetime.strptime(argument, "%d-%m-%Y").date()
                    except ValueError:
                        raise ValueError(f"Date format not recognized. Please use one of the following formats: "
                                         f"`yyyy-mm-dd`, `yyyy.mm.dd`, `dd.mm.yyyy`, `dd-mm-yyyy`")
