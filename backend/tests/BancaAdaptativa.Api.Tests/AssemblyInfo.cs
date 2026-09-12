using Xunit;

// Sin paralelismo: AuthServiceTests manipula la env var JWT_KEY (estado global del
// proceso) y las factories de integración la leen al construir el host.
// La suite es pequeña (~1 min en serie) y así Stryker también es determinista.
[assembly: CollectionBehavior(DisableTestParallelization = true)]
