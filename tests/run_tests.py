import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Ejecutando: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print(f"✅ {description} - EXITOSO")
    else:
        print(f"❌ {description} - FALLÓ")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Ejecutar tests del servicio de clientes"
    )

    parser.add_argument(
        "--mode",
        choices=["quick", "full", "coverage",
                 "unit", "integration", "verbose"],
        default="quick",
        help="Modo de ejecución de tests"
    )

    parser.add_argument(
        "--file",
        help="Archivo específico de test a ejecutar"
    )

    parser.add_argument(
        "--function",
        help="Función específica de test a ejecutar"
    )

    args = parser.parse_args()

    try:
        subprocess.run(["pytest", "--version"],
                       capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest no está instalado. Ejecuta: pip install -r requirements-test.txt")
        sys.exit(1)

    success = True

    if args.mode == "quick":
        cmd = ["pytest", "-v", "--tb=short"]
        if args.file:
            cmd.append(args.file)
        if args.function:
            cmd.extend(["-k", args.function])
        success = run_command(cmd, "Tests Rápidos")

    elif args.mode == "full":
        cmd = [
            "pytest",
            "-v",
            "--cov=app.services.client_service",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ]
        success = run_command(cmd, "Tests Completos con Cobertura")

    elif args.mode == "coverage":
        cmd = [
            "pytest",
            "--cov=app.services.client_service",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=80"
        ]
        success = run_command(cmd, "Análisis de Cobertura")

        if success:
            print("\n📊 Reporte HTML de cobertura disponible en: htmlcov/index.html")

    elif args.mode == "unit":
        cmd = ["pytest", "-v", "-m", "not integration"]
        success = run_command(cmd, "Tests Unitarios")

    elif args.mode == "integration":
        cmd = ["pytest", "-v", "-m", "integration"]
        success = run_command(cmd, "Tests de Integración")

    elif args.mode == "verbose":
        cmd = ["pytest", "-vv", "-s", "--tb=long"]
        success = run_command(cmd, "Tests Detallados")

    if success and args.mode in ["full", "coverage"]:
        print(f"\n{'='*60}")
        print("📋 COMANDOS ÚTILES ADICIONALES:")
        print("="*60)
        print("• Ver cobertura HTML: open htmlcov/index.html")
        print("• Tests específicos: pytest -k 'test_create_client'")
        print("• Tests por clase: pytest -k 'TestCreateClient'")
        print("• Tests con pdb: pytest --pdb")
        print("• Tests paralelos: pytest -n auto (requiere pytest-xdist)")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
