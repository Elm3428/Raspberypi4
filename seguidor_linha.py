# -*- coding: utf-8 -*-
"""
=========================================================
  SEGUIDOR DE LINHA - Raspberry Pi 4
  Dashboard de Simulacao para Thonny
=========================================================

  Descricao:
    Simulador interativo do carrinho seguidor de linha.
    Permite testar toda a logica de sensores, LEDs e motores
    diretamente no terminal do Thonny, sem hardware real.

  Controles (digite no terminal quando solicitado):
    1 = Ambos na linha (frente)
    2 = So esquerdo na linha (vira esquerda)
    3 = So direito na linha (vira direita)
    4 = Nenhum na linha (parado/procurando)
    5 = Obstaculo detectado (ultrassonico)
    6 = Remover obstaculo
    0 = Sair da simulacao

  Autor: Projeto Antigravity
  Data: Abril/2026
=========================================================
"""

import time
import os
import platform
import random
import sys

# Forcar UTF-8 no stdout do Windows para suportar caracteres especiais
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# =========================================================
#  CONFIGURACAO DOS PINOS GPIO (Raspberry Pi 4)
# =========================================================
# Estes sao os pinos sugeridos. Ajuste conforme sua montagem.

PINOS = {
    # Sensores de Linha (IR) - Entrada digital
    "SENSOR_ESQ":    17,   # GPIO 17 (Pino fisico 11)
    "SENSOR_DIR":    27,   # GPIO 27 (Pino fisico 13)

    # Sensor Ultrassonico HC-SR04
    "ULTRA_TRIG":    23,   # GPIO 23 (Pino fisico 16)
    "ULTRA_ECHO":    24,   # GPIO 24 (Pino fisico 18)

    # LEDs indicadores
    "LED_VERDE":     25,   # GPIO 25 (Pino fisico 22)
    "LED_VERMELHO":  8,    # GPIO 8  (Pino fisico 24)

    # Motor Esquerdo (via Ponte H L298N / L293D)
    "MOTOR_ESQ_IN1": 5,    # GPIO 5  (Pino fisico 29)
    "MOTOR_ESQ_IN2": 6,    # GPIO 6  (Pino fisico 31)
    "MOTOR_ESQ_EN":  12,   # GPIO 12 (Pino fisico 32) - PWM

    # Motor Direito (via Ponte H L298N / L293D)
    "MOTOR_DIR_IN1": 13,   # GPIO 13 (Pino fisico 33)
    "MOTOR_DIR_IN2": 19,   # GPIO 19 (Pino fisico 35)
    "MOTOR_DIR_EN":  18,   # GPIO 18 (Pino fisico 12) - PWM
}

# Distancia minima para considerar obstaculo (em cm)
DISTANCIA_OBSTACULO = 15

# =========================================================
#  DETECCAO DE AMBIENTE (Raspberry Pi vs PC/Thonny)
# =========================================================
SIMULANDO = True  # Comeca como True; tenta importar GPIO

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Configurar pinos de entrada (sensores)
    GPIO.setup(PINOS["SENSOR_ESQ"], GPIO.IN)
    GPIO.setup(PINOS["SENSOR_DIR"], GPIO.IN)
    GPIO.setup(PINOS["ULTRA_ECHO"], GPIO.IN)

    # Configurar pinos de saida (LEDs, motores, trigger)
    for pino in ["LED_VERDE", "LED_VERMELHO",
                  "MOTOR_ESQ_IN1", "MOTOR_ESQ_IN2",
                  "MOTOR_DIR_IN1", "MOTOR_DIR_IN2",
                  "ULTRA_TRIG"]:
        GPIO.setup(PINOS[pino], GPIO.OUT)
        GPIO.output(PINOS[pino], GPIO.LOW)

    # PWM para controle de velocidade dos motores
    pwm_esq = GPIO.PWM(PINOS["MOTOR_ESQ_EN"], 1000)
    pwm_dir = GPIO.PWM(PINOS["MOTOR_DIR_EN"], 1000)
    pwm_esq.start(0)
    pwm_dir.start(0)

    SIMULANDO = False
    print("[HW] GPIO da Raspberry Pi detectado com sucesso!")

except (ImportError, RuntimeError):
    SIMULANDO = True
    print("[SIM] Modo de SIMULACAO ativo (sem GPIO detectado).")
    print("[SIM] Use os comandos numericos para testar cenarios.")
    print()
    time.sleep(1)


