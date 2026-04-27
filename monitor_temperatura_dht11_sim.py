"""
SIMULACAO - Monitor de Temperatura Ambiente com DHT11
=====================================================
Versao simulada para rodar em qualquer PC (sem hardware).
Gera temperaturas aleatorias para testar a logica do monitor.

Sensor simulado: DHT11 (GPIO 4)
LED Verde simulado: GPIO 17  (temperatura < 30C)
LED Vermelho simulado: GPIO 27 (temperatura >= 30C)
"""

import sys
import io
import time
import random
import os
import argparse

# Forcar saida UTF-8 no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# -----------------------------------------------
#  CONFIGURACAO
# -----------------------------------------------
PINO_LED_VERDE    = 17     # GPIO 17 - LED verde (simulado)
PINO_LED_VERMELHO = 27     # GPIO 27 - LED vermelho (simulado)

LIMITE_TEMPERATURA = 30.0  # graus Celsius
INTERVALO_LEITURA  = 2     # segundos entre leituras

# Estado simulado dos LEDs
leds = {
    PINO_LED_VERDE: False,
    PINO_LED_VERMELHO: False,
}


def limpar_tela():
    """Limpa o terminal."""
    if sys.stdout.isatty():
        os.system('cls' if os.name == 'nt' else 'clear')


def exibir_cabecalho():
    """Exibe o cabecalho do monitor no terminal."""
    print("=" * 62)
    print("  [TEMP]  MONITOR DE TEMPERATURA AMBIENTE - DHT11 (SIMULACAO)")
    print("  [RPI4]  Raspberry Pi 4 -- Modo Simulado")
    print(f"  [ALRT]  Limite de alerta: {LIMITE_TEMPERATURA} C")
    print("=" * 62)
    print()
    print(f"  {'#':<5} {'Hora':<12} {'Temp (C)':<12} {'Umid (%)':<12} {'LED Verde':<12} {'LED Verm.':<12} {'Status'}")
    print("  " + "-" * 70)


def simular_leitura_dht11():
    """
    Simula a leitura do sensor DHT11.
    Gera temperaturas entre 20C e 38C com variacao realista.
    Umidade entre 30% e 80%.
    Ocasionalmente retorna None para simular falhas de leitura.
    """
    # ~5% de chance de falha na leitura (como o sensor real)
    if random.random() < 0.05:
        return None, None

    temperatura = round(random.uniform(20.0, 38.0), 1)
    umidade = round(random.uniform(30.0, 80.0), 1)
    return temperatura, umidade


def atualizar_leds(temperatura):
    """
    Controla os LEDs simulados com base na temperatura:
      - Abaixo de 30C  -> LED verde LIGADO, vermelho DESLIGADO
      - 30C ou acima   -> LED verde DESLIGADO, vermelho LIGADO
    """
    if temperatura < LIMITE_TEMPERATURA:
        leds[PINO_LED_VERDE] = True
        leds[PINO_LED_VERMELHO] = False
        return "[OK] NORMAL"
    else:
        leds[PINO_LED_VERDE] = False
        leds[PINO_LED_VERMELHO] = True
        return "[!!] ALERTA!"


def main(max_leituras=0):
    """Loop principal de monitoramento simulado."""
    limpar_tela()
    exibir_cabecalho()

    leitura_num = 0

    try:
        while True:
            leitura_num += 1
            if max_leituras > 0 and leitura_num > max_leituras:
                break
            try:
                temperatura, umidade = simular_leitura_dht11()
                hora_atual = time.strftime("%H:%M:%S")

                if temperatura is not None and umidade is not None:
                    status = atualizar_leds(temperatura)
                    led_v = "ON " if leds[PINO_LED_VERDE] else "OFF"
                    led_r = "ON " if leds[PINO_LED_VERMELHO] else "OFF"
                    print(f"  {leitura_num:<5} {hora_atual:<12} {temperatura:<12.1f} {umidade:<12.1f} {led_v:<12} {led_r:<12} {status}")
                else:
                    print(f"  {leitura_num:<5} {hora_atual:<12} {'---':<12} {'---':<12} {'---':<12} {'---':<12} [??] Leitura invalida")

            except Exception as erro:
                print(f"  {leitura_num:<5} {time.strftime('%H:%M:%S'):<12} Erro na leitura: {erro}")

            time.sleep(INTERVALO_LEITURA)

    except KeyboardInterrupt:
        print()
        print()
        print("  " + "=" * 70)
        print("  [STOP]  Monitoramento encerrado pelo usuario.")
        print(f"  [INFO]  Total de leituras realizadas: {leitura_num}")
        print("  " + "=" * 70)

    finally:
        # Simula limpeza dos GPIOs
        leds[PINO_LED_VERDE] = False
        leds[PINO_LED_VERMELHO] = False
        print("  [GPIO]  GPIOs liberados (simulacao). Ate logo!")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', type=int, default=0, help='Numero de leituras para demo (0=infinito)')
    args = parser.parse_args()
    main(max_leituras=args.demo)
