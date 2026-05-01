#!/usr/bin/env python3
# ============================================================
#  Controle de LEDs com Sensor Ultrassônico HC-SR04
#  Plataforma: Raspberry Pi 4
# ============================================================
#
#  CONEXÕES:
#  ─────────────────────────────────────────────────
#   Componente       │  Pino GPIO (BCM)
#  ─────────────────────────────────────────────────
#   HC-SR04 TRIG     │  GPIO 23
#   HC-SR04 ECHO     │  GPIO 24  (usar divisor de tensão!)
#   LED Verde        │  GPIO 17  (resistor 220Ω)
#   LED Amarelo      │  GPIO 27  (resistor 220Ω)
#   LED Vermelho     │  GPIO 22  (resistor 220Ω)
#  ─────────────────────────────────────────────────
#
#  LÓGICA:
#   >= 30 cm          → LED Verde ON   → "Motor ligado rodando"
#   20 a 29 cm        → LED Verde + Amarelo ON → "Atenção - objeto próximo"
#   <= 19 cm          → LED Vermelho ON (verde e amarelo OFF) → "ALERTA - muito próximo"
#   Volta p/ >= 21 cm → Desliga vermelho, acende verde novamente
#
#  ATENÇÃO: O pino ECHO do HC-SR04 opera em 5V.
#  Use um divisor de tensão (resistores 1kΩ + 2kΩ) para
#  reduzir a tensão para 3.3V antes de conectar ao GPIO.
# ============================================================

import RPi.GPIO as GPIO
import time
import os
import sys

# ── Configuração dos pinos (modo BCM) ──────────────────────
TRIG = 23       # Pino Trigger do HC-SR04
ECHO = 24       # Pino Echo do HC-SR04

LED_VERDE    = 17
LED_AMARELO  = 27
LED_VERMELHO = 22

# ── Constantes de distância (cm) ───────────────────────────
DIST_SEGURO      = 30   # >= 30 cm  → zona segura
DIST_ATENCAO     = 20   # 20–29 cm  → zona de atenção
DIST_PERIGO      = 19   # <= 19 cm  → zona de perigo
DIST_RECUPERACAO = 21   # >= 21 cm  → sai da zona de perigo

INTERVALO_LEITURA = 0.5  # segundos entre leituras


