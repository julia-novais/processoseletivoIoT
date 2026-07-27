"""
Sistema de Monitoramento de Temperatura e Abertura de Porta
(Smart Cooler / Estufa) - ESP32 + MPU6050 + Botão
Firmware em MicroPython (sem funções bloqueantes longas no loop principal)
"""

from machine import Pin, I2C
import time

# ------------------------------------------------------------------
# Configuração de hardware
# ------------------------------------------------------------------
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B
TEMP_OUT_H = 0x41

BUTTON_PIN = 4
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21

# ------------------------------------------------------------------
# Parâmetros do sistema
# ------------------------------------------------------------------
LIMITE_TEMPO_X = 5000      # ms - tempo máximo com a porta aberta
LIMITE_VARIACAO_Y = 3.0    # °C - variação térmica tolerada
INTERVALO_LOOP_MS = 100    # ciclo de amostragem (não bloqueante)
WARMUP_MS = 800            # janela inicial em que a referência de temp. é
                           # continuamente recalibrada (evita capturar um
                           # valor "de fábrica" do sensor antes do teste
                           # aplicar a temperatura inicial esperada)

i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)

# Botão ligado ao 3V3 quando pressionado (porta fechada = 1),
# pull-down interno mantém o pino em 0 quando solto (porta aberta = 0)
btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)


def mpu_init():
    """Acorda o MPU6050 (sai do modo sleep)."""
    i2c.writeto_mem(MPU_ADDR, PWR_MGMT_1, bytes([0]))


def read_temp():
    """Lê a temperatura interna do MPU6050 em graus Celsius."""
    data = i2c.readfrom_mem(MPU_ADDR, TEMP_OUT_H, 2)
    raw = (data[0] << 8) | data[1]
    if raw > 32767:
        raw -= 65536
    return raw / 340.0 + 36.53


def is_door_closed():
    """Porta fechada quando o botão está pressionado (leitura = 1)."""
    return btn.value() == 1


def main():
    mpu_init()
    time.sleep_ms(100)
    print("Sistema de Monitoramento Inicializado")

    temp_referencia = read_temp()
    porta_aberta_desde = None
    alarme_porta_ativo = False
    alarme_termico_ativo = False

    inicio = time.ticks_ms()

    while True:
        porta_fechada = is_door_closed()
        temp_atual = read_temp()
        agora = time.ticks_ms()
        em_warmup = time.ticks_diff(agora, inicio) < WARMUP_MS

        # Durante o warm-up, a referência acompanha a leitura atual para
        # capturar o valor real definido pelo ambiente/teste antes de travar
        if em_warmup:
            temp_referencia = temp_atual

        # --- B. Lógica de tempo de porta aberta (Limite X) ---
        if not porta_fechada:
            if porta_aberta_desde is None:
                porta_aberta_desde = agora
            elif (not alarme_porta_ativo and
                  time.ticks_diff(agora, porta_aberta_desde) >= LIMITE_TEMPO_X):
                alarme_porta_ativo = True
                print("ALERTA: Porta aberta por muito tempo!")
        else:
            porta_aberta_desde = None

        # --- C. Lógica de elevação térmica (Variação Y) ---
        delta_t = abs(temp_atual - temp_referencia)
        if not em_warmup and delta_t >= LIMITE_VARIACAO_Y and not alarme_termico_ativo:
            alarme_termico_ativo = True
            print("ALERTA: Degradacao termica detectada!")

        # --- D. Lógica de normalização e restauração de estado ---
        if (not em_warmup and porta_fechada and delta_t < LIMITE_VARIACAO_Y and
                (alarme_porta_ativo or alarme_termico_ativo)):
            alarme_porta_ativo = False
            alarme_termico_ativo = False
            porta_aberta_desde = None
            temp_referencia = temp_atual
            print("Status: Sistema Normalizado.")

        time.sleep_ms(INTERVALO_LOOP_MS)


main()