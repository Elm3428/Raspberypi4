"""
Monitor de Temperatura Ambiente com DHT11 - Raspberry Pi 4
===========================================================
Sensor: DHT11 (pino de dados no GPIO 4)
LED Verde: GPIO 17  (temperatura < 30°C)
LED Vermelho: GPIO 27 (temperatura >= 30°C)

Conexões:
  DHT11:
    VCC  -> 3.3V (pino 1)
    DATA -> GPIO 4 (pino 7)
    GND  -> GND (pino 6)
  LED Verde:
    Anodo (+)  -> Resistor 220Ω -> GPIO 17 (pino 11)
    Catodo (-) -> GND
  LED Vermelho:
    Anodo (+)  -> Resistor 220Ω -> GPIO 27 (pino 13)
    Catodo (-) -> GND

Dependências (executar no terminal do Raspberry Pi):
  sudo apt-get update && sudo apt-get install -y libgpiod2
  sudo pip3 install adafruit-blinka
  sudo pip3 install adafruit-circuitpython-dht
"""

import time
import board
import adafruit_dht
import RPi.GPIO as GPIO

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DOS PINOS
# ─────────────────────────────────────────────
PINO_DHT     = board.D4    # GPIO 4  - dados do DHT11
PINO_LED_VERDE    = 17     # GPIO 17 - LED verde
PINO_LED_VERMELHO = 27     # GPIO 27 - LED vermelho

LIMITE_TEMPERATURA = 30.0  # graus Celsius
INTERVALO_LEITURA  = 2     # segundos entre leituras

# ─────────────────────────────────────────────
#  INICIALIZAÇÃO
# ─────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PINO_LED_VERDE, GPIO.OUT)
GPIO.setup(PINO_LED_VERMELHO, GPIO.OUT)

# Inicia com ambos os LEDs apagados
GPIO.output(PINO_LED_VERDE, GPIO.LOW)
GPIO.output(PINO_LED_VERMELHO, GPIO.LOW)

# Inicializa o sensor DHT11
sensor = adafruit_dht.DHT11(PINO_DHT)


def exibir_cabecalho():
    """Exibe o cabeçalho do monitor no terminal."""
    print("=" * 50)
    print("  MONITOR DE TEMPERATURA AMBIENTE - DHT11")
    print("  Raspberry Pi 4")
    print(f"  Limite: {LIMITE_TEMPERATURA}°C")
    print("=" * 50)
    print(f"{'Hora':<12} {'Temp (°C)':<12} {'Umid (%)':<12} {'Status'}")
    print("-" * 50)


def atualizar_leds(temperatura):
    """
    Controla os LEDs com base na temperatura:
      - Abaixo de 30°C  → LED verde LIGADO, vermelho DESLIGADO
      - 30°C ou acima   → LED verde DESLIGADO, vermelho LIGADO
    """
    if temperatura < LIMITE_TEMPERATURA:
        GPIO.output(PINO_LED_VERDE, GPIO.HIGH)
        GPIO.output(PINO_LED_VERMELHO, GPIO.LOW)
        return "🟢 NORMAL"
    else:
        GPIO.output(PINO_LED_VERDE, GPIO.LOW)
        GPIO.output(PINO_LED_VERMELHO, GPIO.HIGH)
        return "🔴 ALERTA!"


def main():
    """Loop principal de monitoramento."""
    exibir_cabecalho()

    try:
        while True:
            try:
                temperatura = sensor.temperature
                umidade = sensor.humidity

                if temperatura is not None and umidade is not None:
                    status = atualizar_leds(temperatura)
                    hora_atual = time.strftime("%H:%M:%S")
                    print(f"{hora_atual:<12} {temperatura:<12.1f} {umidade:<12.1f} {status}")
                else:
                    print(f"{time.strftime('%H:%M:%S'):<12} {'---':<12} {'---':<12} Leitura inválida")

            except RuntimeError as erro:
                # O DHT11 pode falhar ocasionalmente, isso é normal
                print(f"{time.strftime('%H:%M:%S'):<12} Erro na leitura: {erro}")

            time.sleep(INTERVALO_LEITURA)

    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("  Monitoramento encerrado pelo usuário.")
        print("=" * 50)

    finally:
        # Desliga os LEDs e limpa os GPIOs
        GPIO.output(PINO_LED_VERDE, GPIO.LOW)
        GPIO.output(PINO_LED_VERMELHO, GPIO.LOW)
        GPIO.cleanup()
        sensor.exit()
        print("  GPIOs liberados. Até logo!")


if __name__ == "__main__":
    main()