def configurar_gpio():
    """Inicializa os pinos GPIO."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Sensor ultrassônico
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)

    # LEDs
    GPIO.setup(LED_VERDE, GPIO.OUT)
    GPIO.setup(LED_AMARELO, GPIO.OUT)
    GPIO.setup(LED_VERMELHO, GPIO.OUT)

    # Desliga todos os LEDs no início
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_AMARELO, GPIO.LOW)
    GPIO.output(LED_VERMELHO, GPIO.LOW)

    # Aguarda estabilização do sensor
    print("⏳ Aguardando estabilização do sensor...")
    time.sleep(2)


def medir_distancia():
    """
    Realiza a medição de distância usando o HC-SR04.
    Retorna a distância em centímetros.
    """
    # Envia pulso de 10µs no TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microsegundos
    GPIO.output(TRIG, False)

    # Aguarda o início do pulso ECHO (timeout de 0.1s)
    tempo_inicio = time.time()
    timeout = tempo_inicio + 0.1

    while GPIO.input(ECHO) == 0:
        tempo_inicio = time.time()
        if tempo_inicio > timeout:
            return -1  # Timeout - sem resposta

    # Aguarda o fim do pulso ECHO
    tempo_fim = time.time()
    timeout = tempo_fim + 0.1

    while GPIO.input(ECHO) == 1:
        tempo_fim = time.time()
        if tempo_fim > timeout:
            return -1  # Timeout - pulso muito longo

    # Calcula a distância
    # Velocidade do som ≈ 34300 cm/s
    # Dividido por 2 (ida e volta)
    duracao = tempo_fim - tempo_inicio
    distancia = (duracao * 34300) / 2

    return round(distancia, 1)


def definir_leds(verde, amarelo, vermelho):
    """Liga/desliga os LEDs conforme os parâmetros booleanos."""
    GPIO.output(LED_VERDE, GPIO.HIGH if verde else GPIO.LOW)
    GPIO.output(LED_AMARELO, GPIO.HIGH if amarelo else GPIO.LOW)
    GPIO.output(LED_VERMELHO, GPIO.HIGH if vermelho else GPIO.LOW)


def limpar_terminal():
    """Limpa a tela do terminal."""
    os.system('clear')


def exibir_dashboard(distancia, estado, leds_status):
    """Exibe o dashboard no terminal com informações formatadas."""
    limpar_terminal()

    print("╔══════════════════════════════════════════════════╗")
    print("║     🤖  CONTROLE POR SENSOR ULTRASSÔNICO  🤖    ║")
    print("║            Raspberry Pi 4 - HC-SR04             ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║                                                  ║")

    # Distância com barra visual
    if distancia >= 0:
        barra_max = 30
        barra_len = min(int(distancia), barra_max)
        barra = "█" * barra_len + "░" * (barra_max - barra_len)
        print(f"║  📏 Distância: {distancia:6.1f} cm                     ║")
        print(f"║  [{barra}]  ║")
    else:
        print("║  📏 Distância: --- (erro de leitura)            ║")
        print("║  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  ║")

    print("║                                                  ║")
    print("╠══════════════════════════════════════════════════╣")

    # Status dos LEDs
    led_v = "🟢 ON " if leds_status[0] else "⚫ OFF"
    led_a = "🟡 ON " if leds_status[1] else "⚫ OFF"
    led_r = "🔴 ON " if leds_status[2] else "⚫ OFF"

    print(f"║  LED Verde    : {led_v}   (GPIO {LED_VERDE})            ║")
    print(f"║  LED Amarelo  : {led_a}   (GPIO {LED_AMARELO})            ║")
    print(f"║  LED Vermelho : {led_r}   (GPIO {LED_VERMELHO})            ║")

    print("║                                                  ║")
    print("╠══════════════════════════════════════════════════╣")

    # Estado do motor
    if estado == "SEGURO":
        print("║  ✅ MOTOR LIGADO RODANDO                        ║")
        print("║     Zona segura - operação normal                ║")
    elif estado == "ATENCAO":
        print("║  ⚠️  ATENÇÃO - OBJETO PRÓXIMO                    ║")
        print("║     Motor ligado - monitorando proximidade       ║")
    elif estado == "PERIGO":
        print("║  🛑 ALERTA - OBJETO MUITO PRÓXIMO!               ║")
        print("║     Motor em estado de alerta                    ║")
    else:
        print("║  ❓ Aguardando leitura...                        ║")
        print("║                                                  ║")

    print("║                                                  ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Faixas: ≥30cm=Verde │ 20-29cm=Amar. │ ≤19cm=Verm ║")
    print("║  Pressione Ctrl+C para encerrar                  ║")
    print("╚══════════════════════════════════════════════════╝")


def main():
    """Loop principal do programa."""

    configurar_gpio()

    # Estado anterior para controle de histerese
    em_perigo = False

    print("✅ Sistema iniciado! Monitorando distância...\n")
    time.sleep(1)

    try:
        while True:
            # ── Leitura do sensor ──
            distancia = medir_distancia()

            # Ignora leituras inválidas
            if distancia < 0 or distancia > 400:
                exibir_dashboard(-1, "ERRO", (False, False, False))
                time.sleep(INTERVALO_LEITURA)
                continue

            # ── Lógica de controle dos LEDs ──

            if em_perigo:
                # Estamos em estado de perigo (vermelho ligado)
                # Só sai quando distância >= 21 cm (histerese)
                if distancia >= DIST_RECUPERACAO:
                    # Saiu da zona de perigo → volta ao normal
                    em_perigo = False

                    if distancia >= DIST_SEGURO:
                        # Zona segura: só verde
                        definir_leds(verde=True, amarelo=False, vermelho=False)
                        exibir_dashboard(distancia, "SEGURO", (True, False, False))
                    else:
                        # Zona de atenção: verde + amarelo
                        definir_leds(verde=True, amarelo=True, vermelho=False)
                        exibir_dashboard(distancia, "ATENCAO", (True, True, False))
                else:
                    # Continua em perigo
                    definir_leds(verde=False, amarelo=False, vermelho=True)
                    exibir_dashboard(distancia, "PERIGO", (False, False, True))

            else:
                # Operação normal
                if distancia >= DIST_SEGURO:
                    # >= 30 cm → Zona segura: LED Verde ON
                    definir_leds(verde=True, amarelo=False, vermelho=False)
                    exibir_dashboard(distancia, "SEGURO", (True, False, False))

                elif distancia >= DIST_ATENCAO:
                    # 20 a 29 cm → Zona de atenção: Verde + Amarelo ON
                    definir_leds(verde=True, amarelo=True, vermelho=False)
                    exibir_dashboard(distancia, "ATENCAO", (True, True, False))

                else:
                    # <= 19 cm → Zona de perigo: só Vermelho ON
                    em_perigo = True
                    definir_leds(verde=False, amarelo=False, vermelho=True)
                    exibir_dashboard(distancia, "PERIGO", (False, False, True))

            time.sleep(INTERVALO_LEITURA)

    except KeyboardInterrupt:
        print("\n\n🛑 Programa encerrado pelo usuário.")

    finally:
        # Desliga todos os LEDs e limpa os GPIOs
        definir_leds(verde=False, amarelo=False, vermelho=False)
        GPIO.cleanup()
        print("✅ GPIOs limpos. Sistema desligado com segurança.\n")


if __name__ == "__main__":
    main()
