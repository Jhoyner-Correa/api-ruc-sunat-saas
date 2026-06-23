# test_api.py
import sys
from sunat_service import consultar_ruc, SunatNotFoundError, SunatBlockedError, SunatConnectionError

def run_test(ruc):
    print(f"\n==================================================")
    print(f"Probando consulta para RUC: {ruc}")
    print(f"==================================================")
    try:
        data, source = consultar_ruc(ruc, bypass_cache=True)
        print(f"Resultado obtenido de fuente: {source}")
        print(f"Razón Social: {data['razonSocial']}")
        print(f"Tipo Contribuyente: {data['tipoContribuyente']}")
        print(f"Estado: {data['estado']}")
        print(f"Condición: {data['condicion']}")
        print(f"Dirección Fiscal: {data['direccionFiscal']}")
        print(f"Fecha Inscripción: {data['fechaInscripcion']}")
        print(f"Inicio Actividades: {data['fechaInicioActividades']}")
        print(f"Actividades Económicas: {data['actividadesEconomicas']}")
        print(f"Sistema Emisión: {data['sistemaEmision']}")
        print(f"Sistema Contabilidad: {data['sistemaContabilidad']}")
        print(f"Representantes Legales (Total): {len(data['representantesLegales'])}")
        if data['representantesLegales']:
            print(f"  Primer Rep: {data['representantesLegales'][0]}")
        print(f"Locales Anexos (Total): {len(data['anexos'])}")
        if data['anexos']:
            print(f"  Primer Anexo: {data['anexos'][0]}")
    except ValueError as e:
        print(f"ERROR DE VALIDACIÓN: {e}")
    except SunatNotFoundError as e:
        print(f"ERROR: RUC no encontrado: {e}")
    except SunatBlockedError as e:
        print(f"ERROR: Bloqueado por CAPTCHA o IP: {e}")
    except SunatConnectionError as e:
        print(f"ERROR DE CONEXIÓN: {e}")
    except Exception as e:
        print(f"ERROR INESPERADO: {e}")

if __name__ == "__main__":
    # RUC de SUNAT (Válido)
    run_test("20131312955")
    
    # RUC Inexistente
    run_test("20000000001")
    
    # RUC Inválido en formato
    run_test("12345")
