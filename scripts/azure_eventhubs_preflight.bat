@echo off
setlocal EnableExtensions

rem ============================================================
rem Azure / Event Hubs pre-flight
rem Project: azure-real-time-analytics-pipeline
rem ============================================================

set "EVENTHUB_NAMESPACE=ehns-drone-rti-dev-eus-01.servicebus.windows.net"

echo.
echo ============================================================
echo   AZURE EVENT HUBS PREFLIGHT
echo ============================================================
echo Namespace: %EVENTHUB_NAMESPACE%
echo.

where az >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Azure CLI ^(az^) no esta disponible en PATH.
    exit /b 1
)
echo [OK] Azure CLI disponible.

az account show --output none >nul 2>&1
if errorlevel 1 (
    echo [AUTH] No hay una sesion Azure utilizable.
    echo        Iniciando az login...
    echo.
    az login
    if errorlevel 1 (
        echo.
        echo [FAIL] No fue posible autenticar con Azure.
        exit /b 2
    )
) else (
    echo [OK] Sesion Azure encontrada.
)

echo [CHECK] Validando token para Azure Event Hubs...

az account get-access-token ^
    --scope "https://eventhubs.azure.net/.default" ^
    --output none >nul 2>&1

if errorlevel 1 (
    echo [AUTH] No fue posible obtener un token valido.
    echo        Renovando autenticacion con az login...
    echo.
    az login
    if errorlevel 1 (
        echo.
        echo [FAIL] La reautenticacion con Azure fallo.
        exit /b 3
    )

    az account get-access-token ^
        --scope "https://eventhubs.azure.net/.default" ^
        --output none >nul 2>&1

    if errorlevel 1 (
        echo.
        echo [FAIL] Azure autentico, pero no pudo emitir un token para Event Hubs.
        exit /b 4
    )
)

echo [OK] Token para Azure Event Hubs disponible.

echo [CHECK] Probando TCP 5671 ^(AMQP/TLS^)...

powershell.exe -NoProfile -Command ^
  "$r = Test-NetConnection -ComputerName '%EVENTHUB_NAMESPACE%' -Port 5671 -WarningAction SilentlyContinue; if ($r.TcpTestSucceeded) { exit 0 } else { exit 1 }"

if errorlevel 1 (
    echo [FAIL] No hay conectividad TCP hacia %EVENTHUB_NAMESPACE%:5671
    echo        Revisa red, VPN, proxy o firewall.
    exit /b 5
)

echo [OK] Puerto 5671 accesible.

echo [CHECK] Probando TCP 443 ^(HTTPS^)...

powershell.exe -NoProfile -Command ^
  "$r = Test-NetConnection -ComputerName '%EVENTHUB_NAMESPACE%' -Port 443 -WarningAction SilentlyContinue; if ($r.TcpTestSucceeded) { exit 0 } else { exit 1 }"

if errorlevel 1 (
    echo [FAIL] No hay conectividad TCP hacia %EVENTHUB_NAMESPACE%:443
    echo        Revisa red, VPN, proxy o firewall.
    exit /b 6
)

echo [OK] Puerto 443 accesible.

echo.
echo ============================================================
echo   PREFLIGHT OK
echo ============================================================
echo Azure CLI       : OK
echo Authentication  : OK
echo Event Hubs token: OK
echo TCP 5671        : OK
echo TCP 443         : OK
echo.
echo Ya puedes ejecutar el wrapper del simulador.
echo Ejemplo:
echo   .\scripts\run_simulation.ps1 -Config fleet250_disconnect_cloud.yaml
echo.

exit /b 0
