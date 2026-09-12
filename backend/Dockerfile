# Imagen de producción para BancaAdaptativa.Api (.NET 10 Minimal API).
# El seed de datos demo corre automáticamente al arrancar (Migrate() + DbSeeder).
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY src/BancaAdaptativa.Api/BancaAdaptativa.Api.csproj src/BancaAdaptativa.Api/
RUN dotnet restore src/BancaAdaptativa.Api/BancaAdaptativa.Api.csproj
COPY src/BancaAdaptativa.Api/ src/BancaAdaptativa.Api/
RUN dotnet publish src/BancaAdaptativa.Api/BancaAdaptativa.Api.csproj -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://+:8000
EXPOSE 8000
ENTRYPOINT ["dotnet", "BancaAdaptativa.Api.dll"]
