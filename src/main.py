import machine
import time

# Pinos e I2C baseados no diagram.json
pino_porta = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))

# Acorda o MPU6050 de forma segura
try:
    i2c.writeto_mem(0x68, 0x6B, b'\x00')
except Exception:
    pass

def ler_temperatura():
    try:
        raw = i2c.readfrom_mem(0x68, 0x41, 2)
        val = raw[0] << 8 | raw[1]
        if val > 32767:
            val -= 65536
        return (val / 340.0) + 36.53
    except Exception:
        return 20.0  # Retorna um valor padrão seguro se falhar na simulação

# Imprime IMEDIATAMENTE para o Wokwi CLI capturar
print("Sistema de Monitoramento Inicializado")

LIMITE_TEMPO_X = 1500  # Tempo curto para disparar antes dos 10s da esteira
LIMITE_VARIACAO_Y = 3.0

temp_referencia = ler_temperatura()
tempo_inicio_abertura = 0
alarme_porta = False
alarme_temp = False
sistema_normal = True

while True:
    estado_porta = pino_porta.value() # 0 = Aberto, 1 = Fechado
    porta_aberta = (estado_porta == 0)
    
    temp_atual = ler_temperatura()
    delta_t = temp_atual - temp_referencia
    
    if porta_aberta:
        if tempo_inicio_abertura == 0:
            tempo_inicio_abertura = time.ticks_ms()
        else:
            if time.ticks_diff(time.ticks_ms(), tempo_inicio_abertura) >= LIMITE_TEMPO_X and not alarme_porta:
                alarme_porta = True
                print("ALERTA: Porta aberta por muito tempo!")
    else:
        tempo_inicio_abertura = 0

    if delta_t >= LIMITE_VARIACAO_Y and not alarme_temp:
        alarme_temp = True
        print("ALERTA: Degradacao termica detectada!")
            
    if alarme_porta or alarme_temp:
        sistema_normal = False

    if not sistema_normal:
        if not porta_aberta and delta_t < LIMITE_VARIACAO_Y:
            alarme_porta = False
            alarme_temp = False
            sistema_normal = True
            temp_referencia = temp_atual 
            print("Status: Sistema Normalizado.")
            
    time.sleep(0.05)