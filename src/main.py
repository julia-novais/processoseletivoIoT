import machine
import time

# ==========================================
# 1. PARAMETRIZAÇÃO DO SISTEMA
LIMITE_TEMPO_X = 5000       # Retornado para 5000ms para alinhar com o CI
LIMITE_VARIACAO_Y = 3.0     # Mantém a variação de temperatura em 3 graus

# ==========================================
# 2. CONFIGURAÇÃO DE HARDWARE
# ==========================================
# Configuração PULL_DOWN: Garante que Pressionado = 1 e Solto = 0
pino_porta = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Configuração I2C para o MPU6050 (Pinos 21 SDA, 22 SCL)
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))

# Inicializa/Acorda o MPU6050 (Escreve 0 no registrador de Power Management)
try:
    i2c.writeto_mem(0x68, 0x6B, b'\x00')
except OSError:
    print("Erro: MPU6050 não encontrado no barramento I2C.")

def ler_temperatura():
    """Lê os registradores de temperatura do MPU6050 e converte para Celsius"""
    try:
        raw = i2c.readfrom_mem(0x68, 0x41, 2)
        val = raw[0] << 8 | raw[1]
        # Converte para inteiro com sinal (16 bits)
        if val > 32767:
            val -= 65536
        # Fórmula do datasheet do MPU6050
        return (val / 340.0) + 36.53
    except OSError:
        return 0.0

# ==========================================
# 3. INICIALIZAÇÃO
# ==========================================
print("Sistema de Monitoramento Inicializado")

# Variáveis de Estado
temp_referencia = ler_temperatura()
tempo_inicio_abertura = 0

alarme_porta = False
alarme_temp = False
sistema_normal = True

# ==========================================
# 4. LAÇO PRINCIPAL (FIRMWARE)
# ==========================================
while True:
    # --- Leituras de Sensores ---
    estado_porta = pino_porta.value() # Agora: 0 = Aberto, 1 = Fechado
    porta_aberta = (estado_porta == 0)
    
    temp_atual = ler_temperatura()
    delta_t = temp_atual - temp_referencia
    
    # --- Lógica B: Tempo de Porta Aberta ---
    if porta_aberta:
        if tempo_inicio_abertura == 0:
            tempo_inicio_abertura = time.ticks_ms()
        else:
            tempo_decorrido = time.ticks_diff(time.ticks_ms(), tempo_inicio_abertura)
            if tempo_decorrido >= LIMITE_TEMPO_X and not alarme_porta:
                alarme_porta = True
                print("ALERTA: Porta aberta por muito tempo!")
    else:
        tempo_inicio_abertura = 0 # Reseta o cronômetro se a porta fechar

    # --- Lógica C: Elevação Térmica ---
    if delta_t >= LIMITE_VARIACAO_Y:
        if not alarme_temp:
            alarme_temp = True
            print("ALERTA: Degradacao termica detectada!")
            
    # --- Atualização do Status Geral ---
    if alarme_porta or alarme_temp:
        sistema_normal = False

    # --- Lógica D: Normalização ---
    if not sistema_normal:
        if not porta_aberta and delta_t < LIMITE_VARIACAO_Y:
            alarme_porta = False
            alarme_temp = False
            sistema_normal = True
            
            # Ao normalizar com a porta fechada, atualizamos a referência base
            temp_referencia = temp_atual 
            
            print("Status: Sistema Normalizado.")
            
    # Reduzido para 10ms (non-blocking) para não perder o timing do Wokwi CI
    time.sleep_ms(10)