# =========================================================
#  ESTADO GLOBAL DO CARRINHO
# =========================================================
class EstadoCarrinho:
    """Armazena todo o estado atual do carrinho para exibicao."""
    def __init__(self):
        self.sensor_esq = 0       # 0 = branco, 1 = linha preta
        self.sensor_dir = 0       # 0 = branco, 1 = linha preta
        self.distancia_cm = 99.0  # Distancia do ultrassonico
        self.obstaculo = False
        self.led_verde = False
        self.led_vermelho = False
        self.acao_motores = "PARADO"
        self.velocidade = 0       # 0-100%
        self.rodando = True
        self.cenario_atual = "Aguardando..."

estado = EstadoCarrinho()


# =========================================================
#  FUNCOES DE HARDWARE / SIMULACAO
# =========================================================

def ler_sensores_linha():
    """Le os sensores IR de linha. Retorna (esquerdo, direito)."""
    if SIMULANDO:
        return estado.sensor_esq, estado.sensor_dir
    else:
        esq = GPIO.input(PINOS["SENSOR_ESQ"])
        dir_ = GPIO.input(PINOS["SENSOR_DIR"])
        return esq, dir_


def ler_distancia():
    """Le a distancia do sensor ultrassonico HC-SR04 em cm."""
    if SIMULANDO:
        return estado.distancia_cm
    else:
        # Envia pulso de trigger
        GPIO.output(PINOS["ULTRA_TRIG"], True)
        time.sleep(0.00001)  # 10 microsegundos
        GPIO.output(PINOS["ULTRA_TRIG"], False)

        inicio = time.time()
        fim = time.time()
        timeout = inicio + 0.04  # timeout de 40ms

        while GPIO.input(PINOS["ULTRA_ECHO"]) == 0:
            inicio = time.time()
            if inicio > timeout:
                return 999.0

        while GPIO.input(PINOS["ULTRA_ECHO"]) == 1:
            fim = time.time()
            if fim > timeout:
                return 999.0

        duracao = fim - inicio
        distancia = (duracao * 34300) / 2  # velocidade do som
        return round(distancia, 1)


def controlar_led(led, ligar):
    """Liga ou desliga um LED."""
    if led == "verde":
        estado.led_verde = ligar
        if not SIMULANDO:
            GPIO.output(PINOS["LED_VERDE"], GPIO.HIGH if ligar else GPIO.LOW)
    elif led == "vermelho":
        estado.led_vermelho = ligar
        if not SIMULANDO:
            GPIO.output(PINOS["LED_VERMELHO"], GPIO.HIGH if ligar else GPIO.LOW)


