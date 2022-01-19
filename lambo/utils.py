from datetime import date, datetime
from discord import Guild, Role


from discord.ext.commands import Context, Converter, RoleConverter, RoleNotFound


class FuzzyRoleConverter(RoleConverter):
    async def convert(self, ctx: Context, argument: str) -> Role:
        try:
            role = await super().convert(ctx, argument)
            return role
        except RoleNotFound as e:
            guild: Guild = ctx.guild  # type: ignore
            if guild == None:
                raise e
            matching_roles = [
                role
                for role in guild._roles.values()
                if argument.lower() in role.name.lower()
            ]
            if len(matching_roles) == 0:
                raise e
            return matching_roles[0]


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
                        raise ValueError(
                            f"Date format not recognized. Please use one of the following formats: "
                            f"`yyyy-mm-dd`, `yyyy.mm.dd`, `dd.mm.yyyy`, `dd-mm-yyyy`"
                        )
