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

def get_cpu_usage():
    """
    Lê o uso da CPU (%) na Raspberry Pi lendo /proc/stat.
    No Windows (ambiente de teste), simula um valor de uso.
    """
    if platform.system() == "Windows":
        return random.uniform(5.0, 30.0)
    
    try:
        def read_cpu_times():
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            parts = [float(i) for i in line.split()[1:]]
            # idle = parts[3], iowait = parts[4]
            idle = parts[3] + parts[4]
            total = sum(parts)
            return idle, total
        
        idle1, total1 = read_cpu_times()
        time.sleep(0.5)
        idle2, total2 = read_cpu_times()
        
        delta_total = total2 - total1
        delta_idle = idle2 - idle1
        
        if delta_total > 0:
            return 100.0 * (1.0 - (delta_idle / delta_total))
        return 0.0
    except Exception:
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
            cpu_usage = get_cpu_usage()
            agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if temp is not None and cpu_usage is not None:
                modo = " (Simulado no PC)" if platform.system() == "Windows" else ""
                print(f"[{agora}] Status: OK | Temp: {temp:.1f} °C | CPU: {cpu_usage:.1f}%{modo}")
            else:
                print(f"[{agora}] Status: ERRO | Não foi possível ler as informações da CPU.")
                
            # O get_cpu_usage já espera 0.5s no Linux. Ajustamos o tempo de sleep final para manter o intervalo.
            tempo_espera = intervalo_segundos
            if platform.system() != "Windows" and cpu_usage is not None:
                tempo_espera = max(0, intervalo_segundos - 0.5)
                
            time.sleep(tempo_espera)
            
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado pelo usuário.")

if __name__ == "__main__":
    main()