def controlar_motores(acao, velocidade=70):
    """
    Controla os motores via Ponte H.
    Acoes: 'frente', 'esquerda', 'direita', 'parar', 're'
    """
    estado.velocidade = velocidade

    if acao == "frente":
        estado.acao_motores = ">>> EM FRENTE <<<"
        if not SIMULANDO:
            GPIO.output(PINOS["MOTOR_ESQ_IN1"], GPIO.HIGH)
            GPIO.output(PINOS["MOTOR_ESQ_IN2"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN1"], GPIO.HIGH)
            GPIO.output(PINOS["MOTOR_DIR_IN2"], GPIO.LOW)
            pwm_esq.ChangeDutyCycle(velocidade)
            pwm_dir.ChangeDutyCycle(velocidade)

    elif acao == "esquerda":
        estado.acao_motores = "<<< VIRANDO ESQUERDA"
        if not SIMULANDO:
            GPIO.output(PINOS["MOTOR_ESQ_IN1"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_ESQ_IN2"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN1"], GPIO.HIGH)
            GPIO.output(PINOS["MOTOR_DIR_IN2"], GPIO.LOW)
            pwm_esq.ChangeDutyCycle(0)
            pwm_dir.ChangeDutyCycle(velocidade)

    elif acao == "direita":
        estado.acao_motores = "VIRANDO DIREITA >>>"
        if not SIMULANDO:
            GPIO.output(PINOS["MOTOR_ESQ_IN1"], GPIO.HIGH)
            GPIO.output(PINOS["MOTOR_ESQ_IN2"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN1"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN2"], GPIO.LOW)
            pwm_esq.ChangeDutyCycle(velocidade)
            pwm_dir.ChangeDutyCycle(0)

    elif acao == "re":
        estado.acao_motores = "<<< MARCHA RE >>>"
        if not SIMULANDO:
            GPIO.output(PINOS["MOTOR_ESQ_IN1"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_ESQ_IN2"], GPIO.HIGH)
            GPIO.output(PINOS["MOTOR_DIR_IN1"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN2"], GPIO.HIGH)
            pwm_esq.ChangeDutyCycle(velocidade)
            pwm_dir.ChangeDutyCycle(velocidade)

    elif acao == "parar":
        estado.acao_motores = "--- PARADO ---"
        estado.velocidade = 0
        if not SIMULANDO:
            GPIO.output(PINOS["MOTOR_ESQ_IN1"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_ESQ_IN2"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN1"], GPIO.LOW)
            GPIO.output(PINOS["MOTOR_DIR_IN2"], GPIO.LOW)
            pwm_esq.ChangeDutyCycle(0)
            pwm_dir.ChangeDutyCycle(0)


# =========================================================
#  DASHBOARD NO TERMINAL
# =========================================================

def barra_velocidade(vel):
    """Cria uma barra visual da velocidade."""
    blocos = int(vel / 5)  # 20 blocos no total
    preenchido = "#" * blocos
    vazio = "-" * (20 - blocos)
    return preenchido + vazio


def exibir_status():
    """
    Limpa o terminal e exibe o painel de status completo.
    Atualiza como um 'dashboard fixo' no Thonny.
    """
    # Limpar terminal (compativel com Thonny)
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

    # Determinar status dos sensores para exibicao
    txt_esq = "## LINHA " if estado.sensor_esq else ".. BRANCO"
    txt_dir = "## LINHA " if estado.sensor_dir else ".. BRANCO"

    # Status de distancia
    dist = estado.distancia_cm
    if dist < DISTANCIA_OBSTACULO:
        alerta_dist = "[!!] OBSTACULO DETECTADO!"
    elif dist < 30:
        alerta_dist = "[!]  Objeto proximo"
    else:
        alerta_dist = "[OK] Caminho livre"

    # Indicador de LED visual
    led_v = "[*ACESO*] " if estado.led_verde else "[_apagado]"
    led_r = "[*ACESO*] " if estado.led_vermelho else "[_apagado]"

    # Modo de operacao
    if SIMULANDO:
        modo = "SIMULACAO (Thonny/PC)"
    else:
        modo = "HARDWARE REAL (RPi 4)"

    # Montar o painel
    print("+" + "=" * 51 + "+")
    print("|    SEGUIDOR DE LINHA - DASHBOARD - RPi 4         |")
    print("+" + "=" * 51 + "+")
    print("|  Modo: {:<42s}|".format(modo))
    print("+" + "-" * 51 + "+")
    print("|                                                   |")
    print("|  [SENSORES DE LINHA (IR)]                         |")
    print("|  +-------------------+-------------------+        |")
    print("|  | Esquerdo: {:<8s}| Direito:  {:<8s}|        |".format(txt_esq, txt_dir))
    print("|  +-------------------+-------------------+        |")
    print("|                                                   |")
    print("|  [SENSOR ULTRASSONICO]                            |")
    print("|  Distancia: {:>6.1f} cm                             |".format(dist))
    print("|  Status:    {:<30s}       |".format(alerta_dist))
    print("|                                                   |")
    print("+" + "-" * 51 + "+")
    print("|                                                   |")
    print("|  [LEDS INDICADORES]                               |")
    print("|  +----------------------+----------------------+  |")
    print("|  | Verde:  {:<13s}| Vermelho: {:<11s}|  |".format(led_v, led_r))
    print("|  +----------------------+----------------------+  |")
    print("|                                                   |")
    print("|  [MOTORES]                                        |")
    print("|  Acao:       {:<30s}     |".format(estado.acao_motores))
    print("|  Velocidade: [{}] {:>3d}%  |".format(barra_velocidade(estado.velocidade), estado.velocidade))
    print("|                                                   |")
    print("+" + "-" * 51 + "+")
    print("|  Cenario: {:<40s}|".format(estado.cenario_atual))
    print("+" + "=" * 51 + "+")

    if SIMULANDO:
        print()
        print("  COMANDOS DE TESTE:")
        print("  +-----------------------------------------------+")
        print("  | 1 = Ambos na linha (frente)                   |")
        print("  | 2 = So esquerdo na linha (vira esquerda)      |")
        print("  | 3 = So direito na linha (vira direita)        |")
        print("  | 4 = Nenhum na linha (parado/procurando)       |")
        print("  | 5 = Simular obstaculo proximo                 |")
        print("  | 6 = Remover obstaculo                         |")
        print("  | 0 = Encerrar simulacao                        |")
        print("  +-----------------------------------------------+")


# =========================================================
#  LOGICA PRINCIPAL DO SEGUIDOR DE LINHA
# =========================================================

def processar_logica():
    """
    Logica de decisao do seguidor de linha.
    Le sensores e decide a acao dos motores e LEDs.
    """
    esq, dir_ = ler_sensores_linha()
    distancia = ler_distancia()

    estado.sensor_esq = esq
    estado.sensor_dir = dir_
    estado.distancia_cm = distancia
    estado.obstaculo = distancia < DISTANCIA_OBSTACULO

    # --- Prioridade 1: Obstaculo ---
    if estado.obstaculo:
        controlar_motores("parar")
        controlar_led("verde", False)
        controlar_led("vermelho", True)
        estado.cenario_atual = "[!!] OBSTACULO! Parada emergencia"
        return

    # --- Prioridade 2: Seguir a linha ---
    controlar_led("vermelho", False)

    if esq == 1 and dir_ == 1:
        # Ambos detectam linha -> seguir em frente
        controlar_motores("frente", 70)
        controlar_led("verde", True)
        estado.cenario_atual = "Seguindo em frente na linha"

    elif esq == 1 and dir_ == 0:
        # So o esquerdo detecta -> virar esquerda
        controlar_motores("esquerda", 50)
        controlar_led("verde", True)
        estado.cenario_atual = "Corrigindo: virando a esquerda"

    elif esq == 0 and dir_ == 1:
        # So o direito detecta -> virar direita
        controlar_motores("direita", 50)
        controlar_led("verde", True)
        estado.cenario_atual = "Corrigindo: virando a direita"

    elif esq == 0 and dir_ == 0:
        # Nenhum detecta linha -> perdeu a linha!
        controlar_motores("parar")
        controlar_led("verde", False)
        controlar_led("vermelho", True)
        estado.cenario_atual = "[!] Linha perdida! Procurando..."


def aplicar_cenario_simulado(comando):
    """Aplica um cenario de teste baseado no comando do usuario."""
    if comando == "1":
        estado.sensor_esq = 1
        estado.sensor_dir = 1
        estado.distancia_cm = random.uniform(25, 80)
    elif comando == "2":
        estado.sensor_esq = 1
        estado.sensor_dir = 0
        estado.distancia_cm = random.uniform(25, 80)
    elif comando == "3":
        estado.sensor_esq = 0
        estado.sensor_dir = 1
        estado.distancia_cm = random.uniform(25, 80)
    elif comando == "4":
        estado.sensor_esq = 0
        estado.sensor_dir = 0
        estado.distancia_cm = random.uniform(25, 80)
    elif comando == "5":
        estado.distancia_cm = random.uniform(3, 12)
    elif comando == "6":
        estado.distancia_cm = random.uniform(40, 80)
    elif comando == "0":
        estado.rodando = False


# =========================================================
#  MODO INTERATIVO (compativel 100% com Thonny)
# =========================================================

def modo_interativo_thonny():
    """
    Modo interativo otimizado para o Thonny.
    Usa um loop simples com input() entre as atualizacoes.
    """
    print()
    print("  Iniciando Simulador do Seguidor de Linha...")
    print("  Pressione ENTER sem digitar nada para manter o cenario atual.")
    time.sleep(2)

    ultimo_comando = "1"  # Comeca com ambos na linha

    while estado.rodando:
        # Aplicar o cenario atual
        aplicar_cenario_simulado(ultimo_comando)

        # Processar a logica do seguidor
        processar_logica()

        # Exibir o dashboard
        exibir_status()

        # Esperar comando do usuario
        try:
            cmd = input("\n  >> Comando (0-6) ou ENTER para repetir: ").strip()
            if cmd == "":
                # Manter cenario atual, adicionar variacao na distancia
                if not estado.obstaculo:
                    estado.distancia_cm = random.uniform(20, 80)
            elif cmd == "0":
                estado.rodando = False
            elif cmd in ("1", "2", "3", "4", "5", "6"):
                ultimo_comando = cmd
            else:
                print("  Comando invalido! Use 0-6.")
                time.sleep(0.5)

        except (EOFError, KeyboardInterrupt):
            estado.rodando = False

    # Desligar tudo ao sair
    controlar_motores("parar")
    controlar_led("verde", False)
    controlar_led("vermelho", False)

    print()
    print("  +=========================================+")
    print("  |   Simulacao encerrada com sucesso!       |")
    print("  |   Todos os motores e LEDs desligados.    |")
    print("  +=========================================+")
    print()

    if not SIMULANDO:
        pwm_esq.stop()
        pwm_dir.stop()
        GPIO.cleanup()
        print("  [HW] GPIO limpo com sucesso.")


# =========================================================
#  MODO AUTOMATICO (para hardware real na Raspberry Pi)
# =========================================================

def modo_automatico():
    """
    Modo automatico para execucao na Raspberry Pi com hardware real.
    O loop roda continuamente lendo os sensores reais.
    """
    print("  Modo AUTOMATICO iniciado (hardware real).")
    print("  Pressione Ctrl+C para parar.")
    print()
    time.sleep(1)

    try:
        while estado.rodando:
            processar_logica()
            exibir_status()
            time.sleep(0.5)  # Atualiza a cada 0.5 segundos

    except KeyboardInterrupt:
        estado.rodando = False

    # Desligar tudo
    controlar_motores("parar")
    controlar_led("verde", False)
    controlar_led("vermelho", False)
    pwm_esq.stop()
    pwm_dir.stop()
    GPIO.cleanup()

    print()
    print("  Encerrado. GPIO limpo.")


# =========================================================
#  PONTO DE ENTRADA
# =========================================================

def main():
    """Funcao principal - escolhe o modo de operacao."""
    print()
    print("  +=============================================+")
    print("  |   SEGUIDOR DE LINHA - Raspberry Pi 4        |")
    print("  |   Versao 1.0 | Projeto Antigravity          |")
    print("  +=============================================+")

    if SIMULANDO:
        print("  |   Modo: SIMULACAO (Thonny/PC)               |")
        print("  +=============================================+")
        print()
        print("  Mapa de Pinos GPIO configurado:")
        print("  +----------------------+------------------+")
        print("  | Componente           | GPIO (BCM)       |")
        print("  +----------------------+------------------+")
        print("  | Sensor Linha Esq.    | GPIO {:<12d}|".format(PINOS['SENSOR_ESQ']))
        print("  | Sensor Linha Dir.    | GPIO {:<12d}|".format(PINOS['SENSOR_DIR']))
        print("  | Ultrassonico TRIG    | GPIO {:<12d}|".format(PINOS['ULTRA_TRIG']))
        print("  | Ultrassonico ECHO    | GPIO {:<12d}|".format(PINOS['ULTRA_ECHO']))
        print("  | LED Verde            | GPIO {:<12d}|".format(PINOS['LED_VERDE']))
        print("  | LED Vermelho         | GPIO {:<12d}|".format(PINOS['LED_VERMELHO']))
        print("  | Motor Esq. IN1      | GPIO {:<12d}|".format(PINOS['MOTOR_ESQ_IN1']))
        print("  | Motor Esq. IN2      | GPIO {:<12d}|".format(PINOS['MOTOR_ESQ_IN2']))
        print("  | Motor Esq. PWM      | GPIO {:<12d}|".format(PINOS['MOTOR_ESQ_EN']))
        print("  | Motor Dir. IN1      | GPIO {:<12d}|".format(PINOS['MOTOR_DIR_IN1']))
        print("  | Motor Dir. IN2      | GPIO {:<12d}|".format(PINOS['MOTOR_DIR_IN2']))
        print("  | Motor Dir. PWM      | GPIO {:<12d}|".format(PINOS['MOTOR_DIR_EN']))
        print("  +----------------------+------------------+")
        print()
        modo_interativo_thonny()
    else:
        print("  |   Modo: HARDWARE REAL                       |")
        print("  +=============================================+")
        modo_automatico()


if __name__ == "__main__":
    main()
