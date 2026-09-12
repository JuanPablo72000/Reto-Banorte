using System.Security.Claims;

namespace BancaAdaptativa.Api.Endpoints;

public static class ClaimsExtensions
{
    public static int GetUserId(this ClaimsPrincipal user)
    {
        var id = user.FindFirstValue(ClaimTypes.NameIdentifier)
            ?? user.FindFirstValue("sub")
            ?? throw new UnauthorizedAccessException("MISSING_SUBJECT");
        return int.Parse(id);
    }
}
