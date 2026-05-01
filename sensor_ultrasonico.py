#!/usr/bin/env python3
# ============================================================
#  Controle de LEDs com Sensor Ultrassônico HC-SR04
#  Plataforma: Raspberry Pi 4
# ============================================================
#
#  CONEXÕES:
#  ─────────────────────────────────────────────────
#   Componente         │  Pino GPIO (BCM)
#  ─────────────────────────────────────────────────
#   HC-SR04 DIR TRIG   │  GPIO 23
#   HC-SR04 DIR ECHO   │  GPIO 24
#   HC-SR04 ESQ TRIG   │  GPIO 05
#   HC-SR04 ESQ ECHO   │  GPIO 06
#   LED Verde          │  GPIO 17
#   LED Amarelo        │  GPIO 27
#   LED Vermelho       │  GPIO 22
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
# Sensor Direita (monitorando a direita)
TRIG_DIR = 23
ECHO_DIR = 24

# Sensor Esquerda (monitorando a esquerda)
TRIG_ESQ = 5
ECHO_ESQ = 6

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

    # Sensor Direita
    GPIO.setup(TRIG_DIR, GPIO.OUT)
    GPIO.setup(ECHO_DIR, GPIO.IN)
    GPIO.output(TRIG_DIR, False)

    # Sensor Esquerda
    GPIO.setup(TRIG_ESQ, GPIO.OUT)
    GPIO.setup(ECHO_ESQ, GPIO.IN)
    GPIO.output(TRIG_ESQ, False)

    # LEDs
    GPIO.setup(LED_VERDE, GPIO.OUT)
    GPIO.setup(LED_AMARELO, GPIO.OUT)
    GPIO.setup(LED_VERMELHO, GPIO.OUT)

    # Desliga todos os LEDs no início
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_AMARELO, GPIO.LOW)
    GPIO.output(LED_VERMELHO, GPIO.LOW)

    # Aguarda estabilização dos sensores
    print("⏳ Aguardando estabilização dos sensores...")
    time.sleep(2)


def medir_distancia(trig_pin, echo_pin):
    """
    Realiza a medição de distância usando o HC-SR04.
    Retorna a distância em centímetros.
    """
    # Envia pulso de 10µs no TRIG
    GPIO.output(trig_pin, True)
    time.sleep(0.00001)  # 10 microsegundos
    GPIO.output(trig_pin, False)

    # Aguarda o início do pulso ECHO (timeout de 0.1s)
    tempo_inicio = time.time()
    timeout = tempo_inicio + 0.1

    while GPIO.input(echo_pin) == 0:
        tempo_inicio = time.time()
        if tempo_inicio > timeout:
            return -1  # Timeout - sem resposta

    # Aguarda o fim do pulso ECHO
    tempo_fim = time.time()
    timeout = tempo_fim + 0.1

    while GPIO.input(echo_pin) == 1:
        tempo_fim = time.time()
        if tempo_fim > timeout:
            return -1  # Timeout - pulso muito longo

    # Calcula a distância
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


def exibir_dashboard(dist_dir, dist_esq, estado, leds_status):
    """Exibe o dashboard no terminal com informações formatadas."""
    limpar_terminal()

    print("╔══════════════════════════════════════════════════╗")
    print("║     🤖  CARRINHO AUTÔNOMO - DUAL SENSOR  🤖     ║")
    print("║            Raspberry Pi 4 - HC-SR04             ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║                                                  ║")

    # Função auxiliar para barra visual
    def gerar_barra(dist):
        if dist < 0: return "[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]"
        barra_max = 30
        barra_len = min(int(dist), barra_max)
        return "[" + "█" * barra_len + "░" * (barra_max - barra_len) + "]"

    # Sensor Direita
    val_dir = f"{dist_dir:6.1f} cm" if dist_dir >= 0 else "--- (erro) "
    print(f"║  👉 SENSOR DIREITO : {val_dir}                  ║")
    print(f"║     {gerar_barra(dist_dir)}  ║")

    # Sensor Esquerda
    val_esq = f"{dist_esq:6.1f} cm" if dist_esq >= 0 else "--- (erro) "
    print(f"║  👈 SENSOR ESQUERDO: {val_esq}                  ║")
    print(f"║     {gerar_barra(dist_esq)}  ║")

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
            # ── Leitura dos sensores ──
            dist_dir = medir_distancia(TRIG_DIR, ECHO_DIR)
            dist_esq = medir_distancia(TRIG_ESQ, ECHO_ESQ)

            # Determina a menor distância (segurança em primeiro lugar)
            # Filtra valores negativos (erros) para o cálculo do mínimo
            leituras_validas = [d for d in [dist_dir, dist_esq] if 0 <= d <= 400]
            
            if not leituras_validas:
                distancia = -1
            else:
                distancia = min(leituras_validas)

            # Ignora se ambos derem erro
            if distancia < 0:
                exibir_dashboard(dist_dir, dist_esq, "ERRO", (False, False, False))
                time.sleep(INTERVALO_LEITURA)
                continue

            # ── Lógica de controle dos LEDs (baseada na menor distância) ──

            if em_perigo:
                # Estamos em estado de perigo (vermelho ligado)
                # Só sai quando a menor distância >= 21 cm (histerese)
                if distancia >= DIST_RECUPERACAO:
                    em_perigo = False

                    if distancia >= DIST_SEGURO:
                        definir_leds(verde=True, amarelo=False, vermelho=False)
                        exibir_dashboard(dist_dir, dist_esq, "SEGURO", (True, False, False))
                    else:
                        definir_leds(verde=True, amarelo=True, vermelho=False)
                        exibir_dashboard(dist_dir, dist_esq, "ATENCAO", (True, True, False))
                else:
                    definir_leds(verde=False, amarelo=False, vermelho=True)
                    exibir_dashboard(dist_dir, dist_esq, "PERIGO", (False, False, True))

            else:
                # Operação normal
                if distancia >= DIST_SEGURO:
                    definir_leds(verde=True, amarelo=False, vermelho=False)
                    exibir_dashboard(dist_dir, dist_esq, "SEGURO", (True, False, False))

                elif distancia >= DIST_ATENCAO:
                    definir_leds(verde=True, amarelo=True, vermelho=False)
                    exibir_dashboard(dist_dir, dist_esq, "ATENCAO", (True, True, False))

                else:
                    em_perigo = True
                    definir_leds(verde=False, amarelo=False, vermelho=True)
                    exibir_dashboard(dist_dir, dist_esq, "PERIGO", (False, False, True))

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
