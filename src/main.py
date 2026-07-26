import time
from machine import I2C, Pin

# --- PARAMETRIZAÇÕES DO DESAFIO ---
LIMITE_TEMPO_X = 5000     # Limite de tempo de porta aberta (5000ms = 5s)
LIMITE_VARIACAO_Y = 3.0   # Limite da variação de temperatura Delta T (3.0 °C)

# --- PINAGEM DO HARDWARE ---
PIN_BOTAO = 4            # Pino do botão btn1 (GPIO 4)
I2C_SDA_PIN = 21         # Pino SDA do I2C (GPIO 21)
I2C_SCL_PIN = 22         # Pino SCL do I2C (GPIO 22)

# --- REGISTRADORES DO MPU6050 ---
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
TEMP_OUT_H = 0x41

def init_mpu6050(i2c):
    try:
        i2c.writeto_mem(MPU6050_ADDR, PWR_MGMT_1, b'\x00')
    except Exception:
        pass

def read_temperature(i2c):
    try:
        data = i2c.readfrom_mem(MPU6050_ADDR, TEMP_OUT_H, 2)
        raw_temp = (data[0] << 8) | data[1]
        if raw_temp > 32767:
            raw_temp -= 65536
        return (raw_temp / 340.0) + 36.53
    except Exception:
        return 25.0

def main():
    # Configuração dos periféricos
    btn = Pin(PIN_BOTAO, Pin.IN, Pin.PULL_UP)
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
    init_mpu6050(i2c)

    # A. Inicialização do Sistema
    print("Sistema de Monitoramento Inicializado")

    # A temperatura de referência é fixada no momento da inicialização com a porta fechada
    temp_referencia = read_temperature(i2c)
    carimbo_tempo_abertura = None

    alerta_porta_ativo = False
    alerta_temp_ativo = False
    estava_em_alerta = False

    while True:
        # PULL_UP: quando o botão está solto no Wokwi, btn.value() == 1 (Porta Aberta / 0)
        # Quando o botão está pressionado, btn.value() == 0 (Porta Fechada / 1)
        estado_porta = 1 if btn.value() == 0 else 0
        temp_atual = read_temperature(i2c)
        agora = time.ticks_ms()

        # B. Lógica de Tempo de Porta Aberta
        if estado_porta == 0:  # Porta Aberta
            if carimbo_tempo_abertura is None:
                carimbo_tempo_abertura = agora

            tempo_decorrido = time.ticks_diff(agora, carimbo_tempo_abertura)
            if tempo_decorrido >= LIMITE_TEMPO_X:
                if not alerta_porta_ativo:
                    print("ALERTA: Porta aberta por muito tempo!")
                    alerta_porta_ativo = True
                    estava_em_alerta = True
        else:  # Porta Fechada
            carimbo_tempo_abertura = None
            alerta_porta_ativo = False

        # C. Lógica de Elevação Térmica e Degradação (ΔT)
        delta_t = temp_atual - temp_referencia
        if delta_t >= LIMITE_VARIACAO_Y:
            if not alerta_temp_ativo:
                print("ALERTA: Degradacao termica detectada!")
                alerta_temp_ativo = True
                estava_em_alerta = True
        else:
            alerta_temp_ativo = False

        # D. Lógica de Normalização
        if estado_porta == 1 and delta_t < LIMITE_VARIACAO_Y:
            if estava_em_alerta:
                print("Status: Sistema Normalizado.")
                estava_em_alerta = False

        time.sleep(0.1)

if __name__ == "__main__":
    main()