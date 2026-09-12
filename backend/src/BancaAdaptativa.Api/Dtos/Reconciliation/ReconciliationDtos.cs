namespace BancaAdaptativa.Api.Dtos.Reconciliation;

public record ReconciliationResponse(
    int IdMatch, int IdTransfer, int IdTransaction,
    string Status, float MatchScore, DateTime? MatchedAt, string Notes);
