import time
import os
import datetime
import random
import platform

def get_cpu_temperature():
    """
    Lê a temperatura da CPU da Raspberry Pi.
    Tenta ler primeiro do sistema de arquivos e, se falhar, usa o comando vcgencmd.
    No Windows (ambiente de teste), simula uma temperatura.
    """
    # Fallback para testes no PC (Windows/Mac)
    if platform.system() == "Windows":
        # Ler a temperatura da CPU no Windows nativamente com Python é complexo
        # e geralmente requer bibliotecas extras (WMI) e permissões de administrador.
        # Portanto, geramos um valor aleatório realista para você poder testar o fluxo.
        return random.uniform(40.0, 55.0)

    try:
        # Tenta ler a temperatura do arquivo do sistema (Linux/Raspberry Pi)
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read()
        return float(temp_str) / 1000.0
    except Exception:
        try:
            # Fallback: tenta usar o comando nativo da Raspberry Pi
            # Redirecionamos os erros para evitar sujar a tela
            res = os.popen("vcgencmd measure_temp 2>/dev/null").readline()
            if res and "temp=" in res:
                return float(res.replace("temp=", "").replace("'C\n", ""))
        except Exception:
            pass
            
    return None

def main():
    print("Iniciando monitoramento de temperatura da CPU...")
    # Para testes no PC, vamos usar um intervalo de 5 segundos para ver o resultado mais rápido.
    # Quando for rodar na Raspberry Pi na versão final, mude para: 10 * 60
    intervalo_segundos = 5 
    
    print(f"O status será impresso a cada {intervalo_segundos} segundos (Modo de teste).")
    print("Pressione Ctrl+C para parar.\n")
    
    try:
        while True:
            temp = get_cpu_temperature()
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if temp is not None:
                modo = " (Simulada no PC)" if platform.system() == "Windows" else ""
                print(f"[{agora}] Status: OK | Temperatura atual: {temp:.1f} °C{modo}")
            else:
                print(f"[{agora}] Status: ERRO | Não foi possível ler a temperatura.")
                
            time.sleep(intervalo_segundos)
            
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado pelo usuário.")

if __name__ == "__main__":
    main()
