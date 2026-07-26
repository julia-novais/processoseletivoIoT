import time
from machine import I2C, Pin

# ---------------- PARAMETRIZAÇÕES DO DESAFIO ----------------
LIMITE_TEMPO_X = 5000        # ms - tempo máximo de porta aberta (5s)
LIMITE_VARIACAO_Y = 3.0      # °C - variação máxima de temperatura tolerada
DEBOUNCE_NORMALIZACAO = 600  # ms - tempo de estabilidade para normalizar

# ---------------- HARDWARE E CONFIGURAÇÃO ----------------
PIN_BOTAO = 4
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22

# Botão ligado ao GND: PULL_UP (Fechado/Pressionado = 0, Aberto/Solto = 1)
btn1 = Pin(PIN_BOTAO, Pin.IN, Pin.PULL_UP)

# MPU6050 via I2C
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
TEMP_OUT_H = 0x41
TEMP_SENSITIVITY = 340.0
TEMP_OFFSET = 36.53

def mpu_init():
    try:
        i2c.writeto_mem(MPU6050_ADDR, PWR_MGMT_1, b'\x00')
    except Exception:
        pass

def ler_temperatura():
    try:
        dados = i2c.readfrom_mem(MPU6050_ADDR, TEMP_OUT_H, 2)
        bruto = (dados[0] << 8) | dados[1]
        if bruto > 32767:
            bruto -= 65536
        return (bruto / TEMP_SENSITIVITY) + TEMP_OFFSET
    except Exception:
        return 20.0

def main():
    mpu_init()

    # Mensagem inicial para a esteira de CI do Wokwi
    print("Sistema de Monitoramento Inicializado")

    porta_aberta_desde = None
    temp_referencia = None
    em_alarme = False
    alarme_porta_disparado = False
    alarme_temp_disparado = False
    condicoes_seguras_desde = None
    temp_atual = None

    while True:
        # PULL_UP: Quando o botão está pressionado, ele fecha no GND e o pino lê 0
        porta_fechada = (btn1.value() == 0)

        # Leitura da Temperatura
        try:
            temp_atual = ler_temperatura()
        except Exception:
            if temp_atual is None:
                time.sleep_ms(50)
                continue

        # Captura baseline inicial ou pós-normalização
        if temp_referencia is None and porta_fechada and not em_alarme:
            temp_referencia = temp_atual

        delta_t = (temp_atual - temp_referencia) if temp_referencia is not None else 0.0

        # ---- Lógica A: Porta Aberta por Tempo Limite X ----
        if not porta_fechada:
            if porta_aberta_desde is None:
                porta_aberta_desde = time.ticks_ms()
            tempo_aberta = time.ticks_diff(time.ticks_ms(), porta_aberta_desde)
            if tempo_aberta >= LIMITE_TEMPO_X and not alarme_porta_disparado:
                alarme_porta_disparado = True
                em_alarme = True
                print("ALERTA: Porta aberta por muito tempo!")
        else:
            porta_aberta_desde = None

        # ---- Lógica B: Elevação Térmica Delta T >= Y ----
        if delta_t >= LIMITE_VARIACAO_Y and not alarme_temp_disparado:
            alarme_temp_disparado = True
            em_alarme = True
            print("ALERTA: Degradacao termica detectada!")

        # ---- Lógica C: Normalização com Debounce ----
        condicoes_seguras = porta_fechada and (delta_t < LIMITE_VARIACAO_Y)
        if em_alarme and condicoes_seguras:
            if condicoes_seguras_desde is None:
                condicoes_seguras_desde = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), condicoes_seguras_desde) >= DEBOUNCE_NORMALIZACAO:
                em_alarme = False
                alarme_porta_disparado = False
                alarme_temp_disparado = False
                temp_referencia = temp_atual
                condicoes_seguras_desde = None
                print("Status: Sistema Normalizado.")
        else:
            condicoes_seguras_desde = None

        time.sleep_ms(50)

if __name__ == "__main__":
    main()